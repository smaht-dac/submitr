import contextlib
import datetime
import io  # noqa
import os
import platform
import pytest

from . import test_misc  # noqa
from dcicutils import command_utils as command_utils_module
from dcicutils.common import APP_CGAP, APP_FOURFRONT, APP_SMAHT
from dcicutils.misc_utils import ignored, ignorable, NamedObject
from dcicutils.portal_utils import Portal
from dcicutils.qa_utils import ControlledTime, MockFileSystem, raises_regexp, printed_output
from dcicutils.s3_utils import HealthPageKey
from typing import List, Dict
from unittest import mock

from .test_utils import shown_output
from .. import submission as submission_module
from ..submission import (  # noqa
    SERVER_REGEXP, PROGRESS_CHECK_INTERVAL, ATTEMPTS_BEFORE_TIMEOUT,
    _get_defaulted_institution, _get_defaulted_project,
    _show_upload_info, _show_upload_result,
    execute_prearranged_upload, _get_section, _get_user_record, _ingestion_submission_item_url,
    _resolve_server, resume_uploads, _show_section, submit_any_ingestion,
    upload_file_to_uuid,
    get_s3_encrypt_key_id, get_s3_encrypt_key_id_from_health_page, _running_on_windows_native,
    _resolve_app_args,  # noQA - yes, a protected member, but we still need to test it
    _post_files_data,  # noQA - again, testing a protected member
    _check_ingestion_progress,  # noQA - again, testing a protected member
    _get_defaulted_lab, _get_defaulted_award, SubmissionProtocol, compute_file_post_data,
    GENERIC_SCHEMA_TYPE, DEFAULT_APP, _summarize_submission,
    _get_defaulted_submission_centers, _get_defaulted_consortia, _do_app_arg_defaulting, _monitor_ingestion_process
)
from ..utils import FakeResponse


TEST_ENCRYPT_KEY = 'encrypt-key-for-testing'

SOME_INGESTION_TYPE = 'metadata_bundle'

ANOTHER_INGESTION_TYPE = 'genelist'

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

SOME_CONSORTIUM = '/consortium/good-consortium/'
SOME_CONSORTIA = [SOME_CONSORTIUM]

SOME_SUBMISSION_CENTER = '/submission_center/good-submission-center/'
SOME_SUBMISSION_CENTERS = [SOME_SUBMISSION_CENTER]

SOME_LAB = '/lab/good-lab/'

SOME_OTHER_LAB = '/lab/evil-lab/'

SOME_SERVER = 'http://localhost:7777'  # Dependencies force this to be out of alphabetical order

SOME_ORCHESTRATED_SERVERS = [
    'http://cgap-msa-something.amazonaws.com/',
    'http://cgap-devtest-something.amazonaws.com/'
]

SOME_KEYDICT = {'key': SOME_KEY_ID, 'secret': SOME_SECRET, 'server': SOME_SERVER}

SOME_OTHER_BUNDLE_FOLDER = '/some-other-folder/'

SOME_PROJECT = '/projects/12a92962-8265-4fc0-b2f8-cf14f05db58b/'  # Test Project from master inserts

SOME_AWARD = '/awards/45083e37-0342-4a0f-833d-aa7ab4be60f1/'

SOME_UPLOAD_URL = 'some-url'

SOME_UPLOAD_CREDENTIALS = {
    'AccessKeyId': 'some-access-key',
    'SecretAccessKey': 'some-secret',
    'SessionToken': 'some-session-token',
    'upload_url': SOME_UPLOAD_URL,
}

SOME_FILE_METADATA = {"upload_credentials": SOME_UPLOAD_CREDENTIALS}

SOME_S3_ENCRYPT_KEY_ID = 'some/encrypt/key'

SOME_EXTENDED_UPLOAD_CREDENTIALS = {
    'AccessKeyId': 'some-access-key',
    'SecretAccessKey': 'some-secret',
    'SessionToken': 'some-session-token',
    'upload_url': SOME_UPLOAD_URL,
    's3_encrypt_key_id': SOME_S3_ENCRYPT_KEY_ID,
}

SOME_UPLOAD_CREDENTIALS_RESULT = {'@graph': [SOME_FILE_METADATA]}

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
SOME_USER_TITLE = 'J Doe'
SOME_USER_EMAIL = "jdoe@testing.hms.harvard.edu"

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

ANOTHER_FILE_NAME = "another_file"

SOME_EXTRA_FILE_CREDENTIALS = [
    {"filename": SOME_FILENAME, "upload_credentials": SOME_ENVIRON_WITH_CREDS},
    {"filename": ANOTHER_FILE_NAME, "upload_credentials": SOME_ENVIRON_WITH_CREDS},
]

SOME_FILE_METADATA_WITH_EXTRA_FILE_CREDENTIALS = {
    "extra_files_creds": SOME_EXTRA_FILE_CREDENTIALS
}


def _independently_confirmed_as_running_on_windows_native():
    # There are two ways to tell if we're running on Windows native:
    #    os.name == 'nt' (as opposed to 'posix')
    #    platform.system() == 'Windows' (as opposed to 'Linux', 'Darwin', or 'CYGWIN_NT-<version>'
    # Since we're wanting to test one of these, we  use the other mechansim to confirm things.
    standard_result = _running_on_windows_native()
    independent_result = platform.system() == 'Windows'
    assert standard_result == independent_result, (
        f"Mechanisms for telling whether we're on Windows disagree:"
        f" standard_result={standard_result} independent_result={independent_result}"
    )
    return independent_result


@contextlib.contextmanager
def script_dont_catch_errors():
    # We use this to create a mock context that would allow us to catch errors that fall through here,
    # but we are not relying on errors to actually happen, so it's OK if this never catches anything.
    yield


def test_script_dont_catch_errors():  # test that errors pass through dont_catch_errors
    with pytest.raises(AssertionError):
        with script_dont_catch_errors():
            raise AssertionError("Foo")


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


def make_user_record(title=SOME_USER_TITLE,
                     contact_email=SOME_USER_EMAIL,
                     **kwargs):
    user_record = {
        'title': title,
        'contact_email': contact_email,
        'groups': ['admin']
    }
    user_record.update(kwargs)

    return user_record


