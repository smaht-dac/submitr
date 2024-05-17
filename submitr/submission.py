import ast
import boto3
from botocore.exceptions import NoCredentialsError as BotoNoCredentialsError
from functools import lru_cache
import io
import json
import os
import re
import sys
import time
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Tuple
from typing_extensions import Literal

# get_env_real_url would rely on env_utils
# from dcicutils.env_utils import get_env_real_url
from dcicutils.command_utils import yes_or_no
from dcicutils.common import APP_CGAP, APP_FOURFRONT, APP_SMAHT, OrchestratedApp
from dcicutils.data_readers import Excel
from dcicutils.datetime_utils import format_datetime
from dcicutils.file_utils import (
       compute_file_etag, compute_file_md5,
       get_file_modified_datetime, get_file_size
)
from dcicutils.lang_utils import conjoined_list, disjoined_list, there_are
from dcicutils.misc_utils import (
    environ_bool, format_duration, format_size,
    is_uuid, url_path_join, normalize_spaces
)
from dcicutils.progress_bar import ProgressBar
from dcicutils.schema_utils import EncodedSchemaConstants, JsonSchemaConstants, Schema
from dcicutils.structured_data import Portal, StructuredDataSet
from dcicutils.submitr.progress_constants import PROGRESS_INGESTER, PROGRESS_LOADXL, PROGRESS_PARSE
from dcicutils.submitr.ref_lookup_strategy import ref_lookup_strategy
from submitr.base import DEFAULT_APP
from submitr.exceptions import PortalPermissionError
from submitr.file_for_upload import FilesForUpload
from submitr.metadata_template import check_metadata_version, print_metadata_version_warning
from submitr.output import PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW, get_output_file, setup_for_output_file_option
from submitr.rclone import RCloneGoogle
from submitr.scripts.cli_utils import get_version
from submitr.submission_uploads import do_any_uploads
from submitr.utils import format_path, get_health_page, is_excel_file_name, print_boxed, tobool


def set_output_file(output_file):
    if output_file:
        global PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW
        PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW = setup_for_output_file_option(output_file)


DEFAULT_INGESTION_TYPE = 'metadata_bundle'
GENERIC_SCHEMA_TYPE = 'FileOther'


# Maximum amount of time (approximately) we will wait for a response from server (seconds).
PROGRESS_TIMEOUT = 60 * 10  # ten minutes (note this is for both server validation and submission)
# How often we actually get the IngestionSubmission object from the server (seconds).
PROGRESS_GET_INGESTION_SUBMISSION_INTERVAL = 3
# How often we actually get the IngestionSubmission object from the server (seconds).
PROGRESS_GET_INGESTION_STATUS_INTERVAL = 1
# How often the (tqdm) progress meter updates (seconds).
PROGRESS_INTERVAL = 0.1
# How many times the (tqdm) progress meter updates (derived from above).
PROGRESS_MAX_CHECKS = round(PROGRESS_TIMEOUT / PROGRESS_INTERVAL)


class SubmissionProtocol:
    S3 = 's3'
    UPLOAD = 'upload'


SUBMISSION_PROTOCOLS = [SubmissionProtocol.S3, SubmissionProtocol.UPLOAD]
DEFAULT_SUBMISSION_PROTOCOL = SubmissionProtocol.UPLOAD
STANDARD_HTTP_HEADERS = {"Content-type": "application/json"}
INGESTION_SUBMISSION_TYPE_NAME = "IngestionSubmission"


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
    r"|https?://(fourfront-cgap|cgap-|smaht-)[a-z0-9.-]*"
    r"|https?://([a-z-]+[.])*smaht[.]org"
    r"|https?://([a-z-]+[.])*cgap[.]hms[.]harvard[.]edu)/?$"
)


# TODO: Probably should simplify this to just trust what's in the key file and ignore all other servers. -kmp 2-Aug-2023
def _resolve_server(server, env):
    return  # no longer used - using dcicutils.portal_utils.Portal instead


def _get_user_record(server, auth, quiet=False):
    """
    Given a server and some auth info, gets the user record for the authorized user.

    This works by using the /me endpoint.

    :param server: a server spec
    :param auth: auth info to be used when contacting the server
    :return: the /me page in JSON format
    """

    user_url = server + "/me?format=json"
    user_record_response = Portal(auth).get(user_url)
    try:
        user_record = user_record_response.json()
    except Exception:
        user_record = {}
    try:
        if user_record_response.status_code in (401, 403) and user_record.get("Title") == "Not logged in.":
            if not quiet:
                SHOW("Server did not recognize you with the given credentials.")
    except Exception:
        pass
    if user_record_response.status_code in (401, 403):
        raise PortalPermissionError(server=server)
    user_record_response.raise_for_status()
    user_record = user_record_response.json()
    if not quiet:
        SHOW(f"Portal recognizes you as{' (admin)' if _is_admin_user(user_record) else ''}:"
             f" {user_record['title']} ({user_record['contact_email']}) ✓")
    return user_record


def _is_admin_user(user: dict) -> bool:
    if tobool(os.environ.get("SMAHT_NOADMIN")):
        return False
    return "admin" in user.get("groups", []) if isinstance(user, dict) else False


def _get_defaulted_institution(institution, user_record, portal=None, quiet=False, verbose=False):
    """
    Returns the given institution or else if none is specified, it tries to infer an institution.

    :param institution: the @id of an institution, or None
    :param user_record: the user record for the authorized user
    :return: the @id of an institution to use
    """

    if not institution:
        institution = user_record.get('user_institution', {}).get('@id', None)
        if not institution:
            raise SyntaxError("Your user profile has no institution declared,"
                              " so you must specify --institution explicitly.")
        SHOW("Using institution:", institution)
    return institution


def _get_defaulted_project(project, user_record, portal=None, quiet=False, verbose=False):
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
            SHOW("Project is: ", project)
    return project


def _get_defaulted_award(award, user_record, portal=None, error_if_none=False, quiet=False, verbose=False):
    """
    Returns the given award or else if none is specified, it tries to infer an award.

    :param award: the @id of an award, or None
    :param user_record: the user record for the authorized user
    :param error_if_none: boolean true if failure to infer an award should raise an error, and false otherwise.
    :return: the @id of an award to use
    """

    if not award:
        # The lab is expected to have awards looking like:
        #  [
        #    {"@id": "/awards/foo", ...},
        #    {"@id": "/awards/bar", ...},
        #    {"@id": "/awards/baz", ...},
        #  ]
        lab = user_record.get('lab', {})
        lab_awards = lab.get('awards', [])
        if len(lab_awards) == 0:
            if error_if_none:
                raise SyntaxError("Your user profile declares no lab with awards.")
        elif len(lab_awards) > 1:
            options = disjoined_list([award['@id'] for award in lab_awards])
            if error_if_none:
                raise SyntaxError(f"Your lab ({lab['@id']}) declares multiple awards."
                                  f" You must explicitly specify one of {options} with --award.")
        else:
            [lab_award] = lab_awards
            award = lab_award['@id']
        if not award:
            SHOW("No award was inferred.")
        else:
            SHOW("Award is (inferred):", award)
    else:
        SHOW("Award is:", award)
    return award


def _get_defaulted_lab(lab, user_record, portal=None, error_if_none=False, quiet=False, verbose=False):
    """
    Returns the given lab or else if none is specified, it tries to infer a lab.

    :param lab: the @id of a lab, or None
    :param user_record: the user record for the authorized user
    :param error_if_none: boolean true if failure to infer a lab should raise an error, and false otherwise.
    :return: the @id of a lab to use
    """

    if not lab:
        lab = user_record.get('lab', {}).get('@id', None)
        if not lab:
            if error_if_none:
                raise SyntaxError("Your user profile has no lab declared,"
                                  " so you must specify --lab explicitly.")
            SHOW("No lab was inferred.")
        else:
            SHOW("Lab is (inferred):", lab)
    else:
        SHOW("Lab is:", lab)
    return lab


def _get_defaulted_consortia(consortia, user_record, portal=None, error_if_none=False, quiet=False, verbose=False):
    """
    Returns the given consortia or else if none is specified, it tries to infer any consortia.

    :param consortia: a list of @id's of consortia, or None
    :param user_record: the user record for the authorized user
    :param error_if_none: boolean true if failure to infer any consortia should raise an error, and false otherwise.
    :return: the @id of a consortium to use (or a comma-separated list)
    """
    def show_consortia():
        nonlocal portal
        if portal:
            if consortia := _get_consortia(portal):
                SHOW("CONSORTIA SUPPORTED:")
                for consortium in consortia:
                    SHOW(f"- {consortium.get('name')} ({consortium.get('uuid')})")
    suffix = ""
    if not consortia:
        consortia = [consortium.get('@id', None) for consortium in user_record.get('consortia', [])]
        if not consortia:
            if error_if_none:
                raise SyntaxError("Your user profile has no consortium declared,"
                                  " so you must specify --consortium explicitly.")
            SHOW("ERROR: No consortium was inferred. Use the --consortium option.")
            show_consortia()
            exit(1)
        else:
            suffix = " (inferred)"
    annotated_consortia = []
    if portal:
        for consortium in consortia:
            consortium_path = f"/Consortium/{consortium}" if not consortium.startswith("/") else consortium
            if not (consortium_object := portal.get_metadata(consortium_path, raise_exception=False)):
                SHOW(f"ERROR: Consortium not found: {consortium}")
                show_consortia()
                exit(1)
            elif consortium_name := consortium_object.get("identifier"):
                consortium_uuid = consortium_object.get("uuid")
                if verbose:
                    annotated_consortia.append(f"{consortium_name} ({consortium_uuid})")
                else:
                    annotated_consortia.append(f"{consortium_name}")
    if annotated_consortia:
        if not quiet:
            SHOW(f"Consortium is{suffix}:", ", ".join(annotated_consortia))
    else:
        if not quiet:
            SHOW(f"Consortium is{suffix}:", ", ".join(consortia))
    return consortia


def _get_defaulted_submission_centers(submission_centers, user_record, portal=None,
                                      error_if_none=False, quiet=False, verbose=False):
    """
    Returns the given submission center or else if none is specified, it tries to infer a submission center.

    :param submission_centers: the @id of a submission center, or None
    :param user_record: the user record for the authorized user
    :param error_if_none: boolean true if failure to infer a submission center should raise an error,
        and false otherwise.
    :return: the @id of a submission center to use
    """
    def show_submission_centers():
        nonlocal portal
        if portal:
            if submission_centers := _get_submission_centers(portal):
                SHOW("SUBMISSION CENTERS SUPPORTED:")
                for submission_center in submission_centers:
                    SHOW(f"- {submission_center.get('name')} ({submission_center.get('uuid')})")
    suffix = ""
    if not submission_centers:
        submits_for = [sc.get('@id', None) for sc in user_record.get('submits_for', [])]
        submission_centers = [sc.get('@id', None) for sc in user_record.get('submission_centers', [])]
        submission_centers = list(set(submits_for + submission_centers))
        if not submission_centers:
            if error_if_none:
                raise SyntaxError("Your user profile has no submission center declared,"
                                  " so you must specify --submission-center explicitly.")
            SHOW("ERROR: No submission center was inferred. Use the --submission-center option.")
            show_submission_centers()
            exit(1)
        else:
            suffix = " (inferred)"
    annotated_submission_centers = []
    if portal:
        for submission_center in submission_centers:
            submission_center_path = (
                f"/SubmissionCenter/{submission_center}"
                if not submission_center.startswith("/") else submission_center)
            if not (submission_center_object := portal.get_metadata(submission_center_path, raise_exception=False)):
                SHOW(f"ERROR: Submission center not found: {submission_center}")
                show_submission_centers()
                exit(1)
            elif submission_center_name := submission_center_object.get("identifier"):
                submission_center_uuid = submission_center_object.get("uuid")
                if verbose:
                    annotated_submission_centers.append(f"{submission_center_name} ({submission_center_uuid})")
                else:
                    annotated_submission_centers.append(f"{submission_center_name}")
    if annotated_submission_centers:
        if not quiet:
            SHOW(f"Submission center is{suffix}:", ", ".join(annotated_submission_centers))
    else:
        if not quiet:
            SHOW(f"Submission center is{suffix}:", ", ".join(submission_centers))
    return submission_centers


APP_ARG_DEFAULTERS = {
    'institution': _get_defaulted_institution,
    'project': _get_defaulted_project,
    'lab': _get_defaulted_lab,
    'award': _get_defaulted_award,
    'consortia': _get_defaulted_consortia,
    'submission_centers': _get_defaulted_submission_centers,
}


def _do_app_arg_defaulting(app_args, user_record, portal=None, quiet=False, verbose=False):
    for arg in list(app_args.keys()):
        val = app_args[arg]
        defaulter = APP_ARG_DEFAULTERS.get(arg)
        if defaulter:
            val = defaulter(val, user_record, portal, quiet=quiet, verbose=verbose)
            if val:
                app_args[arg] = val
            elif val is None:
                del app_args[arg]


PROGRESS_CHECK_INTERVAL = 7  # seconds
ATTEMPTS_BEFORE_TIMEOUT = 100
ATTEMPTS_BEFORE_TIMEOUT = 4


def _ingestion_submission_item_url(server, uuid):
    # Note that we use datastore=database for quicker feedback.
    return url_path_join(server, "ingestion-submissions", uuid) + "?format=json&datastore=database"


# TRY_OLD_PROTOCOL = True
DEBUG_PROTOCOL = environ_bool("DEBUG_PROTOCOL", default=False)


