import contextlib
import io
import os
import pytest
import re

from dcicutils.qa_utils import override_environ, ignored, ControlledTime, MockFileSystem, local_attrs, raises_regexp
from unittest import mock
from .test_utils import shown_output
from .. import submission as submission_module
from ..base import PRODUCTION_SERVER
from ..exceptions import CGAPPermissionError
from ..submission import (
    SERVER_REGEXP, get_defaulted_institution, get_defaulted_project, do_any_uploads, do_uploads, show_upload_info,
    execute_prearranged_upload, get_section, get_user_record, ingestion_submission_item_url,
    resolve_server, resume_uploads, script_catch_errors, show_section, submit_any_ingestion,
    upload_file_to_uuid, upload_item_data, PROGRESS_CHECK_INTERVAL
)
from ..utils import FakeResponse


SOME_AUTH = ('my-key-id', 'good-secret')

SOME_BAD_AUTH = ('my-key-id', 'bad-secret')

SOME_BAD_RESULT = {'message': 'Houston, we have a problem.'}

SOME_BUNDLE_FILENAME = '/some-folder/foo.xls'

SOME_BUNDLE_FILENAME_FOLDER = os.path.dirname(SOME_BUNDLE_FILENAME)

SOME_ENV = 'some-env'

SOME_FILENAME = 'some-filename'

SOME_KEY_ID, SOME_SECRET = SOME_AUTH

SOME_INSTITUTION = '/institutions/hms-dbmi/'

SOME_OTHER_INSTITUTION = '/institutions/big-pharma/'

SOME_SERVER = 'http://localhost:7777'  # Dependencies force this to be out of alphabetical order

SOME_ORCHESTRATED_SERVERS = [
    'http://cgap-msa-something.amazonaws.com/',
    'http://cgap-devtest-something.amazonaws.com/'
]

SOME_KEYDICT = {'key': SOME_KEY_ID, 'secret': SOME_SECRET, 'server': SOME_SERVER}

SOME_OTHER_BUNDLE_FOLDER = '/some-other-folder/'

SOME_PROJECT = '/projects/12a92962-8265-4fc0-b2f8-cf14f05db58b/'  # Test Project from master inserts

SOME_UPLOAD_URL = 'some-url'

SOME_UPLOAD_CREDENTIALS = {
    'AccessKeyId': 'some-access-key',
    'SecretAccessKey': 'some-secret',
    'SessionToken': 'some-session-token',
    'upload_url': SOME_UPLOAD_URL,
}

SOME_UPLOAD_CREDENTIALS_RESULT = {
    '@graph': [
        {'upload_credentials': SOME_UPLOAD_CREDENTIALS}
    ]
}

SOME_UPLOAD_INFO = [
    {'uuid': '1234', 'filename': 'f1.fastq.gz'},
    {'uuid': '9876', 'filename': 'f2.fastq.gz'}
]

SOME_UPLOAD_INFO_RESULT = {
    'additional_data': {
        'upload_info': SOME_UPLOAD_INFO
    }
}

SOME_USER = "jdoe"

SOME_USER_HOMEDIR = os.path.join('/home', SOME_USER)

SOME_UUID = '123-4444-5678'

SOME_UUID_UPLOAD_URL = SOME_SERVER + "/ingestion-submissions/" + SOME_UUID

SOME_ENVIRON = {
    'USER': SOME_USER
}

SOME_ENVIRON_WITH_CREDS = {
    'USER': SOME_USER,
    'AWS_ACCESS_KEY_ID': 'some-access-key',
    'AWS_SECRET_ACCESS_KEY': 'some-secret',
    'AWS_SECURITY_TOKEN': 'some-session-token',
}


@contextlib.contextmanager
def script_dont_catch_errors():
    yield


def test_server_regexp():

    schemas = ['http', 'https']
    hosts = [
        'localhost',
        'localhost:5000',
        'fourfront-cgapfoo.what-ever.com',
        'cgap-foo.what-ever.com',
        'cgap.hms.harvard.edu',
        'foo.bar.cgap.hms.harvard.edu',
    ]
    final_slashes = ['/', '']  # 1 or 0 is good

    for schema in schemas:
        for host in hosts:
            for final_slash in final_slashes:
                url_to_check = schema + "://" + host + final_slash
                print("Trying", url_to_check, "expecting match...")
                assert SERVER_REGEXP.match(url_to_check)

    non_matches = [
        "ftp://localhost:8000",
        "ftp://localhost:80ab",
        "http://localhost.localnet",
        "http://foo.bar",
        "https://foo.bar",
    ]

    for non_match in non_matches:
        print("Trying", non_match, "expecting NO match...")
        assert not SERVER_REGEXP.match(non_match)


def test_resolve_server():

    def mocked_get_beanstalk_real_url(env):
        # We don't HAVE to be mocking this function, but it's slow so this will speed up testing. -kmp 4-Sep-2020
        if env == 'fourfront-cgap':
            return PRODUCTION_SERVER
        elif env in ['fourfront-cgapdev', 'fourfront-cgapwolf', 'fourfront-cgaptest']:
            return 'http://' + env + ".something.elasticbeanstalk.com"
        else:
            raise ValueError("Unexpected beanstalk env: %s" % env)

    with mock.patch.object(submission_module, "get_beanstalk_real_url", mocked_get_beanstalk_real_url):

        with pytest.raises(SyntaxError):
            resolve_server(env='something', server='something_else')

        with override_environ(SUBMIT_CGAP_DEFAULT_ENV=None):

            with mock.patch.object(submission_module, "DEFAULT_ENV", None):

                assert resolve_server(env=None, server=None) == PRODUCTION_SERVER

            with mock.patch.object(submission_module, "DEFAULT_ENV", 'fourfront-cgapdev'):

                cgap_dev_server = resolve_server(env=None, server=None)

                assert re.match("http://fourfront-cgapdev[.].*[.]elasticbeanstalk.com",
                                cgap_dev_server)

        with pytest.raises(SyntaxError):
            resolve_server(env='fourfront-cgapfoo', server=None)

        with pytest.raises(SyntaxError):
            resolve_server(env='cgapfoo', server=None)

        with pytest.raises(ValueError):
            resolve_server(server="http://foo.bar", env=None)

        assert re.match("http://fourfront-cgapdev[.].*[.]elasticbeanstalk.com",
                        resolve_server(env='fourfront-cgapdev', server=None))

        assert re.match("http://fourfront-cgapdev[.].*[.]elasticbeanstalk.com",
                        resolve_server(env='cgapdev', server=None))  # Omitting 'fourfront-' is allowed

        assert re.match("http://fourfront-cgapdev[.].*[.]elasticbeanstalk.com",
                        resolve_server(server=cgap_dev_server, env=None))  # Identity operation

        for orchestrated_server in SOME_ORCHESTRATED_SERVERS:
            assert re.match("http://cgap-[a-z]+.+amazonaws.com",
                            resolve_server(server=orchestrated_server, env=None))  # non-fourfront environments