def test_get_user_record():

    def make_mocked_get(auth_failure_code=400):
        def mocked_get(url, *, auth, **kwargs):
            ignored(url, kwargs)
            if auth != SOME_AUTH:
                return FakeResponse(status_code=auth_failure_code, json={'Title': 'Not logged in.'})
            return FakeResponse(status_code=200, json={'title': SOME_USER_TITLE, 'contact_email': SOME_USER_EMAIL})
        return mocked_get

    with mock.patch("requests.get", return_value=FakeResponse(401, content='["not dictionary"]')):
        with pytest.raises(Exception):
            _get_user_record(server="http://localhost:12345", auth=None)

    with mock.patch("requests.get", make_mocked_get(auth_failure_code=401)):
        with pytest.raises(Exception):
            _get_user_record(server="http://localhost:12345", auth=None)

    with mock.patch("requests.get", make_mocked_get(auth_failure_code=403)):
        with pytest.raises(Exception):
            _get_user_record(server="http://localhost:12345", auth=None)

    with mock.patch("requests.get", make_mocked_get()):
        _get_user_record(server="http://localhost:12345", auth=SOME_AUTH)

    with mock.patch("requests.get", lambda *x, **y: FakeResponse(status_code=400)):
        with pytest.raises(Exception):  # Body is not JSON
            _get_user_record(server="http://localhost:12345", auth=SOME_AUTH)


def test_get_defaulted_institution():

    assert _get_defaulted_institution(institution=SOME_INSTITUTION, user_record='does-not-matter') == SOME_INSTITUTION
    assert _get_defaulted_institution(institution='anything', user_record='does-not-matter') == 'anything'

    try:
        _get_defaulted_institution(institution=None, user_record=make_user_record())
    except Exception as e:
        assert str(e).startswith("Your user profile has no institution")

    successful_result = _get_defaulted_institution(institution=None,
                                                   user_record=make_user_record(
                                                       # this is the old-fashioned place for it - a decoy
                                                       institution={'@id': SOME_OTHER_INSTITUTION},
                                                       # this is the right place to find the info
                                                       user_institution={'@id': SOME_INSTITUTION}
                                                   ))

    print("successful_result=", successful_result)

    assert successful_result == SOME_INSTITUTION


def test_get_defaulted_project():

    assert _get_defaulted_project(project=SOME_PROJECT, user_record='does-not-matter') == SOME_PROJECT
    assert _get_defaulted_project(project='anything', user_record='does-not-matter') == 'anything'

    try:
        _get_defaulted_project(project=None, user_record=make_user_record())
    except Exception as e:
        assert str(e).startswith("Your user profile declares no project")

    try:
        _get_defaulted_project(project=None,
                               user_record=make_user_record(project_roles=[]))
    except Exception as e:
        assert str(e).startswith("Your user profile declares no project")
    else:
        raise AssertionError("Expected error was not raised.")  # pragma: no cover

    try:
        _get_defaulted_project(project=None,
                               user_record=make_user_record(project_roles=[
                                   {"project": {"@id": "/projects/foo"}, "role": "developer"},
                                   {"project": {"@id": "/projects/bar"}, "role": "clinician"},
                                   {"project": {"@id": "/projects/baz"}, "role": "director"},
                               ]))
    except Exception as e:
        assert str(e).startswith("You must use --project to specify which project")
    else:
        raise AssertionError("Expected error was not raised.")  # pragma: no cover - we hope never to see this executed

    successful_result = _get_defaulted_project(project=None,
                                               user_record=make_user_record(project_roles=[
                                                   {"project": {"@id": "/projects/the_only_project"},
                                                    "role": "scientist"}
                                               ]))

    print("successful_result=", successful_result)

    assert successful_result == "/projects/the_only_project"


def test_get_section():

    assert _get_section({}, 'foo') is None
    assert _get_section({'alpha': 3, 'beta': 4}, 'foo') is None
    assert _get_section({'alpha': 3, 'foo': 5, 'beta': 4}, 'foo') == 5
    assert _get_section({'additional_data': {}, 'alpha': 3, 'foo': 5, 'beta': 4}, 'omega') is None
    assert _get_section({'additional_data': {'omega': 24}, 'alpha': 3, 'foo': 5, 'beta': 4}, 'epsilon') is None
    assert _get_section({'additional_data': {'omega': 24}, 'alpha': 3, 'foo': 5, 'beta': 4}, 'omega') == 24


def test_progress_check_interval():

    assert isinstance(PROGRESS_CHECK_INTERVAL, int) and PROGRESS_CHECK_INTERVAL > 0


def test_attempts_before_timeout():
    assert isinstance(ATTEMPTS_BEFORE_TIMEOUT, int) and ATTEMPTS_BEFORE_TIMEOUT > 0


def test_ingestion_submission_item_url():

    assert _ingestion_submission_item_url(
        server='http://foo.com',
        uuid='123-4567-890'
    ) == 'http://foo.com/ingestion-submissions/123-4567-890?format=json&datastore=database'