def _initiate_server_ingestion_process(
        portal: Portal,
        ingestion_filename: str,
        consortia: Optional[List[str]] = None,
        submission_centers: Optional[List[str]] = None,
        add_submission_center: Optional[str] = None,
        is_server_validation: bool = False,
        is_resume_submission: bool = False,
        validate_remote_skip: bool = False,
        validation_ingestion_submission_object: Optional[dict] = None,
        post_only: bool = False,
        patch_only: bool = False,
        autoadd: Optional[dict] = None,
        datafile_size: Optional[Any] = None,
        datafile_checksum: Optional[Any] = None,
        user: Optional[dict] = None,
        debug: bool = False,
        debug_sleep: Optional[str] = None) -> str:

    if isinstance(validation_ingestion_submission_object, dict):
        # This ingestion action is for a submission (rather than for a validation),
        # and we were given an associated validation UUID (i.e. from a previous client
        # initiated server validation); so we record this validation UUID in the actual
        # submission IngestionSubmission object (to be created just below); and we will
        # do the converse below, after the submission IngestionSubmission object creation.
        validation_ingestion_submission_uuid = validation_ingestion_submission_object.get("uuid", None)
        if not (isinstance(validation_parameters := validation_ingestion_submission_object.get("parameters"), dict)):
            validation_parameters = None
    else:
        validation_ingestion_submission_object = None
        validation_ingestion_submission_uuid = None
        validation_parameters = None

    submission_post_data = {
        "validate_only": is_server_validation,
        "validate_skip": validate_remote_skip,
        "post_only": post_only,
        "patch_only": patch_only,
        "ref_nocache": False,  # Do not do this server-side at all; only client-side for testing.
        "autoadd": json.dumps(autoadd),
        "ingestion_directory": os.path.dirname(ingestion_filename) if ingestion_filename else None,
        "datafile_size": datafile_size or get_file_size(ingestion_filename),
        "datafile_checksum": datafile_checksum or compute_file_md5(ingestion_filename),
        "submitr_version": get_version(),
        "user": json.dumps(user) if user else None
    }

    if validation_ingestion_submission_uuid:
        submission_post_data["validation_uuid"] = validation_ingestion_submission_uuid
    if debug_sleep:
        submission_post_data["debug_sleep"] = debug_sleep

    if is_resume_submission and validation_ingestion_submission_object:
        if validation_parameters := validation_ingestion_submission_object.get("parameters"):
            submission_post_data["validation_datafile"] = validation_parameters.get("datafile")
            submission_post_data["ingestion_directory"] = validation_parameters.get("ingestion_directory")

    response = _post_submission(portal=portal,
                                is_resume_submission=is_resume_submission,
                                ingestion_filename=ingestion_filename,
                                consortia=consortia,
                                submission_centers=submission_centers,
                                add_submission_center=add_submission_center,
                                submission_post_data=submission_post_data,
                                is_server_validation=is_server_validation, debug=debug)
    submission_uuid = response["submission_id"]

    if validation_ingestion_submission_uuid and validation_parameters:
        # This ingestion action is for a submission (rather than for a validation),
        # and we were given an associated validation UUID (i.e. from a previous client
        # initiated server validation); so we record the associated submission UUID,
        # created just above, in the validation IngestionSubmission object (via PATCH).
        validation_parameters["submission_uuid"] = submission_uuid
        validation_parameters = {"parameters": validation_parameters}
        portal.patch_metadata(object_id=validation_ingestion_submission_uuid, data=validation_parameters)

    return submission_uuid


def _post_submission(portal: Portal,
                     ingestion_filename: str,
                     consortia: List[str],
                     submission_centers: List[str],
                     submission_post_data: dict,
                     add_submission_center: Optional[str] = None,
                     ingestion_type: str = DEFAULT_INGESTION_TYPE,
                     submission_protocol: str = DEFAULT_SUBMISSION_PROTOCOL,
                     is_server_validation: bool = False,
                     is_resume_submission: bool = False,
                     debug: bool = False):

    creation_submission_centers = [*submission_centers]
    if isinstance(add_submission_center, str) and (add_submission_center not in creation_submission_centers):
        creation_submission_centers.append(add_submission_center)
    creation_post_data = {
        "ingestion_type": ingestion_type,
        "processing_status": {"state": "submitted"},
        "consortia": consortia,
        "submission_centers": creation_submission_centers
    }
    if is_server_validation:
        creation_post_data["parameters"] = {"validate_only": True}
    # This creates the IngestionSubmission object.
    creation_post_url = url_path_join(portal.server, INGESTION_SUBMISSION_TYPE_NAME)
    creation_response = portal.post(creation_post_url, json=creation_post_data, raise_for_status=True)
    [submission] = creation_response.json()['@graph']
    submission_id = submission['@id']
    if debug:
        PRINT(f"DEBUG: Created ingestion submission object: {submission_id}")
    # This actually kicks off the ingestion process and updates the IngestionSubmission object created above.
    new_style_submission_url = url_path_join(portal.server, submission_id, "submit_for_ingestion")
    if debug:
        if is_server_validation:
            PRINT(f"DEBUG: Initiating server validation process.")
        elif is_resume_submission:
            PRINT(f"DEBUG: Initiating server submission process after server validation timeout.")
        else:
            PRINT(f"DEBUG: Initiating server submission process.")
    if is_resume_submission:
        # Dummy /dev/null file when "resuming" submission after server validation timed out.
        file_post_data = _post_files_data(submission_protocol=submission_protocol, ingestion_filename=None)
    else:
        file_post_data = _post_files_data(submission_protocol=submission_protocol,
                                          ingestion_filename=ingestion_filename)
    response = portal.post(new_style_submission_url,
                           data=submission_post_data,
                           files=file_post_data,
                           headers=None, raise_for_status=True)
    if debug:
        PRINT(f"DEBUG: Initiated server {'validation' if is_server_validation else 'submission'} process.")
    return response.json()


def _post_files_data(submission_protocol, ingestion_filename) -> Dict[Literal['datafile'], Optional[BinaryIO]]:
    """
    This composes a dictionary of the form {'datafile': <maybe-stream>}.

    If the submission protocol is SubmissionProtocol.UPLOAD (i.e., 'upload'), the given ingestion filename is opened
    and used as the datafile value in the dictionary. If it is something else, no file is opened and None is used.

    :param submission_protocol:
    :param ingestion_filename:
    :return: a dictionary with key 'datafile' whose value is either an open binary input stream or None
    """
    if submission_protocol == SubmissionProtocol.UPLOAD:
        if ingestion_filename:
            return {"datafile": io.open(ingestion_filename, 'rb')}
        else:
            return {"datafile": io.open("/dev/null", "rb")}
    else:
        return {"datafile": None}


def _resolve_app_args(institution, project, lab, award, app, consortium, submission_center):

    app_args = {}
    if app == APP_CGAP:
        required_args = {'institution': institution, 'project': project}
        unwanted_args = {'lab': lab, 'award': award,
                         'consortium': consortium, 'submission_center': submission_center}
    elif app == APP_FOURFRONT:
        required_args = {'lab': lab, 'award': award}
        unwanted_args = {'institution': institution, 'project': project,
                         'consortium': consortium, 'submission_center': submission_center}
    elif app == APP_SMAHT:

        def splitter(x):
            return None if x is None else [y for y in [x.strip() for x in x.split(',')] if y]

        consortia = None if consortium is None else splitter(consortium)
        submission_centers = None if submission_center is None else splitter(submission_center)
        required_args = {'consortia': consortia, 'submission_centers': submission_centers}
        unwanted_args = {'institution': institution, 'project': project,
                         'lab': lab, 'award': award}
    else:
        raise ValueError(f"Unknown application: {app}")

    for argname, argvalue in required_args.items():
        app_args[argname] = argvalue

    extra_keys = []
    for argname, argvalue in unwanted_args.items():
        if argvalue:
            # We use '-', not '_' in the user interface for argument names,
            # so --submission_center will need --submission-center
            ui_argname = argname.replace('_', '-')
            extra_keys.append(f"--{ui_argname}")

    if extra_keys:
        raise ValueError(there_are(extra_keys, kind="inappropriate argument", joiner=conjoined_list, punctuate=True))

    return app_args


def submit_any_ingestion(ingestion_filename, *,
                         ingestion_type,
                         server,
                         env,
                         institution=None,
                         project=None,
                         lab=None,
                         award=None,
                         consortium=None,
                         submission_center=None,
                         add_submission_center=None,
                         app: OrchestratedApp = None,
                         upload_folder=None,
                         no_query=False,
                         subfolders=False,
                         submission_protocol=DEFAULT_SUBMISSION_PROTOCOL,
                         submit=False,
                         rclone_google=None,
                         validate_local_only=False,
                         validate_remote_only=False,
                         validate_local_skip=False,
                         validate_remote_skip=False,
                         post_only=False,
                         patch_only=False,
                         keys_file=None,
                         show_details=False,
                         noanalyze=False,
                         json_only=False,
                         ref_nocache=False,
                         verbose_json=False,
                         verbose=False,
                         noprogress=False,
                         output_file=None,
                         env_from_env=False,
                         timeout=None,
                         noversion=False,
                         debug=False,
                         debug_sleep=None):

    """
    Does the core action of submitting a metadata bundle.

    :param ingestion_filename: the name of the main data file to be ingested
    :param ingestion_type: the type of ingestion to be performed (an ingestion_type in the IngestionSubmission schema)
    :param server: the server to upload to
    :param env: the portal environment to upload to
    :param validate_remote_only: whether to do stop after validation instead of proceeding to post metadata
    :param app: an orchestrated app name
    :param institution: the @id of the institution for which the submission is being done (when app='cgap')
    :param project: the @id of the project for which the submission is being done (when app='cgap')
    :param lab: the @id of the lab for which the submission is being done (when app='fourfront')
    :param award: the @id of the award for which the submission is being done (when app='fourfront')
    :param consortium: the @id of the consortium for which the submission is being done (when app='smaht')
    :param submission_center: the @id of the submission_center for which the submission is being done (when app='smaht')
    :param upload_folder: folder in which to find files to upload (default: same as bundle_filename)
    :param no_query: bool to suppress requests for user input
    :param subfolders: bool to search subdirectories within upload_folder for files
    :param submission_protocol: which submission protocol to use (default: 's3')
    :param show_details: bool controls whether to show the details from the results file in S3.
    """

    """
    if app is None:  # Better to pass explicitly, but some legacy situations might require this to default
        app = DEFAULT_APP
        app_default = True
    else:
        app_default = False
        PRINT(f"App name is: {app}")
    """
    validation = not submit

    # Setup for output to specified output file, in addition to stdout),
    # except in this case we will not output large amounts of output to stdout.
    if output_file:
        global PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW
        PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW = setup_for_output_file_option(output_file)

    portal = _define_portal(env=env, env_from_env=env_from_env, server=server, app=app,
                            keys_file=keys_file, report=not json_only or verbose, verbose=verbose,
                            note="Metadata Validation" if validation else "Metadata Submission")

    app_args = _resolve_app_args(institution=institution, project=project, lab=lab, award=award, app=portal.app,
                                 consortium=consortium, submission_center=submission_center)

    if not portal.ping():
        SHOW(f"Portal credentials do not seem to work: {portal.keys_file} ({env})")
        exit(1)

    user_record = _get_user_record(portal.server, auth=portal.key_pair, quiet=json_only and not verbose)

    # Nevermind: Too confusing for both testing and general usage
    # to have different behaviours for admin and non-admin users.
    # is_admin_user = _is_admin_user(user_record)
    exit_immediately_on_errors = True
    if validate_local_only or validate_remote_skip:
        if validate_remote_only or validate_local_skip:
            PRINT("WARNING: Skipping all validation is definitely not recommended.")
        else:
            PRINT("WARNING: Skipping remote (server) validation is not recommended.")
    elif validate_remote_only or validate_local_skip:
        PRINT("WARNING: Skipping local (client) validation is not recommended.")

    if debug:
        PRINT(f"DEBUG: submit = {submit}")
        PRINT(f"DEBUG: validation = {validation}")
        PRINT(f"DEBUG: validate_local_only = {validate_local_only}")
        PRINT(f"DEBUG: validate_remote_only = {validate_remote_only}")
        PRINT(f"DEBUG: validate_local_skip = {validate_local_skip}")
        PRINT(f"DEBUG: validate_remote_skip = {validate_remote_skip}")

    metadata_bundles_bucket = get_metadata_bundles_bucket_from_health_path(key=portal.key)
    if not _do_app_arg_defaulting(app_args, user_record, portal, quiet=json_only and not verbose, verbose=verbose):
        pass
    if not json_only:
        PRINT(f"Submission file to {'validate' if validation else 'ingest'}: {format_path(ingestion_filename)}")

    autoadd = None
    if app_args and isinstance(submission_centers := app_args.get("submission_centers"), list):
        if len(submission_centers) == 1:
            def extract_identifying_value_from_path(path: str) -> str:
                if path.endswith("/"):
                    path = path[:-1]
                parts = path.split("/")
                return parts[-1] if parts else ""
            autoadd = {"submission_centers": [extract_identifying_value_from_path(submission_centers[0])]}
        elif len(submission_centers) > 1:
            PRINT(f"Multiple submission centers: {', '.join(submission_centers)}")
            PRINT(f"You must specify onely one submission center using the --submission-center option.")
            exit(1)

    if add_submission_center:
        if not _is_admin_user(user_record):
            PRINT("ERROR: Cannot use the --add-submission-center if you are not an admin user.")
            exit(1)
        known_submission_centers = _get_submission_centers(portal)
        found_submission_centers = [submission_center for submission_center in known_submission_centers
                                    if (submission_center.get("name") == add_submission_center) or
                                       (submission_center.get("uuid") == add_submission_center)]
        if not found_submission_centers or not found_submission_centers[0].get("uuid"):
            PRINT(f"ERROR: Specified submission center ({add_submission_center}) not found. Use one of:")
            for known_submission_center in known_submission_centers:
                PRINT(f"- {known_submission_center.get('name')} ({known_submission_center.get('uuid')})")
            exit(1)
        add_submission_center = f"/submission-centers/{found_submission_centers[0]['uuid']}/"

    if verbose:
        SHOW(f"Metadata bundle upload bucket: {metadata_bundles_bucket}")

    if rclone_google:
        rclone_google.verify_connectivity()

    if not noversion:
        check_metadata_version(ingestion_filename, portal=portal)

    if not validate_remote_only and not validate_local_skip:
        structured_data = _validate_locally(ingestion_filename, portal,
                                            validation=validation,
                                            validate_local_only=validate_local_only,
                                            autoadd=autoadd, upload_folder=upload_folder, subfolders=subfolders,
                                            rclone_google=rclone_google,
                                            exit_immediately_on_errors=exit_immediately_on_errors,
                                            ref_nocache=ref_nocache, output_file=output_file, noprogress=noprogress,
                                            noanalyze=noanalyze, json_only=json_only, verbose_json=verbose_json,
                                            verbose=verbose, debug=debug, debug_sleep=debug_sleep)
        if validate_local_only:
            # We actually do exit from _validate_locally if validate_local_only is True.
            # This return is just emphasize that fact.
            return
    else:
        structured_data = None
        PRINT(f"Skipping local (client) validation (as requested via"
              f" {'--validate-remote-only' if validate_remote_only else '--validate-local-skip'}).")

    # Nevermind: Too confusing for both testing and general usage
    # to have different behaviours for admin and non-admin users.
    # if is_admin_user and not no_query:
    #     # More feedback/points-of-contact for admin users; more automatic for non-admin.
    #     if not yes_or_no(f"Continue with server {'validation' if validation else 'submission'}"
    #                      f" against {portal.server}?"):
    #         SHOW("Aborting before server validation.")
    #         exit(1)

    # Server validation.

    if not validate_local_only and not validate_remote_skip:

        SHOW(f"Continuing with additional (server) validation: {portal.server}")

        validation_uuid = _initiate_server_ingestion_process(
            portal=portal,
            ingestion_filename=ingestion_filename,
            is_server_validation=True,
            consortia=app_args.get("consortia"),
            submission_centers=app_args.get("submission_centers"),
            add_submission_center=add_submission_center,
            post_only=post_only,
            patch_only=patch_only,
            autoadd=autoadd,
            user={"uuid": user_record.get("uuid"),
                  "email": user_record.get("email"),
                  "name": user_record.get("display_title")} if user_record else None,
            debug=debug,
            debug_sleep=debug_sleep)

        SHOW(f"Validation tracking ID: {validation_uuid}")

        server_validation_done, server_validation_status, server_validation_response = _monitor_ingestion_process(
                validation_uuid, portal.server, portal.env, app=portal.app, keys_file=portal.keys_file,
                show_details=show_details, report=False, messages=True,
                validation=True,
                rclone_google=rclone_google,
                nofiles=True, noprogress=noprogress, timeout=timeout,
                verbose=verbose, debug=debug, debug_sleep=debug_sleep)

        if server_validation_status != "success":
            exit(1)

        PRINT("Validation results (server): OK")

    else:
        server_validation_response = None
        PRINT("Skipping remote (server) validation (as requested via"
              f" {'--validate-local-only' if validate_local_only else '--validate-remote-skip'}).")

    if validation:
        do_any_uploads(structured_data,
                       metadata_file=ingestion_filename,
                       main_search_directory=upload_folder,
                       main_search_directory_recursively=subfolders,
                       config_google=rclone_google,
                       portal=portal,
                       verbose=True,
                       review_only=True)
        exit(0)

    # Server submission.

    SHOW(f"Ready to submit your metadata to {portal.server}: {format_path(ingestion_filename)}")
    if not yes_or_no("Continue on with the actual submission?"):
        exit(0)

    submission_uuid = _initiate_server_ingestion_process(
        portal=portal,
        ingestion_filename=ingestion_filename,
        is_server_validation=False,
        validate_remote_skip=validate_remote_skip,
        validation_ingestion_submission_object=server_validation_response,
        consortia=app_args.get("consortia"),
        submission_centers=app_args.get("submission_centers"),
        add_submission_center=add_submission_center,
        post_only=post_only,
        patch_only=patch_only,
        autoadd=autoadd,
        user={"uuid": user_record.get("uuid"),
              "email": user_record.get("email"),
              "name": user_record.get("display_title")} if user_record else None,
        debug=debug,
        debug_sleep=debug_sleep)

    SHOW(f"Submission tracking ID: {submission_uuid}")

    submission_done, submission_status, submission_response = _monitor_ingestion_process(
            submission_uuid, portal.server, portal.env, app=portal.app, keys_file=portal.keys_file,
            show_details=show_details, report=False, messages=True,
            rclone_google=rclone_google,
            validation=False,
            nofiles=True, noprogress=noprogress, timeout=timeout,
            verbose=verbose, debug=debug, debug_sleep=debug_sleep)

    if submission_status != "success":
        exit(1)

    PRINT("Submission complete!")

    # Now that submission has successfully complete, review the files to upload and then do it.

    do_any_uploads(submission_response,
                   metadata_file=ingestion_filename,
                   main_search_directory=upload_folder,
                   main_search_directory_recursively=subfolders,
                   config_google=rclone_google,
                   portal=portal,
                   verbose=verbose)


