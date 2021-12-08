import contextlib
import glob
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
from dcicutils.ff_utils import get_health_page
from dcicutils.lang_utils import n_of, conjoined_list
from dcicutils.misc_utils import check_true, environ_bool, PRINT, url_path_join
from dcicutils.s3_utils import HealthPageKey
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
    r"|https?://(fourfront-cgap|cgap-)[a-z0-9.-]*"
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
        institution = user_record.get('user_institution', {}).get('@id', None)
        if not institution:
            raise SyntaxError("Your user profile has no institution declared,"
                              " so you must specify --institution explicitly.")
        show("Using institution:", institution)
    return institution


def get_defaulted_project(project, user_record):
    """
    Returns the given project or else if none is specified, it tries to infer a project.

    :param project: the @id of a project, or None
    :param user_record: the user record for the authorized user
    :return: the @id of a project to use
    """

    if not project:
        # Ref: https://hms-dbmi.atlassian.net/browse/C4-371
        # The project_roles are expected to look like:
        #  [
        #    {"project": {"@id": "/projects/foo"}, "role": "developer"},
        #    {"project": {"@id": "/projects/bar"}, "role": "clinician"},
        #    {"project": {"@id": "/projects/baz"}, "role": "director"},
        #  ]
        project_roles = user_record.get('project_roles', [])
        if len(project_roles) == 0:
            raise SyntaxError("Your user profile declares no project roles.")
        elif len(project_roles) > 1:
            raise SyntaxError("You must use --project to specify which project you are submitting for"
                              " (probably one of: %s)." % ", ".join([x['project']['@id'] for x in project_roles]))
        else:
            [project_role] = project_roles
            project = project_role['project']['@id']
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
    return url_path_join(server, "ingestion-submissions", uuid) + "?format=json"


@contextlib.contextmanager
def script_catch_errors():
    try:
        yield
        exit(0)
    except Exception as e:
        show("%s: %s" % (e.__class__.__name__, str(e)))
        exit(1)


DEBUG_PROTOCOL = environ_bool("DEBUG_PROTOCOL", default=False)


def _post_submission(server, keypair, ingestion_filename, creation_post_data, submission_post_data):
    """ This takes care of managing the compatibility step of using either the old or new ingestion protocol.

    OLD PROTOCOL: Post directly to /submit_for_ingestion

    NEW PROTOCOL: Create an IngestionSubmission and then use /ingestion-submissions/<guid>/submit_for_ingestion

    :param server: the name of the server as a URL
    :param keypair: a tuple which is a keypair (key_id, secret_key)
    :param ingestion_filename: the bundle filename to be submitted
    :param creation_post_data: data to become part of the post data for the creation
    :param submission_post_data: data to become part of the post data for the ingestion
    :return: the results of the ingestion call (whether by the one-step or two-step process)
    """

    def post_files_data():
        return {"datafile": io.open(ingestion_filename, 'rb')}

    old_style_submission_url = url_path_join(server, "submit_for_ingestion")
    old_style_post_data = dict(creation_post_data, **submission_post_data)

    response = requests.post(old_style_submission_url,
                             auth=keypair,
                             data=old_style_post_data,
                             headers={'Content-type': 'application/json'},
                             files=post_files_data())

    if DEBUG_PROTOCOL:
        PRINT("old_style_submission_url=", old_style_submission_url)
        PRINT("old_style_post_data=", json.dumps(old_style_post_data, indent=2))
        PRINT("keypair=", keypair)
        PRINT("response=", response)

    if response.status_code == 404:

        if DEBUG_PROTOCOL:
            PRINT("Retrying with new protocol.")

        creation_post_headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }
        creation_post_url = url_path_join(server, "IngestionSubmission")
        if DEBUG_PROTOCOL:
            PRINT("creation_post_data=", json.dumps(creation_post_data, indent=2))
            PRINT("creation_post_url=", creation_post_url)
        creation_response = requests.post(creation_post_url, auth=keypair,
                                          headers=creation_post_headers,
                                          json=creation_post_data
                                          # data=json.dumps(creation_post_data)
                                          )
        if DEBUG_PROTOCOL:
            PRINT("headers:", creation_response.request.headers)
        creation_response.raise_for_status()
        [submission] = creation_response.json()['@graph']
        submission_id = submission['@id']

        if DEBUG_PROTOCOL:
            PRINT("server=", server, "submission_id=", submission_id)
        new_style_submission_url = url_path_join(server, submission_id, "submit_for_ingestion")
        if DEBUG_PROTOCOL:
            PRINT("submitting new_style_submission_url=", new_style_submission_url)
        response = requests.post(new_style_submission_url, auth=keypair, data=submission_post_data,
                                 files=post_files_data())
        if DEBUG_PROTOCOL:
            PRINT("response received for submission post:", response)
            PRINT("response.content:", response.content)

    else:

        if DEBUG_PROTOCOL:
            PRINT("Old style protocol worked.")

    return response