def make_user_record(title='J Doe',
                     contact_email='jdoe@cgap.hms.harvard.edu',
                     **kwargs):
    user_record = {
        'title': title,
        'contact_email': contact_email,
    }
    user_record.update(kwargs)

    return user_record


def test_get_user_record():

    def make_mocked_get(auth_failure_code=400):
        def mocked_get(url, *, auth):
            ignored(url)
            if auth != SOME_AUTH:
                return FakeResponse(status_code=auth_failure_code, json={'Title': 'Not logged in.'})
            return FakeResponse(status_code=200, json={'title': 'J Doe', 'contact_email': 'jdoe@cgap.hms.harvard.edu'})
        return mocked_get

    with mock.patch("requests.get", return_value=FakeResponse(401, content='["not dictionary"]')):
        with pytest.raises(CGAPPermissionError):
            get_user_record(server="http://localhost:12345", auth=None)

    with mock.patch("requests.get", make_mocked_get(auth_failure_code=401)):
        with pytest.raises(CGAPPermissionError):
            get_user_record(server="http://localhost:12345", auth=None)

    with mock.patch("requests.get", make_mocked_get(auth_failure_code=403)):
        with pytest.raises(CGAPPermissionError):
            get_user_record(server="http://localhost:12345", auth=None)

    with mock.patch("requests.get", make_mocked_get()):
        get_user_record(server="http://localhost:12345", auth=SOME_AUTH)

    with mock.patch("requests.get", lambda *x, **y: FakeResponse(status_code=400)):
        with pytest.raises(Exception):  # Body is not JSON
            get_user_record(server="http://localhost:12345", auth=SOME_AUTH)


def test_get_defaulted_institution():

    assert get_defaulted_institution(institution=SOME_INSTITUTION, user_record='does-not-matter') == SOME_INSTITUTION
    assert get_defaulted_institution(institution='anything', user_record='does-not-matter') == 'anything'

    try:
        get_defaulted_institution(institution=None, user_record=make_user_record())
    except Exception as e:
        assert str(e).startswith("Your user profile has no institution")

    successful_result = get_defaulted_institution(institution=None,
                                                  user_record=make_user_record(
                                                      # this is the old-fashioned place for it - a decoy
                                                      institution={'@id': SOME_OTHER_INSTITUTION},
                                                      # this is the right place to find he info
                                                      user_institution={'@id': SOME_INSTITUTION}
                                                  ))

    print("successful_result=", successful_result)

    assert successful_result == SOME_INSTITUTION


def test_get_defaulted_project():

    assert get_defaulted_project(project=SOME_PROJECT, user_record='does-not-matter') == SOME_PROJECT
    assert get_defaulted_project(project='anything', user_record='does-not-matter') == 'anything'

    try:
        get_defaulted_project(project=None, user_record=make_user_record())
    except Exception as e:
        assert str(e).startswith("Your user profile declares no project")

    try:
        get_defaulted_project(project=None,
                              user_record=make_user_record(project_roles=[]))
    except Exception as e:
        assert str(e).startswith("Your user profile declares no project")
    else:
        raise AssertionError("Expected error was not raised.")  # pragma: no cover

    try:
        get_defaulted_project(project=None,
                              user_record=make_user_record(project_roles=[
                                  {"project": {"@id": "/projects/foo"}, "role": "developer"},
                                  {"project": {"@id": "/projects/bar"}, "role": "clinician"},
                                  {"project": {"@id": "/projects/baz"}, "role": "director"},
                              ]))
    except Exception as e:
        assert str(e).startswith("You must use --project to specify which project")
    else:
        raise AssertionError("Expected error was not raised.")  # pragma: no cover - we hope never to see this executed

    successful_result = get_defaulted_project(project=None,
                                              user_record=make_user_record(project_roles=[
                                                  {"project": {"@id": "/projects/the_only_project"},
                                                   "role": "scientist"}
                                              ]))

    print("successful_result=", successful_result)

    assert successful_result == "/projects/the_only_project"


def test_get_section():

    assert get_section({}, 'foo') is None
    assert get_section({'alpha': 3, 'beta': 4}, 'foo') is None
    assert get_section({'alpha': 3, 'foo': 5, 'beta': 4}, 'foo') == 5
    assert get_section({'additional_data': {}, 'alpha': 3, 'foo': 5, 'beta': 4}, 'omega') is None
    assert get_section({'additional_data': {'omega': 24}, 'alpha': 3, 'foo': 5, 'beta': 4}, 'epsilon') is None
    assert get_section({'additional_data': {'omega': 24}, 'alpha': 3, 'foo': 5, 'beta': 4}, 'omega') == 24


def test_progress_check_interval():

    assert isinstance(PROGRESS_CHECK_INTERVAL, int) and PROGRESS_CHECK_INTERVAL > 0


def test_ingestion_submission_item_url():

    assert ingestion_submission_item_url(
        server='http://foo.com',
        uuid='123-4567-890'
    ) == 'http://foo.com/ingestion-submissions/123-4567-890?format=json'


def test_show_upload_info():

    json_result = None  # Actual value comes later

    def mocked_get(url, *, auth):
        assert url.startswith(SOME_UUID_UPLOAD_URL)
        assert auth == SOME_AUTH
        return FakeResponse(200, json=json_result)

    with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
        with mock.patch("requests.get", mocked_get):

            json_result = {}
            with shown_output() as shown:
                show_upload_info(SOME_UUID, server=SOME_SERVER, env=None, keydict=SOME_KEYDICT)
                assert shown.lines == ['No uploads.']

            json_result = SOME_UPLOAD_INFO_RESULT
            with shown_output() as shown:
                show_upload_info(SOME_UUID, server=SOME_SERVER, env=None, keydict=SOME_KEYDICT)
                expected_lines = ['----- Upload Info -----', *map(str, SOME_UPLOAD_INFO)]
                assert shown.lines == expected_lines


