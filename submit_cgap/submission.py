import contextlib
import io
import json
import os
import re
import requests
import subprocess
import time

from dcicutils import ff_utils
from dcicutils.beanstalk_utils import get_beanstalk_real_url
from dcicutils.command_utils import yes_or_no
from dcicutils.env_utils import full_cgap_env_name
from dcicutils.lang_utils import n_of
from dcicutils.misc_utils import check_true
from .auth import get_keydict_for_server, keydict_to_keypair
from .base import DEFAULT_ENV, DEFAULT_ENV_VAR, PRODUCTION_ENV
from .exceptions import CGAPPermissionError
from .utils import show, keyword_as_title


# TODO: Will asks whether some of the errors in this file that are called "SyntaxError" really should be something else.
#  The thought was that they're syntax errors because they tend to reflect as a need for a change in the
#  command line argument syntax, but maybe I should raise other errors and just have them converted to syntax
#  errors in the command itself. Something to think about another day. -kmp 8-Sep-2020


SERVER_REGEXP = re.compile(
    # Note that this regular expression does NOT contain 4dnucleome.org for the same reason it requires
    # a fourfront-cgapXXX address. It is trying only to match cgap addresses, though of course it has to make an
    # exception for localhost debugging. You're on your own to make sure the right server is connected there.
    # -kmp 16-Aug-2020
    r"^(https?://localhost(:[0-9]+)?"
    r"|https?://fourfront-cgap[a-z0-9.-]*"
    r"|https?://([a-z-]+[.])*cgap[.]hms[.]harvard[.]edu)/?$"
)


def resolve_server(server, env):
    """
    Given a server spec or a beanstalk environment (or neither, but not both), returns a server spec.

    :param server: a server spec or None
      A server is the first part of a url (containing the schema, host and, optionally, port).
      e.g., http://cgap.hms.harvard.edu or http://localhost:8000
    :param env: a cgap beanstalk environment
    :return: a server spec
    """

    check_true(not server or not env, "You may not specify both 'server' and 'env'.", error_class=SyntaxError)

    if not server and not env:
        if DEFAULT_ENV:
            show("Defaulting to beanstalk environment '%s' because %s is set." % (env, DEFAULT_ENV_VAR))
            env = DEFAULT_ENV
        else:
            # Production default needs no explanation.
            env = PRODUCTION_ENV

    if env:
        try:
            env = full_cgap_env_name(env)
            server = get_beanstalk_real_url(env)
        except Exception:
            raise SyntaxError("The specified env is not a valid CGAP beanstalk name.")

    matched = SERVER_REGEXP.match(server)
    if not matched:
        raise ValueError("The server should be 'http://localhost:<port>' or 'https://<cgap-hostname>', not: %s"
                         % server)
    server = matched.group(1)

    return server


def get_user_record(server, auth):
    """
    Given a server and some auth info, gets the user record for the authorized user.

    This works by using the /me endpoint.

    :param server: a server spec
    :param auth: auth info to be used when contacting the server
    :return: the /me page in JSON format
    """

    user_url = server + "/me?format=json"
    user_record_response = requests.get(user_url, auth=auth)
    try:
        user_record = user_record_response.json()
    except Exception:
        user_record = {}
    try:
        if user_record_response.status_code in (401, 403) and user_record.get("Title") == "Not logged in.":
            show("Server did not recognize you with the given credentials.")
    except Exception:
        pass
    if user_record_response.status_code in (401, 403):
        raise CGAPPermissionError(server=server)
    user_record_response.raise_for_status()
    user_record = user_record_response.json()
    show("The server %s recognizes you as %s <%s>."
         % (server, user_record['title'], user_record['contact_email']))
    return user_record


def get_defaulted_institution(institution, user_record):
    """
    Returns the given institution or else if none is specified, it tries to infer an institution.

    :param institution: the @id of an institution
    :param user_record: the user record for the authorized user
    :return: the @id of an institution to use
    """

    if not institution:
        submits_for = user_record.get('submits_for', [])
        if len(submits_for) == 0:
            raise SyntaxError("Your user profile declares no institution"
                              " on behalf of which you are authorized to make submissions.")
        elif len(submits_for) > 1:
            raise SyntaxError("You must use --institution to specify which institution you are submitting for"
                              " (probably one of: %s)." % ", ".join([x['@id'] for x in submits_for]))
        else:
            institution = submits_for[0]['@id']
            show("Using institution:", institution)
    return institution