def _get_recent_submissions(portal: Portal, count: int = 30, name: Optional[str] = None) -> List[dict]:
    url = f"/search/?type=IngestionSubmission&sort=-date_created&from=0&limit={count}"
    if name:
        # TODO: Does not seem to return the same stuff; of not great consequence yet.
        url += f"&q={name}"
    if submissions := portal.get_metadata(url):
        if submissions := submissions.get("@graph"):
            return submissions
    return []


def _print_recent_submissions(portal: Portal, count: int = 30, message: Optional[str] = None,
                              details: bool = False, verbose: bool = False,
                              mine: bool = False, user: Optional[str] = None) -> bool:
    user_name = None
    if mine:
        try:
            user_record = _get_user_record(portal.server, auth=portal.key_pair, quiet=True)
            user_name = user_record.get("display_title")
        except Exception:
            PRINT(f"Cannot find your user info.")
            exit(1)
    elif user:
        if "@" in user or is_uuid(user):
            try:
                user_record = portal.get_metadata(f"/users/{user.lower()}")
                user_name = user_record.get("display_title")
            except Exception:
                PRINT(f"Cannot find user info: {user}")
                exit(1)
        else:
            user_name = user

    lines = []
    if submissions := _get_recent_submissions(portal, count, name=user_name):
        if message:
            PRINT(message)
        lines.append("===")
        lines.append("Recent Submissions [COUNT]")
        lines.append("===")
        index = 0
        for submission in submissions:
            if details and (index > 0):
                lines.append("===")
            if verbose:
                PRINT()
                _print_submission_summary(portal, submission, verbose=verbose)
                continue
            submission_uuid = submission.get("uuid")
            submission_created = submission.get("date_created")
            line = f"{submission_uuid}: {format_datetime(submission_created, notz=True)}"
            if tobool(submission.get("parameters", {}).get("validate_only")):
                line += f" [V]"
            else:
                line += f" [S]"
            if submission.get("processing_status", {}).get("outcome") == "success":
                line += f" ✓"
            else:
                line += f" ✗"
            lines.append(line)
            if details:
                line_detail = ""
                if submitted_by := submission.get("submitted_by", {}).get("display_title"):
                    if line_detail:
                        line_detail += " | "
                    line_detail += f"{submitted_by}"
                if ((submission_params := submission.get("parameters")) and
                    (submission_file := submission_params.get("datafile"))):  # noqa
                    if submission_file == "null":
                        if validation_datafile := submission_params.get("validation_datafile"):
                            # was_server_validation_timeout = True
                            submission_file = f"{validation_datafile} (ω)"
                    if line_detail:
                        line_detail += " | "
                    line_detail += f"{submission_file}"
                if line_detail:
                    lines.append(line_detail)
            index += 1
        if not verbose:
            lines.append("===")
            print_boxed(lines, right_justified_macro=("[COUNT]", lambda: f"Showing: {len(submissions)}"))
        return True
    return False