def test_show_section_without_caveat():

    nothing_to_show = [
        '----- Foo -----',
        'Nothing to show.'
    ]

    # Lines section available, without caveat.
    with shown_output() as shown:
        show_section(
            res={'foo': ['abc', 'def']},
            section='foo',
            caveat_outcome=None)
        assert shown.lines == [
            '----- Foo -----',
            'abc',
            'def',
        ]

    # Lines section available, without caveat, but no section entry.
    with shown_output() as shown:
        show_section(
            res={},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == nothing_to_show

    # Lines section available, without caveat, but empty.
    with shown_output() as shown:
        show_section(
            res={'foo': []},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == nothing_to_show

    # Lines section available, without caveat, but null.
    with shown_output() as shown:
        show_section(
            res={'foo': None},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == nothing_to_show

    # Dictionary section available, without caveat, and with a dictionary.
    with shown_output() as shown:
        show_section(
            res={'foo': {'alpha': 'beta', 'gamma': 'delta'}},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == [
            '----- Foo -----',
            '{\n'
            '  "alpha": "beta",\n'
            '  "gamma": "delta"\n'
            '}'
        ]

    # Dictionary section available, without caveat, and with an empty dictionary.
    with shown_output() as shown:
        show_section(
            res={'foo': {}},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == nothing_to_show

    # Random unexpected data, with caveat.
    with shown_output() as shown:
        show_section(
            res={'foo': 17},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == [
            '----- Foo -----',
            '17',
        ]


def test_show_section_with_caveat():

    # Some output is shown marked by a caveat, that indicates execution stopped early for some reason
    # and the output is partial.

    caveat = 'some error'

    # Lines section available, with caveat.
    with shown_output() as shown:
        show_section(
            res={'foo': ['abc', 'def']},
            section='foo',
            caveat_outcome=caveat
        )
        assert shown.lines == [
            '----- Foo (prior to %s) -----' % caveat,
            'abc',
            'def',
        ]

    # Lines section available, with caveat.
    with shown_output() as shown:
        show_section(
            res={},
            section='foo',
            caveat_outcome=caveat
        )
        assert shown.lines == []  # Nothing shown if there is a caveat specified


def test_script_catch_errors():
    try:
        with script_catch_errors():
            pass
    except SystemExit as e:
        assert e.code == 0, "Expected status code 0, but got %s." % e.code
    else:
        raise AssertionError("SystemExit not raised.")  # pragma: no cover - we hope never to see this executed

    with shown_output() as shown:

        try:
            with script_catch_errors():
                raise RuntimeError("Some error")
        except SystemExit as e:
            assert e.code == 1, "Expected status code 1, but got %s." % e.code
        else:
            raise AssertionError("SystemExit not raised.")  # pragma: no cover - we hope never to see this executed

        assert shown.lines == ["RuntimeError: Some error"]


def test_do_any_uploads():

    # With no files, nothing to query about or load
    with mock.patch.object(submission_module, "yes_or_no", return_value=True) as mock_yes_or_no:
        with mock.patch.object(submission_module, "do_uploads") as mock_uploads:
            do_any_uploads(
                res={'additional_info': {'upload_info': []}},
                keydict=SOME_KEYDICT,
                ingestion_filename=SOME_BUNDLE_FILENAME
            )
            assert mock_yes_or_no.call_count == 0
            assert mock_uploads.call_count == 0

    with mock.patch.object(submission_module, "yes_or_no", return_value=False) as mock_yes_or_no:
        with mock.patch.object(submission_module, "do_uploads") as mock_uploads:
            with shown_output() as shown:
                do_any_uploads(
                    res={'additional_data': {'upload_info': [{'uuid': '1234', 'filename': 'f1.fastq.gz'}]}},
                    keydict=SOME_KEYDICT,
                    ingestion_filename=SOME_BUNDLE_FILENAME
                )
                mock_yes_or_no.assert_called_with("Upload 1 file?")
                assert mock_uploads.call_count == 0
                assert shown.lines == ['No uploads attempted.']

    with mock.patch.object(submission_module, "yes_or_no", return_value=True) as mock_yes_or_no:
        with mock.patch.object(submission_module, "do_uploads") as mock_uploads:

            n_uploads = len(SOME_UPLOAD_INFO)

            with shown_output() as shown:
                do_any_uploads(
                    res=SOME_UPLOAD_INFO_RESULT,
                    keydict=SOME_KEYDICT,
                    ingestion_filename=SOME_BUNDLE_FILENAME,  # from which a folder can be inferred
                )
                mock_yes_or_no.assert_called_with("Upload %s files?" % n_uploads)
                mock_uploads.assert_called_with(
                    SOME_UPLOAD_INFO,
                    auth=SOME_KEYDICT,
                    folder=SOME_BUNDLE_FILENAME_FOLDER,  # the folder part of given SOME_BUNDLE_FILENAME
                    no_query=False,
                    subfolders=False,
                )
                assert shown.lines == []

            with shown_output() as shown:
                do_any_uploads(
                    res=SOME_UPLOAD_INFO_RESULT,
                    keydict=SOME_KEYDICT,
                    upload_folder=SOME_OTHER_BUNDLE_FOLDER,  # rather than ingestion_filename
                )
                mock_yes_or_no.assert_called_with("Upload %s files?" % n_uploads)
                mock_uploads.assert_called_with(
                    SOME_UPLOAD_INFO,
                    auth=SOME_KEYDICT,
                    folder=SOME_OTHER_BUNDLE_FOLDER,  # passed straight through
                    no_query=False,
                    subfolders=False,
                )
                assert shown.lines == []

            with shown_output() as shown:
                do_any_uploads(
                    res=SOME_UPLOAD_INFO_RESULT,
                    keydict=SOME_KEYDICT,
                    # No ingestion_filename or bundle_folder
                )
                mock_yes_or_no.assert_called_with("Upload %s files?" % n_uploads)
                mock_uploads.assert_called_with(
                    SOME_UPLOAD_INFO,
                    auth=SOME_KEYDICT,
                    folder=None,  # No folder
                    no_query=False,
                    subfolders=False,
                )
                assert shown.lines == []

            with shown_output() as shown:
                do_any_uploads(
                    res=SOME_UPLOAD_INFO_RESULT,
                    keydict=SOME_KEYDICT,
                    ingestion_filename=SOME_BUNDLE_FILENAME,  # from which a folder can be inferred
                    no_query=False,
                    subfolders=True,
                )
                mock_uploads.assert_called_with(
                    SOME_UPLOAD_INFO,
                    auth=SOME_KEYDICT,
                    folder=SOME_BUNDLE_FILENAME_FOLDER,  # the folder part of given SOME_BUNDLE_FILENAME
                    no_query=False,
                    subfolders=True,
                )
                assert shown.lines == []

    with mock.patch.object(submission_module, "do_uploads") as mock_uploads:

        n_uploads = len(SOME_UPLOAD_INFO)

        with shown_output() as shown:
            do_any_uploads(
                res=SOME_UPLOAD_INFO_RESULT,
                keydict=SOME_KEYDICT,
                ingestion_filename=SOME_BUNDLE_FILENAME,  # from which a folder can be inferred
                no_query=True,
            )
            mock_uploads.assert_called_with(
                SOME_UPLOAD_INFO,
                auth=SOME_KEYDICT,
                folder=SOME_BUNDLE_FILENAME_FOLDER,  # the folder part of given SOME_BUNDLE_FILENAME
                no_query=True,
                subfolders=False,
            )
            assert shown.lines == []


def test_resume_uploads():

    with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
        with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
            with mock.patch.object(submission_module, "get_keydict_for_server", return_value=SOME_KEYDICT):
                some_response_json = {'some': 'json'}
                with mock.patch("requests.get", return_value=FakeResponse(200, json=some_response_json)):
                    with mock.patch.object(submission_module, "do_any_uploads") as mock_do_any_uploads:
                        resume_uploads(SOME_UUID, server=SOME_SERVER, env=None, bundle_filename=SOME_BUNDLE_FILENAME,
                                       keydict=SOME_KEYDICT)
                        mock_do_any_uploads.assert_called_with(
                            some_response_json,
                            keydict=SOME_KEYDICT,
                            ingestion_filename=SOME_BUNDLE_FILENAME,
                            upload_folder=None,
                            no_query=False,
                            subfolders=False,
                        )

    with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
        with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
            with mock.patch.object(submission_module, "get_keydict_for_server", return_value=SOME_KEYDICT):
                with mock.patch("requests.get", return_value=FakeResponse(401, json=SOME_BAD_RESULT)):
                    with mock.patch.object(submission_module, "do_any_uploads") as mock_do_any_uploads:
                        with pytest.raises(Exception):
                            resume_uploads(SOME_UUID, server=SOME_SERVER, env=None,
                                           bundle_filename=SOME_BUNDLE_FILENAME, keydict=SOME_KEYDICT)
                        assert mock_do_any_uploads.call_count == 0


class MockTime:
    def __init__(self, **kwargs):
        self._time = ControlledTime(**kwargs)

    def time(self):
        return (self._time.now() - self._time.INITIAL_TIME).total_seconds()


def test_execute_prearranged_upload():

    with mock.patch.object(os, "environ", SOME_ENVIRON.copy()):
        with shown_output() as shown:
            with pytest.raises(ValueError):
                bad_credentials = SOME_UPLOAD_CREDENTIALS.copy()
                bad_credentials.pop('SessionToken')
                # This will abort quite early because it can't construct a proper set of credentials as env vars.
                # Nothing has to be mocked because it won't get that far.
                execute_prearranged_upload('this-file-name-is-not-used', bad_credentials)
            assert shown.lines == []

    with mock.patch.object(os, "environ", SOME_ENVIRON.copy()):
        with shown_output() as shown:
            with mock.patch("time.time", MockTime().time):
                with mock.patch("subprocess.call", return_value=0) as mock_aws_call:
                    execute_prearranged_upload(path=SOME_FILENAME, upload_credentials=SOME_UPLOAD_CREDENTIALS)
                    mock_aws_call.assert_called_with(
                        ['aws', 's3', 'cp', '--only-show-errors', SOME_FILENAME, SOME_UPLOAD_URL],
                        env=SOME_ENVIRON_WITH_CREDS
                    )
                    assert shown.lines == [
                        "Going to upload some-filename to some-url.",
                        "Uploaded in 1.00 seconds"  # 1 tick (at rate of 1 second per tick in our controlled time)
                    ]

    with mock.patch.object(os, "environ", SOME_ENVIRON.copy()):
        with shown_output() as shown:
            with mock.patch("time.time", MockTime().time):
                with mock.patch("subprocess.call", return_value=17) as mock_aws_call:
                    with raises_regexp(RuntimeError, "Upload failed with exit code 17"):
                        execute_prearranged_upload(path=SOME_FILENAME, upload_credentials=SOME_UPLOAD_CREDENTIALS)
                    mock_aws_call.assert_called_with(
                        ['aws', 's3', 'cp', '--only-show-errors', SOME_FILENAME, SOME_UPLOAD_URL],
                        env=SOME_ENVIRON_WITH_CREDS
                    )
                    assert shown.lines == [
                        "Going to upload some-filename to some-url.",
                    ]


def test_upload_file_to_uuid():

    with mock.patch("dcicutils.ff_utils.patch_metadata", return_value=SOME_UPLOAD_CREDENTIALS_RESULT):
        with mock.patch.object(submission_module, "execute_prearranged_upload") as mocked_upload:
            upload_file_to_uuid(filename=SOME_FILENAME, uuid=SOME_UUID, auth=SOME_AUTH)
            mocked_upload.assert_called_with(SOME_FILENAME, upload_credentials=SOME_UPLOAD_CREDENTIALS)

    with mock.patch("dcicutils.ff_utils.patch_metadata", return_value=SOME_BAD_RESULT):
        with mock.patch.object(submission_module, "execute_prearranged_upload") as mocked_upload:
            try:
                upload_file_to_uuid(filename=SOME_FILENAME, uuid=SOME_UUID, auth=SOME_AUTH)
            except Exception as e:
                assert str(e).startswith("Unable to obtain upload credentials")
            else:
                raise Exception("Expected error was not raised.")  # pragma: no cover - we hope this never happens
            assert mocked_upload.call_count == 0


def make_alternator(*values):

    class Alternatives:

        def __init__(self, values):
            self.values = values
            self.pos = 0

        def next_value(self, *args, **kwargs):
            ignored(args, kwargs)
            result = self.values[self.pos]
            self.pos = (self.pos + 1) % len(self.values)
            return result

    alternatives = Alternatives(values)

    return alternatives.next_value


def test_do_uploads(tmp_path):

    @contextlib.contextmanager
    def mock_uploads():

        uploaded = {}

        def mocked_upload_file(filename, uuid, auth):
            if auth != SOME_AUTH:
                raise Exception("Bad auth")
            uploaded[uuid] = filename

        with mock.patch.object(submission_module, "upload_file_to_uuid", mocked_upload_file):
            yield uploaded  # This starts out empty when yielded, but as uploads occur will get populated.

    with mock.patch.object(submission_module, "yes_or_no", return_value=True):

        with mock_uploads() as mock_uploaded:
            do_uploads(upload_spec_list=[], auth=SOME_AUTH)
            assert mock_uploaded == {}

        some_uploads_to_do = [
            {'uuid': '1234', 'filename': 'foo.fastq.gz'},
            {'uuid': '2345', 'filename': 'bar.fastq.gz'},
            {'uuid': '3456', 'filename': 'baz.fastq.gz'}
        ]

        with mock_uploads() as mock_uploaded:
            with shown_output() as shown:
                do_uploads(upload_spec_list=some_uploads_to_do, auth=SOME_BAD_AUTH)
                assert mock_uploaded == {}  # Nothing uploaded because of bad auth
                assert shown.lines == [
                    'Uploading ./foo.fastq.gz to item 1234 ...',
                    'Exception: Bad auth',
                    'Uploading ./bar.fastq.gz to item 2345 ...',
                    'Exception: Bad auth',
                    'Uploading ./baz.fastq.gz to item 3456 ...',
                    'Exception: Bad auth'
                ]

        with mock_uploads() as mock_uploaded:
            with shown_output() as shown:
                do_uploads(upload_spec_list=some_uploads_to_do, auth=SOME_AUTH)
                assert mock_uploaded == {
                    '1234': './foo.fastq.gz',
                    '2345': './bar.fastq.gz',
                    '3456': './baz.fastq.gz'
                }
                assert shown.lines == [
                    'Uploading ./foo.fastq.gz to item 1234 ...',
                    'Upload of ./foo.fastq.gz to item 1234 was successful.',
                    'Uploading ./bar.fastq.gz to item 2345 ...',
                    'Upload of ./bar.fastq.gz to item 2345 was successful.',
                    'Uploading ./baz.fastq.gz to item 3456 ...',
                    'Upload of ./baz.fastq.gz to item 3456 was successful.',
                ]

    with mock_uploads() as mock_uploaded:
        with shown_output() as shown:
            do_uploads(upload_spec_list=some_uploads_to_do, auth=SOME_AUTH, no_query=True)
            assert mock_uploaded == {
                '1234': './foo.fastq.gz',
                '2345': './bar.fastq.gz',
                '3456': './baz.fastq.gz'
            }
            assert shown.lines == [
                'Uploading ./foo.fastq.gz to item 1234 ...',
                'Upload of ./foo.fastq.gz to item 1234 was successful.',
                'Uploading ./bar.fastq.gz to item 2345 ...',
                'Upload of ./bar.fastq.gz to item 2345 was successful.',
                'Uploading ./baz.fastq.gz to item 3456 ...',
                'Upload of ./baz.fastq.gz to item 3456 was successful.',
            ]

    with local_attrs(submission_module, CGAP_SELECTIVE_UPLOADS=True):
        with mock.patch.object(submission_module, "yes_or_no", make_alternator(True, False)):
            with mock_uploads() as mock_uploaded:
                with shown_output() as shown:
                    do_uploads(
                        upload_spec_list=[
                            {'uuid': '1234', 'filename': 'foo.fastq.gz'},
                            {'uuid': '2345', 'filename': 'bar.fastq.gz'},
                            {'uuid': '3456', 'filename': 'baz.fastq.gz'}
                        ],
                        auth=SOME_AUTH,
                        folder='/x/yy/zzz/'
                    )
                    assert mock_uploaded == {
                        '1234': '/x/yy/zzz/foo.fastq.gz',
                        # The mock yes_or_no will have omitted this element.
                        # '2345': './bar.fastq.gz',
                        '3456': '/x/yy/zzz/baz.fastq.gz'
                    }
                    assert shown.lines == [
                        'Uploading /x/yy/zzz/foo.fastq.gz to item 1234 ...',
                        'Upload of /x/yy/zzz/foo.fastq.gz to item 1234 was successful.',
                        # The query about uploading bar.fastq has been mocked out here
                        # in favor of an unconditional False result, so the question does no I/O.
                        # The only output is the result of simulating a 'no' answer.
                        'OK, not uploading it.',
                        'Uploading /x/yy/zzz/baz.fastq.gz to item 3456 ...',
                        'Upload of /x/yy/zzz/baz.fastq.gz to item 3456 was successful.',
                    ]

    folder = tmp_path / "to_upload"
    folder.mkdir()
    subfolder = folder / "files"
    subfolder.mkdir()
    file_path = subfolder / "foo.fastq.gz"
    file_path.write_text("")
    file_path = file_path.as_posix()
    upload_spec_list = [{'uuid': '1234', 'filename': 'foo.fastq.gz'}]
    filename = upload_spec_list[0]["filename"]
    uuid = upload_spec_list[0]["uuid"]

    with mock.patch.object(submission_module, "upload_file_to_uuid") as mock_upload:
        # File in subfolder and found.
        do_uploads(
            upload_spec_list,
            auth=SOME_AUTH,
            folder=subfolder,
            no_query=True,
        )
        mock_upload.assert_called_with(
            filename=file_path,
            uuid=uuid,
            auth=SOME_AUTH,
        )

    with mock.patch.object(submission_module, "upload_file_to_uuid") as mock_upload:
        # File not found, so pass join of folder and file.
        do_uploads(
            upload_spec_list,
            auth=SOME_AUTH,
            folder=folder,
            no_query=True,
        )
        mock_upload.assert_called_with(
            filename=(folder.as_posix() + "/" + filename),
            uuid=uuid,
            auth=SOME_AUTH,
        )

    with mock.patch.object(submission_module, "upload_file_to_uuid") as mock_upload:
        # File found within subfolder and upload called.
        do_uploads(
            upload_spec_list,
            auth=SOME_AUTH,
            folder=folder,
            no_query=True,
            subfolders=True,
        )
        mock_upload.assert_called_with(
            filename=file_path,
            uuid=uuid,
            auth=SOME_AUTH,
        )

    with mock.patch.object(submission_module, "upload_file_to_uuid") as mock_upload:
        # Multiple matching files found; show lines and don't call for upload.
        with shown_output() as shown:
            another_file_path = folder / "foo.fastq.gz"
            another_file_path.write_text("")
            another_file_path = another_file_path.as_posix()
            folder_str = folder.as_posix()
            do_uploads(
                upload_spec_list,
                auth=SOME_AUTH,
                folder=folder,
                no_query=True,
                subfolders=True,
            )
            mock_upload.assert_not_called()
            assert shown.lines == [
                "No upload attempted for file %s because multiple copies were found"
                " in folder %s: %s."
                % (filename, folder_str + "/**", ", ".join([another_file_path, file_path]))
            ]


def test_upload_item_data():

    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER) as mock_resolve:
        with mock.patch.object(submission_module, "get_keydict_for_server", return_value=SOME_KEYDICT) as mock_get:
            with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                with mock.patch.object(submission_module, "upload_file_to_uuid") as mock_upload:

                    upload_item_data(item_filename=SOME_FILENAME, uuid=SOME_UUID, server=SOME_SERVER, env=SOME_ENV)

                    mock_resolve.assert_called_with(env=SOME_ENV, server=SOME_SERVER)
                    mock_get.assert_called_with(SOME_SERVER)
                    mock_upload.assert_called_with(filename=SOME_FILENAME, uuid=SOME_UUID, auth=SOME_KEYDICT)

    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER) as mock_resolve:
        with mock.patch.object(submission_module, "get_keydict_for_server", return_value=SOME_KEYDICT) as mock_get:
            with mock.patch.object(submission_module, "yes_or_no", return_value=False):
                with mock.patch.object(submission_module, "upload_file_to_uuid") as mock_upload:

                    with shown_output() as shown:

                        try:
                            upload_item_data(item_filename=SOME_FILENAME, uuid=SOME_UUID, server=SOME_SERVER,
                                             env=SOME_ENV)
                        except SystemExit as e:
                            assert e.code == 1
                        else:
                            raise AssertionError("Expected SystemExit not raised.")  # pragma: no cover

                        assert shown.lines == ['Aborting submission.']

                    mock_resolve.assert_called_with(env=SOME_ENV, server=SOME_SERVER)
                    mock_get.assert_called_with(SOME_SERVER)
                    assert mock_upload.call_count == 0

    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER) as mock_resolve:
        with mock.patch.object(submission_module, "get_keydict_for_server", return_value=SOME_KEYDICT) as mock_get:
            with mock.patch.object(submission_module, "upload_file_to_uuid") as mock_upload:

                upload_item_data(item_filename=SOME_FILENAME, uuid=SOME_UUID,
                                 server=SOME_SERVER, env=SOME_ENV, no_query=True)

                mock_resolve.assert_called_with(env=SOME_ENV, server=SOME_SERVER)
                mock_get.assert_called_with(SOME_SERVER)
                mock_upload.assert_called_with(filename=SOME_FILENAME, uuid=SOME_UUID,
                                               auth=SOME_KEYDICT)


def test_submit_any_ingestion_old_protocol():

    with shown_output() as shown:
        with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
            with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                with mock.patch.object(submission_module, "yes_or_no", return_value=False):
                    try:
                        submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                             ingestion_type='metadata_bundle',
                                             institution=SOME_INSTITUTION,
                                             project=SOME_PROJECT,
                                             server=SOME_SERVER,
                                             env=None,
                                             validate_only=False,
                                             no_query=False,
                                             subfolders=False,
                                             )
                    except SystemExit as e:
                        assert e.code == 1
                    else:
                        raise AssertionError("Expected SystemExit did not happen.")  # pragma: no cover

                    assert shown.lines == ["Aborting submission."]

    def mocked_post(url, auth, data, headers, files):
        # We only expect requests.post to be called on one particular URL, so this definition is very specialized
        # mostly just to check that we're being called on what we think so we can return something highly specific
        # with some degree of confidence. -kmp 6-Sep-2020
        assert url.endswith('/submit_for_ingestion')
        assert auth == SOME_AUTH
        ignored(data)
        assert isinstance(files, dict) and 'datafile' in files and isinstance(files['datafile'], io.BytesIO)
        assert headers == {'Content-type': 'application/json'}
        return FakeResponse(201, json={'submission_id': SOME_UUID})

    partial_res = {
        'submission_id': SOME_UUID,
        "processing_status": {
            "state": "processing",
            "outcome": "unknown",
            "progress": "not done yet",
        }
    }

    final_res = {
        'submission_id': SOME_UUID,
        "additional_data": {
            "validation_output": [],
            "post_output": [],
            "upload_info": SOME_UPLOAD_INFO,
        },
        "processing_status": {
            "state": "done",
            "outcome": "success",
            "progress": "irrelevant"
        }
    }

    error_res = {
        'submission_id': SOME_UUID,
        'errors': [
            "ouch"
        ],
        "additional_data": {
            "validation_output": [],
            "post_output": [],
            "upload_info": SOME_UPLOAD_INFO,
        },
        "processing_status": {
            "state": "done",
            "outcome": "error",
            "progress": "irrelevant"
        }
    }

    def make_mocked_get(success=True, done_after_n_tries=1):
        if success:
            responses = (partial_res,) * (done_after_n_tries - 1) + (final_res,)
        else:
            responses = (partial_res,) * (done_after_n_tries - 1) + (error_res,)
        response_maker = make_alternator(*responses)

        def mocked_get(url, auth):
            print("in mocked_get, url=", url, "auth=", auth)
            assert auth == SOME_AUTH
            if url.endswith("/me?format=json"):
                return FakeResponse(200, json=make_user_record(
                    project=SOME_PROJECT,
                    user_institution=[
                        {'@id': SOME_INSTITUTION}
                    ]
                ))
            else:
                assert url.endswith('/ingestion-submissions/' + SOME_UUID + "?format=json")
                return FakeResponse(200, json=response_maker())
        return mocked_get

    mfs = MockFileSystem()

    dt = ControlledTime()

    # TODO: Will says he wants explanatory doc here and elsewhere with a big cascade like this.
    with mock.patch("os.path.exists", mfs.exists):
        with mock.patch("io.open", mfs.open):
            with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                    with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                        with mock.patch.object(submission_module, "get_keydict_for_server",
                                               return_value=SOME_KEYDICT):
                            with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                                with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                                    with mock.patch.object(submission_module, "get_keydict_for_server",
                                                           return_value=SOME_KEYDICT):
                                        with mock.patch("requests.post", mocked_post):
                                            with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3)):
                                                try:
                                                    submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                         ingestion_type='metadata_bundle',
                                                                         institution=SOME_INSTITUTION,
                                                                         project=SOME_PROJECT,
                                                                         server=SOME_SERVER,
                                                                         env=None,
                                                                         validate_only=False,
                                                                         no_query=False,
                                                                         subfolders=False,
                                                                         )
                                                except ValueError as e:
                                                    # submit_any_ingestion will raise ValueError if its
                                                    # bundle_filename argument is not the name of a
                                                    # metadata bundle file. We did nothing in this mock to
                                                    # create the file SOME_BUNDLE_FILENAME, so we expect something
                                                    # like: "The file '/some-folder/foo.xls' does not exist."
                                                    assert "does not exist" in str(e)
                                                else:  # pragma: no cover
                                                    raise AssertionError("Expected ValueError did not happen.")

    # This tests the normal case with validate_only=False and a successful result.

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mocked_post):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except SystemExit as e:  # pragma: no cover
                                                            # This is just in case. In fact it's more likely
                                                            # that a normal 'return' not 'exit' was done.
                                                            assert e.code == 0

                                                        assert mock_do_any_uploads.call_count == 1
                                                        mock_do_any_uploads.assert_called_with(
                                                            final_res,
                                                            ingestion_filename=SOME_BUNDLE_FILENAME,
                                                            keydict=SOME_KEYDICT,
                                                            upload_folder=None,
                                                            no_query=False,
                                                            subfolders=False,
                                                        )
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Final status: success',
            # Output from uploads is not present because we mocked that out.
            # See test of the call to the uploader higher up.
        ]

    dt.reset_datetime()

    # Test for suppression of user input when submission with no_query=True.

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "get_keydict_for_server",
                                               return_value=SOME_KEYDICT):
                            with mock.patch("requests.post", mocked_post):
                                with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3)):
                                    with mock.patch("datetime.datetime", dt):
                                        with mock.patch("time.sleep", dt.sleep):
                                            with mock.patch.object(submission_module, "show_section"):
                                                with mock.patch.object(submission_module,
                                                                       "do_any_uploads") as mock_do_any_uploads:
                                                    try:
                                                        submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                             ingestion_type='metadata_bundle',
                                                                             institution=SOME_INSTITUTION,
                                                                             project=SOME_PROJECT,
                                                                             server=SOME_SERVER,
                                                                             env=None,
                                                                             validate_only=False,
                                                                             no_query=True,
                                                                             subfolders=False,
                                                                             )
                                                    except SystemExit as e:  # pragma: no cover
                                                        # This is just in case. In fact it's more likely
                                                        # that a normal 'return' not 'exit' was done.
                                                        assert e.code == 0

                                                    assert mock_do_any_uploads.call_count == 1
                                                    mock_do_any_uploads.assert_called_with(
                                                        final_res,
                                                        ingestion_filename=SOME_BUNDLE_FILENAME,
                                                        keydict=SOME_KEYDICT,
                                                        upload_folder=None,
                                                        no_query=True,
                                                        subfolders=False,
                                                    )
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Final status: success',
            # Output from uploads is not present because we mocked that out.
            # See test of the call to the uploader higher up.
        ]

    dt.reset_datetime()

    # This tests the normal case with validate_only=False and a post error due to multipart/form-data unsupported,
    # a symptom of the metadata bundle submission protocol being unsupported.

    def unsupported_media_type(*args, **kwargs):
        ignored(args, kwargs)
        return FakeResponse(415, json={
            "status": "error",
            "title": "Unsupported Media Type",
            "detail": "Request content type multipart/form-data is not 'application/json'"
        })

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", unsupported_media_type):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3,
                                                                                    success=False)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except Exception as e:
                                                            assert "raised for status" in str(e)
                                                        else:  # pragma: no cover
                                                            raise AssertionError("Expected error did not occur.")

                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            "The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.",
            "Unsupported Media Type: Request content type multipart/form-data is not 'application/json'",
            "NOTE: This error is known to occur if the server does not support metadata bundle submission."
        ]

    dt.reset_datetime()

    # This tests the normal case with validate_only=False and a post error for some unknown reason.

    def mysterious_error(*args, **kwargs):
        ignored(args, kwargs)
        return FakeResponse(400, json={
            "status": "error",
            "title": "Mysterious Error",
            "detail": "If I told you, there'd be no mystery."
        })

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mysterious_error):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3,
                                                                                    success=False)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except Exception as e:
                                                            assert "raised for status" in str(e)
                                                        else:  # pragma: no cover
                                                            raise AssertionError("Expected error did not occur.")

                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            "The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.",
            "Mysterious Error: If I told you, there'd be no mystery.",
        ]

    dt.reset_datetime()

    # This tests the normal case with validate_only=False and an error result.

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mocked_post):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3,
                                                                                    success=False)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except SystemExit as e:  # pragma: no cover
                                                            # This is just in case. In fact it's more likely
                                                            # that a normal 'return' not 'exit' was done.
                                                            assert e.code == 0

                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Final status: error',
            # Output from uploads is not present because we mocked that out.
            # See test of the call to the uploader higher up.
        ]

    dt.reset_datetime()

    # This tests the normal case with validate_only=True

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mocked_post):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=True,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except SystemExit as e:  # pragma: no cover
                                                            assert e.code == 0
                                                        # It's also OK if it doesn't do an exit(0)

                                                        # For validation only, we won't have tried uploads.
                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Final status: success',
            # Output from uploads is not present because we mocked that out.
            # See test of the call to the uploader higher up.
        ]

    dt.reset_datetime()

    # This tests what happens if the normal case times out.

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mocked_post):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=10)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except SystemExit as e:
                                                            # We expect to time out for too many waits before success.
                                                            assert e.code == 1

                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:01:05 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:01:21 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:01:37 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:01:53 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:02:09 Progress is not done yet. Continuing to wait...',
            # After 1 second to recheck the time...
            '12:02:10 Timed out after 8 tries.',
        ]