def get_defaulted_project(project, user_record):
    """
    Returns the given project or else if none is specified, it tries to infer a project.

    :param project: the @id of a project
    :param user_record: the user record for the authorized user
    :return: the @id of a project to use
    """
    if not project:
        project = user_record.get('project', {}).get('@id', None)
        if not project:
            raise SyntaxError("Your user profile has no project declared,"
                              " so you must specify a --project explicitly.")
        show("Using project:", project)
    return project


PROGRESS_CHECK_INTERVAL = 15


def get_section(res, section):
    """
    Given a description of an ingestion submission, returns a section name within that ingestion.

    :param res: the description of an ingestion submission as a python dictionary that represents JSON data
    :param section: the name of a section to find either in the toplevel or in additional_data.
    :return: the section's content
    """

    return res.get(section) or res.get('additional_data', {}).get(section)


def show_section(res, section, caveat_outcome=None):
    """
    Shows a given named section from a description of an ingestion submission.

    The caveat is used when there has been an error and should be a phrase that describes the fact that output
    shown is only up to the point of the caveat situation. Instead of a "My Heading" header the output will be
    "My Heading (prior to <caveat>)."

    :param res: the description of an ingestion submission as a python dictionary that represents JSON data
    :param section: the name of a section to find either in the toplevel or in additional_data.
    :param caveat_outcome: a phrase describing some caveat on the output
    """

    section_data = get_section(res, section)
    if caveat_outcome and not section_data:
        # In the case of non-success, be brief unless there's data to show.
        return
    if caveat_outcome:
        caveat = " (prior to %s)" % caveat_outcome
    else:
        caveat = ""
    show("----- %s%s -----" % (keyword_as_title(section), caveat))
    if not section_data:
        show("Nothing to show.")
    elif isinstance(section_data, dict):
        show(json.dumps(section_data, indent=2))
    elif isinstance(section_data, list):
        for line in section_data:
            show(line)
    else:  # We don't expect this, but such should be shown as-is, mostly to see what it is.
        show(section_data)


def ingestion_submission_item_url(server, uuid):
    return server + "/ingestion-submissions/" + uuid + "?format=json"


@contextlib.contextmanager
def script_catch_errors():
    try:
        yield
        exit(0)
    except Exception as e:
        show("%s: %s" % (e.__class__.__name__, str(e)))
        exit(1)