def _monitor_ingestion_process(uuid: str, server: str, env: str, keys_file: Optional[str] = None,
                               app: Optional[OrchestratedApp] = None,
                               show_details: bool = False,
                               validation: bool = False,
                               env_from_env: bool = False,
                               report: bool = True, messages: bool = False,
                               nofiles: bool = False, noprogress: bool = False,
                               check_submission_script: bool = False,
                               upload_directory: Optional[str] = None,
                               upload_directory_recursive: bool = False,
                               rclone_google: Optional[RCloneGoogle] = None,
                               timeout: Optional[int] = None,
                               verbose: bool = False, debug: bool = False,
                               note: Optional[str] = None,
                               output_file: Optional[str] = None,
                               debug_sleep: Optional[int] = None) -> Tuple[bool, str, dict]:

    if output_file:
        set_output_file(output_file)

    if timeout:
        global PROGRESS_TIMEOUT, PROGRESS_MAX_CHECKS
        PROGRESS_TIMEOUT = timeout
        PROGRESS_MAX_CHECKS = max(round(PROGRESS_TIMEOUT / PROGRESS_INTERVAL), 1)

    def define_progress_callback(max_checks: int, title: str,
                                 interrupt_exit_message: Optional[Callable] = None,
                                 include_status: bool = False) -> None:
        nonlocal validation
        bar = ProgressBar(max_checks, "Calculating",
                          interrupt_exit=True,
                          interrupt_exit_message=interrupt_exit_message,
                          interrupt_message=f"{'validation' if validation else 'submission'} waiting process")
        nchecks = 0
        nchecks_server = 0
        check_status = "Unknown"
        next_check = 0
        # From (new/2024-03-25) /ingestion-status/{submission_uuid} call.
        loadxl_total = 0
        loadxl_started = None
        loadxl_started_second_round = None
        phases_seen = []
        def progress_report(status: dict) -> None:  # noqa
            nonlocal bar, max_checks, nchecks, nchecks_server, next_check, check_status, noprogress, validation
            nonlocal loadxl_total, loadxl_started, loadxl_started_second_round, verbose
            if noprogress:
                return
            # This are from the (new/2024-03-25) /ingestion-status/{submission_uuid} call.
            # Some of these key name come ultimately from snovault.loadxl.PROGRESS; others
            # from smaht-portal/ingestion. Note difference between ingester_initiated and
            # loadxl_started; the former is when the ingester listener is first hit.
            ingester_initiated = status.get(PROGRESS_INGESTER.INITIATE, None)
            ingester_parse_started = status.get(PROGRESS_INGESTER.PARSE_LOAD_INITIATE, None)
            ingester_parse_nrows = status.get(PROGRESS_PARSE.LOAD_COUNT_ROWS, 0)
            ingester_parse_nitems = status.get(PROGRESS_PARSE.LOAD_ITEM, 0)
            ingester_validate_started = status.get(PROGRESS_INGESTER.VALIDATE_LOAD_INITIATE, None)
            ingester_queued = status.get(PROGRESS_INGESTER.QUEUED, None)
            ingester_cleanup = status.get(PROGRESS_INGESTER.CLEANUP, None)
            ingester_queue_cleanup = status.get(PROGRESS_INGESTER.QUEUE_CLEANUP, None)
            ingester_done = status.get(PROGRESS_INGESTER.DONE, None)
            loadxl_initiated = status.get(PROGRESS_INGESTER.LOADXL_INITIATE, None)
            loadxl_total = status.get(PROGRESS_LOADXL.TOTAL, 0)
            loadxl_started = status.get(PROGRESS_LOADXL.START, None)
            loadxl_item = status.get(PROGRESS_LOADXL.ITEM, 0)
            loadxl_started_second_round = status.get(PROGRESS_LOADXL.START_SECOND_ROUND, None)
            loadxl_item_second_round = status.get(PROGRESS_LOADXL.ITEM_SECOND_ROUND, 0)
            loadxl_done = status.get(PROGRESS_LOADXL.DONE, None)
            # This string is from the /ingestion-status endpoint, really as a convenience/courtesey
            # so we don't have to cobble together our own string; but we could also build the
            # message ourselves manually here from the counts contained in the same response.
            ingestion_message = (status.get("loadxl_message_verbose", "")
                                 if verbose else status.get("loadxl_message", ""))
            # Phases: 0 means waiting for server response; 1 means loadxl round one; 2 means loadxl round two.
            loadxl_phase = 2 if loadxl_started_second_round is not None else (1 if loadxl_started is not None else 0)
            # FYI this is a normal ordering of phases in practice ...
            # ingester_queued              PROGRESS_INGESTER.QUEUED
            # ingester_initiate            PROGRESS_INGESTER.INITIATE
            # # ingester_parse_initiate      PROGRESS_INGESTER.PARSE_LOAD_INITIATE
            # parse_start                  PROGRESS_PARSE.LOAD_START
            # parse_done                   PROGRESS_PARSE.LOAD_DONE
            # ingester_parse_done          PROGRESS_INGESTER.PARSE_LOAD_DONE
            # ingester_validate_initiate   PROGRESS_INGESTER.VALIDATE_LOAD_INITIATE
            # ingester_validate_done       PROGRESS_INGESTER.VALIDATE_LOAD_DONE
            # ingester_loadxl_initiate     PROGRESS_INGESTER.LOADXL_INITIATE
            # loadxl_start                 PROGRESS_LOADXL.START
            # loadxl_start_second_round    PROGRESS_LOADXL.START_SECOND_ROUND
            # loadxl_done                  PROGRESS_LOADXL.DONE
            # ingester_loadxl_done         PROGRESS_INGESTER.LOADXL_DONE
            # ingester_cleanup             PROGRESS_INGESTER.CLEANUP
            # ingester_done                PROGRESS_INGESTER.DONE
            # ingester_queue_cleanup       PROGRESS_INGESTER.QUEUE_CLEANUP
            def reset_eta_if_necessary():  # noqa
                nonlocal loadxl_started, loadxl_started_second_round, loadxl_done, phases_seen
                if loadxl_started is not None:
                    if (phase := PROGRESS_LOADXL.START) not in phases_seen:
                        phases_seen.append(phase)
                        bar.reset_eta()
                if loadxl_started_second_round is not None:
                    if (phase := PROGRESS_LOADXL.START_SECOND_ROUND) not in phases_seen:
                        phases_seen.append(phase)
                        if loadxl_done is None and not ingester_done:
                            bar.reset_eta()
            done = False
            message = f"▶ Pings: {nchecks_server}"
            if ingester_done is not None:
                message += " | Done"
                bar.set_progress(bar.total)
                done = True
            elif status.get("finish") or (nchecks >= max_checks):
                check_status = status.get("status")
                if loadxl_phase == 0:
                    bar.increment_progress(max_checks - nchecks)
                done = True
            elif status.get("check_server"):
                check_status = status.get("status")
                nchecks_server += 1
            elif status.get("check"):
                if (next_check := status.get("next")) is not None:
                    next_check = round(status.get("next") or 0)
                nchecks += 1
                if loadxl_phase == 0:
                    bar.increment_progress(1)
            if (loadxl_started is None) and (ingester_done is None):
                if loadxl_initiated is not None:
                    message += f" | Initializing"
                elif ingester_parse_started is not None:
                    message += f" | Parsing"
                    if ingester_parse_nrows > 0:
                        bar.set_total(ingester_parse_nrows)
                        bar.set_progress(ingester_parse_nitems)
                elif ingester_validate_started is not None:
                    message += f" | Validating"
                elif ingester_initiated is not None:
                    message += f" | Acknowledged"
                elif ingester_queued is not None:
                    message += f" | Queued"
                else:
                    message += f" | Waiting on server"
            elif ingester_done is None:
                if loadxl_done is not None:
                    bar.set_total(loadxl_total)
                    bar.set_progress(loadxl_total)
                elif loadxl_phase == 2:
                    bar.set_total(loadxl_total)
                    bar.set_progress(loadxl_item_second_round)
                elif loadxl_phase == 1:
                    bar.set_total(loadxl_total)
                    bar.set_progress(loadxl_item)
                if (ingester_queue_cleanup is not None) or done:
                    message += " | Done"
                elif ingester_cleanup is not None:
                    message += " | Cleanup"
                elif loadxl_done is not None:
                    message += " | Finishing Up"
                if ingestion_message:
                    message += " | " + ingestion_message
            if include_status:
                message += f" | Status: {check_status}"  # Next: {'Now' if next_check == 0 else str(next_check) + 's'}
            reset_eta_if_necessary()
            bar.set_description(message)
            if done:
                bar.done()
        return progress_report

    portal = _define_portal(env=env, server=server, keys_file=keys_file, app=app or DEFAULT_APP,
                            env_from_env=env_from_env, report=report, note=note)

    def interrupt_exit_message(bar: ProgressBar):
        nonlocal uuid, server, env, validation, portal
        command_summary = _summarize_submission(uuid=uuid, server=server, env=env, app=portal.app)
        SHOW(f"Your {'validation' if validation else 'submission'} is still running on the server: {uuid}")
        SHOW(f"Use this command to check its status: {command_summary}")

    if not (uuid_metadata := portal.get_metadata(uuid, raise_exception=False)):
        found_non_suffixed_uuid = False
        if (dot := uuid.find(".")) > 0:
            if uuid_metadata := portal.get_metadata(uuid := uuid[:dot], raise_exception=False):
                found_non_suffixed_uuid = True
        if not found_non_suffixed_uuid:
            message = f"Submission ID not found: {uuid}" if uuid != "dummy" else "No submission ID specified."
            message += "\nSome recent submission IDs below. Use list-submissions to view more."
            if _print_recent_submissions(portal, message=message, count=4):
                if check_submission_script:
                    exit(1)
                return
            raise Exception(f"Cannot find object given uuid: {uuid}")
    if not portal.is_schema_type(uuid_metadata, INGESTION_SUBMISSION_TYPE_NAME):
        if portal.is_schema_file_type(uuid_metadata):
            _print_upload_file_summary(portal, uuid_metadata)
            # TODO: This is for special case of check-submission UPLOAD-FILE-UUID
            return
        undesired_type = portal.get_schema_type(uuid_metadata)
        raise Exception(f"Given ID is not for a submission or validation: {uuid} ({undesired_type})"
                        f" | Accession: {uuid_metadata.get('accession')}")
    if tobool(uuid_metadata.get("parameters", {}).get("validate_only")):
        validation = True

    if check_submission_script and validation:
        PRINT(f"This ID is for a server validation that had not yet completed.")

    action = "validation" if validation else "ingestion"
    if validation:
        SHOW(f"Waiting{f' (up to about {PROGRESS_TIMEOUT}s)' if verbose else ''}"
             f" for server validation results{f': {uuid}' if check_submission_script else '.'}")
    else:
        SHOW(f"Waiting{f' (up to about {PROGRESS_TIMEOUT}s)' if verbose else ''}"
             f" for submission results{f': {uuid}' if check_submission_script else '.'}")

    started = time.time()
    progress = define_progress_callback(PROGRESS_MAX_CHECKS,
                                        title="Validation" if validation else "Submission",
                                        interrupt_exit_message=interrupt_exit_message,
                                        include_status=False)
    most_recent_get_ingestion_submission_time = None
    most_recent_get_ingestion_status_time = None
    check_done = False
    check_status = None
    check_response = None
    ingestion_status = {}
    for n in range(PROGRESS_MAX_CHECKS):
        # Do the (new/2024-03-25) portal ingestion-status check here which reads
        # from Redis where the ingester is (now/2024-03-25) writing.
        # This is a very cheap call so do it on every progress iteration.
        if ((most_recent_get_ingestion_status_time is None) or
            ((time.time() - most_recent_get_ingestion_status_time) >= PROGRESS_GET_INGESTION_STATUS_INTERVAL)):  # noqa
            ingestion_status = portal.get(f"/ingestion-status/{uuid}")
            if (ingestion_status.status_code == 200) and (ingestion_status := ingestion_status.json()):
                loadxl_done = (ingestion_status.get(PROGRESS_LOADXL.DONE, None) is not None)
            else:
                ingestion_status = {}
                loadxl_done = False
            most_recent_get_ingestion_status_time = time.time()
        if (loadxl_done or (most_recent_get_ingestion_submission_time is None) or
            ((time.time() - most_recent_get_ingestion_submission_time) >= PROGRESS_GET_INGESTION_SUBMISSION_INTERVAL)):  # noqa
            if most_recent_get_ingestion_submission_time is None:
                progress(ingestion_status)
            else:
                progress({"check_server": True, "status": (check_status or "unknown").title(), **ingestion_status})
            # Do the actual portal check here (i.e by fetching the IngestionSubmission object)..
            [check_done, check_status, check_response] = (
                _check_ingestion_progress(uuid, keypair=portal.key_pair, server=portal.server))
            if check_done:
                break
            most_recent_get_ingestion_submission_time = time.time()
        progress({"check": True,
                  "next": PROGRESS_GET_INGESTION_SUBMISSION_INTERVAL -
                          (time.time() - most_recent_get_ingestion_submission_time),  # noqa
                  **ingestion_status})
        time.sleep(PROGRESS_INTERVAL)
    if check_done:
        progress({"finish": True, "done": True,
                  "status": (check_status or "unknown").title(), "response": check_response, **ingestion_status})
    else:
        progress({"finish": True, **ingestion_status})

    if not check_done:
        command_summary = _summarize_submission(uuid=uuid, server=server, env=env, app=portal.app)
        SHOW(f"Timed out (after {format_duration(round(time.time() - started))}) WAITING for {action}.")
        SHOW(f"Your {'validation' if validation else 'submission'} is still running on the server: {uuid}")
        SHOW(f"Use this command to check its status: {command_summary}")
        exit(1)

    if (check_submission_script and check_response and
        (check_parameters := check_response.get("parameters", {})) and
        tobool(check_parameters.get("validate_only")) and
        not check_parameters.get("submission_uuid")):  # noqa
        # This is the check-submission script waiting for a VALIDATION (not a submission)
        # to complete, i.e. the server validation part of submit-metadata-bundle had timed
        # out previously. And this which server validation is now complete. We now want
        # to give the user the opportunity to continue with the submission process,
        # ala submit_any_ingestion; see around line 830 of that function.
        PRINT(f"Details for this server validation ({uuid}) below:")
        _print_submission_summary(portal, check_response, nofiles=nofiles,
                                  check_submission_script=True, include_errors=True,
                                  verbose=verbose, debug=debug)
        validation_info = check_response.get("additional_data", {}).get("validation_output")
        # TODO: Cleanup/unify error structure from client and server!
        if isinstance(validation_info, list):
            validation_errors = [item for item in validation_info if item.lower().startswith("errored")]
            if validation_errors:
                PRINT("\nServer validation errors were encountered for this metadata.")
                PRINT("You will need to correct any errors and resubmit via submit-metadata-bundle.")
                exit(1)
        elif isinstance(validation_info, dict):
            if validation_info.get("ref") or validation_info.get("validation"):
                PRINT("\nServer validation errors were encountered for this metadata.")
                PRINT("You will need to correct any errors and resubmit via submit-metadata-bundle.")
                exit(1)
        if check_status != "success":
            exit(1)
        PRINT("Validation results (server): OK")
        if not yes_or_no("Do you want to now continue with the submission for this metadata?"):
            PRINT("Exiting with no action.")
            exit(0)
        # Get parameters for this submission from the validation IngestionSubmission object.
        consortia = None
        submission_centers = None
        if consortium := check_parameters.get("consortium"):
            consortia = [consortium]
        if submission_center := check_parameters.get("submission_center"):
            submission_centers = [submission_center]
        if isinstance(autoadd := check_parameters.get("autoadd"), str):
            try:
                autoadd = json.loads(autoadd)
            except Exception:
                autoadd = None
        if isinstance(user := check_parameters.get("user"), str):
            try:
                user = json.loads(user)
            except Exception:
                user = None
        if debug:
            PRINT("DEBUG: Continuing with submission process after a previous server validation timeout.")
        submission_uuid = _initiate_server_ingestion_process(
            portal=portal,
            ingestion_filename=None,
            is_server_validation=False,
            is_resume_submission=True,
            validation_ingestion_submission_object=check_response,
            consortia=consortia,
            submission_centers=submission_centers,
            autoadd=autoadd,
            datafile_size=check_parameters.get("datafile_size"),
            datafile_checksum=check_parameters.get("datafile_checksum"),
            user=user,
            debug=debug,
            debug_sleep=debug_sleep)
        SHOW(f"Submission tracking ID: {submission_uuid}")
        submission_done, submission_status, submission_response = _monitor_ingestion_process(
                submission_uuid, portal.server, portal.env, app=portal.app, keys_file=portal.keys_file,
                show_details=show_details, report=False, messages=True,
                validation=False,
                nofiles=True, noprogress=noprogress, timeout=timeout,
                verbose=verbose, debug=debug, debug_sleep=debug_sleep)
        if submission_status != "success":
            exit(1)
        PRINT("Submission complete!")
        do_any_uploads(submission_response,
                       main_search_directory=upload_directory,
                       main_search_directory_recursively=upload_directory_recursive,
                       config_google=rclone_google,
                       portal=portal,
                       verbose=verbose)
        return

    if check_submission_script or verbose or debug:  # or not validation
        PRINT(f"Details for this server {'validation' if validation else 'submission'} ({uuid}) below:")
        _print_submission_summary(portal, check_response,
                                  nofiles=nofiles, check_submission_script=check_submission_script,
                                  verbose=verbose, debug=debug)

    # If not sucessful then output any validation/submission results.
    if check_status != "success":
        PRINT(f"{'Validation' if validation else 'Submission'} results (server): ERROR"
              f"{f' ({check_status})' if check_status not in ['failure', 'error'] else ''}")
        printed_newline = False
        if check_response and (additional_data := check_response.get("additional_data")):
            if (validation_info := additional_data.get("validation_output")):
                if isinstance(validation_info, list):
                    if errors := [info for info in validation_info if info.lower().startswith("error:")]:
                        if not printed_newline:
                            PRINT_OUTPUT()
                            printed_newline = True
                        for error in errors:
                            PRINT_OUTPUT(f"- {_format_server_error(error, indent=2, debug=debug)}")
                elif isinstance(validation_info, dict):
                    if ((validation_errors := validation_info.get("validation")) and
                        isinstance(validation_errors, list) and validation_errors):  # noqa
                        if not printed_newline:
                            PRINT_OUTPUT()
                            printed_newline = True
                        PRINT_OUTPUT(f"- Data errors: {len(validation_errors)}")
                        for validation_error in validation_errors:
                            PRINT_OUTPUT(f"  - {_format_issue(validation_error)}")
                    if debug:
                        ref_errors = validation_info.get("ref")
                    elif not (ref_errors := validation_info.get("ref_grouped")):
                        ref_errors = validation_info.get("ref")
                    if ref_errors and (ref_errors := _validate_references(ref_errors, None, debug=debug)):
                        if not printed_newline:
                            PRINT_OUTPUT()
                            printed_newline = True
                        _print_reference_errors(ref_errors, verbose=verbose, debug=debug)
        if check_response and isinstance(other_errors := check_response.get("errors"), list) and other_errors:
            if not printed_newline:
                PRINT_OUTPUT()
                printed_newline = True
            for error in other_errors:
                PRINT_OUTPUT("- " + error)
        if output_file := get_output_file():
            PRINT_STDOUT(f"Exiting with server validation errors; see your output file: {output_file}")
        else:
            PRINT_STDOUT("\nExiting with no action with server validation errors.")
            PRINT_STDOUT("Use the --output FILE option to write errors to a file.")
        exit(1)

    return check_done, check_status, check_response