def test_submit_any_ingestion_new_protocol():

    with shown_output() as shown:
        with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
            with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                with mock.patch.object(submission_module, "yes_or_no", return_value=False):
                    try:
                        submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                             ingestion_type='metadata_bundle',
                                             institution=SOME_INSTITUTION,
                                             project=SOME_PROJECT,
                                             server=SOME_SERVER,
                                             env=None,
                                             validate_only=False,
                                             no_query=False,
                                             subfolders=False,)
                    except SystemExit as e:
                        assert e.code == 1
                    else:
                        raise AssertionError("Expected SystemExit did not happen.")  # pragma: no cover

                    assert shown.lines == ["Aborting submission."]

    def mocked_post(url, auth, data=None, json=None, files=None, headers=None):
        ignored(data, json)
        content_type = headers and headers.get('Content-type')
        if content_type:
            assert content_type == 'application/json'
        if url.endswith("/IngestionSubmission"):
            return FakeResponse(201,
                                json={
                                    "status": "success",
                                    "@type": ["result"],
                                    "@graph": [
                                        {
                                            "institution": SOME_INSTITUTION,
                                            "project": SOME_PROJECT,
                                            "ingestion_type": 'metadata_bundle',
                                            "processing_status": {
                                                "state": "created",
                                                "outcome": "unknown",
                                                "progress": "unavailable"
                                            },
                                            "result": {},
                                            "errors": [],
                                            "additional_data": {},
                                            "@id": "/ingestion-submissions/" + SOME_UUID,
                                            "@type": ["IngestionSubmission", "Item"],
                                            "uuid": SOME_UUID,
                                            # ... other properties not needed ...
                                        }
                                    ]
                                })
        elif url.endswith("/submit_for_ingestion"):
            # We only expect requests.post to be called on one particular URL, so this definition is very specialized
            # mostly just to check that we're being called on what we think so we can return something highly specific
            # with some degree of confidence. -kmp 6-Sep-2020
            m = re.match(".*/ingestion-submissions/([a-f0-9-]*)/submit_for_ingestion$", url)
            if m:
                assert m.group(1) == SOME_UUID
                assert auth == SOME_AUTH
                assert isinstance(files, dict) and 'datafile' in files and isinstance(files['datafile'], io.BytesIO)
                return FakeResponse(201, json={'submission_id': SOME_UUID})
            else:
                # Old protocol used
                return FakeResponse(404, json={})

    partial_res = {
        'submission_id': SOME_UUID,
        "processing_status": {
            "state": "processing",
            "outcome": "unknown",
            "progress": "not done yet",
        }
    }

    final_res = {
        'submission_id': SOME_UUID,
        "additional_data": {
            "validation_output": [],
            "post_output": [],
            "upload_info": SOME_UPLOAD_INFO,
        },
        "processing_status": {
            "state": "done",
            "outcome": "success",
            "progress": "irrelevant"
        }
    }

    error_res = {
        'submission_id': SOME_UUID,
        'errors': [
            "ouch"
        ],
        "additional_data": {
            "validation_output": [],
            "post_output": [],
            "upload_info": SOME_UPLOAD_INFO,
        },
        "processing_status": {
            "state": "done",
            "outcome": "error",
            "progress": "irrelevant"
        }
    }

    def make_mocked_get(success=True, done_after_n_tries=1):
        if success:
            responses = (partial_res,) * (done_after_n_tries - 1) + (final_res,)
        else:
            responses = (partial_res,) * (done_after_n_tries - 1) + (error_res,)
        response_maker = make_alternator(*responses)

        def mocked_get(url, auth):
            print("in mocked_get, url=", url, "auth=", auth)
            assert auth == SOME_AUTH
            if url.endswith("/me?format=json"):
                return FakeResponse(200, json=make_user_record(
                    project=SOME_PROJECT,
                    user_institution=[
                        {'@id': SOME_INSTITUTION}
                    ]
                ))
            else:
                assert url.endswith('/ingestion-submissions/' + SOME_UUID + "?format=json")
                return FakeResponse(200, json=response_maker())
        return mocked_get

    mfs = MockFileSystem()

    dt = ControlledTime()

    with mock.patch("os.path.exists", mfs.exists):
        with mock.patch("io.open", mfs.open):
            with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                    with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                        with mock.patch.object(submission_module, "get_keydict_for_server",
                                               return_value=SOME_KEYDICT):
                            with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                                with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                                    with mock.patch.object(submission_module, "get_keydict_for_server",
                                                           return_value=SOME_KEYDICT):
                                        with mock.patch("requests.post", mocked_post):
                                            with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3)):
                                                try:
                                                    submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                         ingestion_type='metadata_bundle',
                                                                         institution=SOME_INSTITUTION,
                                                                         project=SOME_PROJECT,
                                                                         server=SOME_SERVER,
                                                                         env=None,
                                                                         validate_only=False,
                                                                         no_query=False,
                                                                         subfolders=False,)
                                                except ValueError as e:
                                                    # submit_any_ingestion will raise ValueError if its
                                                    # bundle_filename argument is not the name of a
                                                    # metadata bundle file. We did nothing in this mock to
                                                    # create the file SOME_BUNDLE_FILENAME, so we expect something
                                                    # like: "The file '/some-folder/foo.xls' does not exist."
                                                    assert "does not exist" in str(e)
                                                else:  # pragma: no cover
                                                    raise AssertionError("Expected ValueError did not happen.")

    # This tests the normal case with validate_only=False and a successful result.

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mocked_post):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except SystemExit as e:  # pragma: no cover
                                                            # This is just in case. In fact it's more likely
                                                            # that a normal 'return' not 'exit' was done.
                                                            assert e.code == 0

                                                        assert mock_do_any_uploads.call_count == 1
                                                        mock_do_any_uploads.assert_called_with(
                                                            final_res,
                                                            ingestion_filename=SOME_BUNDLE_FILENAME,
                                                            keydict=SOME_KEYDICT,
                                                            upload_folder=None,
                                                            no_query=False,
                                                            subfolders=False,
                                                        )
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Final status: success',
            # Output from uploads is not present because we mocked that out.
            # See test of the call to the uploader higher up.
        ]

    dt.reset_datetime()

    # This tests the normal case with validate_only=False and a post error due to multipart/form-data unsupported,
    # a symptom of the metadata bundle submission protocol being unsupported.

    def unsupported_media_type(*args, **kwargs):
        ignored(args, kwargs)
        return FakeResponse(415, json={
            "status": "error",
            "title": "Unsupported Media Type",
            "detail": "Request content type multipart/form-data is not 'application/json'"
        })

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", unsupported_media_type):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3,
                                                                                    success=False)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except Exception as e:
                                                            assert "raised for status" in str(e)
                                                        else:  # pragma: no cover
                                                            raise AssertionError("Expected error did not occur.")

                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            "The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.",
            "Unsupported Media Type: Request content type multipart/form-data is not 'application/json'",
            "NOTE: This error is known to occur if the server does not support metadata bundle submission."
        ]

    dt.reset_datetime()

    # This tests the normal case with validate_only=False and a post error for some unknown reason.

    def mysterious_error(*args, **kwargs):
        ignored(args, kwargs)
        return FakeResponse(400, json={
            "status": "error",
            "title": "Mysterious Error",
            "detail": "If I told you, there'd be no mystery."
        })

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mysterious_error):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3,
                                                                                    success=False)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except Exception as e:
                                                            assert "raised for status" in str(e)
                                                        else:  # pragma: no cover
                                                            raise AssertionError("Expected error did not occur.")

                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            "The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.",
            "Mysterious Error: If I told you, there'd be no mystery.",
        ]

    dt.reset_datetime()

    # This tests the normal case with validate_only=False and an error result.

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mocked_post):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3,
                                                                                    success=False)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except SystemExit as e:  # pragma: no cover
                                                            # This is just in case. In fact it's more likely
                                                            # that a normal 'return' not 'exit' was done.
                                                            assert e.code == 0

                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Final status: error',
            # Output from uploads is not present because we mocked that out.
            # See test of the call to the uploader higher up.
        ]

    dt.reset_datetime()

    # This tests the normal case with validate_only=True

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mocked_post):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=3)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=True,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 subfolders=False,
                                                                                 )
                                                        except SystemExit as e:  # pragma: no cover
                                                            assert e.code == 0
                                                        # It's also OK if it doesn't do an exit(0)

                                                        # For validation only, we won't have tried uploads.
                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Final status: success',
            # Output from uploads is not present because we mocked that out.
            # See test of the call to the uploader higher up.
        ]

    dt.reset_datetime()

    # This tests what happens if the normal case times out.

    with shown_output() as shown:
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch("io.open", mfs.open):
                with io.open(SOME_BUNDLE_FILENAME, 'w') as fp:
                    print("Data would go here.", file=fp)
                with mock.patch.object(submission_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch.object(submission_module, "resolve_server", return_value=SOME_SERVER):
                        with mock.patch.object(submission_module, "yes_or_no", return_value=True):
                            with mock.patch.object(submission_module, "get_keydict_for_server",
                                                   return_value=SOME_KEYDICT):
                                with mock.patch("requests.post", mocked_post):
                                    with mock.patch("requests.get", make_mocked_get(done_after_n_tries=10)):
                                        with mock.patch("datetime.datetime", dt):
                                            with mock.patch("time.sleep", dt.sleep):
                                                with mock.patch.object(submission_module, "show_section"):
                                                    with mock.patch.object(submission_module,
                                                                           "do_any_uploads") as mock_do_any_uploads:
                                                        try:
                                                            submit_any_ingestion(SOME_BUNDLE_FILENAME,
                                                                                 ingestion_type='metadata_bundle',
                                                                                 institution=SOME_INSTITUTION,
                                                                                 project=SOME_PROJECT,
                                                                                 server=SOME_SERVER,
                                                                                 env=None,
                                                                                 validate_only=False,
                                                                                 upload_folder=None,
                                                                                 no_query=False,
                                                                                 )
                                                        except SystemExit as e:
                                                            # We expect to time out for too many waits before success.
                                                            assert e.code == 1

                                                        assert mock_do_any_uploads.call_count == 0
        assert shown.lines == [
            'The server http://localhost:7777 recognizes you as J Doe <jdoe@cgap.hms.harvard.edu>.',
            # We're ticking the clock once for each check of the virtual clock at 1 second per tick.
            # 1 second after we started our virtual clock...
            '12:00:01 Bundle uploaded, assigned uuid 123-4444-5678 for tracking. Awaiting processing...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:17 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:33 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:00:49 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:01:05 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:01:21 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:01:37 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:01:53 Progress is not done yet. Continuing to wait...',
            # After 15 seconds sleep plus 1 second to recheck the time...
            '12:02:09 Progress is not done yet. Continuing to wait...',
            # After 1 second to recheck the time...
            '12:02:10 Timed out after 8 tries.',
        ]