def submit_metadata_bundle(bundle_filename, institution, project, server, env, validate_only):
    """
    Does the core action of submitting a metadata bundle.

    :param bundle_filename: the name of the bundle file (.xls file) to be uploaded
    :param institution: the @id of the institution for which the submission is being done
    :param project: the @id of the project for which the submission is being done
    :param server: the server to upload to
    :param env: the beanstalk environment to upload to
    :param validate_only: whether to do stop after validation instead of proceeding to post metadata
    """

    with script_catch_errors():

        server = resolve_server(server=server, env=env)

        validation_qualifier = " (for validation only)" if validate_only else ""

        if not yes_or_no("Submit %s to %s%s?" % (bundle_filename, server, validation_qualifier)):
            show("Aborting submission.")
            exit(1)

        keydict = get_keydict_for_server(server)
        keypair = keydict_to_keypair(keydict)

        user_record = get_user_record(server, auth=keypair)

        institution = get_defaulted_institution(institution, user_record)
        project = get_defaulted_project(project, user_record)

        if not os.path.exists(bundle_filename):
            raise ValueError("The file '%s' does not exist." % bundle_filename)

        post_files = {
            "datafile": io.open(bundle_filename, 'rb')
        }

        post_data = {
            'ingestion_type': 'metadata_bundle',
            'institution': institution,
            'project': project,
            'validate_only': validate_only,
        }

        submission_url = server + "/submit_for_ingestion"

        response = requests.post(submission_url, auth=keypair, data=post_data, files=post_files)
        res = response.json()

        try:
            response.raise_for_status()
        except Exception:
            # For example, if you call this on an old version of cgap-portal that does not support this request,
            # the error will be a 415 error, because the tween code defaultly insists on applicatoin/json:
            # {
            #     "@type": ["HTTPUnsupportedMediaType", "Error"],
            #     "status": "error",
            #     "code": 415,
            #     "title": "Unsupported Media Type",
            #     "description": "",
            #     "detail": "Request content type multipart/form-data is not 'application/json'"
            # }
            title = res.get('title')
            message = title
            detail = res.get('detail')
            if detail:
                message += ": " + detail
            show(message)
            if title == "Unsupported Media Type":
                show("NOTE: This error is known to occur if the server does not support metadata bundle submission.")
            raise

        uuid = res['submission_id']

        show("Bundle uploaded, assigned uuid %s for tracking. Awaiting processing..." % uuid, with_time=True)

        tracking_url = ingestion_submission_item_url(server=server, uuid=uuid)

        outcome = None
        n_tries = 8
        tries_left = n_tries
        done = False
        while tries_left > 0:
            # Pointless to hit the queue immediately, so we avoid some
            # server stress by sleeping even before the first try.
            time.sleep(PROGRESS_CHECK_INTERVAL)
            res = requests.get(tracking_url, auth=keypair).json()
            processing_status = res['processing_status']
            done = processing_status['state'] == 'done'
            if done:
                outcome = processing_status['outcome']
                break
            else:
                progress = processing_status['progress']
                show("Progress is %s. Continuing to wait..." % progress, with_time=True)
            tries_left -= 1

        if not done:
            show("Timed out after %d tries." % n_tries, with_time=True)
            exit(1)

        show("Final status: %s" % outcome, with_time=True)

        if outcome == 'error' and res.get('errors'):
            show_section(res, 'errors')

        caveat_outcome = None if outcome == 'success' else outcome

        show_section(res, 'validation_output', caveat_outcome=caveat_outcome)

        if validate_only:
            exit(0)

        show_section(res, 'post_output', caveat_outcome=caveat_outcome)

        if outcome == 'success':
            show_section(res, 'upload_info')
            do_any_uploads(res, keydict=keydict, bundle_filename=bundle_filename)

        exit(0)


def show_upload_info(uuid, server=None, env=None, keydict=None):
    """
    Uploads the files associated with a given metadata_bundle. This is useful if you answered "no" to the query
    about uploading your data and then later are ready to do that upload.

    :param uuid: a string guid that identifies the metadata_bundle's ingestion_submission
    :param server: the server to upload to
    :param env: the beanstalk environment to upload to
    :param keydict: keydict-style auth, a dictionary of 'key', 'secret', and 'server'
    """

    with script_catch_errors():

        server = resolve_server(server=server, env=env)
        keydict = keydict or get_keydict_for_server(server)
        url = ingestion_submission_item_url(server, uuid)
        response = requests.get(url, auth=keydict_to_keypair(keydict))
        response.raise_for_status()
        res = response.json()
        if get_section(res, 'upload_info'):
            show_section(res, 'upload_info')
        else:
            show("No uploads.")


def do_any_uploads(res, keydict, bundle_folder=None, bundle_filename=None):
    upload_info = get_section(res, 'upload_info')
    if upload_info:
        if yes_or_no("Upload %s?" % n_of(len(upload_info), "file")):
            do_uploads(upload_info, auth=keydict,
                       folder=bundle_folder or (os.path.dirname(bundle_filename) if bundle_filename else None))
        else:
            show("No uploads attempted.")


def resume_uploads(uuid, server=None, env=None, bundle_filename=None, keydict=None):
    """
    Uploads the files associated with a given metadata_bundle. This is useful if you answered "no" to the query
    about uploading your data and then later are ready to do that upload.

    :param uuid: a string guid that identifies the metadata_bundle's ingestion_submission
    :param server: the server to upload to
    :param env: the beanstalk environment to upload to
    :param bundle_filename: th metadata_bundle file to be uploaded
    :param keydict: keydict-style auth, a dictionary of 'key', 'secret', and 'server'
    """

    with script_catch_errors():

        server = resolve_server(server=server, env=env)
        keydict = keydict or get_keydict_for_server(server)
        url = ingestion_submission_item_url(server, uuid)
        response = requests.get(url, auth=keydict_to_keypair(keydict))
        response.raise_for_status()
        do_any_uploads(response.json(),
                       keydict=keydict,
                       bundle_filename=bundle_filename or os.path.abspath(os.path.curdir))