DEFAULT_INGESTION_TYPE = 'metadata_bundle'


def submit_any_ingestion(ingestion_filename, ingestion_type, institution, project, server, env, validate_only,
                         upload_folder=None, no_query=False, subfolders=False):
    """
    Does the core action of submitting a metadata bundle.

    :param ingestion_filename: the name of the main data file to be ingested
    :param ingestion_type: the type of ingestion to be performed (an ingestion_type in the IngestionSubmission schema)
    :param institution: the @id of the institution for which the submission is being done
    :param project: the @id of the project for which the submission is being done
    :param server: the server to upload to
    :param env: the beanstalk environment to upload to
    :param validate_only: whether to do stop after validation instead of proceeding to post metadata
    :param upload_folder: folder in which to find files to upload (default: same as bundle_filename)
    :param no_query: bool to suppress requests for user input
    :param subfolders: bool to search subdirectories within upload_folder for files
    """

    with script_catch_errors():

        server = resolve_server(server=server, env=env)

        validation_qualifier = " (for validation only)" if validate_only else ""

        maybe_ingestion_type = ''
        if ingestion_type != DEFAULT_INGESTION_TYPE:
            maybe_ingestion_type = " (%s)" % ingestion_type

        if not no_query:
            if not yes_or_no("Submit %s%s to %s%s?"
                             % (ingestion_filename, maybe_ingestion_type, server, validation_qualifier)):
                show("Aborting submission.")
                exit(1)

        keydict = get_keydict_for_server(server)
        keypair = keydict_to_keypair(keydict)

        user_record = get_user_record(server, auth=keypair)

        institution = get_defaulted_institution(institution, user_record)
        project = get_defaulted_project(project, user_record)

        if not os.path.exists(ingestion_filename):
            raise ValueError("The file '%s' does not exist." % ingestion_filename)

        response = _post_submission(server=server, keypair=keypair,
                                    ingestion_filename=ingestion_filename,
                                    creation_post_data={
                                        'ingestion_type': ingestion_type,
                                        'institution': institution,
                                        'project': project,
                                        "processing_status": {
                                            "state": "submitted"
                                        }
                                    },
                                    submission_post_data={
                                        'validate_only': validate_only,
                                    })

        try:
            # This can fail if the body doesn't contain JSON
            res = response.json()
        except Exception:
            res = None

        try:
            response.raise_for_status()
        except Exception:
            if res is not None:
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
                    show("NOTE: This error is known to occur if the server"
                         " does not support metadata bundle submission.")
            raise

        if res is None:
            raise Exception("Bad JSON body in %s submission result." % response.status_code)

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
            do_any_uploads(res, keydict=keydict, ingestion_filename=ingestion_filename,
                           upload_folder=upload_folder, no_query=no_query,
                           subfolders=subfolders)

        exit(0)