def _format_server_error(error: str, indent: int = 0, debug: bool = False) -> str:
    """
    Make an attempt at parsing and formatting a server (validation/submission) error.
    If we can't do it then just return the string as given. Here for example is what
    we hope a "typical" server error message looks like:
    'Error: /Software/DAX_SOFTWARE_VEPX Exception encountered on VirtualAppURL: /Software?skip_indexing=true&check_only=true&skip_links=trueBODY: {\'submitted_id\': \'DAX_SOFTWARE_VEPX\', \'category\': [\'Variant Annotation\'], \'title\': \'VEP\', \'version\': \'1.0.1\', \'consortia\': [\'smaht\'], \'submission_centers\': [\'9626d82e-8110-4213-ac75-0a50adf890ff\']}MSG: HTTP POST failed.Raw Exception: Bad response: 422 Unprocessable Entity (not 200 OK or 3xx redirect for http://localhost/Software?skip_indexing=true&check_only=true&skip_links=true)b\'{"@type": ["ValidationFailure", "Error"], "status": "error", "code": 422, "title": "Unprocessable Entity", "description": "Failed validation", "errors": [{"location": "submitted_id", "name": "Submission Code Mismatch", "description": "Submitted ID DAX_SOFTWARE_VEPX start (DAX) does not match options for given submission centers: [\\\'DAC\\\']."}]}\''  # noqa
    """

    def load_json_fuzzy(value: str) -> Optional[dict]:
        if isinstance(value, str):
            if (value := normalize_spaces(value)).endswith("'"):
                value = value[:-1]
            try:
                value = json.loads(value)
            except Exception:
                try:
                    value = ast.literal_eval(value)
                except Exception:
                    try:
                        value = json.loads(value := value.replace("\\", ""))
                    except Exception:
                        try:
                            value = json.loads(value := value.replace("'", '"'))
                        except Exception:
                            pass
            if isinstance(value, dict):
                value.pop("@type", None)
                return value

    def format_json_with_indent(value: dict, indent: int = 0) -> Optional[str]:
        if isinstance(value, dict):
            result = json.dumps(value, indent=4)
            if indent > 0:
                result = f"{indent * ' '}{result}"
                result = result.replace("\n", f"\n{indent * ' '}")
            return result

    pattern = r"\s*Error:\s*(.+?)\s*Exception.*BODY:\s*({.*})MSG:\s*(.*?)Raw Exception.*({\"@type\":.*)"
    match = re.match(pattern, error)
    if match and len(match.groups()) == 4:
        path = match.group(1)
        body = match.group(2)
        message = match.group(3)
        if message.endswith("."):
            message = message[:-1]
        error = match.group(4)
        body = load_json_fuzzy(body)
        error = load_json_fuzzy(error)
        if path and message and error and body:
            result = f"ERROR: {message} ▶ {path}"
            result += f"\n{format_json_with_indent(error, indent=indent)}"
            result += f"\n{format_json_with_indent(body, indent=indent)}"
            if not debug and error.get('title') and error.get('code') and error.get('description'):
                result = f"ERROR: {message} {path}"
                result += f"\n{indent * ' '}{error.get('title')} ({error.get('code')}): {error.get('description')}"
                if isinstance(errors := error.get('errors', []), list) and errors:
                    for error in errors:
                        result += f"\n{indent * ' '}{error.get('name')} ({error.get('location')})"
                        result += f"\n{indent * ' '}{error.get('description')}"
            return result
    return error.replace("Error:", "ERROR:")


def _check_ingestion_progress(uuid, *, keypair, server) -> Tuple[bool, str, dict]:
    """
    Calls endpoint to get this status of the IngestionSubmission uuid (in outer scope);
    this is used as an argument to check_repeatedly below to call over and over.
    Returns tuple with: done-indicator (True or False), short-status (str), full-response (dict)
    From outer scope: server, keypair, uuid (of IngestionSubmission)
    """
    tracking_url = _ingestion_submission_item_url(server=server, uuid=uuid)
    response = Portal(keypair).get(tracking_url)
    response_status_code = response.status_code
    response = response.json()
    if response_status_code == 404:
        return True, f"Not found - {uuid}", response
    # FYI this processing_status and its state, progress, outcome properties were ultimately set
    # from within the ingester process, from within types.ingestion.SubmissionFolio.processing_status.
    status = response.get("processing_status", {})
    if status.get("state") == "done":
        outcome = status.get("outcome")
        return True, outcome, response
    else:
        progress = status.get("progress")
        return False, progress, response


def _summarize_submission(uuid: str, app: str, server: Optional[str] = None, env: Optional[str] = None):
    if env:
        command_summary = f"check-submission --env {env} {uuid}"
    elif server:
        command_summary = f"check-submission --server {server} {uuid}"
    else:  # unsatisfying, but not worth raising an error
        command_summary = f"check-submission {uuid}"
    return command_summary


def _print_submission_summary(portal: Portal, result: dict,
                              nofiles: bool = False,
                              check_submission_script: bool = False,
                              include_errors: bool = False,
                              verbose: bool = False, debug: bool = False) -> None:
    if not result:
        return
    def is_admin_user(user_record: Optional[dict]) -> bool:  # noqa
        nonlocal portal, check_submission_script
        if not check_submission_script or not user_record or not (user_uuid := user_record.get("uuid")):
            return None
        try:
            return _is_admin_user(portal.get_metadata(user_uuid))
        except Exception:
            return None
    lines = []
    errors = []
    validation_info = None
    submission_type = "Submission"
    validation = None
    was_server_validation_timeout = False
    submitr_version = None
    if submission_parameters := result.get("parameters", {}):
        if validation := tobool(submission_parameters.get("validate_only")):
            submission_type = "Validation"
        if submission_file := submission_parameters.get("datafile"):
            if submission_file == "null":
                # This submission was a continuance via check-submission of a
                # server validation (via submit-metadata-bundle) which timed out;
                # we will note this fact very subtly in the output.
                if validation_datafile := submission_parameters.get("validation_datafile"):
                    submission_file = validation_datafile
                    was_server_validation_timeout = True
            lines.append(f"Submission File: {submission_file}")
    if submission_uuid := result.get("uuid"):
        lines.append(f"{submission_type} ID: {submission_uuid}")
    if date_created := format_datetime(result.get("date_created"), verbose=True):
        lines.append(f"{submission_type} Time: {date_created}")
    if submission_parameters:
        extra_file_info = ""
        if (datafile_size := submission_parameters.get("datafile_size", None)) is not None:
            if not isinstance(datafile_size, int) and isinstance(datafile_size, str) and datafile_size.isdigit():
                datafile_size = int(datafile_size)
            if isinstance(datafile_size, int):
                extra_file_info += f"{format_size(datafile_size)}"
        if datafile_checksum := submission_parameters.get("datafile_checksum"):
            if extra_file_info:
                extra_file_info += " | "
            extra_file_info += f"Checksum: {datafile_checksum}"
        if extra_file_info:
            lines.append(f"Submission File Info: {extra_file_info}")
        submitr_version = submission_parameters.get("submitr_version")
    if validation:
        lines.append(f"Validation Only: Yes ◀ ◀ ◀")
        if submission_parameters and (associated_submission_uuid := submission_parameters.get("submission_uuid")):
            lines.append(f"Associated Submission ID: {associated_submission_uuid}")
    elif submission_parameters and (associated_validation_uuid := submission_parameters.get("validation_uuid")):
        lines.append(f"Associated Validation ID:"
                     f" {associated_validation_uuid}{' (ω)' if was_server_validation_timeout else ''}")
    if submitted_by := result.get("submitted_by", {}).get("display_title"):
        consortia = None
        submission_center = None
        if consortia := result.get("consortia", []):
            consortium = consortia[0].get("display_title")
        if submission_centers := result.get("submission_centers", []):
            submission_center = submission_centers[0].get("display_title")
        if consortia:
            if submission_center:
                lines.append(f"Submitted By: {submitted_by} ({consortium} | {submission_center})")
            else:
                lines.append(f"Submitted By: {submitted_by} ({consortia})")
        elif submission_center:
            lines.append(f"Submitted By: {submitted_by} ({submission_center})")
        else:
            lines.append(f"Submitted By: {submitted_by}")
        if is_admin_user(result.get("submitted_by")) is True:
            lines[len(lines) - 1] += " ▶ Admin"
        # If more than one submission center print on separate line (only first one printed above).
        if len(submission_centers) > 1:
            submission_centers_line = ""
            for submission_center in submission_centers:
                if submission_centers_line:
                    submission_centers_line += " | "
                submission_centers_line += submission_center.get("display_title")
            lines.append(f"Submission Centers: {submission_centers_line}")
    if additional_data := result.get("additional_data"):
        if (validation_info := additional_data.get("validation_output")) and isinstance(validation_info, dict):
            # TODO: Cleanup/unify error structure from client and server!
            if ref_errors := _validate_references(validation_info.get("ref"), None):
                errors.extend(_format_reference_errors(ref_errors, verbose=verbose, debug=debug))
            if validation_errors := validation_info.get("validation"):
                errors.append(f"- Validation errors: {len(validation_errors)}")
                for validation_error in validation_errors:
                    errors.append(f"  - {_format_issue(validation_error)}")
    if processing_status := result.get("processing_status"):
        summary_lines = []
        if additional_data := result.get("additional_data"):
            if (validation_info := additional_data.get("validation_output")) and isinstance(validation_info, list):
                if status := [info for info in validation_info if info.lower().startswith("status:")]:
                    summary_lines.append(status[0])
        if state := processing_status.get("state"):
            summary_lines.append(f"State: {state.title()}")
        if progress := processing_status.get("progress"):
            summary_lines.append(f"Progress: {progress.title()}")
        if outcome := processing_status.get("outcome"):
            summary_lines.append(f"Outcome: {outcome.title()}")
        if main_status := result.get("status"):
            summary_lines.append(f"{main_status.title()}")
        if summary := " | ".join(summary_lines):
            lines.append("===")
            lines.append(summary)
    if additional_data := result.get("additional_data"):
        if (validation_info := additional_data.get("validation_output")) and isinstance(validation_info, list):
            summary_lines = []
            if types := [info for info in validation_info if info.lower().startswith("types")]:
                summary_lines.append(types[0])
            if created := [info for info in validation_info if info.lower().startswith("created")]:
                summary_lines.append(created[0])
            if updated := [info for info in validation_info if info.lower().startswith("updated")]:
                summary_lines.append(updated[0])
            if skipped := [info for info in validation_info if info.lower().startswith("skipped")]:
                summary_lines.append(skipped[0])
            if checked := [info for info in validation_info if info.lower().startswith("checked")]:
                summary_lines.append(checked[0])
            if errored := [info for info in validation_info if info.lower().startswith("errored")]:
                summary_lines.append(errored[0].replace("Errored", "Errors"))
            if errors := [info for info in validation_info if info.lower().startswith("error:")]:
                pass
            if total := [info for info in validation_info if info.lower().startswith("total")]:
                summary_lines.append(total[0])
            if summary := " | ".join(summary_lines):
                lines.append("===")
                lines.append(summary)
    if validation_info:
        summary_lines = []
        if s3_data_file := [info for info in validation_info if info.lower().startswith("s3 file: ")]:
            s3_data_file = s3_data_file[0][9:]
            if (rindex := s3_data_file.rfind("/")) > 0:
                s3_data_bucket = s3_data_file[5:rindex] if s3_data_file.startswith("s3://") else ""
                s3_data_file = s3_data_file[rindex + 1:]
                if s3_data_bucket:
                    if len(s3_data_bucket_parts := s3_data_bucket.split("/")) == 2:
                        summary_lines.append(f"AWS S3 Bucket: {s3_data_bucket_parts[0]}")
                        summary_lines.append(f"AWS S3 Key: {s3_data_bucket_parts[1]}")
                    else:
                        summary_lines.append(f"AWS S3: {s3_data_bucket}")
                summary_lines.append(f"AWS S3 File: {s3_data_file}")
        if s3_details_file := [info for info in validation_info if info.lower().startswith("details: ")]:
            s3_details_file = s3_details_file[0][9:]
            if (rindex := s3_details_file.rfind("/")) > 0:
                s3_details_bucket = s3_details_file[5:rindex] if s3_details_file.startswith("s3://") else ""
                s3_details_file = s3_details_file[rindex + 1:]
                if s3_details_bucket != s3_data_bucket:
                    summary_lines.append(f"S3 Bucket: {s3_details_bucket}")
                summary_lines.append(f"AWS S3 Details: {s3_details_file}")
        if summary_lines:
            lines.append("===")
            lines += summary_lines
    if additional_data and not nofiles:
        if upload_files := additional_data.get("upload_info"):
            lines.append("===")
            lines.append(f"Upload Files: {len(upload_files)} ...")
            for upload_file in upload_files:
                upload_file_uuid = upload_file.get("uuid")
                upload_file_name = upload_file.get("filename")
                if verbose:
                    upload_file_accession_name, upload_file_type = _get_upload_file_info(portal, upload_file_uuid)
                else:
                    upload_file_accession_name = None
                    upload_file_type = None
                lines.append("===")
                lines.append(f"Upload File: {upload_file_name}")
                lines.append(f"Upload File ID: {upload_file_uuid}")
                if upload_file_accession_name:
                    lines.append(f"Upload File Accession ID: {upload_file_accession_name}")
                if upload_file_type:
                    lines.append(f"Upload File Type: {upload_file_type}")
    if isinstance(toplevel_errors := result.get("errors"), list):
        errors.extend(toplevel_errors)
    if lines:
        lines = ["===", f"SMaHT {'Validation' if validation else 'Submission'} Summary"
                        f"{f' ({submitr_version})' if submitr_version else ''} [UUID]", "==="] + lines + ["==="]
        if errors and include_errors:
            lines += ["ERRORS ITEMIZED BELOW ...", "==="]
        print_boxed(lines, right_justified_macro=("[UUID]", lambda: submission_uuid), printf=PRINT)
        if errors and include_errors:
            for error in errors:
                PRINT(f"- {_format_server_error(error, indent=2, debug=debug)}")