def execute_prearranged_upload(path, upload_credentials):
    """
    This performs a file upload using special credentials received from ff_utils.patch_metadata.

    :param path: the name of a local file to upload
    :param upload_credentials: a dictionary of credentials to be used for the upload,
        containing the keys 'AccessKeyId', 'SecretAccessKey', 'SessionToken', and 'upload_url'.
    """

    try:
        env = dict(os.environ,
                   AWS_ACCESS_KEY_ID=upload_credentials['AccessKeyId'],
                   AWS_SECRET_ACCESS_KEY=upload_credentials['SecretAccessKey'],
                   AWS_SECURITY_TOKEN=upload_credentials['SessionToken'])
    except Exception as e:
        raise ValueError("Upload specification is not in good form. %s: %s" % (e.__class__.__name__, e))

    start = time.time()
    try:
        source = path
        target = upload_credentials['upload_url']
        show("Going to upload %s to %s." % (source, target))
        subprocess.check_call(['aws', 's3', 'cp', '--only-show-errors', source, target], env=env)
    except subprocess.CalledProcessError as e:
        show("Upload failed with exit code %d" % e.returncode)
    else:
        end = time.time()
        duration = end - start
        show("Uploaded in %.2f seconds" % duration)


def upload_file_to_uuid(filename, uuid, auth):
    """
    Upload file to a target environment.

    :param filename: the name of a file to upload.
    :param uuid: the item into which the filename is to be uploaded.
    :param auth: auth info in the form of a dictionary containing 'key', 'secret', and 'server'.
    """

    # filename here should not include path
    patch_data = {'filename': os.path.basename(filename)}

    response = ff_utils.patch_metadata(patch_data, uuid, key=auth)

    try:
        [metadata] = response['@graph']
        upload_credentials = metadata['upload_credentials']
    except Exception:
        raise RuntimeError("Unable to obtain upload credentials for file %s." % filename)

    execute_prearranged_upload(filename, upload_credentials=upload_credentials)


def do_uploads(upload_spec_list, auth, folder=None):
    """
    Uploads the files mentioned in the give upload_spec_list.

    :param upload_spec_list: a list of upload_spec dictionaries, each of the form {'filename': ..., 'uuid': ...},
        representing uploads to be formed.
    :param auth: a dictionary-form auth spec, of the form {'key': ..., 'secret': ..., 'server': ...}
        representing destination and credentials.
    :param folder: a string naming a folder in which to find the filenames to be uploaded.
    :return: None
    """
    for upload_spec in upload_spec_list:
        filename = os.path.join(folder or os.path.curdir, upload_spec['filename'])
        uuid = upload_spec['uuid']
        if not yes_or_no("Upload %s?" % (filename,)):
            show("OK, not uploading it.")
            continue
        try:
            show("Uploading %s to item %s ..." % (filename, uuid))
            upload_file_to_uuid(filename=filename, uuid=uuid, auth=auth)
            show("Upload of %s to item %s was successful." % (filename, uuid))
        except Exception as e:
            show("%s: %s" % (e.__class__.__name__, e))


def upload_item_data(item_filename, uuid, server, env):
    """
    Given a part_filename, uploads that filename to the Item specified by uuid on the given server.

    Only one of server or env may be specified.

    :param item_filename: the name of a file to be uploaded
    :param uuid: the UUID of the Item with which the uploaded data is to be associated
    :param server: the server to upload to (where the Item is defined)
    :param env: the beanstalk environment to upload to (where the Item is defined)
    :return:
    """

    server = resolve_server(server=server, env=env)

    keydict = get_keydict_for_server(server)

    # print("keydict=", json.dumps(keydict, indent=2))

    if not yes_or_no("Upload %s to %s?" % (item_filename, server)):
        show("Aborting submission.")
        exit(1)

    upload_file_to_uuid(filename=item_filename, uuid=uuid, auth=keydict)