def show_upload_info(uuid, server=None, env=None, keydict=None):
    """
    Uploads the files associated with a given ingestion submission. This is useful if you answered "no" to the query
    about uploading your data and then later are ready to do that upload.

    :param uuid: a string guid that identifies the ingestion submission
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


def do_any_uploads(res, keydict, upload_folder=None, ingestion_filename=None,
                   no_query=False, subfolders=False):
    upload_info = get_section(res, 'upload_info')
    folder = upload_folder or (os.path.dirname(ingestion_filename) if ingestion_filename else None)
    if upload_info:
        if no_query:
            do_uploads(upload_info, auth=keydict, no_query=no_query, folder=folder,
                       subfolders=subfolders)
        else:
            if yes_or_no("Upload %s?" % n_of(len(upload_info), "file")):
                do_uploads(upload_info, auth=keydict, no_query=no_query, folder=folder,
                           subfolders=subfolders)
            else:
                show("No uploads attempted.")


def resume_uploads(uuid, server=None, env=None, bundle_filename=None, keydict=None,
                   upload_folder=None, no_query=False, subfolders=False):
    """
    Uploads the files associated with a given ingestion submission. This is useful if you answered "no" to the query
    about uploading your data and then later are ready to do that upload.

    :param uuid: a string guid that identifies the ingestion submission
    :param server: the server to upload to
    :param env: the beanstalk environment to upload to
    :param bundle_filename: the bundle file to be uploaded
    :param keydict: keydict-style auth, a dictionary of 'key', 'secret', and 'server'
    :param upload_folder: folder in which to find files to upload (default: same as ingestion_filename)
    :param no_query: bool to suppress requests for user input
    :param subfolders: bool to search subdirectories within upload_folder for files
    """

    with script_catch_errors():

        server = resolve_server(server=server, env=env)
        keydict = keydict or get_keydict_for_server(server)
        url = ingestion_submission_item_url(server, uuid)
        keypair = keydict_to_keypair(keydict)
        response = requests.get(url, auth=keypair)
        response.raise_for_status()
        do_any_uploads(response.json(),
                       keydict=keydict,
                       ingestion_filename=bundle_filename,
                       upload_folder=upload_folder,
                       no_query=no_query,
                       subfolders=subfolders)


def get_s3_encrypt_key_id(auth):
    try:
        health = get_health_page(key=auth)
        return health.get(HealthPageKey.S3_ENCRYPT_KEY_ID)
    except Exception:
        return None


def execute_prearranged_upload(path, upload_credentials, auth=None, s3_encrypt_key_id=None):
    """
    This performs a file upload using special credentials received from ff_utils.patch_metadata.

    :param path: the name of a local file to upload
    :param upload_credentials: a dictionary of credentials to be used for the upload,
        containing the keys 'AccessKeyId', 'SecretAccessKey', 'SessionToken', and 'upload_url'.
    """

    if DEBUG_PROTOCOL:
        PRINT(f"Upload credentials contain {conjoined_list(list(upload_credentials.keys()))}.")
    try:
        if s3_encrypt_key_id:
            if DEBUG_PROTOCOL:
                PRINT(f"s3_encrypt_key_id was supplied along with upload_credentials: {s3_encrypt_key_id}")
        else:
            if DEBUG_PROTOCOL:
                PRINT(f"Fetching s3_encrypt_key_id from health page.")
            s3_encrypt_key_id = get_s3_encrypt_key_id(auth)
            if DEBUG_PROTOCOL:
                PRINT(f" =id=> {s3_encrypt_key_id!r}")
        extra_env = dict(AWS_ACCESS_KEY_ID=upload_credentials['AccessKeyId'],
                         AWS_SECRET_ACCESS_KEY=upload_credentials['SecretAccessKey'],
                         AWS_SECURITY_TOKEN=upload_credentials['SessionToken'])
        env = dict(os.environ, **extra_env)
    except Exception as e:
        raise ValueError("Upload specification is not in good form. %s: %s" % (e.__class__.__name__, e))

    start = time.time()
    try:
        source = path
        target = upload_credentials['upload_url']
        show("Going to upload %s to %s." % (source, target))
        command = ['aws', 's3', 'cp']
        if s3_encrypt_key_id:
            command = command + ['--sse', 'aws:kms', '--sse-kms-key-id', s3_encrypt_key_id]
        command = command + ['--only-show-errors', source, target]
        if DEBUG_PROTOCOL:
            PRINT(f"Executing: {command}")
            PRINT(f" ==> {' '.join(command)}")
            PRINT(f"Environment variables include {conjoined_list(list(extra_env.keys()))}.")
        subprocess.check_call(command, env=env)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Upload failed with exit code %d" % e.returncode)
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
        s3_encrypt_key_id = metadata.get('s3_encrypt_key_id')
        if DEBUG_PROTOCOL:
            PRINT(f"Extracted from metadata: s3_encrypt_key_id = {s3_encrypt_key_id}")
    except Exception:
        raise RuntimeError("Unable to obtain upload credentials for file %s." % filename)

    execute_prearranged_upload(filename, upload_credentials=upload_credentials, auth=auth,
                               s3_encrypt_key_id=s3_encrypt_key_id)


# This can be set to True in unusual situations, but normally will be False to avoid unnecessary querying.
CGAP_SELECTIVE_UPLOADS = environ_bool("CGAP_SELECTIVE_UPLOADS")


def do_uploads(upload_spec_list, auth, folder=None, no_query=False, subfolders=False):
    """
    Uploads the files mentioned in the give upload_spec_list.

    :param upload_spec_list: a list of upload_spec dictionaries, each of the form {'filename': ..., 'uuid': ...},
        representing uploads to be formed.
    :param auth: a dictionary-form auth spec, of the form {'key': ..., 'secret': ..., 'server': ...}
        representing destination and credentials.
    :param folder: a string naming a folder in which to find the filenames to be uploaded.
    :param no_query: bool to suppress requests for user input
    :param subfolders: bool to search subdirectories within upload_folder for files
    :return: None
    """
    folder = folder or os.path.curdir
    if subfolders:
        folder = os.path.join(folder, '**')
    for upload_spec in upload_spec_list:
        file_path = os.path.join(folder, upload_spec['filename'])
        file_search = glob.glob(file_path, recursive=subfolders)
        if len(file_search) == 1:
            filename = file_search[0]
        elif len(file_search) > 1:
            show(
                "No upload attempted for file %s because multiple copies were found"
                " in folder %s: %s."
                % (upload_spec['filename'], folder, ", ".join(file_search))
            )
            continue
        else:
            filename = file_path
        uuid = upload_spec['uuid']
        if not no_query:
            if CGAP_SELECTIVE_UPLOADS and not yes_or_no("Upload %s?" % (filename,)):
                show("OK, not uploading it.")
                continue
        try:
            show("Uploading %s to item %s ..." % (filename, uuid))
            upload_file_to_uuid(filename=filename, uuid=uuid, auth=auth)
            show("Upload of %s to item %s was successful." % (filename, uuid))
        except Exception as e:
            show("%s: %s" % (e.__class__.__name__, e))


def upload_item_data(item_filename, uuid, server, env, no_query=False):
    """
    Given a part_filename, uploads that filename to the Item specified by uuid on the given server.

    Only one of server or env may be specified.

    :param item_filename: the name of a file to be uploaded
    :param uuid: the UUID of the Item with which the uploaded data is to be associated
    :param server: the server to upload to (where the Item is defined)
    :param env: the beanstalk environment to upload to (where the Item is defined)
    :param no_query: bool to suppress requests for user input
    :return:
    """

    server = resolve_server(server=server, env=env)

    keydict = get_keydict_for_server(server)

    # print("keydict=", json.dumps(keydict, indent=2))

    if not no_query:
        if not yes_or_no("Upload %s to %s?" % (item_filename, server)):
            show("Aborting submission.")
            exit(1)

    upload_file_to_uuid(filename=item_filename, uuid=uuid, auth=keydict)
