# To be written

import contextlib
import datetime
import io
import json
import os
import pytest
import re
import requests
import subprocess
import time

from dcicutils import ff_utils
from dcicutils.beanstalk_utils import get_beanstalk_real_url
from dcicutils.command_utils import yes_or_no
from dcicutils.env_utils import full_cgap_env_name
from dcicutils.lang_utils import n_of
from dcicutils.qa_utils import override_environ
from dcicutils.misc_utils import check_true, PRINT
from unittest import mock
from .. import submission as submission_module
from ..auth import get_keydict_for_server, keydict_to_keypair
from ..base import DEFAULT_ENV, DEFAULT_ENV_VAR, PRODUCTION_ENV, PRODUCTION_SERVER
from ..exceptions import CGAPPermissionError
from ..submission import (
    SERVER_REGEXP, check_institution, check_project, do_any_uploads, do_uploads,
    execute_prearranged_upload, get_section, get_user_record, ingestion_submission_item_url,
    resolve_server, resume_uploads, script_catch_errors, show_section, submit_metadata_bundle,
    upload_file_to_uuid, upload_item_data,
)
from ..utils import FakeResponse


def test_server_regexp():

    schemas = ['http', 'https']
    hosts = ['localhost', 'localhost:5000', 'fourfront-cgapfoo.what-ever.com',
             'cgap.hms.harvard.edu', 'foo.bar.cgap.hms.harvard.edu']
    final_slashes = ['/', '']  # 1 or 0 is good

    for schema in schemas:
        for host in hosts:
            for final_slash in ['/', '']:
                url_to_check = schema + "://" + host + final_slash
                print("Trying", url_to_check, "expecting match...")
                assert SERVER_REGEXP.match(url_to_check)

    non_matches = [
        "ftp://localhost:8000",
        "ftp://localhost:80ab",
        "http://localhost.localnet",
        "http://foo.bar",
        "https://foo.bar"
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


good_institution = '/institutions/hms-dbmi/'
good_project = '/projects/12a92962-8265-4fc0-b2f8-cf14f05db58b/'


def make_user_record(title='J Doe',
                     contact_email='jdoe@cgap.hms.harvard.edu',
                     **kwargs):
    user_record = {
        'title': title,
        'contact_email': contact_email,
    }
    user_record.update(kwargs)

    return user_record


def make_good_response(title='J Doe',
                       contact_email='jdoe@cgap.hms.harvard.edu',
                       **kwargs):
    return FakeResponse(status_code=200, json=make_user_record(title=title, contact_email=contact_email, **kwargs))


def test_get_user_record():

    good_auth = ('mykey', 'mysecret')

    def make_mocked_get(auth_failure_code=400):
        def mocked_get(url, *, auth):
            if auth != good_auth:
                return FakeResponse(status_code=auth_failure_code, json={'Title': 'Not logged in.'})
            return FakeResponse(status_code=200, json={'title': 'J Doe', 'contact_email': 'jdoe@cgap.hms.harvard.edu'})
        return mocked_get

    with mock.patch("requests.get", make_mocked_get(auth_failure_code=401)):
        with pytest.raises(CGAPPermissionError):
            get_user_record(server="http://localhost:12345", auth=None)

    with mock.patch("requests.get", make_mocked_get(auth_failure_code=403)):
        with pytest.raises(CGAPPermissionError):
            get_user_record(server="http://localhost:12345", auth=None)

    with mock.patch("requests.get", make_mocked_get()):
        get_user_record(server="http://localhost:12345", auth=good_auth)


def test_check_institution():

    assert check_institution(institution=good_institution, user_record='does-not-matter') == good_institution
    assert check_institution(institution='anything', user_record='does-not-matter') == 'anything'

    try:
        check_institution(institution=None, user_record=make_user_record())
    except Exception as e:
        assert str(e).startswith("Your user profile declares no institution")

    try:
        check_institution(institution=None,
                          user_record=make_user_record(submits_for=[]))
    except Exception as e:
        assert str(e).startswith("Your user profile declares no institution")
    else:
        raise AssertionError("Expected error was not raised.")

    successful_result = check_institution(institution=None,
                                          user_record=make_user_record(submits_for=[
                                              {"@id": "/institutions/bwh"}
                                          ]))

    try:
        check_institution(institution=None,
                          user_record=make_user_record(submits_for=[
                              {"@id": "/institutions/hms-dbmi/"},
                              {"@id": "/institutions/bch/"},
                              {"@id": "/institutions/bwh"}
                          ]
                          ))
    except Exception as e:
        assert str(e).startswith("You must use --institution to specify which institution")
    else:
        raise AssertionError("Expected error was not raised.")

    print("successful_result=", successful_result)

    assert successful_result == "/institutions/bwh"


def test_check_project():

    assert check_project(project=good_project, user_record='does-not-matter') == good_project
    assert check_project(project='anything', user_record='does-not-matter') == 'anything'

    try:
        check_project(project=None, user_record=make_user_record())
    except Exception as e:
        assert str(e).startswith("Your user profile has no project declared")

    try:
        check_project(project=None,
                      user_record=make_user_record(project={}))
    except Exception as e:
        assert str(e).startswith("Your user profile has no project declared")
    else:
        raise AssertionError("Expected error was not raised.")

    successful_result = check_project(project=None,
                                      user_record=make_user_record(project={'@id': good_project})
                                      )

    print("successful_result=", successful_result)

    assert successful_result == good_project


# PROGRESS_CHECK_INTERVAL = 15
#
#
# def get_section(res, section):
#     return res.get(section) or res.get('additional_data', {}).get(section)
#
#
# def show_section(res, section, caveat_outcome=None):
#     section_data = get_section(res, section)
#     if caveat_outcome and not section_data:
#         # In the case of non-success, be brief unless there's data to show.
#         return
#     if caveat_outcome:
#         caveat = " (prior to %s)" % caveat_outcome
#     else:
#         caveat = ""
#     show("----- %s%s -----" % (section.replace("_", " ").title(), caveat))
#     if isinstance(section_data, dict):
#         show(json.dumps(section_data, indent=2))
#     elif isinstance(section_data, list):
#         lines = section_data
#         if lines:
#             for line in lines:
#                 show(line)
#         else:
#             show("Nothing to show.")
#     else:
#         # This should not happen.
#         show(section_data)
#
#
# def ingestion_submission_item_url(server, uuid):
#     return server + "/ingestion-submissions/" + uuid + "?format=json"
#
#
# @contextlib.contextmanager
# def script_catch_errors():
#     try:
#         yield
#         exit(0)
#     except Exception as e:
#         show("%s: %s" % (e.__class__.__name__, str(e)))
#         exit(1)
#
#
# def submit_metadata_bundle(bundle_filename, institution, project, server, env, validate_only):
#
#     with script_catch_errors():
#
#         server = resolve_server(server=server, env=env)
#
#         validation_qualifier = " (for validation only)" if validate_only else ""
#
#         if not yes_or_no("Submit %s to %s%s?" % (bundle_filename, server, validation_qualifier)):
#             show("Aborting submission.")
#             exit(1)
#
#         keydict = get_keydict_for_server(server)
#         keypair = keydict_to_keypair(keydict)
#
#         user_record = get_user_record(server, auth=keypair)
#
#         institution = check_institution(institution, user_record)
#         project = check_project(project, user_record)
#
#         if not os.path.exists(bundle_filename):
#             raise ValueError("The file '%s' does not exist." % bundle_filename)
#
#         post_files = {
#             "datafile": io.open(bundle_filename, 'rb')
#         }
#
#         post_data = {
#             'ingestion_type': 'metadata_bundle',
#             'institution': institution,
#             'project': project,
#             'validate_only': validate_only,
#         }
#
#         submission_url = server + "/submit_for_ingestion"
#
#         res = requests.post(submission_url, auth=keypair, data=post_data, files=post_files).json()
#
#         # print(json.dumps(res, indent=2))
#
#         uuid = res['submission_id']
#
#         show("Bundle uploaded, assigned uuid %s for tracking. Awaiting processing..." % uuid, with_time=True)
#
#         tracking_url = ingestion_submission_item_url(server=server, uuid=uuid)
#
#         outcome = None
#         n_tries = 8
#         tries_left = n_tries
#         done = False
#         while tries_left > 0:
#             # Pointless to hit the queue immediately, so we avoid some
#             # server stress by sleeping even before the first try.
#             time.sleep(PROGRESS_CHECK_INTERVAL)
#             res = requests.get(tracking_url, auth=keypair).json()
#             processing_status = res['processing_status']
#             done = processing_status['state'] == 'done'
#             if done:
#                 outcome = processing_status['outcome']
#                 break
#             else:
#                 progress = processing_status['progress']
#                 show("Progress is %s. Continuing to wait..." % progress, with_time=True)
#             tries_left -= 1
#
#         if not done:
#             show("Timed out after %d tries." % n_tries, with_time=True)
#             exit(1)
#
#         show("Final status: %s" % outcome, with_time=True)
#
#         if outcome == 'error' and res.get('errors'):
#             show_section(res, 'errors')
#
#         caveat_outcome = None if outcome == 'success' else outcome
#
#         show_section(res, 'validation_output', caveat_outcome=caveat_outcome)
#
#         if validate_only:
#             exit(0)
#
#         show_section(res, 'post_output', caveat_outcome=caveat_outcome)
#
#         if outcome == 'success':
#             show_section(res, 'upload_info')
#             do_any_uploads(res, keydict, bundle_filename=bundle_filename)
#
#
# def do_any_uploads(res, keydict, bundle_folder=None, bundle_filename=None):
#     upload_info = get_section(res, 'upload_info')
#     if upload_info:
#         if yes_or_no("Upload %s?" % n_of(len(upload_info), "file")):
#             do_uploads(upload_info, auth=keydict,
#                        folder=bundle_folder or (os.path.dirname(bundle_filename) if bundle_filename else None))
#
#
# def resume_uploads(uuid, server=None, env=None, bundle_filename=None, keydict=None):
#
#     with script_catch_errors():
#
#         server = resolve_server(server=server, env=env)
#         keydict = keydict or get_keydict_for_server(server)
#         url = ingestion_submission_item_url(server, uuid)
#         response = requests.get(url, auth=keydict_to_keypair(keydict))
#         response.raise_for_status()
#         do_any_uploads(response.json(), keydict, bundle_filename=bundle_filename or os.path.abspath(os.path.curdir))
#
#
# def execute_prearranged_upload(path, upload_credentials):
#     """
#     This performs a file upload using special credentials received from ff_utils.patch_metadata.
#
#     :param path: the name of a local file to upload
#     :param upload_credentials: a dictionary of credentials to be used for the upload,
#         containing the keys 'AccessKeyId', 'SecretAccessKey', 'SessionToken', and 'upload_url'.
#     """
#
#     try:
#         env = dict(os.environ,
#                    AWS_ACCESS_KEY_ID=upload_credentials['AccessKeyId'],
#                    AWS_SECRET_ACCESS_KEY=upload_credentials['SecretAccessKey'],
#                    AWS_SECURITY_TOKEN=upload_credentials['SessionToken'])
#     except Exception as e:
#         raise("Upload specification is not in good form. %s: %s" % (e.__class__.__name__, e))
#
#     start = time.time()
#     try:
#         source = path
#         target = upload_credentials['upload_url']
#         show("Going to upload %s to %s." % (source, target))
#         subprocess.check_call(['aws', 's3', 'cp', '--only-show-errors', source, target], env=env)
#     except subprocess.CalledProcessError as e:
#         show("Upload failed with exit code %d" % e.returncode)
#     else:
#         end = time.time()
#         duration = end - start
#         show("Uploaded in %.2f seconds" % duration)
#
#
# def upload_file_to_uuid(filename, uuid, auth):
#     """
#     Upload file to a target environment.
#
#     :param filename: the name of a file to upload.
#     :param uuid: the item into which the filename is to be uploaded.
#     :param auth: auth info in the form of a dictionary containing 'key', 'secret', and 'server'.
#     """
#
#     # filename here should not include path
#     patch_data = {'filename': os.path.basename(filename)}
#
#     response = ff_utils.patch_metadata(patch_data, uuid, key=auth)
#
#     try:
#         [metadata] = response['@graph']
#         upload_credentials = metadata['upload_credentials']
#     except Exception:
#         raise RuntimeError("Unable to obtain upload credentials for file %s." % filename)
#
#     execute_prearranged_upload(filename, upload_credentials=upload_credentials)
#
#
# def do_uploads(upload_spec_list, auth, folder=None):
#     """
#
#     :param upload_spec_list: a list of upload_spec dictionaries, each of the form {'filename': ..., 'uuid': ...},
#         representing uploads to be formed.
#     :param auth: a dictionary-form auth spec, of the form {'key': ..., 'secret': ..., 'server': ...}
#         representing destination and credentials.
#     :param folder: a string naming a folder in which to find the filenames to be uploaded.
#     :return: None
#     """
#     for upload_spec in upload_spec_list:
#         filename = os.path.join(folder or os.path.curdir, upload_spec['filename'])
#         uuid = upload_spec['uuid']
#         if not yes_or_no("Upload %s?" % (filename,)):
#             show("OK, not uploading it.")
#             continue
#         try:
#             show("Uploading %s to item %s ..." % (filename, uuid))
#             upload_file_to_uuid(filename=filename, uuid=uuid, auth=auth)
#             show("Upload of %s to item %s was successful." % (filename, uuid))
#         except Exception as e:
#             show("%s: %s" % (e.__class__.__name__, e))
#
#
# def upload_item_data(part_filename, uuid, server, env):
#
#     server = resolve_server(server=server, env=env)
#
#     keydict = get_keydict_for_server(server)
#
#     # print("keydict=", json.dumps(keydict, indent=2))
#
#     if not yes_or_no("Upload %s to %s?" % (part_filename, server)):
#         show("Aborting submission.")
#         exit(1)
#
#     upload_file_to_uuid(filename=part_filename, uuid=uuid, auth=keydict)