def _print_upload_file_summary(portal: Portal, file_object: dict) -> None:
    file_uuid = file_object.get("uuid") or ""
    file_type = portal.get_schema_type(file_object) or ""
    file_name = file_object.get("filename") or ""
    file_format = file_object.get("file_format", {}).get("display_title") or ""
    file_title = file_object.get("display_title") or ""
    file_accession = file_object.get("accession") or ""
    file_size = file_object.get("file_size") or ""
    file_size_formatted = format_size(file_size) or ""
    file_status = file_object.get("status") or ""
    file_md5 = file_object.get("md5sum") or ""
    file_md5_content = file_object.get("content_md5sum") or ""
    file_md5_submitted = file_object.get("submitted_md5sum") or ""
    file_submitted_by = file_object.get("submitted_by", {}).get("display_title") or ""
    file_submitted_id = file_object.get("submitted_id") or ""
    file_created = format_datetime(file_object.get("date_created")) or ""
    file_modified = format_datetime(file_object.get("last_modified", {}).get("date_modified")) or ""
    file_modified_by = file_object.get("last_modified", {}).get("modified_by", {}).get("display_title") or ""
    submission_centers = _format_submission_centers(file_object.get("submission_centers")) or ""
    if file_md5_content == file_md5:
        file_md5_content = None
    if file_md5_submitted == file_md5:
        file_md5_submitted = None
    lines = [
        "===",
        "SMaHT Uploaded File [UUID]",
        f"===" if file_submitted_id else None,
        f"{file_submitted_id}" if file_submitted_id else None,
        "===",
        f"File: {file_title}" if file_title else None,
        f"File Name: {file_name}" if file_name else None,
        f"File Type: {file_type}" if file_type else None,
        f"File Format: {file_format}" if file_format else None,
        f"File Accession: {file_accession}" if file_accession else None,
        f"===",
        f"Status: {file_status.title()}" if file_status else None,
        f"Size: {file_size_formatted} ({file_size} bytes)" if file_size else None,
        f"Checksum: {file_md5}" if file_md5 else None,
        f"Content Checksum: {file_md5_content}" if file_md5_content else None,
        f"Submitted Checksum: {file_md5_submitted}" if file_md5_submitted else None,
        f"===",
        f"Submitted: {file_created} | {file_submitted_by}" if file_created and file_submitted_by else None,
        f"Modified: {file_modified} | {file_modified_by}" if file_modified and file_modified_by else None,
        f"Submission Centers: {submission_centers}" if submission_centers else None,
        "==="
    ]
    print_boxed(lines, right_justified_macro=("[UUID]", lambda: file_uuid))


def _format_submission_centers(submission_centers: Optional[List[dict]]) -> Optional[str]:
    if (not isinstance(submission_centers, List)) or (not submission_centers):
        return None
    result = ""
    for submission_center in submission_centers:
        if result:
            result += " | "
        result += submission_center.get("display_title")
    return result