def test_show_upload_info():

    json_result = None  # Actual value comes later

    index = 0

    URLS = [
        f"{SOME_SERVER}/ingestion-submissions/{SOME_UUID}?format=json&datastore=database",
        f"{SOME_SERVER}/health",
        f"{SOME_SERVER}/{SOME_UPLOAD_INFO[0]['uuid']}",
        f"{SOME_SERVER}/{SOME_UPLOAD_INFO[1]['uuid']}"
    ]

    def mocked_get(url, *, auth, **kwargs):
        nonlocal index
        ignored(kwargs)
        assert url == URLS[index]
        assert auth == SOME_AUTH
        index += 1
        return FakeResponse(200, json=json_result)

    with mock.patch("dcicutils.portal_utils.Portal.get_schemas", return_value={"dummy": "dummy"}):
        with mock.patch("dcicutils.portal_utils.Portal.get_metadata", return_value={"dummy": "dummy"}):
            with mock.patch("dcicutils.portal_utils.Portal.is_schema_type", return_value=True):
                with mock.patch.object(command_utils_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch("requests.get", mocked_get):
                        index = 0
                        json_result = {}
                        with shown_output() as shown:
                            _show_upload_info(SOME_UUID, server=SOME_SERVER, env=None, keydict=SOME_KEYDICT)
                            assert shown.lines == ['Uploads: None']
                        index = 0
                        del URLS[1]
                        json_result = SOME_UPLOAD_INFO_RESULT
                        with shown_output() as shown:
                            _show_upload_info(SOME_UUID, server=SOME_SERVER, env=None, keydict=SOME_KEYDICT)
                            expected_lines = ['\n----- Upload Info -----']
                            assert shown.lines == expected_lines


def test_show_upload_info_with_app():

    expected_app = APP_FOURFRONT

    class TestFinished(BaseException):
        pass

    def mocked_get(url, *, auth, **kwargs):
        ignored(url, auth, kwargs)
        # This checks that the recursive call in _show_upload_info actually happened, binding the selected_app
        # to the given app. Once we've verified that, this test is done.
        raise TestFinished

    with mock.patch("dcicutils.portal_utils.Portal.get_schemas", return_value={"dummy": "dummy"}):
        with mock.patch("dcicutils.portal_utils.Portal.get_metadata", return_value={"dummy": "dummy"}):
            with mock.patch("dcicutils.portal_utils.Portal.is_schema_type", return_value=True):
                with mock.patch.object(command_utils_module, "script_catch_errors", script_dont_catch_errors):
                    with mock.patch("requests.get") as mock_get:
                        mock_get.side_effect = mocked_get
                        with mock.patch.object(submission_module, "_show_upload_result"):
                            assert mock_get.call_count == 0
                            with pytest.raises(TestFinished):
                                _show_upload_info(SOME_UUID,
                                                  server=SOME_SERVER, env=None, keydict=SOME_KEYDICT, app=expected_app)
                            assert mock_get.call_count == 1


def test_show_upload_result():

    # The primary output is handled a bit differently than other parts, so capture that nuance...
    upload_info_items: List
    for upload_info_items in [[], ['alpha', 'bravo']]:
        with shown_output() as shown:
            _show_upload_result({'upload_info': upload_info_items},
                                show_primary_result=True,
                                show_validation_output=False,
                                show_processing_status=False,
                                show_datafile_url=False)
            assert shown.lines == upload_info_items or "Uploads: None"  # special case for no uploads

    sample_validation_output = ['yep', 'uh huh', 'wait, what?']
    for show_validation in [False, True]:
        with shown_output() as shown:
            _show_upload_result({'validation_output': sample_validation_output},
                                show_primary_result=False,
                                show_validation_output=show_validation,
                                show_processing_status=False,
                                show_datafile_url=False)
            # assert shown.lines == (['----- Validation Output -----'] + sample_validation_output
            #                        if show_validation
            #                        else [])

    # Special case for 'parameters' relates to presence or absence of 'datafile_url' within it
    sample_non_data_parameters = {'some_key': 'some_value'}
    sample_datafile_url = 'some-datafile-url'
    test_cases = [
        (False, {}),
        (True, {'datafile_url': sample_datafile_url}),
        (False, {'datafile_url': ''}),
        (False, {'datafile_url': None})]
    sample_data_parameters: Dict
    for datafile_should_be_shown, sample_data_parameters in test_cases:
        with shown_output() as shown:
            _show_upload_result({'parameters': dict(sample_non_data_parameters, **sample_data_parameters)},
                                show_primary_result=False,
                                show_validation_output=False,
                                show_processing_status=False,
                                show_datafile_url=True)
            if datafile_should_be_shown:
                assert shown.lines == [
                    "----- DataFile URL -----",
                    sample_datafile_url,
                ]
            else:
                assert shown.lines == []

    for show_it in [False, True]:
        with shown_output() as shown:
            _show_upload_result({
                'processing_status': {
                    'state': 'some-state',
                    'outcome': 'some-outcome',
                    'progress': 'some-progress',
                }},
                show_primary_result=False,
                show_validation_output=False,
                show_processing_status=show_it,
                show_datafile_url=False)
            assert bool(shown.lines) is show_it

    for state in ['some-state', None]:
        n = 1 if state else 0
        for outcome in ['some-outcome', None]:
            n += 1 if outcome else 0
            for progress in ['some-progress', None]:
                n += 1 if progress else 0
                with shown_output() as shown:
                    _show_upload_result({
                        'processing_status': {
                            'state': state, 'outcome': outcome, 'progress': progress
                        }},
                        show_primary_result=False,
                        show_validation_output=False,
                        show_processing_status=True,
                        show_datafile_url=False)
                    # Heading is shown if there are n times, so that's the +1
                    # Otherwise one output line is shown for each non-null item
                    assert len(shown.lines) == 0 if n == 0 else n + 1


def test_show_section_without_caveat():

    nothing_to_show = []

    # Lines section available, without caveat.
    with shown_output() as shown:
        _show_section(
            res={'foo': ['abc', 'def']},
            section='foo',
            caveat_outcome=None)
        assert shown.lines == [
            '\n----- Foo -----',
            'abc',
            'def',
        ]

    # Lines section available, without caveat, but no section entry.
    with shown_output() as shown:
        _show_section(
            res={},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == nothing_to_show

    # Lines section available, without caveat, but empty.
    with shown_output() as shown:
        _show_section(
            res={'foo': []},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == nothing_to_show

    # Lines section available, without caveat, but null.
    with shown_output() as shown:
        _show_section(
            res={'foo': None},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == nothing_to_show

    # Dictionary section available, without caveat, and with a dictionary.
    with shown_output() as shown:
        _show_section(
            res={'foo': {'alpha': 'beta', 'gamma': 'delta'}},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == ['\n----- Foo -----']

    # Dictionary section available, without caveat, and with an empty dictionary.
    with shown_output() as shown:
        _show_section(
            res={'foo': {}},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == nothing_to_show

    # Random unexpected data, with caveat.
    with shown_output() as shown:
        _show_section(
            res={'foo': 17},
            section='foo',
            caveat_outcome=None
        )
        assert shown.lines == [
            '\n----- Foo -----',
            '17',
        ]


def test_show_section_with_caveat():

    # Some output is shown marked by a caveat, that indicates execution stopped early for some reason
    # and the output is partial.

    caveat = 'some error'

    # Lines section available, with caveat.
    with shown_output() as shown:
        _show_section(
            res={'foo': ['abc', 'def']},
            section='foo',
            caveat_outcome=caveat
        )
        assert shown.lines == [
            '\n----- Foo (prior to %s) -----' % caveat,
            'abc',
            'def',
        ]

    # Lines section available, with caveat.
    with shown_output() as shown:
        _show_section(
            res={},
            section='foo',
            caveat_outcome=caveat
        )
        assert shown.lines == []  # Nothing shown if there is a caveat specified


class MockTime:
    def __init__(self, **kwargs):
        self._time = ControlledTime(**kwargs)

    def time(self):
        return (self._time.now() - self._time.INITIAL_TIME).total_seconds()


OS_SIMULATION_MODES = {
    "windows": {"os.name": "nt", "platform.system": "Windows"},
    "cygwin": {"os.name": "posix", "platform.system": "CYGWIN_NT-10.0"},  # just one of many examples
    "linux": {"os.name": "posix", "platform.system": "Linux"},
    "macos": {"os.name": "posix", "platform.system": "Darwin"}
}

OS_SIMULATION_MODE_NAMES = list(OS_SIMULATION_MODES.keys())


@contextlib.contextmanager
def os_simulation(*, simulation_mode):

    assert simulation_mode in OS_SIMULATION_MODES, f"{simulation_mode} is not a defined os simulation mode."
    info = OS_SIMULATION_MODES[simulation_mode]
    os_name = info['os.name']

    def mocked_system():
        return info['platform.system']

    with mock.patch.object(os, "name", os_name):
        with mock.patch.object(platform, "system") as mock_system:
            mock_system.side_effect = mocked_system
            yield


@pytest.mark.parametrize("os_simulation_mode", OS_SIMULATION_MODE_NAMES)
def obsolete_test_execute_prearranged_upload(os_simulation_mode: str):
    Portal.KEYS_FILE_DIRECTORY = "/dummy"
    with os_simulation(simulation_mode=os_simulation_mode):
        with mock.patch.object(os, "environ", SOME_ENVIRON.copy()):
            with shown_output() as shown:
                with pytest.raises(ValueError):
                    bad_credentials = SOME_UPLOAD_CREDENTIALS.copy()
                    bad_credentials.pop('SessionToken')
                    # This will abort quite early because it can't construct a proper set of credentials as env vars.
                    # Nothing has to be mocked because it won't get that far.
                    execute_prearranged_upload('this-file-name-is-not-used', bad_credentials)
                assert shown.lines == []

        subprocess_options = {}
        if _independently_confirmed_as_running_on_windows_native():
            subprocess_options = {'shell': True}

        with mock.patch.object(os, "environ", SOME_ENVIRON.copy()):
            with shown_output() as shown:
                with mock.patch("time.time", MockTime().time):
                    with mock.patch("subprocess.call", return_value=0) as mock_aws_call:
                        execute_prearranged_upload(path=SOME_FILENAME, upload_credentials=SOME_UPLOAD_CREDENTIALS)
                        mock_aws_call.assert_called_with(
                            ['aws', 's3', 'cp', '--only-show-errors', SOME_FILENAME, SOME_UPLOAD_URL],
                            env=SOME_ENVIRON_WITH_CREDS,
                            **subprocess_options
                        )
                        assert shown.lines == [
                            "Uploading some-filename to: some-url",
                            "Upload of some-filename: OK -> 1.0 seconds",
                            # 1 tick (at rate of 1 second per tick in our controlled time)
                            # "Upload duration: 1.00 seconds"
                        ]

        with mock.patch.object(os, "environ", SOME_ENVIRON.copy()):
            with shown_output() as shown:
                with mock.patch("time.time", MockTime().time):
                    with mock.patch("subprocess.call", return_value=0) as mock_aws_call:
                        execute_prearranged_upload(path=SOME_FILENAME,
                                                   upload_credentials=SOME_EXTENDED_UPLOAD_CREDENTIALS)
                        mock_aws_call.assert_called_with(
                            ['aws', 's3', 'cp',
                             '--sse', 'aws:kms', '--sse-kms-key-id', SOME_S3_ENCRYPT_KEY_ID,
                             '--only-show-errors', SOME_FILENAME, SOME_UPLOAD_URL],
                            env=SOME_ENVIRON_WITH_CREDS,
                            **subprocess_options
                        )
                        assert shown.lines == [
                            "Uploading some-filename to: some-url",
                            "Upload of some-filename: OK -> 1.0 seconds",
                            # 1 tick (at rate of 1 second per tick in our controlled time)
                            # "Upload duration: 1.00 seconds"
                        ]

        with mock.patch.object(os, "environ", SOME_ENVIRON.copy()):
            with shown_output() as shown:
                with mock.patch("time.time", MockTime().time):
                    with mock.patch("subprocess.call", return_value=17) as mock_aws_call:
                        with raises_regexp(RuntimeError, "Upload failed with exit code 17"):
                            execute_prearranged_upload(path=SOME_FILENAME, upload_credentials=SOME_UPLOAD_CREDENTIALS)
                        mock_aws_call.assert_called_with(
                            ['aws', 's3', 'cp', '--only-show-errors', SOME_FILENAME, SOME_UPLOAD_URL],
                            env=SOME_ENVIRON_WITH_CREDS,
                            **subprocess_options
                        )
                        assert shown.lines == [
                            "Uploading some-filename to: some-url",
                        ]


@pytest.mark.parametrize('debug_protocol', [False, True])
def test_get_s3_encrypt_key_id(debug_protocol):

    with mock.patch.object(submission_module, 'get_s3_encrypt_key_id_from_health_page') as mock_health_page_getter:
        mock_health_page_getter.return_value = 'gotten-from-health-page'

        with printed_output() as printed:
            with mock.patch.object(submission_module, "DEBUG_PROTOCOL", debug_protocol):
                upload_creds = {'s3_encrypt_key_id': 'gotten-from-upload-creds', 'other-stuff': 'yes'}
                assert (get_s3_encrypt_key_id(upload_credentials=upload_creds, auth='not-used-by-mock')
                        == 'gotten-from-upload-creds')
                assert mock_health_page_getter.call_count == 0
                assert printed.lines == (['Extracted s3_encrypt_key_id from upload_credentials:'
                                          ' gotten-from-upload-creds']
                                         if debug_protocol
                                         else [])

                printed.lines = []
                upload_creds = {'s3_encrypt_key_id': None, 'other-stuff': 'yes'}
                assert (get_s3_encrypt_key_id(upload_credentials=upload_creds, auth='not-used-by-mock')
                        is None)
                assert mock_health_page_getter.call_count == 0
                assert printed.lines == (['Extracted s3_encrypt_key_id from upload_credentials: None']
                                         if debug_protocol
                                         else [])

                printed.lines = []
                upload_creds = {'other-stuff': 'yes'}
                assert (get_s3_encrypt_key_id(upload_credentials=upload_creds, auth='not-used-by-mock')
                        == 'gotten-from-health-page')
                assert mock_health_page_getter.call_count == 1
                assert printed.lines == (["No s3_encrypt_key_id entry found in upload_credentials.",
                                          "Fetching s3_encrypt_key_id from health page.",
                                          " =id=> 'gotten-from-health-page'"]
                                         if debug_protocol
                                         else [])

                mock_health_page_getter.return_value = None

                printed.lines = []
                upload_creds = {'other-stuff': 'yes'}
                assert get_s3_encrypt_key_id(upload_credentials=upload_creds, auth='not-used-by-mock') is None
                assert mock_health_page_getter.call_count == 2
                assert printed.lines == (["No s3_encrypt_key_id entry found in upload_credentials.",
                                          "Fetching s3_encrypt_key_id from health page.",
                                          " =id=> None"]
                                         if debug_protocol
                                         else [])


@pytest.mark.parametrize("mocked_s3_encrypt_key_id", [None, "", TEST_ENCRYPT_KEY])
def test_get_s3_encrypt_key_id_from_health_page(mocked_s3_encrypt_key_id):
    with mock.patch.object(submission_module, "_get_health_page") as mock_get_health_page:
        mock_get_health_page.return_value = {HealthPageKey.S3_ENCRYPT_KEY_ID: mocked_s3_encrypt_key_id}
        assert get_s3_encrypt_key_id_from_health_page(auth='not-used-by-mock') == mocked_s3_encrypt_key_id


def test_upload_file_to_uuid():

    with mock.patch("dcicutils.portal_utils.Portal.patch_metadata", return_value=SOME_UPLOAD_CREDENTIALS_RESULT):
        with mock.patch.object(submission_module, "execute_prearranged_upload") as mocked_upload:
            metadata = upload_file_to_uuid(filename=SOME_FILENAME, uuid=SOME_UUID,
                                           rclone_google_config=None,
                                           auth=SOME_AUTH, first_time=False, portal=None)
            assert metadata == SOME_FILE_METADATA
            mocked_upload.assert_called_with(SOME_FILENAME, auth=SOME_AUTH,
                                             rclone_google_config=None,
                                             upload_credentials=SOME_UPLOAD_CREDENTIALS)

    with mock.patch("dcicutils.portal_utils.Portal.patch_metadata", return_value=SOME_BAD_RESULT):
        with mock.patch.object(submission_module, "execute_prearranged_upload") as mocked_upload:
            try:
                upload_file_to_uuid(filename=SOME_FILENAME, uuid=SOME_UUID,
                                    rclone_google_config=None,
                                    auth=SOME_AUTH, first_time=False, portal=None)
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


def get_today_datetime_for_time(time_to_use):
    today = datetime.date.today()
    time = datetime.time.fromisoformat(time_to_use)
    datetime_at_time_to_use = datetime.datetime.fromisoformat(
        f"{today.isoformat()}T{time.isoformat()}"
    )
    return datetime_at_time_to_use


class Scenario:

    START_TIME_FOR_TESTS = "12:00:00"
    WAIT_TIME_FOR_TEST_UPDATES_SECONDS = 1

    def __init__(self, start_time=None, wait_time_delta=None, bundles_bucket=None):
        self.bundles_bucket = bundles_bucket
        self.start_time = start_time or self.START_TIME_FOR_TESTS
        self.wait_time_delta = wait_time_delta or self.WAIT_TIME_FOR_TEST_UPDATES_SECONDS

    def get_time_after_wait(self):
        datetime_at_start_time = get_today_datetime_for_time(self.start_time)
        time_delta = datetime.timedelta(seconds=self.wait_time_delta)
        datetime_at_end_time = datetime_at_start_time + time_delta
        end_time = datetime_at_end_time.time()
        return end_time.isoformat()

    def make_uploaded_lines(self):
        uploaded_time = self.get_time_after_wait()
        result = [
            f"The server {SOME_SERVER} recognizes you as: {SOME_USER_TITLE} <{SOME_USER_EMAIL}>",
            f'Using given consortium: {SOME_CONSORTIUM}',
            f'Using given submission center: {SOME_SUBMISSION_CENTER}',
        ]
        if submission_module.DEBUG_PROTOCOL:  # pragma: no cover - useful if it happens to help, but not a big deal
            result.append(f"Created IngestionSubmission object: s3://{self.bundles_bucket}/{SOME_UUID}")
        result.append(f"{uploaded_time} Metadata bundle uploaded to bucket ({self.bundles_bucket});"
                      f" tracking UUID: {SOME_UUID} Awaiting processing...")
        return result

    def make_wait_lines(self, wait_attempts, outcome: str = None, start_delta: int = 0):
        ignored(start_delta)
        result = []
        time_delta_from_start = 0
        uploaded_time = self.get_time_after_wait()

        adjusted_scenario = Scenario(start_time=uploaded_time, wait_time_delta=time_delta_from_start)
        wait_time = adjusted_scenario.get_time_after_wait()
        result.append(f"{wait_time} Checking ingestion process for IngestionSubmission uuid {SOME_UUID} ...")
        time_delta_from_start += 1

        nchecks = 0
        ERASE_LINE = "\033[K"
        for idx in range(wait_attempts + 1):
            time_delta_from_start += 1
            adjusted_scenario = Scenario(start_time=uploaded_time, wait_time_delta=time_delta_from_start)
            wait_time = adjusted_scenario.get_time_after_wait()
            wait_line = (f"{ERASE_LINE}{wait_time} Checking processing"
                         f" | Status: Not Done Yet | Checked: {nchecks} time{'s' if nchecks != 1 else ''} ...\r")
            result.append(wait_line)
            if nchecks >= wait_attempts:
                time_delta_from_start += 1
                adjusted_scenario = Scenario(start_time=uploaded_time, wait_time_delta=time_delta_from_start)
                wait_time = adjusted_scenario.get_time_after_wait()
                if outcome == "timeout":
                    wait_line = (f"{ERASE_LINE}{wait_time} Giving up waiting for processing completion"
                                 f" | Status: Not Done Yet | Checked: {nchecks + 1} times\n\r")
                else:
                    wait_line = (f"{ERASE_LINE}{wait_time} Processing complete"
                                 f" | Status: {outcome.title() if outcome else 'Unknown'}"
                                 f" | Checked: {nchecks + 1} times\n\r")
                result.append(wait_line)
                break
            nchecks += 1
            for i in range(PROGRESS_CHECK_INTERVAL):
                time_delta_from_start += 2  # Extra 1 for the 1-second sleep loop in utils.check_repeatedly
                adjusted_scenario = Scenario(start_time=uploaded_time, wait_time_delta=time_delta_from_start)
                wait_time = adjusted_scenario.get_time_after_wait()
                wait_line = (
                    f"{ERASE_LINE}{wait_time} Waiting for processing completion"
                    f" | Status: Not Done Yet | Checked: {idx + 1} time{'s' if idx + 1 != 1 else ''}"
                    f" | Next check: {PROGRESS_CHECK_INTERVAL - i}"
                    f" second{'s' if PROGRESS_CHECK_INTERVAL - i != 1 else ''} ...\r"
                )
                result.append(wait_line)
        return result

    @classmethod
    def make_timeout_lines(cls, *, get_attempts=ATTEMPTS_BEFORE_TIMEOUT):
        ignored(get_attempts)
        # wait_time = self.get_elapsed_time_for_get_attempts(get_attempts)
        # adjusted_scenario = Scenario(start_time=wait_time, wait_time_delta=self.wait_time_delta)
        # time_out_time = adjusted_scenario.get_time_after_wait()
        return [f"Exiting after check processing timeout"
                f" using 'check-submision --server {SOME_SERVER} {SOME_UUID}'."]

    def make_outcome_lines(self, get_attempts, *, outcome):
        end_time = self.get_elapsed_time_for_get_attempts(get_attempts)
        return [f"{end_time} Final status: {outcome.title()}"]

    def get_elapsed_time_for_get_attempts(self, get_attempts):
        initial_check_time_delta = self.wait_time_delta
        # Extra PROGRESS_CHECK_INTERVAL for the 1-second sleep loop in utils.check_repeatedly,
        # via make_wait_lines; and extra 3 for the extra (first/last) lines in make_wait_lines and a header line.
        extra_waits = 3
        wait_time_delta = ((PROGRESS_CHECK_INTERVAL + self.wait_time_delta) * get_attempts
                           + PROGRESS_CHECK_INTERVAL
                           + extra_waits)
        elapsed_time_delta = initial_check_time_delta + wait_time_delta
        adjusted_scenario = Scenario(start_time=self.start_time, wait_time_delta=elapsed_time_delta)
        return adjusted_scenario.get_time_after_wait()

    @classmethod
    def make_submission_lines(cls, get_attempts, outcome):
        scenario = Scenario()
        result = []
        wait_attempts = get_attempts - 1
        result += scenario.make_uploaded_lines()  # uses one tick, so we start wait lines offset by 1
        if wait_attempts > 0:
            result += scenario.make_wait_lines(wait_attempts, outcome=outcome, start_delta=1)
        result += scenario.make_outcome_lines(get_attempts, outcome=outcome)
        return result

    @classmethod
    def make_successful_submission_lines(cls, get_attempts):
        return cls.make_submission_lines(get_attempts, outcome="success")

    @classmethod
    def make_failed_submission_lines(cls, get_attempts):
        return cls.make_submission_lines(get_attempts, outcome="error")

    @classmethod
    def make_timeout_submission_lines(cls):
        scenario = Scenario()
        result = []
        result += scenario.make_uploaded_lines()  # uses one tick, so we start wait lines offset by 1
        result += scenario.make_wait_lines(ATTEMPTS_BEFORE_TIMEOUT - 1, outcome="timeout", start_delta=1)
        result += scenario.make_timeout_lines()
        return result


# SOME_ORG_ARGS = {'institution': SOME_INSTITUTION, 'project': SOME_PROJECT}
SOME_ORG_ARGS = {'consortium': SOME_CONSORTIUM, 'submission_center': SOME_SUBMISSION_CENTER}


def test_running_on_windows_native():
    for pair in [("nt", True), ("posix", False)]:
        os_name, is_windows = pair
        with mock.patch.object(os, "name", os_name):
            assert _running_on_windows_native() is is_windows


def test_resolve_app_args():

    # No arguments specified. Presumably they'll later be defaulted.

    res = _resolve_app_args(institution=None, project=None, lab=None, award=None,
                            consortium=None, submission_center=None, app=APP_CGAP)
    assert res == {'institution': None, 'project': None}

    res = _resolve_app_args(institution=None, project=None, lab=None, award=None,
                            consortium=None, submission_center=None, app=APP_FOURFRONT)
    assert res == {'lab': None, 'award': None}

    res = _resolve_app_args(institution=None, project=None, lab=None, award=None,
                            consortium=None, submission_center=None, app=APP_SMAHT)
    assert res == {'consortia': None, 'submission_centers': None}

    res = _resolve_app_args(institution=None, project=None, lab=None, award=None,
                            consortium="", submission_center="", app=APP_SMAHT)
    assert res == {'consortia': [], 'submission_centers': []}

    # Exactly the right arguments.

    res = _resolve_app_args(institution='foo', project='bar', lab=None, award=None,
                            consortium=None, submission_center=None, app=APP_CGAP)
    assert res == {'institution': 'foo', 'project': 'bar'}

    res = _resolve_app_args(institution=None, project=None, lab='foo', award='bar',
                            consortium=None, submission_center=None, app=APP_FOURFRONT)
    assert res == {'lab': 'foo', 'award': 'bar'}

    # Testing this for consortium= and submission_center= is slightly more elaborate because we allow
    # comma-separated values. We use the singular in the keywords since it looks better, but you can
    # say not just consortium=C1 but also consortium=C1,C2. Same for submission_centers=SC1 or ...=SC1,SC2.

    sample_consortium = 'C1'
    sample_consortia = 'C1,C2'
    sample_consortia_list = ['C1', 'C2']
    sample_submission_center = 'SC1'
    sample_submission_centers = 'SC1,SC2'
    sample_submission_centers_list = ['SC1', 'SC2']

    res = _resolve_app_args(consortium=sample_consortium, submission_center=sample_submission_center,
                            institution=None, project=None, lab=None, award=None,
                            app=APP_SMAHT)
    assert res == {'consortia': [sample_consortium], 'submission_centers': [sample_submission_center]}

    res = _resolve_app_args(consortium=sample_consortia, submission_center=sample_submission_centers,
                            institution=None, project=None, lab=None, award=None,
                            app=APP_SMAHT)
    assert res == {'consortia': sample_consortia_list, 'submission_centers': sample_submission_centers_list}

    # Bad arguments for CGAP.

    with pytest.raises(ValueError) as exc:
        _resolve_app_args(institution=None, project=None, lab='foo', award='bar',
                          consortium=None, submission_center=None, app=APP_CGAP)
    assert str(exc.value) == 'There are 2 inappropriate arguments: --lab and --award.'

    with pytest.raises(ValueError) as exc:
        _resolve_app_args(institution=None, project=None, lab='foo', award=None,
                          consortium=None, submission_center=None, app=APP_CGAP)
    assert str(exc.value) == 'There is 1 inappropriate argument: --lab.'

    for argname in ['award', 'consortium', 'submission_center']:

        with pytest.raises(ValueError) as exc:
            kwargs = {'institution': None, 'project': None, 'lab': None, 'award': None,
                      'consortium': None, 'submission_center': None}
            kwargs[argname] = 'foo'
            _resolve_app_args(**kwargs, app=APP_CGAP)
        ui_argname = argname.replace('_', '-')
        assert str(exc.value) == f'There is 1 inappropriate argument: --{ui_argname}.'

    # Bad arguments for Fourfront

    with pytest.raises(ValueError) as exc:
        _resolve_app_args(institution='foo', project='bar', lab=None, award=None,
                          consortium=None, submission_center=None, app=APP_FOURFRONT)
    assert str(exc.value) == 'There are 2 inappropriate arguments: --institution and --project.'

    with pytest.raises(ValueError) as exc:
        _resolve_app_args(institution='foo', project=None, lab=None, award=None,
                          consortium=None, submission_center=None, app=APP_FOURFRONT)
    assert str(exc.value) == 'There is 1 inappropriate argument: --institution.'

    with pytest.raises(ValueError) as exc:
        _resolve_app_args(institution=None, project='bar', lab=None, award=None,
                          consortium=None, submission_center=None, app=APP_FOURFRONT)
    assert str(exc.value) == 'There is 1 inappropriate argument: --project.'

    # Bogus application name

    with pytest.raises(ValueError) as exc:
        invalid_app = 'NOT-' + DEFAULT_APP  # make a bogus app name
        _resolve_app_args(institution=None, project=None, lab=None, award=None,
                          consortium=None, submission_center=None, app=invalid_app)
    assert str(exc.value) == f"Unknown application: {invalid_app}"


def test_submit_any_ingestion():

    print()  # start on a fresh line

    expected_app = APP_FOURFRONT

    class StopEarly(BaseException):
        pass

    def mocked_resolve_app_args(*, institution, project, lab, award, consortium, submission_center, app):
        ignored(institution, project, award, lab, consortium, submission_center)  # not relevant to this mock
        assert app == expected_app
        raise StopEarly()

    original_submit_any_ingestion = submit_any_ingestion

    def wrapped_submit_any_ingestion(*args, **kwargs):
        return original_submit_any_ingestion(*args, **kwargs)

    mfs = MockFileSystem()
    with mock.patch.object(Portal, "key", new_callable=mock.PropertyMock) as mocked_portal_key_property:
        mocked_portal_key_property.return_value = SOME_KEYDICT
        with mock.patch("os.path.exists", mfs.exists):
            with mock.patch.object(submission_module, 'submit_any_ingestion') as mock_submit_any_ingestion:
                mock_submit_any_ingestion.side_effect = wrapped_submit_any_ingestion
                with mock.patch.object(submission_module, "_resolve_app_args") as mock_resolve_app_args:
                    try:
                        mock_resolve_app_args.side_effect = mocked_resolve_app_args
                        mock_submit_any_ingestion(
                            ingestion_filename=SOME_FILENAME,
                            ingestion_type=SOME_INGESTION_TYPE, server=SOME_SERVER, env=SOME_ENV,
                            validate_remote_only=True, institution=SOME_INSTITUTION, project=SOME_PROJECT,
                            lab=SOME_LAB, award=SOME_AWARD,
                            consortium=SOME_CONSORTIUM, submission_center=SOME_SUBMISSION_CENTER,
                            upload_folder=SOME_FILENAME,
                            no_query=True, subfolders=False,
                            # This is what we're testing...
                            app=expected_app)
                    except StopEarly:
                        assert mock_submit_any_ingestion.call_count == 1
                        pass  # in this case, it also means pass the test


def test_get_defaulted_lab():

    assert _get_defaulted_lab(lab=SOME_LAB, user_record='does-not-matter') == SOME_LAB
    assert _get_defaulted_lab(lab='anything', user_record='does-not-matter') == 'anything'

    user_record = make_user_record(
        # this is the old-fashioned place for it, but what fourfront uses
        lab={'@id': SOME_LAB},
    )

    successful_result = _get_defaulted_lab(lab=None, user_record=user_record)

    print("successful_result=", successful_result)

    assert successful_result == SOME_LAB

    assert _get_defaulted_lab(lab=None, user_record=make_user_record()) is None
    assert _get_defaulted_lab(lab=None, user_record=make_user_record(), error_if_none=False) is None

    with pytest.raises(Exception) as exc:
        _get_defaulted_lab(lab=None, user_record=make_user_record(), error_if_none=True)
    assert str(exc.value).startswith("Your user profile has no lab")


def test_get_defaulted_award():

    assert _get_defaulted_award(award=SOME_AWARD, user_record='does-not-matter') == SOME_AWARD
    assert _get_defaulted_award(award='anything', user_record='does-not-matter') == 'anything'

    successful_result = _get_defaulted_award(award=None,
                                             user_record=make_user_record(
                                                 lab={
                                                     '@id': SOME_LAB,
                                                     'awards': [
                                                         {"@id": SOME_AWARD},
                                                     ]}))

    print("successful_result=", successful_result)

    assert successful_result == SOME_AWARD

    # We decided to make this function not report errors on lack of award,
    # but we did add a way to request the error reporting, so we test that with an explicit
    # error_if_none=True argument. -kmp 27-Mar-2023

    try:
        _get_defaulted_award(award=None,
                             user_record=make_user_record(award_roles=[]),
                             error_if_none=True)
    except Exception as e:
        assert str(e).startswith("Your user profile declares no lab with awards.")
    else:
        raise AssertionError("Expected error was not raised.")  # pragma: no cover

    with pytest.raises(Exception) as exc:
        _get_defaulted_award(award=None,
                             user_record=make_user_record(lab={
                                 '@id': SOME_LAB,
                                 'awards': [
                                     {"@id": "/awards/foo"},
                                     {"@id": "/awards/bar"},
                                     {"@id": "/awards/baz"},
                                 ]}),
                             error_if_none=True)
    assert str(exc.value) == ("Your lab (/lab/good-lab/) declares multiple awards."
                              " You must explicitly specify one of /awards/foo, /awards/bar"
                              " or /awards/baz with --award.")

    assert _get_defaulted_award(award=None, user_record=make_user_record()) is None
    assert _get_defaulted_award(award=None, user_record=make_user_record(), error_if_none=False) is None

    with pytest.raises(Exception) as exc:
        _get_defaulted_award(award=None, user_record=make_user_record(), error_if_none=True)
    assert str(exc.value).startswith("Your user profile declares no lab with awards.")


def test_get_defaulted_consortia():

    assert _get_defaulted_consortia(consortia=SOME_CONSORTIA, user_record='does-not-matter') == SOME_CONSORTIA
    assert _get_defaulted_consortia(consortia=['anything'], user_record='does-not-matter') == ['anything']

    user_record = make_user_record(consortia=[{'@id': SOME_CONSORTIUM}])

    successful_result = _get_defaulted_consortia(consortia=None, user_record=user_record)

    print("successful_result=", successful_result)

    assert successful_result == SOME_CONSORTIA

    with pytest.raises(SystemExit) as exc:
        _get_defaulted_consortia(consortia=None, user_record=make_user_record()) == []
        _get_defaulted_consortia(consortia=None, user_record=make_user_record(),
                                 error_if_none=False) == []

    with pytest.raises(Exception) as exc:
        _get_defaulted_consortia(consortia=None, user_record=make_user_record(), error_if_none=True)
    assert str(exc.value).startswith("Your user profile has no consortium")


def test_get_defaulted_submission_centers():

    assert _get_defaulted_submission_centers(submission_centers=SOME_SUBMISSION_CENTERS,
                                             user_record='does-not-matter') == SOME_SUBMISSION_CENTERS
    assert _get_defaulted_submission_centers(submission_centers=['anything'],
                                             user_record='does-not-matter') == ['anything']

    user_record = make_user_record(submission_centers=[{'@id': SOME_SUBMISSION_CENTER}])

    successful_result = _get_defaulted_submission_centers(submission_centers=None, user_record=user_record)

    print("successful_result=", successful_result)

    assert successful_result == SOME_SUBMISSION_CENTERS

    with pytest.raises(SystemExit) as exc:
        _get_defaulted_submission_centers(submission_centers=None, user_record=make_user_record()) == []
        _get_defaulted_submission_centers(submission_centers=None, user_record=make_user_record(),
                                          error_if_none=False) == []

    with pytest.raises(Exception) as exc:
        _get_defaulted_submission_centers(submission_centers=None, user_record=make_user_record(), error_if_none=True)
    assert str(exc.value).startswith("Your user profile has no submission center")


def test_post_files_data():

    with mock.patch("io.open") as mock_open:

        test_filename = 'file_to_be_posted.something'
        mock_open.return_value = mocked_open_file = NamedObject('mocked open file')

        d = _post_files_data(SubmissionProtocol.UPLOAD, test_filename)
        assert d == {'datafile': mocked_open_file}
        mock_open.called_with(test_filename, 'rb')

        mock_open.reset_mock()

        d = _post_files_data(SubmissionProtocol.S3, test_filename)
        assert d == {'datafile': None}
        mock_open.assert_not_called()


def test_compute_file_post_data():

    assert compute_file_post_data('foo.bar', dict(lab=None, award=None, institution=None, project=None)) == {
        'filename': 'foo.bar',
        'file_format': 'bar',
    }

    assert compute_file_post_data('foo.bar', dict(lab='/labs/L1/', award='/awards/A1/',
                                                  institution=None, project=None)) == {
        'filename': 'foo.bar',
        'file_format': 'bar',
        'lab': '/labs/L1/',
        'award': '/awards/A1/',
    }

    assert compute_file_post_data('foo.bar', dict(lab=None, award=None,
                                                  institution='/institutions/I1/', project='/projects/P1/')) == {
        'filename': 'foo.bar',
        'file_format': 'bar',
        'institution': '/institutions/I1/',
        'project': '/projects/P1/'
    }


mocked_key = 'an_authorized_key'
mocked_secret = 'an_authorized_secret'
mocked_good_auth = {'key': mocked_key, 'secret': mocked_secret}
mocked_bad_auth = {'key': f'not_{mocked_key}', 'secret': f'not_{mocked_secret}'}
mocked_good_uuid = 'good-uuid-0000-0001'
mocked_good_at_id = '/things/good-thing/'
mocked_award_and_lab = {'award': '/awards/A1/', 'lab': '/labs/L1/'}
mocked_institution_and_project = {'institution': '/institution/I1/', 'project': '/projects/P1/'}
mocked_good_filename_base = 'some_good'
mocked_good_filename_ext = 'file'
mocked_good_filename = f'{mocked_good_filename_base}.{mocked_good_filename_ext}'
mocked_s3_upload_bucket = 'some-bucket'
mocked_s3_upload_key = f'{mocked_good_uuid}/{mocked_good_filename}'
mocked_s3_url = f's3://{mocked_s3_upload_bucket}/{mocked_s3_upload_key}'
mocked_good_upload_credentials = {
    'key': mocked_s3_upload_key,
    'upload_url': mocked_s3_url,
    'upload_credentials': {
        'AccessKeyId': 'some-access-key-id',
        'SecretAccessKey': 'some-secret-access-key',
        'SessionToken': 'some-session-token-much-longer-than-this-mock'
    }
}
mocked_good_file_metadata = {
    'uuid': mocked_good_uuid,
    'accession': mocked_good_at_id,
    '@id': mocked_good_at_id,
    'key': mocked_good_filename,
    'upload_credentials': mocked_good_upload_credentials,
}
expected_schema_name = GENERIC_SCHEMA_TYPE


def test_do_app_arg_defaulting():

    default_default_foo = 17

    def get_defaulted_foo(foo, user_record, error_if_none=False, quiet=False, verbose=False):
        ignored(error_if_none)  # not needed for this mock
        return user_record.get('default-foo', default_default_foo) if foo is None else foo

    defaulters_for_testing = {
        'foo': get_defaulted_foo,
    }

    with mock.patch.object(submission_module, "APP_ARG_DEFAULTERS", defaulters_for_testing):

        args1 = {'foo': 1, 'bar': 2}
        user1 = {'default-foo': 4}
        _do_app_arg_defaulting(args1, user1)
        assert args1 == {'foo': 1, 'bar': 2}

        args2 = {'foo': None, 'bar': 2}
        user2 = {'default-foo': 4}
        _do_app_arg_defaulting(args2, user2)
        assert args2 == {'foo': 4, 'bar': 2}

        args3 = {'foo': None, 'bar': 2}
        user3 = {}
        _do_app_arg_defaulting(args3, user3)
        assert args3 == {'foo': 17, 'bar': 2}

        # Only the args already expressly present are defaulted
        args4 = {'bar': 2}
        user4 = {}
        _do_app_arg_defaulting(args4, user4)
        assert args4 == {'bar': 2}

        # If the defaulter returns None, the argument is removed rather than be None
        default_default_foo = None  # make defaulter return None if default not found on the user
        ignorable(default_default_foo)  # it gets used in the closure, PyCharm should know
        args5 = {'foo': None, 'bar': 2}
        user5 = {}
        _do_app_arg_defaulting(args5, user5)
        assert args4 == {'bar': 2}


def test_summarize_submission():

    # env supplied
    summary = _summarize_submission(uuid='some-uuid', env='some-env', app='some-app')
    assert summary == "check-submission --env some-env some-uuid"

    # server supplied
    summary = _summarize_submission(uuid='some-uuid', server='some-server', app='some-app')
    assert summary == "check-submission --server some-server some-uuid"

    # If both are supplied, env wins.
    summary = _summarize_submission(uuid='some-uuid', server='some-server', env='some-env', app='some-app')
    assert summary == "check-submission --env some-env some-uuid"

    # If neither is supplied, well, that shouldn't really happen, but we'll see this:
    summary = _summarize_submission(uuid='some-uuid', server=None, env=None, app='some-app')
    assert summary == "check-submission some-uuid"


def test_check_ingestion_progress():

    def test_it(data, *, expect_done, expect_short_status):
        def mocked_get(self, url, **kwargs):
            return FakeResponse(status_code=200, json=data)
        with mock.patch("dcicutils.portal_utils.Portal.get", mocked_get):
            res = _check_ingestion_progress('some-uuid',
                                            keypair=('some-keypair', 'some-keypair'), server='http://some-server')
        assert res == (expect_done, expect_short_status, data)

    test_it({}, expect_done=False, expect_short_status=None)
    test_it({'processing_status': {}}, expect_done=False, expect_short_status=None)
    test_it({'processing_status': {'progress': '13%'}}, expect_done=False, expect_short_status='13%')
    test_it({'processing_status': {'progress': 'working'}}, expect_done=False, expect_short_status='working')
    test_it({'processing_status': {'state': 'started', 'outcome': 'indexed'}},
            expect_done=False, expect_short_status=None)
    test_it({'processing_status': {'state': 'started'}},
            expect_done=False, expect_short_status=None)
    test_it({'processing_status': {'state': 'done', 'outcome': 'indexed'}},
            expect_done=True, expect_short_status='indexed')
    test_it({'processing_status': {'state': 'done'}},
            expect_done=True, expect_short_status=None)