@lru_cache(maxsize=256)
def _get_upload_file_info(portal: Portal, uuid: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        upload_file_info = portal.get(f"/{uuid}").json()
        upload_file_accession_based_name = upload_file_info.get("display_title")
        if upload_file_type := upload_file_info.get("data_type"):
            if isinstance(upload_file_type, list) and len(upload_file_type) > 0:
                upload_file_type = upload_file_type[0]
            elif not isinstance(upload_file_type, str):
                upload_file_type = None
            if upload_file_type:
                upload_file_type = Schema.type_name(upload_file_type)
        return upload_file_accession_based_name, upload_file_type
    except Exception:
        return None


def resume_uploads(uuid, server=None, env=None, bundle_filename=None, keydict=None,
                   upload_folder=None, no_query=False, subfolders=False,
                   rclone_google=None,
                   output_file=None, app=None, keys_file=None, env_from_env=False, verbose=False):

    if output_file:
        global PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW
        PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW = setup_for_output_file_option(output_file)

    portal = _define_portal(key=keydict, keys_file=keys_file, env=env,
                            server=server, app=app, env_from_env=env_from_env,
                            report=True, note="Resuming File Upload")
    if rclone_google:
        rclone_google.verify_connectivity()

    do_any_uploads(uuid,
                   metadata_file=bundle_filename,
                   main_search_directory=upload_folder,
                   main_search_directory_recursively=subfolders,
                   config_google=rclone_google,
                   portal=portal,
                   verbose=verbose)


def get_metadata_bundles_bucket_from_health_path(key: dict) -> str:
    return get_health_page(key=key).get("metadata_bundles_bucket")


# This can be set to True in unusual situations, but normally will be False to avoid unnecessary querying.
SUBMITR_SELECTIVE_UPLOADS = environ_bool("SUBMITR_SELECTIVE_UPLOADS")


def _fetch_submission_results(metadata_bundles_bucket: str, uuid: str) -> Optional[Tuple[str, dict]]:
    return _fetch_results(metadata_bundles_bucket, uuid, "submission.json")


def _fetch_exception_results(metadata_bundles_bucket: str, uuid: str) -> Optional[Tuple[str, str]]:
    return _fetch_results(metadata_bundles_bucket, uuid, "traceback.txt")


def _fetch_results(metadata_bundles_bucket: str, uuid: str, file: str) -> Optional[Tuple[str, str]]:
    results_key = f"{uuid}/{file}"
    results_location = f"s3://{metadata_bundles_bucket}/{results_key}"
    try:
        s3 = boto3.client("s3")
        response = s3.get_object(Bucket=metadata_bundles_bucket, Key=f"{uuid}/{file}")
        results = response['Body'].read().decode('utf-8')
        if file.endswith(".json"):
            results = json.loads(results)
        return (results_location, results)
    except BotoNoCredentialsError:
        PRINT(f"No credentials found for fetching: {results_location}")
    except Exception as e:
        if hasattr(e, "response") and e.response.get("Error", {}).get("Code", "").lower() == "accessdenied":
            PRINT(f"Access denied fetching: {results_location}")
        return (results_location, None)


def _validate_locally(ingestion_filename: str, portal: Portal, autoadd: Optional[dict] = None,
                      validation: bool = False, validate_local_only: bool = False,
                      upload_folder: Optional[str] = None, subfolders: bool = False,
                      rclone_google: Optional[RCloneGoogle] = None,
                      exit_immediately_on_errors: bool = False,
                      ref_nocache: bool = False, output_file: Optional[str] = None,
                      noanalyze: bool = False, json_only: bool = False, noprogress: bool = False,
                      verbose_json: bool = False, verbose: bool = False, quiet: bool = False,
                      debug: bool = False, debug_sleep: Optional[str] = None) -> StructuredDataSet:

    if json_only:
        noprogress = True

    structured_data = None  # TEMPORARY WORKAROUND FOR DCICUTILS BUG

    def define_progress_callback(debug: bool = False) -> None:
        nsheets = 0
        nrows = 0
        nrows_processed = 0
        nrefs_total = 0
        nrefs_resolved = 0
        nrefs_unresolved = 0
        nrefs_lookup = 0
        nrefs_exists_cache_hit = 0
        nrefs_lookup_cache_hit = 0
        nrefs_invalid = 0
        bar = ProgressBar(nrows, "Calculating", interrupt_exit=True)

        def progress_report(status: dict) -> None:  # noqa
            nonlocal bar, nsheets, nrows, nrows_processed, verbose, noprogress
            nonlocal nrefs_total, nrefs_resolved, nrefs_unresolved, nrefs_lookup
            nonlocal nrefs_exists_cache_hit, nrefs_lookup_cache_hit, nrefs_invalid
            if noprogress:
                return
            increment = 1
            if status.get(PROGRESS_PARSE.LOAD_START):
                nsheets = status.get(PROGRESS_PARSE.LOAD_COUNT_SHEETS) or 0
                nrows = status.get(PROGRESS_PARSE.LOAD_COUNT_ROWS) or 0
                if nrows > 0:
                    bar.set_total(nrows)
                    if nsheets > 0:
                        PRINT(
                            f"Parsing submission file which has{' only' if nsheets == 1 else ''}"
                            f" {nsheets} sheet{'s' if nsheets != 1 else ''} and a total of {nrows} rows.")
                    else:
                        PRINT(f"Parsing submission file which has a total of {nrows} row{'s' if nrows != 1 else ''}.")
                elif nsheets > 0:
                    PRINT(f"Parsing submission file which has {nsheets} sheet{'s' if nsheets != 1 else ''}.")
                else:
                    PRINT(f"Parsing submission file which has a total of {nrows} row{'s' if nrows != 1 else ''}.")
                return
            elif status.get(PROGRESS_PARSE.LOAD_ITEM) or status.get(PROGRESS_PARSE.LOAD_DONE):
                if not status.get(PROGRESS_PARSE.LOAD_DONE):
                    nrows_processed += increment
                nrefs_total = status.get(PROGRESS_PARSE.LOAD_COUNT_REFS) or 0
                nrefs_resolved = status.get(PROGRESS_PARSE.LOAD_COUNT_REFS_FOUND) or 0
                nrefs_unresolved = status.get(PROGRESS_PARSE.LOAD_COUNT_REFS_NOT_FOUND) or 0
                nrefs_lookup = status.get(PROGRESS_PARSE.LOAD_COUNT_REFS_LOOKUP) or 0
                nrefs_exists_cache_hit = status.get(PROGRESS_PARSE.LOAD_COUNT_REFS_EXISTS_CACHE_HIT) or 0
                nrefs_lookup_cache_hit = status.get(PROGRESS_PARSE.LOAD_COUNT_REFS_LOOKUP_CACHE_HIT) or 0
                nrefs_invalid = status.get(PROGRESS_PARSE.LOAD_COUNT_REFS_INVALID) or 0
                if not status.get(PROGRESS_PARSE.LOAD_DONE):
                    bar.increment_progress(increment)
            elif not status.get(PROGRESS_PARSE.LOAD_DONE):
                bar.increment_progress(increment)
            message = f"▶ Rows: {nrows} | Parsed: {nrows_processed}"
            if nrefs_total > 0:
                message += f" ‖ Refs: {nrefs_total}"
                if nrefs_unresolved > 0:
                    message += f" | Unresolved: {nrefs_unresolved}"
                if nrefs_lookup > 0:
                    message += f" | Lookups: {nrefs_lookup}"
                if nrefs_invalid > 0:
                    message += f" | Invalid: {nrefs_invalid}"
                if (verbose or debug) and (nrefs_exists_cache_hit > 0):
                    message += f" | Hits: {nrefs_exists_cache_hit}"
                    if debug:
                        message += f" [{nrefs_lookup_cache_hit}]"
            bar.set_description(message)
            if status.get(PROGRESS_PARSE.LOAD_DONE):
                bar.done()

        return progress_report

    if debug:
        PRINT("DEBUG: Starting client validation.")

    structured_data = StructuredDataSet(None, portal, autoadd=autoadd,
                                        ref_lookup_strategy=ref_lookup_strategy,
                                        ref_lookup_nocache=ref_nocache,
                                        progress=None if noprogress else define_progress_callback(debug=debug),
                                        debug_sleep=debug_sleep)
    structured_data.load_file(ingestion_filename)

    if debug:
        PRINT("DEBUG: Finished client validation.")

    if debug:
        PRINT_OUTPUT(f"DEBUG: Reference total count: {structured_data.ref_total_count}")
        PRINT_OUTPUT(f"DEBUG: Reference total found count: {structured_data.ref_total_found_count}")
        PRINT_OUTPUT(f"DEBUG: Reference total not found count: {structured_data.ref_total_notfound_count}")
        PRINT_OUTPUT(f"DEBUG: Reference exists cache hit count: {structured_data.ref_exists_cache_hit_count}")
        PRINT_OUTPUT(f"DEBUG: Reference exists cache miss count: {structured_data.ref_exists_cache_miss_count}")
        PRINT_OUTPUT(f"DEBUG: Reference exists internal count: {structured_data.ref_exists_internal_count}")
        PRINT_OUTPUT(f"DEBUG: Reference exists external count: {structured_data.ref_exists_external_count}")
        PRINT_OUTPUT(f"DEBUG: Reference lookup cache hit count: {structured_data.ref_lookup_cache_hit_count}")
        PRINT_OUTPUT(f"DEBUG: Reference lookup cache miss count: {structured_data.ref_lookup_cache_miss_count}")
        PRINT_OUTPUT(f"DEBUG: Reference lookup count: {structured_data.ref_lookup_count}")
        PRINT_OUTPUT(f"DEBUG: Reference lookup found count: {structured_data.ref_lookup_found_count}")
        PRINT_OUTPUT(f"DEBUG: Reference lookup not found count: {structured_data.ref_lookup_notfound_count}")
        PRINT_OUTPUT(f"DEBUG: Reference lookup error count: {structured_data.ref_lookup_error_count}")
        PRINT_OUTPUT(f"DEBUG: Reference invalid identifying property count:"
                     f" {structured_data.ref_invalid_identifying_property_count}")
    if json_only:
        PRINT_OUTPUT(json.dumps(structured_data.data, indent=4))
        exit(1)
    if verbose_json:
        PRINT_OUTPUT(f"Parsed JSON:")
        PRINT_OUTPUT(json.dumps(structured_data.data, indent=4))
    validation_okay = _validate_data(structured_data, portal, ingestion_filename,
                                     upload_folder, recursive=subfolders, verbose=verbose, debug=debug)
    if validation_okay:
        PRINT("Validation results (preliminary): OK")
    elif exit_immediately_on_errors:
        if verbose:
            _print_structured_data_verbose(portal, structured_data, ingestion_filename, upload_folder=upload_folder,
                                           recursive=subfolders, rclone_google=rclone_google,
                                           validation=validation, noanalyze=True, verbose=verbose)
        if output_file:
            PRINT_STDOUT(f"Exiting with preliminary validation errors; see your output file: {output_file}")
        else:
            if not verbose:
                PRINT_STDOUT()
            PRINT_STDOUT(f"Exiting with preliminary validation errors.")
            PRINT_STDOUT("Use the --output FILE option to write errors to a file.")
        exit(1)

    if verbose:
        _print_structured_data_verbose(portal, structured_data, ingestion_filename,
                                       upload_folder=upload_folder, recursive=subfolders,
                                       rclone_google=rclone_google,
                                       validation=validation, verbose=verbose)
    elif not quiet:
        if not noanalyze:
            _print_structured_data_status(portal, structured_data, validation=validation,
                                          report_updates_only=True, noprogress=noprogress, verbose=verbose, debug=debug)
        else:
            PRINT("Skipping analysis of metadata wrt creates/updates to be done (per --noanalyze).")
    if not validation_okay:
        if not yes_or_no(f"There are some preliminary errors outlined above;"
                         f" do you want to continue with {'validation' if validation else 'submission'}?"):
            exit(1)
    if validate_local_only:
        PRINT("Terminating as requested (per --validate-local-only).")
        exit(0 if validation_okay else 1)

    return structured_data


def _validate_data(structured_data: StructuredDataSet, portal: Portal, ingestion_filename: str,
                   upload_folder: str, recursive: bool, verbose: bool = False, debug: bool = False) -> bool:
    nerrors = 0

    if initial_validation_errors := _validate_initial(structured_data, portal):
        nerrors += len(initial_validation_errors)

    if ref_validation_errors := _validate_references(structured_data.ref_errors, ingestion_filename, debug=debug):
        nerrors += len(ref_validation_errors)

    structured_data.validate()
    if data_validation_errors := structured_data.validation_errors:
        nerrors += len(data_validation_errors)

    if nerrors > 0:
        PRINT_OUTPUT("Validation results (preliminary): ERROR")

    printed_newline = False

    if initial_validation_errors:
        if not printed_newline:
            PRINT_OUTPUT()
            printed_newline = True
        PRINT_OUTPUT(f"- Initial errors: {len(initial_validation_errors)}")
        for error in initial_validation_errors:
            PRINT_OUTPUT(f"  - ERROR: {error}")

    if data_validation_errors:
        if not printed_newline:
            PRINT_OUTPUT()
            printed_newline = True
        PRINT_OUTPUT(f"- Data errors: {len(data_validation_errors)}")
        for error in data_validation_errors:
            PRINT_OUTPUT(f"  - ERROR: {_format_issue(error, ingestion_filename)}")

    if ref_validation_errors:
        if not printed_newline:
            PRINT_OUTPUT()
            printed_newline = True
        _print_reference_errors(ref_validation_errors, verbose=verbose, debug=debug)
        # PRINT_OUTPUT(f"- Reference errors: {len(ref_validation_errors)}")
        # if debug:
        #     for error in ref_validation_errors:
        #         PRINT_OUTPUT(f"  - ERROR: {error}")
        # else:
        #     for error in ref_validation_errors:
        #         PRINT_OUTPUT(f"  - ERROR: {error['ref']} (refs: {error['count']})")

    return not (nerrors > 0)


def _validate_references(ref_errors: Optional[List[dict]], ingestion_filename: str, debug: bool = False) -> List[str]:
    def normalize(ref_errors: Optional[List[dict]]) -> None:  # noqa
        # Server sends back fill path to "file"; adjust to basename; fix on server (TODO).
        if isinstance(ref_errors, list):
            for ref_error in ref_errors:
                if isinstance(src := ref_error.get("src"), dict) and isinstance(file := src.get("file"), str):
                    src["file"] = os.path.basename(file)
    normalize(ref_errors)
    ref_validation_errors = []
    ref_validation_errors_truncated = None
    if isinstance(ref_errors, list):
        for ref_error in ref_errors:
            if debug:
                ref_validation_errors.append(f"{_format_issue(ref_error, ingestion_filename)}")
            elif ref_error.get("truncated") is True:
                ref_validation_errors_truncated = {"ref": f"{_format_issue(ref_error, ingestion_filename)}"}
            elif ref_error.get("ref"):
                # TODO: Can we actually get here?
                ref_validation_errors.append(ref_error)
            else:
                if ref := ref_error.get("error"):
                    if ref_error_existing := [r for r in ref_validation_errors if r.get("ref") == ref]:
                        ref_error_existing = ref_error_existing[0]
                        ref_error_existing["count"] += 1
                        if isinstance(src := ref_error.get("src"), dict):
                            if isinstance(ref_error_existing.get("srcs"), list):
                                ref_error_existing["srcs"].append(src)
                            else:
                                ref_error_existing["srcs"] = [src]
                    else:
                        ref_validation_error = {"ref": ref, "count": 1}
                        if isinstance(src := ref_error.get("src"), dict):
                            ref_validation_error["srcs"] = [src]
                        ref_validation_errors.append(ref_validation_error)
    if debug:
        ref_validation_errors = sorted(ref_validation_errors)
    else:
        ref_validation_errors = sorted(ref_validation_errors, key=lambda item: item.get("ref"))
    if ref_validation_errors_truncated:
        ref_validation_errors.append(ref_validation_errors_truncated)
    return ref_validation_errors


def _print_reference_errors(ref_errors: List[dict], verbose: bool = False, debug: bool = False) -> None:
    if errors := _format_reference_errors(ref_errors=ref_errors, verbose=verbose, debug=debug):
        for error in errors:
            PRINT_OUTPUT(error)


def _format_reference_errors(ref_errors: List[dict], verbose: bool = False, debug: bool = False) -> List[str]:
    errors = []
    if isinstance(ref_errors, list) and ref_errors:
        nref_errors = len([r for r in ref_errors
                           if (not isinstance(r, dict)) or (not r.get('ref', '').startswith('Truncated'))])
        errors.append(f"- Reference errors: {nref_errors}")
        if debug:
            for ref_error in ref_errors:
                errors.append(f"  - ERROR: {ref_error}")
        else:
            truncated = None
            for ref_error in ref_errors:
                if ref_error["ref"].startswith("Truncated"):
                    truncated = ref_error["ref"]
                elif isinstance(count := ref_error.get("count"), int):
                    errors.append(f"  - ERROR: {ref_error['ref']} (refs: {count})")
                    if verbose and isinstance(srcs := ref_error.get("srcs"), list):
                        for src in srcs:
                            errors.append(f"    - {_format_src(src)}")
                else:
                    errors.append(f"  - ERROR: {ref_error['ref']}")
            if truncated:
                errors.append(f"  - {truncated}")
    return errors


def _validate_initial(structured_data: StructuredDataSet, portal: Portal) -> List[str]:
    # TODO: Move this more specific "pre" validation checking to dcicutils.structured_data.
    # Just for nicer more specific (non-jsonschema) error messages for common problems.
    initial_validation_errors = []
    if not (portal and structured_data and structured_data.data):
        return initial_validation_errors
    for schema_name in structured_data.data:
        if schema_data := portal.get_schema(schema_name):
            if identifying_properties := schema_data.get(EncodedSchemaConstants.IDENTIFYING_PROPERTIES):
                identifying_properties = set(identifying_properties)
                if data := structured_data.data[schema_name]:
                    data_properties = set(data[0].keys())
                    if not data_properties & identifying_properties:
                        # No identifying properties for this object.
                        initial_validation_errors.append(f"No identifying properties for type: {schema_name}")
            if required_properties := schema_data.get(JsonSchemaConstants.REQUIRED):
                required_properties = set(required_properties) - set("submission_centers")
                if data := structured_data.data[schema_name]:
                    data_properties = set(data[0].keys())
                    if (data_properties & required_properties) != required_properties:
                        if missing_required_properties := required_properties - data_properties:
                            # Missing required properties for this object.
                            for missing_required_property in missing_required_properties:
                                initial_validation_errors.append(
                                    f"Missing required property ({missing_required_property})"
                                    f" for type: {schema_name}")
    return initial_validation_errors


def _print_structured_data_verbose(portal: Portal, structured_data: StructuredDataSet, ingestion_filename: str,
                                   upload_folder: str, recursive: bool,
                                   rclone_google: Optional[RCloneGoogle] = None,
                                   validation: bool = False,
                                   noanalyze: bool = False, noprogress: bool = False, verbose: bool = False) -> None:
    if (reader_warnings := structured_data.reader_warnings):
        PRINT_OUTPUT(f"\n> Parser warnings:")
        for reader_warning in reader_warnings:
            PRINT_OUTPUT(f"  - {_format_issue(reader_warning, ingestion_filename)}")
    if structured_data.data:
        PRINT_OUTPUT(f"\n> Types submitting:")
        for type_name in sorted(structured_data.data):
            PRINT_OUTPUT(f"  - {type_name}: {len(structured_data.data[type_name])}"
                         f" object{'s' if len(structured_data.data[type_name]) != 1 else ''}")
    if resolved_refs := structured_data.resolved_refs:
        PRINT_OUTPUT(f"\n> Resolved object (linkTo) references:")
        for resolved_ref in sorted(resolved_refs):
            PRINT_OUTPUT(f"  - {resolved_ref}")
    files_for_upload = FilesForUpload.assemble(structured_data.upload_files,
                                               main_search_directory=upload_folder,
                                               main_search_directory_recursively=recursive,
                                               config_google=rclone_google)
    if files_for_upload:
        PRINT_OUTPUT()
        FilesForUpload.review(files_for_upload, review_only=True, verbose=verbose)
        PRINT_OUTPUT()
    if not noanalyze:
        _print_structured_data_status(portal, structured_data,
                                      validation=validation,
                                      report_updates_only=True, noprogress=noprogress, verbose=verbose)
    else:
        PRINT("Skipping analysis of metadata wrt creates/updates to be done (per --noanalyze).")


def _print_structured_data_status(portal: Portal, structured_data: StructuredDataSet,
                                  validation: bool = False,
                                  report_updates_only: bool = False,
                                  noprogress: bool = False, verbose: bool = False, debug: bool = False) -> None:

    if verbose:
        report_updates_only = False

    def define_progress_callback(debug: bool = False) -> None:
        ntypes = 0
        nobjects = 0
        ncreates = 0
        nupdates = 0
        nlookups = 0
        bar = ProgressBar(nobjects, "Calculating", interrupt_exit=True, interrupt_message="analysis")
        def progress_report(status: dict) -> None:  # noqa
            nonlocal bar, ntypes, nobjects, ncreates, nupdates, nlookups, noprogress
            if noprogress:
                return
            increment = 1
            if status.get(PROGRESS_PARSE.ANALYZE_START):
                ntypes = status.get(PROGRESS_PARSE.ANALYZE_COUNT_TYPES)
                nobjects = status.get(PROGRESS_PARSE.ANALYZE_COUNT_ITEMS)
                bar.set_total(nobjects)
                PRINT(f"Analyzing submission file which has {ntypes} type{'s' if ntypes != 1 else ''}"
                      f" and a total of {nobjects} item{'s' if nobjects != 1 else ''}.")
                return
            elif status.get(PROGRESS_PARSE.ANALYZE_DONE):
                bar.done()
                return
            elif status.get(PROGRESS_PARSE.ANALYZE_CREATE):
                ncreates += increment
                nlookups += status.get(PROGRESS_PARSE.ANALYZE_LOOKUPS) or 0
                bar.increment_progress(increment)
            elif status.get(PROGRESS_PARSE.ANALYZE_UPDATE):
                nupdates += increment
                nlookups += status.get(PROGRESS_PARSE.ANALYZE_LOOKUPS) or 0
                bar.increment_progress(increment)
            else:
                nlookups += status.get(PROGRESS_PARSE.ANALYZE_LOOKUPS) or 0
                bar.increment_progress(increment)
            # duration = time.time() - started
            # nprocessed = ncreates + nupdates
            # rate = nprocessed / duration
            # nremaining = nobjects - nprocessed
            # duration_remaining = (nremaining / rate) if rate > 0 else 0
            message = (
                f"▶ Items: {nobjects} | Checked: {ncreates + nupdates}"
                f" ‖ Creates: {ncreates} | Updates: {nupdates} | Lookups: {nlookups}")
            bar.set_description(message)
        return progress_report

    # TODO: Allow abort of compare by returning some value from the
    # progress callback that just breaks out of the loop in structured_data.
    diffs = structured_data.compare(progress=define_progress_callback(debug=debug))

    ncreates = 0
    nupdates = 0
    nsubstantive_updates = 0
    for object_type in diffs:
        for object_info in diffs[object_type]:
            if object_info.uuid:
                if object_info.diffs:
                    nsubstantive_updates += 1
                nupdates += 1
            else:
                ncreates += 1

    to_or_which_would = "which would" if validation else "to"

    if ncreates > 0:
        if nupdates > 0:
            message = f"Objects {to_or_which_would} be -> Created: {ncreates} | Updated: {nupdates}"
            if nsubstantive_updates == 0:
                message += " (no substantive differences)"
        else:
            message = f"Objects {to_or_which_would} be created: {ncreates}"
    elif nupdates:
        message = f"Objects {to_or_which_would} be updated: {nupdates}"
        if nsubstantive_updates == 0:
            message += " (no substantive differences)"
    else:
        message = "No objects {to_or_which_would} create or update."
        return

    if report_updates_only and nsubstantive_updates == 0:
        PRINT(f"{message}")
        return
    else:
        if report_updates_only:
            PRINT(f"{message} | Update details below ...")
        else:
            PRINT(f"{message} | Details below ...")

    will_or_would = "Would" if validation else "Will"

    nreported = 0
    printed_newline = False
    for object_type in sorted(diffs):
        printed_type = False
        for object_info in diffs[object_type]:
            if report_updates_only and (not object_info.uuid or not object_info.diffs):
                # Create or non-substantive update, and report-updates-only.
                continue
            nreported += 1
            if not printed_newline:
                PRINT()
                printed_newline = True
            if not printed_type:
                PRINT(f"  TYPE: {object_type}")
                printed_type = True
            PRINT(f"  - OBJECT: {object_info.path}")
            if not object_info.uuid:
                PRINT(f"    Does not exist -> {will_or_would} be CREATED")
            else:
                message = f"    Already exists -> {object_info.uuid} -> {will_or_would} be UPDATED"
                if not object_info.diffs:
                    message += " (no substantive diffs)"
                    PRINT(message)
                else:
                    message += " (substantive DIFFs below)"
                    PRINT(message)
                    for diff_path in object_info.diffs:
                        if (diff := object_info.diffs[diff_path]).creating_value:
                            PRINT(f"     CREATE {diff_path}: {diff.value}")
                        elif diff.updating_value:
                            PRINT(f"     UPDATE {diff_path}: {diff.updating_value} -> {diff.value}")
                        elif (diff := object_info.diffs[diff_path]).deleting_value:
                            PRINT(f"     DELETE {diff_path}: {diff.value}")
    if nreported:
        PRINT()


def _print_json_with_prefix(data, prefix):
    json_string = json.dumps(data, indent=4)
    json_string = f"\n{prefix}".join(json_string.split("\n"))
    PRINT_OUTPUT(prefix, end="")
    PRINT_OUTPUT(json_string)


def _format_issue(issue: dict, original_file: Optional[str] = None) -> str:
    issue_message = None
    if issue:
        if error := issue.get("error"):
            issue_message = error.replace("'$.", "'")
            issue_message = error.replace("Validation error at '$': ", "")
        elif warning := issue.get("warning"):
            issue_message = warning
        elif issue.get("truncated"):
            return f"Truncated result set | More: {issue.get('more')} | See: {issue.get('details')}"
    return f"{_format_src(issue)}: {issue_message}" if issue_message else ""


def _format_src(issue: dict) -> str:
    def file_without_extension(file: str) -> str:
        if isinstance(file, str):
            if file.endswith(".gz"):
                file = file[:-3]
            if (dot := file.rfind(".")) > 0:
                file = file[:dot]
        return file
    if not isinstance(issue, dict):
        return ""
    if not isinstance(issue_src := issue.get("src"), dict):
        issue_src = issue
    if src_type := issue_src.get("type"):
        src = src_type
    elif src_sheet := issue_src.get("sheet"):
        src = src_sheet
    elif src_file := file_without_extension(issue_src.get("file")):
        src = src_file
    else:
        src = ""
    if src_column := issue_src.get("column"):
        src = f"{src}.{src_column}" if src else src_column
    if (src_row := issue_src.get("row", 0)) > 0:
        src = f"{src} [{src_row}]" if src else f"[{src_row}]"
    if not src:
        if issue.get("warning"):
            src = "Warning"
        elif issue.get("error"):
            src = "Error"
        else:
            src = "Issue"
    return src


def _define_portal(key: Optional[dict] = None, env: Optional[str] = None, server: Optional[str] = None,
                   app: Optional[str] = None, keys_file: Optional[str] = None, env_from_env: bool = False,
                   report: bool = False, verbose: bool = False,
                   note: Optional[str] = None, ping: bool = False) -> Portal:

    def get_default_keys_file():
        nonlocal app
        return os.path.expanduser(os.path.join(Portal.KEYS_FILE_DIRECTORY, f".{app.lower()}-keys.json"))

    def sanity_check_keys_file(keys_file: Optional[str] = None) -> Optional[str]:
        keys_file_from_env = False
        if not keys_file:
            keys_file = os.environ.get("SMAHT_KEYS")
            keys_file_from_env = os.environ.get("SMAHT_KEYS")
        if keys_file:
            if not keys_file.endswith(".json"):
                PRINT(f"ERROR: The specified keys file{' (from SMAHT_KEYS)' if keys_file_from_env else ''}"
                      f" is not a .json file: {keys_file}")
                exit(1)
            if not keys_file.endswith(".json") or not os.path.exists(keys_file):
                PRINT(f"ERROR: The specified keys file{' (from SMAHT_KEYS)' if keys_file_from_env else ''}"
                      f" must be the name of an existing .json file: {keys_file}")
                exit(1)
            try:
                with open(keys_file, "r") as f:
                    json.load(f)
            except Exception:
                PRINT(f"ERROR: The specified keys file{' (from SMAHT_KEYS)' if keys_file_from_env else ''}"
                      f" cannot be loaded as JSON: {keys_file}")
                exit(1)
        return keys_file

    if not env and not env_from_env:
        if env_from_env := os.environ.get("SMAHT_ENV"):
            env = env_from_env

    raise_exception = True
    if not app:
        app = DEFAULT_APP
        app_default = True
    else:
        app_default = False
    portal = None
    keys_file = sanity_check_keys_file(keys_file)
    try:
        # TODO: raise_exception does not totally work here (see portal_utils.py).
        portal = Portal(key or keys_file, env=env, server=server, app=app, raise_exception=True)
    except Exception as e:
        if "not found in keys-file" in str(e):
            if not env:
                PRINT(f"No environment specified from keys file: {keys_file or get_default_keys_file()}")
                PRINT(f"Use the --env option with a name from that file; or set your SMAHT_ENV environment variable.")
            else:
                PRINT(f"Environment ({env}) not found in keys file: {keys_file or get_default_keys_file()}")
            exit(1)
        else:
            PRINT(e)
            exit(1)
    if not portal or not portal.key:
        try:
            if keys_file and not os.path.exists(keys_file):
                PRINT(f"No keys file found: {keys_file or get_default_keys_file()}")
                exit(1)
            else:
                default_keys_file = get_default_keys_file()
                if not os.path.exists(default_keys_file):
                    PRINT(f"No default keys file found: {default_keys_file}")
                    exit(1)
        except Exception:
            pass
        if raise_exception:
            raise Exception(
                f"No portal key defined; setup your ~/.{app or 'smaht'}-keys.json file and use the --env argument.")
    if report:
        message = f"SMaHT submitr version: {get_version()}"
        if note:
            message += f" | {note}"
        PRINT(message)
        if verbose:
            PRINT(f"Portal app name is{' (default)' if app_default else ''}: {app}")
        if not env and server and not portal.env:
            # TODO: Handle portal_utils bug where not setting corresponding portal.env if server specified.
            if portal.keys_file:
                try:
                    with io.open(portal.keys_file) as f:
                        keys = json.load(f)
                        if env := [k for k in keys if Portal._normalize_server(keys[k].get("server")) == server]:
                            portal._env = env[0]
                except Exception:
                    pass
        PRINT(f"Portal environment (in keys file) is: {portal.env}{' (from SMAHT_ENV)' if env_from_env else ''}")
        PRINT(f"Portal keys file is: {format_path(portal.keys_file)}")
        PRINT(f"Portal server is: {portal.server}")
        if portal.key_id and len(portal.key_id) > 2:
            PRINT(f"Portal key prefix is: {portal.key_id[:2]}******")
    if ping and not portal.ping():
        PRINT(f"Cannot ping Portal!")
        exit(1)
    return portal


@lru_cache(maxsize=1)
def _get_consortia(portal: Portal) -> List[str]:
    results = []
    if consortia := portal.get_metadata("/consortia?limit=1000"):
        consortia = sorted(consortia.get("@graph", []), key=lambda key: key.get("identifier"))
        for consortium in consortia:
            if ((consortium_name := consortium.get("identifier")) and
                (consortium_uuid := consortium.get("uuid"))):  # noqa
                results.append({"name": consortium_name, "uuid": consortium_uuid})
    return results


@lru_cache(maxsize=1)
def _get_submission_centers(portal: Portal) -> List[str]:
    results = []
    if submission_centers := portal.get_metadata("/submission-centers?limit=1000"):
        submission_centers = sorted(submission_centers.get("@graph", []), key=lambda key: key.get("identifier"))
        for submission_center in submission_centers:
            if ((submission_center_name := submission_center.get("identifier")) and
                (submission_center_uuid := submission_center.get("uuid"))):  # noqa
                results.append({"name": submission_center_name, "uuid": submission_center_uuid})
    return results


def _print_metadata_file_info(file: str, env: str,
                              refs: bool = False, files: bool = False,
                              upload_folder: Optional[str] = None,
                              subfolders: bool = False,
                              rclone_google: Optional[RCloneGoogle] = None,
                              output_file: Optional[str] = None,
                              verbose: bool = False) -> None:
    if output_file:
        set_output_file(output_file)
    PRINT(f"Metadata File: {os.path.basename(file)}")
    if size := get_file_size(file):
        PRINT(f"Size: {format_size(size)} ({size})")
    if modified := get_file_modified_datetime(file):
        PRINT(f"Modified: {modified}")
    if md5 := compute_file_md5(file):
        PRINT(f"MD5: {md5}")
    if (etag := compute_file_etag(file)) and etag != md5:
        PRINT(f"S3 ETag: {etag}")
    sheet_lines = []
    if is_excel_file_name(file):
        excel = Excel(file)
        nrows_total = 0
        for sheet_name in sorted(excel.sheet_names):
            nrows = excel.sheet_reader(sheet_name).nrows
            sheet_lines.append(f"- Sheet: {sheet_name} ▶ Rows: {nrows}")
            nrows_total += nrows
        sheet_lines = "\n" + "\n".join(sheet_lines)
        PRINT(f"Sheets: {excel.nsheets} | Rows: {nrows_total}{sheet_lines}")
    portal = None
    if (refs is True) or (files is True):
        max_output = 10
        portal = _define_portal(env=env, ping=True)
        structured_data = StructuredDataSet(file, portal, norefs=True)
        if refs is True:
            def print_refs(refs: List[dict], max_output: int, output_file: str, verbose: bool = False) -> None:
                def note_output():
                    nonlocal max_output, output_file, noutput, printf, truncated
                    noutput += 1
                    if noutput >= max_output and output_file and not truncated:
                        PRINT_STDOUT(f"+ Truncated results | See your output file for full listing: {output_file}")
                        printf = PRINT_OUTPUT
                        truncated = True
                printf = PRINT
                noutput = 0
                truncated = False
                for ref in sorted(refs, key=lambda ref: ref["path"]):
                    printf(f"- {ref['path']} (references: {len(ref['srcs'])})")
                    note_output()
                    if verbose:
                        srcs = sorted(ref["srcs"], key=lambda src: f"{src['type']}|{src['column']}|"
                                                                   f"{str(src['row']).rjust(8)}")
                        for src in srcs:
                            printf(f"  - {_format_src(src)}")
                            note_output()
            unchecked_refs = structured_data.unchecked_refs
            PRINT(f"References: {len(unchecked_refs)}")
            print_refs(unchecked_refs, max_output=max_output, output_file=output_file, verbose=verbose)
        if files is True:
            files_for_upload = FilesForUpload.assemble(structured_data,
                                                       main_search_directory=upload_folder,
                                                       main_search_directory_recursively=subfolders,
                                                       config_google=rclone_google)
            FilesForUpload.review(files_for_upload, portal=portal, review_only=True, verbose=True, printf=PRINT)
    if not (refs is True):
        if not (files is True):
            PRINT("Note: Use --refs to view references; and --files to view files for upload.")
        else:
            PRINT("Note: Use --refs to view references (linkTo) paths.")
    elif not (files is True):
        PRINT("Note: Use --files to view files for upload.")
    if not portal:
        portal = _define_portal(env=env, ping=True)
    this_metadata_template_version, current_metadata_template_version = (
        check_metadata_version(file, portal=portal, quiet=True))
    if this_metadata_template_version:
        if this_metadata_template_version == current_metadata_template_version:
            PRINT(f"Based on the latest HMS metadata template: {current_metadata_template_version} ✓")
        else:
            print_metadata_version_warning(this_metadata_template_version, current_metadata_template_version)


def _ping(app: str, env: str, server: str, keys_file: str,
          env_from_env: bool = False, verbose: bool = False) -> bool:
    portal = _define_portal(env=env, server=server, app=app, keys_file=keys_file,
                            env_from_env=env_from_env, report=verbose)
    return portal.ping()


def _pytesting():
    return "pytest" in sys.modules
