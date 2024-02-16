import boto3
from botocore.exceptions import NoCredentialsError as BotoNoCredentialsError
import io
import json
import os
import re
import subprocess
import sys
import time
from typing import BinaryIO, Dict, List, Optional, Tuple
import yaml

# get_env_real_url would rely on env_utils
# from dcicutils.env_utils import get_env_real_url
from dcicutils.command_utils import yes_or_no
from dcicutils.common import APP_CGAP, APP_FOURFRONT, APP_SMAHT, OrchestratedApp
from dcicutils.exceptions import InvalidParameterError
from dcicutils.file_utils import search_for_file
from dcicutils.lang_utils import conjoined_list, disjoined_list, there_are
from dcicutils.misc_utils import (
    environ_bool, is_uuid,
    PRINT, url_path_join, ignorable, remove_prefix
)
from dcicutils.s3_utils import HealthPageKey
from dcicutils.schema_utils import EncodedSchemaConstants, JsonSchemaConstants, Schema
from dcicutils.structured_data import Portal, StructuredDataSet
from typing_extensions import Literal
from urllib.parse import urlparse
from .base import DEFAULT_APP
from .exceptions import PortalPermissionError
from .utils import show, keyword_as_title, check_repeatedly
from dcicutils.function_cache_decorator import function_cache


class SubmissionProtocol:
    S3 = 's3'
    UPLOAD = 'upload'


SUBMISSION_PROTOCOLS = [SubmissionProtocol.S3, SubmissionProtocol.UPLOAD]
DEFAULT_SUBMISSION_PROTOCOL = SubmissionProtocol.UPLOAD
STANDARD_HTTP_HEADERS = {"Content-type": "application/json"}
INGESTION_SUBMISSION_TYPE_NAME = "IngestionSubmission"
FILE_TYPE_NAME = "File"


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


def _get_user_record(server, auth):
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
            show("Server did not recognize you with the given credentials.")
    except Exception:
        pass
    if user_record_response.status_code in (401, 403):
        raise PortalPermissionError(server=server)
    user_record_response.raise_for_status()
    user_record = user_record_response.json()
    show(f"Portal server recognizes you as{' (admin)' if _is_admin_user(user_record) else ''}:"
         f" {user_record['title']} ({user_record['contact_email']})")
    return user_record


def _is_admin_user(user: dict, noadmin: bool = False) -> bool:
    return False if noadmin else ("admin" in user.get("groups", []))


def _get_defaulted_institution(institution, user_record):
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
        show("Using institution:", institution)
    return institution


def _get_defaulted_project(project, user_record):
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
            show("Project is: ", project)
    return project


def _get_defaulted_award(award, user_record, error_if_none=False):
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
            show("No award was inferred.")
        else:
            show("Award is (inferred):", award)
    else:
        show("Award is:", award)
    return award


def _get_defaulted_lab(lab, user_record, error_if_none=False):
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
            show("No lab was inferred.")
        else:
            show("Lab is (inferred):", lab)
    else:
        show("Lab is:", lab)
    return lab


def _get_defaulted_consortia(consortia, user_record, error_if_none=False):
    """
    Returns the given consortia or else if none is specified, it tries to infer any consortia.

    :param consortia: a list of @id's of consortia, or None
    :param user_record: the user record for the authorized user
    :param error_if_none: boolean true if failure to infer any consortia should raise an error, and false otherwise.
    :return: the @id of a consortium to use (or a comma-separated list)
    """
    consortia = consortia
    if not consortia:
        consortia = [consortium.get('@id', None)
                     for consortium in user_record.get('consortia', [])]
        if not consortia:
            if error_if_none:
                raise SyntaxError("Your user profile has no consortium declared,"
                                  " so you must specify --consortium explicitly.")
            show("No consortium was inferred.")
        else:
            show("Consortium is (inferred):", ','.join(consortia))
    else:
        show("Consortium is:", ','.join(consortia))
    return consortia


def _get_defaulted_submission_centers(submission_centers, user_record, error_if_none=False):
    """
    Returns the given submission center or else if none is specified, it tries to infer a submission center.

    :param submission_centers: the @id of a submission center, or None
    :param user_record: the user record for the authorized user
    :param error_if_none: boolean true if failure to infer a submission center should raise an error,
        and false otherwise.
    :return: the @id of a submission center to use
    """
    if not submission_centers:
        submission_centers = [submission_center.get('@id', None)
                              for submission_center in user_record.get('submission_centers', {})]
        if not submission_centers:
            if error_if_none:
                raise SyntaxError("Your user profile has no submission center declared,"
                                  " so you must specify --submission-center explicitly.")
            show("No submission center was inferred.")
        else:
            show("Submission center is (inferred):", ','.join(submission_centers))
    else:
        show("Submission center is:", ','.join(submission_centers))
    return submission_centers


APP_ARG_DEFAULTERS = {
    'institution': _get_defaulted_institution,
    'project': _get_defaulted_project,
    'lab': _get_defaulted_lab,
    'award': _get_defaulted_award,
    'consortia': _get_defaulted_consortia,
    'submission_centers': _get_defaulted_submission_centers,
}


def _do_app_arg_defaulting(app_args, user_record):
    for arg in list(app_args.keys()):
        val = app_args[arg]
        defaulter = APP_ARG_DEFAULTERS.get(arg)
        if defaulter:
            val = defaulter(val, user_record)
            if val:
                app_args[arg] = val
            elif val is None:
                del app_args[arg]


PROGRESS_CHECK_INTERVAL = 7  # seconds
ATTEMPTS_BEFORE_TIMEOUT = 100


def _get_section(res, section):
    """
    Given a description of an ingestion submission, returns a section name within that ingestion.

    :param res: the description of an ingestion submission as a python dictionary that represents JSON data
    :param section: the name of a section to find either in the toplevel or in additional_data.
    :return: the section's content
    """

    return res.get(section) or res.get('additional_data', {}).get(section)


def _show_section(res, section, caveat_outcome=None, portal=None):
    """
    Shows a given named section from a description of an ingestion submission.

    The caveat is used when there has been an error and should be a phrase that describes the fact that output
    shown is only up to the point of the caveat situation. Instead of a "My Heading" header the output will be
    "My Heading (prior to <caveat>)."

    :param res: the description of an ingestion submission as a python dictionary that represents JSON data
    :param section: the name of a section to find either in the toplevel or in additional_data.
    :param caveat_outcome: a phrase describing some caveat on the output
    """

    section_data = _get_section(res, section)
    if caveat_outcome and not section_data:
        # In the case of non-success, be brief unless there's data to show.
        return
    if caveat_outcome:
        caveat = " (prior to %s)" % caveat_outcome
    else:
        caveat = ""
    if not section_data:
        return
#   if section == "validation_output" and (ingestion_submission_uuid := res.get("uuid")):
#       PRINT(f"\nIngestion Submission UUID: {ingestion_submission_uuid}")
    show("\n----- %s%s -----" % (keyword_as_title(section), caveat))
    if isinstance(section_data, dict):
        if file := section_data.get("file"):
            PRINT(f"File: {file}")
        if s3_file := section_data.get("s3_file"):
            PRINT(f"S3 File: {s3_file}")
        if details := section_data.get("details"):
            PRINT(f"Details: {details}")
        for item in section_data:
            if isinstance(section_data[item], list) and section_data[item]:
                if item == "reader":
                    PRINT(f"Parser Warnings:")
                elif item == "validation":
                    PRINT(f"Validation Errors:")
                elif item == "ref":
                    PRINT(f"Reference (linkTo) Errors:")
                elif item == "errors":
                    PRINT(f"Other Errors:")
                else:
                    continue
                for issue in section_data[item]:
                    if isinstance(issue, dict):
                        PRINT(f"  - {_format_issue(issue, file)}")
                    elif isinstance(issue, str):
                        PRINT(f"  - {issue}")
    elif isinstance(section_data, list):
        if section == "upload_info":
            for info in section_data:
                if isinstance(info, dict) and info.get("filename") and (uuid := info.get("uuid")):
                    if portal and (fileobject := portal.get(f"/{uuid}")) and (fileobject := fileobject.json()):
                        if (display_title := fileobject.get("display_title")):
                            info["target"] = display_title
                        if (data_type := fileobject.get("data_type")):
                            if isinstance(data_type, list) and len(data_type) > 0:
                                data_type = data_type[0]
                            elif isinstance(data_type, str):
                                data_type = data_type
                            else:
                                data_type = None
                            if data_type:
                                info["type"] = Schema.type_name(data_type)
            print(yaml.dump(section_data))
        else:
            [show(line) for line in section_data]
    else:  # We don't expect this, but such should be shown as-is, mostly to see what it is.
        show(section_data)


def _ingestion_submission_item_url(server, uuid):
    return url_path_join(server, "ingestion-submissions", uuid) + "?format=json"


DEBUG_PROTOCOL = environ_bool("DEBUG_PROTOCOL", default=False)

TRY_OLD_PROTOCOL = True


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
        return {"datafile": io.open(ingestion_filename, 'rb')}
    else:
        return {"datafile": None}


def _post_submission(server, keypair, ingestion_filename, creation_post_data, submission_post_data,
                     submission_protocol=DEFAULT_SUBMISSION_PROTOCOL):
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
    portal = Portal(keypair, server=server)

    if submission_protocol == SubmissionProtocol.UPLOAD and TRY_OLD_PROTOCOL:

        old_style_submission_url = url_path_join(server, "submit_for_ingestion")
        old_style_post_data = dict(creation_post_data, **submission_post_data)

        response = portal.post(old_style_submission_url,
                               data=old_style_post_data,
                               files=_post_files_data(submission_protocol=submission_protocol,
                                                      ingestion_filename=ingestion_filename), headers=None)

        if response.status_code != 404:

            if DEBUG_PROTOCOL:  # pragma: no cover
                PRINT("Old style protocol worked.")

            return response

        else:  # on 404, try new protocol ...

            if DEBUG_PROTOCOL:  # pragma: no cover
                PRINT("Retrying with new protocol.")

    creation_post_url = url_path_join(server, INGESTION_SUBMISSION_TYPE_NAME)
    if DEBUG_PROTOCOL:  # pragma: no cover
        PRINT(f"Creating {INGESTION_SUBMISSION_TYPE_NAME} (bundle) type object ...")
    if submission_protocol == SubmissionProtocol.S3:
        # New with Fourfront ontology ingestion work (March 2023).
        # Store the submission data in the parameters of the IngestionSubmission object
        # here (it will get there later anyway via patch in ingester process), so that we can
        # get at this info via show-upload-info, before the ingester picks this up; specifically,
        # this is the FileOther object info, its uuid and associated data file, which was uploaded
        # in this case (SubmissionProtocol.S3) directly to S3 from submit-ontology.
        creation_post_data["parameters"] = submission_post_data
    creation_response = portal.post(creation_post_url, json=creation_post_data, raise_for_status=True)
    [submission] = creation_response.json()['@graph']
    submission_id = submission['@id']
    if DEBUG_PROTOCOL:  # pragma: no cover
        show(f"Created {INGESTION_SUBMISSION_TYPE_NAME} (bundle) type object: {submission.get('uuid', 'not-found')}")
    new_style_submission_url = url_path_join(server, submission_id, "submit_for_ingestion")
    response = portal.post(new_style_submission_url,
                           data=submission_post_data,
                           files=_post_files_data(submission_protocol=submission_protocol,
                                                  ingestion_filename=ingestion_filename), headers=None)
    return response


DEFAULT_INGESTION_TYPE = 'metadata_bundle'

GENERIC_SCHEMA_TYPE = 'FileOther'


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
                         app: OrchestratedApp = None,
                         upload_folder=None,
                         no_query=False,
                         subfolders=False,
                         submission_protocol=DEFAULT_SUBMISSION_PROTOCOL,
                         show_details=False,
                         post_only=False,
                         patch_only=False,
                         validate_only=False,
                         validate_first=False,
                         validate_local=False,
                         validate_local_only=False,
                         keys_file=None,
                         noadmin=False,
                         verbose=False,
                         debug=False):
    """
    Does the core action of submitting a metadata bundle.

    :param ingestion_filename: the name of the main data file to be ingested
    :param ingestion_type: the type of ingestion to be performed (an ingestion_type in the IngestionSubmission schema)
    :param server: the server to upload to
    :param env: the portal environment to upload to
    :param validate_only: whether to do stop after validation instead of proceeding to post metadata
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

    portal = _define_portal(env=env, server=server, app=app, keys_file=keys_file, report=True)

    app_args = _resolve_app_args(institution=institution, project=project, lab=lab, award=award, app=portal.app,
                                 consortium=consortium, submission_center=submission_center)

    if portal.get("/health").status_code != 200:  # TODO: with newer version dcicutils do: if not portal.ping():
        show(f"Portal credentials do not seem to work: {portal.keys_file} ({env})")
        exit(1)

    exit_immediately_on_errors = False
    user_record = _get_user_record(portal.server, auth=portal.key_pair)
    if not _is_admin_user(user_record, noadmin=noadmin) and not (validate_only or validate_first or
                                                                 validate_local or validate_local_only):
        # If user is not an admin, and no other validate related options are
        # specified, then default to server-side and client-side validation,
        # i.e. act as-if the --validate option was specified.
        exit_immediately_on_errors = True
        validate_local = True
        validate_first = True

    if debug:
        PRINT(f"DEBUG: validate_only = {validate_only}")
        PRINT(f"DEBUG: validate_first = {validate_first}")
        PRINT(f"DEBUG: validate_local = {validate_local}")
        PRINT(f"DEBUG: validate_local_only = {validate_local_only}")

    metadata_bundles_bucket = get_metadata_bundles_bucket_from_health_path(key=portal.key)
    _do_app_arg_defaulting(app_args, user_record)
    PRINT(f"Submission file to ingest: {ingestion_filename}")

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

    if validate_local or validate_local_only:
        _validate_locally(ingestion_filename, portal, validate_local_only=validate_local_only, autoadd=autoadd,
                          upload_folder=upload_folder, subfolders=subfolders,
                          exit_immediately_on_errors=exit_immediately_on_errors, verbose=verbose)

    validation_qualifier = " (for validation only)" if validate_only else ""

    maybe_ingestion_type = ''
    if ingestion_type != DEFAULT_INGESTION_TYPE:
        maybe_ingestion_type = " (%s)" % ingestion_type

    if not no_query:
        if not yes_or_no("Submit %s%s to %s%s?"
                         % (ingestion_filename, maybe_ingestion_type, portal.server, validation_qualifier)):
            show("Aborting submission.")
            exit(1)

    if not os.path.exists(ingestion_filename):
        raise ValueError("The file '%s' does not exist." % ingestion_filename)

    creation_post_data = {
        'ingestion_type': ingestion_type,
        "processing_status": {
            "state": "submitted"
        },
        **app_args,  # institution & project or lab & award
    }

    if submission_protocol == SubmissionProtocol.S3:

        upload_result = upload_file_to_new_uuid(filename=ingestion_filename, schema_name=GENERIC_SCHEMA_TYPE,
                                                auth=portal.key, **app_args)

        submission_post_data = compute_s3_submission_post_data(ingestion_filename=ingestion_filename,
                                                               ingestion_post_result=upload_result,
                                                               # The rest of this is other_args to pass through...
                                                               validate_only=validate_only, **app_args)

    elif submission_protocol == SubmissionProtocol.UPLOAD:

        submission_post_data = {
            'validate_only': validate_only,
            'validate_first': validate_first,
            'post_only': post_only,
            'patch_only': patch_only,
            'sheet_utils': False,
            'autoadd': json.dumps(autoadd),
            'ingestion_directory': os.path.dirname(ingestion_filename)
        }

    else:

        raise InvalidParameterError(parameter='submission_protocol', value=submission_protocol,
                                    options=SUBMISSION_PROTOCOLS)

    response = _post_submission(server=portal.server, keypair=portal.key_pair,
                                ingestion_filename=ingestion_filename,
                                creation_post_data=creation_post_data,
                                submission_post_data=submission_post_data,
                                submission_protocol=submission_protocol)

    try:
        # This can fail if the body doesn't contain JSON
        res = response.json()
    except Exception:  # pragma: no cover
        # This clause is not ordinarily entered. It handles a pathological case that we only hypothesize.
        # It does not require careful unit test coverage. -kmp 23-Feb-2022
        res = None

    try:
        response.raise_for_status()
    except Exception:
        if res is not None:
            # For example, if you call this on an old version of cgap-portal that does not support this request,
            # the error will be a 415 error, because the tween code defaultly insists on application/json:
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

    if res is None:  # pragma: no cover
        # This clause is not ordinarily entered. It handles a pathological case that we only hypothesize.
        # It does not require careful unit test coverage. -kmp 23-Feb-2022
        raise Exception("Bad JSON body in %s submission result." % response.status_code)

    uuid = res['submission_id']

    if DEBUG_PROTOCOL:  # pragma: no cover
        show(f"Created {INGESTION_SUBMISSION_TYPE_NAME} object: s3://{metadata_bundles_bucket}/{uuid}", with_time=True)
    show(f"Metadata bundle uploaded to bucket ({metadata_bundles_bucket}); tracking UUID: {uuid}", with_time=True)
    show(f"Awaiting processing ...", with_time=True)

    check_done, check_status, check_response = _check_submit_ingestion(
            uuid, portal.server, portal.env, portal.app, show_details, report=False)

    if validate_only:
        exit(0)

    if check_status == "success":
        do_any_uploads(check_response, keydict=portal.key, ingestion_filename=ingestion_filename,
                       upload_folder=upload_folder, no_query=no_query,
                       subfolders=subfolders)

    exit(0)


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


def _check_submit_ingestion(uuid: str, server: str, env: str,
                            app: Optional[OrchestratedApp] = None,
                            show_details: bool = False, report: bool = True) -> Tuple[bool, str, dict]:

    if app is None:  # Better to pass explicitly, but some legacy situations might require this to default
        app = DEFAULT_APP

    portal = _define_portal(env=env, server=server, app=app, report=report)

    if not _pytesting():
        if not (uuid_metadata := portal.get_metadata(uuid)):
            raise Exception(f"Cannot find object given uuid: {uuid}")
        if not portal.is_schema_type(uuid_metadata, INGESTION_SUBMISSION_TYPE_NAME):
            undesired_type = portal.get_schema_type(uuid_metadata)
            raise Exception(f"Given UUID is not an {INGESTION_SUBMISSION_TYPE_NAME} type: {uuid} ({undesired_type})")

    show(f"Checking ingestion process for {INGESTION_SUBMISSION_TYPE_NAME} uuid %s ..." % uuid, with_time=True)

    def check_ingestion_progress():
        return _check_ingestion_progress(uuid, keypair=portal.key_pair, server=portal.server)

    # Check the ingestion processing repeatedly, up to ATTEMPTS_BEFORE_TIMEOUT times,
    # and waiting PROGRESS_CHECK_INTERVAL seconds between each check.
    [check_done, check_status, check_response] = (
        check_repeatedly(check_ingestion_progress,
                         wait_seconds=PROGRESS_CHECK_INTERVAL,
                         repeat_count=ATTEMPTS_BEFORE_TIMEOUT)
    )

    if not check_done:
        command_summary = _summarize_submission(uuid=uuid, server=server, env=env, app=portal.app)
        show(f"Exiting after check processing timeout using {command_summary!r}.")
        exit(1)

    show("Final status: %s" % check_status.title(), with_time=True)

    if check_status == "error" and check_response.get("errors"):
        _show_section(check_response, "errors")

    caveat_check_status = None if check_status == "success" else check_status
    _show_section(check_response, "validation_output", caveat_outcome=caveat_check_status)
    _show_section(check_response, "post_output", caveat_outcome=caveat_check_status)
    _show_section(check_response, "result")

    if check_status == "success":
        _show_section(check_response, "upload_info", portal=portal)

    if show_details:
        metadata_bundles_bucket = get_metadata_bundles_bucket_from_health_path(key=portal.key)
        _show_detailed_results(uuid, metadata_bundles_bucket)

    return check_done, check_status, check_response


def _summarize_submission(uuid: str, app: str, server: Optional[str] = None, env: Optional[str] = None):
    if env:
        command_summary = f"check-submit --app {app} --env {env} {uuid}"
    elif server:
        command_summary = f"check-submit --app {app} --server {server} {uuid}"
    else:  # unsatisfying, but not worth raising an error
        command_summary = f"check-submit --app {app} {uuid}"
    return command_summary


def compute_s3_submission_post_data(ingestion_filename, ingestion_post_result, **other_args):
    uuid = ingestion_post_result['uuid']
    at_id = ingestion_post_result['@id']
    accession = ingestion_post_result.get('accession')  # maybe not always there?
    upload_credentials = ingestion_post_result['upload_credentials']
    upload_urlstring = upload_credentials['upload_url']
    upload_url = urlparse(upload_urlstring)
    upload_key = upload_credentials['key']
    upload_bucket = upload_url.netloc
    # Possible sanity check, probably not needed...
    # check_true(upload_key == remove_prefix('/', upload_url.path, required=True),
    #            message=f"The upload_key, {upload_key!r}, did not match path of {upload_url}.")
    submission_post_data = {
        'datafile_uuid': uuid,
        'datafile_accession': accession,
        'datafile_@id': at_id,
        'datafile_url': upload_urlstring,
        'datafile_bucket': upload_bucket,
        'datafile_key': upload_key,
        'datafile_source_filename': os.path.basename(ingestion_filename),
        **other_args  # validate_only, and any of institution, project, lab, or award that caller gave us
    }
    return submission_post_data


def _show_upload_info(uuid, server=None, env=None, keydict=None, app: str = None,
                      show_primary_result=True,
                      show_validation_output=True,
                      show_processing_status=True,
                      show_datafile_url=True,
                      show_details=True):
    """
    Uploads the files associated with a given ingestion submission. This is useful if you answered "no" to the query
    about uploading your data and then later are ready to do that upload.

    :param uuid: a string guid that identifies the ingestion submission
    :param server: the server to upload to
    :param env: the portal environment to upload to
    :param keydict: keydict-style auth, a dictionary of 'key', 'secret', and 'server'
    :param app: the name of the app to use
        e.g., affects whether to expect --lab, --award, --institution, --project, --consortium or --submission_center
        and whether to use .fourfront-keys.json, .cgap-keys.json, or .smaht-keys.json
    :param show_primary_result: bool controls whether the primary result is shown
    :param show_validation_output: bool controls whether to show output resulting from validation checks
    :param show_processing_status: bool controls whether to show the current processing status
    :param show_datafile_url: bool controls whether to show the datafile_url parameter from the parameters.
    :param show_details: bool controls whether to show the details from the results file in S3.
    """

    if app is None:  # Better to pass explicitly, but some legacy situations might require this to default
        app = DEFAULT_APP

    portal = _define_portal(key=keydict, env=env, server=server, app=app, report=True)

    if not (uuid_metadata := portal.get_metadata(uuid)):
        raise Exception(f"Cannot find object given uuid: {uuid}")

    if not portal.is_schema_type(uuid_metadata, INGESTION_SUBMISSION_TYPE_NAME):
        undesired_type = portal.get_schema_type(uuid_metadata)
        raise Exception(f"Given UUID is not an {INGESTION_SUBMISSION_TYPE_NAME} type: {uuid} ({undesired_type})")

    url = _ingestion_submission_item_url(portal.server, uuid)
    response = portal.get(url)
    response.raise_for_status()
    res = response.json()
    _show_upload_result(res,
                        show_primary_result=show_primary_result,
                        show_validation_output=show_validation_output,
                        show_processing_status=show_processing_status,
                        show_datafile_url=show_datafile_url,
                        show_details=show_details,
                        portal=portal)
    if show_details:
        metadata_bundles_bucket = get_metadata_bundles_bucket_from_health_path(key=portal.key)
        _show_detailed_results(uuid, metadata_bundles_bucket)


def _show_upload_result(result,
                        show_primary_result=True,
                        show_validation_output=True,
                        show_processing_status=True,
                        show_datafile_url=True,
                        show_details=True,
                        portal=None):

    if show_primary_result:
        if _get_section(result, 'upload_info'):
            _show_section(result, 'upload_info', portal=portal)
        else:
            show("Uploads: None")

    # New March 2023 ...

    if show_validation_output and _get_section(result, 'validation_output'):
        _show_section(result, 'validation_output')

    if show_processing_status and result.get('processing_status'):
        show("\n----- Processing Status -----")
        state = result['processing_status'].get('state')
        if state:
            show(f"State: {state.title()}")
        outcome = result['processing_status'].get('outcome')
        if outcome:
            show(f"Outcome: {outcome.title()}")
        progress = result['processing_status'].get('progress')
        if progress:
            show(f"Progress: {progress.title()}")

    if show_datafile_url and result.get('parameters'):
        datafile_url = result['parameters'].get('datafile_url')
        if datafile_url:
            show("----- DataFile URL -----")
            show(datafile_url)


def do_any_uploads(res, keydict, upload_folder=None, ingestion_filename=None, no_query=False, subfolders=False):

    def display_file_info(file: str) -> None:
        nonlocal upload_folder, subfolders
        if file:
            if file_paths := search_for_file(file, location=upload_folder, recursive=subfolders):
                if len(file_paths) == 1:
                    PRINT(f"File to upload: {file_paths[0]} ({_format_file_size(_get_file_size(file_paths[0]))})")
                    return True
                else:
                    PRINT(f"No upload attempted for file {file} because multiple"
                          f" copies were found in folder {upload_folder}: {', '.join(file_paths)}.")
                    return False
            PRINT(f"Cannot find file to upload: {file}")
        return False

    upload_info = _get_section(res, 'upload_info')
    if not upload_folder:
        if ingestion_directory := res.get("parameters", {}).get("ingestion_directory"):
            if os.path.isdir(ingestion_directory):
                upload_folder = ingestion_directory
    if not upload_folder and ingestion_filename:
        if ingestion_directory := os.path.dirname(ingestion_filename):
            upload_folder = ingestion_directory
    if upload_info:
        files_to_upload = []
        for upload_file_info in upload_info:
            if display_file_info(upload_file_info.get("filename")):
                files_to_upload.append(upload_file_info)
        if len(files_to_upload) == 0:
            return
        if no_query:
            do_uploads(files_to_upload, auth=keydict, no_query=no_query, folder=upload_folder,
                       subfolders=subfolders)
        else:
            message = ("Upload this file?" if len(files_to_upload) == 1
                       else f"Upload these {len(files_to_upload)} files?")
            if yes_or_no(message):
                do_uploads(files_to_upload, auth=keydict,
                           no_query=no_query, folder=upload_folder,
                           subfolders=subfolders)
            else:
                show("No uploads attempted.")


def resume_uploads(uuid, server=None, env=None, bundle_filename=None, keydict=None,
                   upload_folder=None, no_query=False, subfolders=False, app=None, keys_file=None):
    """
    Uploads the files associated with a given ingestion submission. This is useful if you answered "no" to the query
    about uploading your data and then later are ready to do that upload.

    :param uuid: a string guid that identifies the ingestion submission
    :param server: the server to upload to
    :param env: the portal environment to upload to
    :param bundle_filename: the bundle file to be uploaded
    :param keydict: keydict-style auth, a dictionary of 'key', 'secret', and 'server'
    :param upload_folder: folder in which to find files to upload (default: same as ingestion_filename)
    :param no_query: bool to suppress requests for user input
    :param subfolders: bool to search subdirectories within upload_folder for files
    """

    portal = _define_portal(key=keydict, keys_file=keys_file, env=env, server=server, app=app, report=True)

    if not (response := portal.get_metadata(uuid)):
        if accession_id := _extract_accession_id(uuid):
            if not (response := portal.get_metadata(uuid := accession_id)):
                raise Exception(f"Given accession ID not found: {uuid}")
        else:
            raise Exception(f"Given UUID not found: {uuid}")

    if not portal.is_schema_type(response, INGESTION_SUBMISSION_TYPE_NAME):

        # Subsume function of upload-item-data into resume-uploads for convenience.
        if portal.is_schema_type(response, FILE_TYPE_NAME):
            _upload_item_data(item_filename=uuid, uuid=None, server=portal.server,
                              env=portal.env, directory=upload_folder, no_query=no_query, app=app, report=False)
            return

        undesired_type = portal.get_schema_type(response)
        raise Exception(f"Given UUID is not an {INGESTION_SUBMISSION_TYPE_NAME} type: {uuid} ({undesired_type})")

    do_any_uploads(response,
                   keydict=portal.key,
                   ingestion_filename=bundle_filename,
                   upload_folder=upload_folder,
                   no_query=no_query,
                   subfolders=subfolders)


@function_cache(serialize_key=True)
def _get_health_page(key: dict) -> dict:
    return Portal(key).get_health().json()


def get_metadata_bundles_bucket_from_health_path(key: dict) -> str:
    return _get_health_page(key=key).get("metadata_bundles_bucket")


def get_s3_encrypt_key_id_from_health_page(auth):
    try:
        return _get_health_page(key=auth).get(HealthPageKey.S3_ENCRYPT_KEY_ID)
    except Exception:  # pragma: no cover
        # We don't actually unit test this section because _get_health_page realistically always returns
        # a dictionary, and so health.get(...) always succeeds, possibly returning None, which should
        # already be tested. Returning None here amounts to the same and needs no extra unit testing.
        # The presence of this error clause is largely pro forma and probably not really needed.
        return None


def get_s3_encrypt_key_id(*, upload_credentials, auth):
    if 's3_encrypt_key_id' in upload_credentials:
        s3_encrypt_key_id = upload_credentials.get('s3_encrypt_key_id')
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f"Extracted s3_encrypt_key_id from upload_credentials: {s3_encrypt_key_id}")
    else:
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f"No s3_encrypt_key_id entry found in upload_credentials.")
            PRINT(f"Fetching s3_encrypt_key_id from health page.")
        s3_encrypt_key_id = get_s3_encrypt_key_id_from_health_page(auth)
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f" =id=> {s3_encrypt_key_id!r}")
    return s3_encrypt_key_id


def execute_prearranged_upload(path, upload_credentials, auth=None):
    """
    This performs a file upload using special credentials received from ff_utils.patch_metadata.

    :param path: the name of a local file to upload
    :param upload_credentials: a dictionary of credentials to be used for the upload,
        containing the keys 'AccessKeyId', 'SecretAccessKey', 'SessionToken', and 'upload_url'.
    :param auth: auth info in the form of a dictionary containing 'key', 'secret', and 'server',
        and possibly other useful information such as an encryption key id.
    """

    if DEBUG_PROTOCOL:  # pragma: no cover
        PRINT(f"Upload credentials contain {conjoined_list(list(upload_credentials.keys()))}.")
    try:
        s3_encrypt_key_id = get_s3_encrypt_key_id(upload_credentials=upload_credentials, auth=auth)
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
        show("Uploading local file %s directly (via AWS CLI) to: %s" % (source, target))
        command = ['aws', 's3', 'cp']
        if s3_encrypt_key_id:
            command = command + ['--sse', 'aws:kms', '--sse-kms-key-id', s3_encrypt_key_id]
        command = command + ['--only-show-errors', source, target]
        options = {}
        if _running_on_windows_native():
            options = {"shell": True}
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f"DEBUG CLI: {' '.join(command)} | ENV INCLUDES: {conjoined_list(list(extra_env.keys()))}")
        subprocess.check_call(command, env=env, **options)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Upload failed with exit code %d" % e.returncode)
    else:
        end = time.time()
        duration = end - start
        show("Upload duration: %.2f seconds" % duration)


def _running_on_windows_native():
    return os.name == 'nt'


def compute_file_post_data(filename, context_attributes):
    file_basename = os.path.basename(filename)
    _, ext = os.path.splitext(file_basename)  # could probably get a nicer error message if file in bad format
    file_format = remove_prefix('.', ext, required=True)
    return {
        'filename': file_basename,
        'file_format': file_format,
        **{attr: val for attr, val in context_attributes.items() if val}
    }


def upload_file_to_new_uuid(filename, schema_name, auth, **context_attributes):
    """
    Upload file to a target environment.

    :param filename: the name of a file to upload.
    :param schema_name: the schema_name to use when creating a new file item whose content is to be uploaded.
    :param auth: auth info in the form of a dictionary containing 'key', 'secret', and 'server'.
    :returns: item metadata dict or None
    """

    post_item = compute_file_post_data(filename=filename, context_attributes=context_attributes)

    if DEBUG_PROTOCOL:  # pragma: no cover
        show("Creating FileOther type object ...")
    response = Portal(auth).post_metadata(object_type=schema_name, data=post_item)
    if DEBUG_PROTOCOL:  # pragma: no cover
        type_object_message = f" {response.get('@graph', [{'uuid': 'not-found'}])[0].get('uuid', 'not-found')}"
        show(f"Created FileOther type object: {type_object_message}")

    metadata, upload_credentials = extract_metadata_and_upload_credentials(response,
                                                                           method='POST', schema_name=schema_name,
                                                                           filename=filename, payload_data=post_item)

    execute_prearranged_upload(filename, upload_credentials=upload_credentials, auth=auth)

    return metadata


def upload_file_to_uuid(filename, uuid, auth):
    """
    Upload file to a target environment.

    :param filename: the name of a file to upload.
    :param uuid: the item into which the filename is to be uploaded.
    :param auth: auth info in the form of a dictionary containing 'key', 'secret', and 'server'.
    :returns: item metadata dict or None
    """
    metadata = None
    ignorable(metadata)  # PyCharm might need this if it worries it isn't set below

    # filename here should not include path
    patch_data = {'filename': os.path.basename(filename)}

    response = Portal(auth).patch_metadata(object_id=uuid, data=patch_data)

    metadata, upload_credentials = extract_metadata_and_upload_credentials(response,
                                                                           method='PATCH', uuid=uuid,
                                                                           filename=filename, payload_data=patch_data)

    execute_prearranged_upload(filename, upload_credentials=upload_credentials, auth=auth)

    return metadata


def extract_metadata_and_upload_credentials(response, filename, method, payload_data, uuid=None, schema_name=None):
    try:
        [metadata] = response['@graph']
        upload_credentials = metadata['upload_credentials']
    except Exception as e:
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f"Problem trying to {method} to get upload credentials.")
            PRINT(f" payload_data={payload_data}")
            if uuid:
                PRINT(f" uuid={uuid}")
            if schema_name:
                PRINT(f" schema_name={schema_name}")
            PRINT(f" response={response}")
            PRINT(f"Got error {type(e)}: {e}")
        raise RuntimeError(f"Unable to obtain upload credentials for file {filename}.")
    return metadata, upload_credentials


# This can be set to True in unusual situations, but normally will be False to avoid unnecessary querying.
SUBMITR_SELECTIVE_UPLOADS = environ_bool("SUBMITR_SELECTIVE_UPLOADS")


def do_uploads(upload_spec_list, auth, folder=None, no_query=False, subfolders=False):
    """
    Uploads the files mentioned in the give upload_spec_list.

    If any files have associated extra files, upload those as well.

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
        file_name = upload_spec["filename"]
        if not (file_paths := search_for_file(file_name, location=folder, recursive=subfolders)) or len(file_paths) > 1:
            if len(file_paths) > 1:
                show(f"No upload attempted for file {file_name} because multiple copies"
                     f" were found in folder {folder}: {', '.join(file_paths)}.")
            else:
                show(f"Upload file not found: {file_name}")
            continue
        file_path = file_paths[0]
        uuid = upload_spec['uuid']
        uploader_wrapper = UploadMessageWrapper(uuid, no_query=no_query)
        wrapped_upload_file_to_uuid = uploader_wrapper.wrap_upload_function(
            upload_file_to_uuid, file_path
        )
        file_metadata = wrapped_upload_file_to_uuid(
            filename=file_path, uuid=uuid, auth=auth
        )
        if file_metadata:
            extra_files_credentials = file_metadata.get("extra_files_creds", [])
            if extra_files_credentials:
                _upload_extra_files(
                    extra_files_credentials,
                    uploader_wrapper,
                    folder,
                    auth,
                    recursive=subfolders,
                )


class UploadMessageWrapper:
    """Class to provide consistent queries/messages to user when
    uploading file(s) to given File UUID.
    """

    def __init__(self, uuid, no_query=False):
        """Initialize instance for given UUID

        :param uuid: UUID of File item for uploads
        :param no_query: Whether to suppress asking for user
            confirmation prior to upload
        """
        self.uuid = uuid
        self.no_query = no_query

    def wrap_upload_function(self, function, file_name):
        """Wrap upload given function with messages conerning upload.

        :param function: Upload function to wrap
        :param file_name: File to upload
        :returns: Wrapped function
        """
        def wrapper(*args, **kwargs):
            result = None
            perform_upload = True
            if not self.no_query:
                if (
                    SUBMITR_SELECTIVE_UPLOADS
                    and not yes_or_no(f"Upload {file_name}?")
                ):
                    show("OK, not uploading it.")
                    perform_upload = False
            if perform_upload:
                try:
                    show("Uploading %s to item %s ..." % (file_name, self.uuid))
                    result = function(*args, **kwargs)
                    show(
                        "Upload of %s to item %s was successful."
                        % (file_name, self.uuid)
                    )
                except Exception as e:
                    show("%s: %s" % (e.__class__.__name__, e))
            return result
        return wrapper


def _upload_extra_files(
    credentials, uploader_wrapper, folder, auth, recursive=False
):
    """Attempt upload of all extra files.

    Similar to "do_uploads", search for each file and then call a
    wrapped upload function. Here, since extra files do not correspond
    to Items on the portal, no need to PATCH an Item to retrieve AWS
    credentials; they are directly passed in from the parent File's
    metadata.

    :param credentials: AWS credentials dictionary
    :param uploader_wrapper: UploadMessageWrapper instance
    :param folder: Directory to search for files
    :param auth: a portal authorization tuple
    :param recursive: Whether to search subdirectories for file
    """
    for extra_file_item in credentials:
        extra_file_name = extra_file_item.get("filename")
        extra_file_credentials = extra_file_item.get("upload_credentials")
        if not extra_file_name or not extra_file_credentials:
            continue
        if (not (extra_file_paths := search_for_file(extra_file_name, location=folder,
                                                     recursive=recursive)) or len(extra_file_paths) > 1):
            if len(extra_file_paths) > 1:
                show(f"No upload attempted for file {extra_file_name} because multiple"
                     f" copies were found in folder {folder}: {', '.join(extra_file_paths)}.")
            else:
                show(f"Upload file not found: {extra_file_name}")
            continue
        extra_file_path = extra_file_paths[0]
        wrapped_execute_prearranged_upload = uploader_wrapper.wrap_upload_function(
            execute_prearranged_upload, extra_file_path
        )
        wrapped_execute_prearranged_upload(extra_file_path, extra_file_credentials, auth=auth)


def _upload_item_data(item_filename, uuid, server, env, no_query=False, app=None, report=True, **kwargs):
    """
    Given a part_filename, uploads that filename to the Item specified by uuid on the given server.

    Only one of server or env may be specified.

    :param item_filename: the name of a file to be uploaded
    :param uuid: the UUID of the Item with which the uploaded data is to be associated
    :param server: the server to upload to (where the Item is defined)
    :param env: the portal environment to upload to (where the Item is defined)
    :param no_query: bool to suppress requests for user input
    :return:
    """

    directory = kwargs.get("directory")

    # Allow the given "file name" to be uuid for submitted File object, or associated accession
    # ID (e.g. SMAFIP2PIEDG), or the (S3) accession ID based file name (e.g. SMAFIP2PIEDG.fastq).
    if not uuid:
        if is_uuid(item_filename) or _is_accession_id(item_filename):
            uuid = item_filename
            item_filename = None
        elif accession_id := _extract_accession_id(item_filename):
            uuid = accession_id
            item_filename = None

    portal = _define_portal(env=env, server=server, app=app, report=report)

    if not (uuid_metadata := portal.get_metadata(uuid)):
        raise Exception(f"Cannot find object given uuid: {uuid}")

    if not portal.is_schema_type(uuid_metadata, FILE_TYPE_NAME):
        undesired_type = portal.get_schema_type(uuid_metadata)
        raise Exception(f"Given uuid is not a file type: {uuid} ({undesired_type})")

    if not item_filename:
        if not (item_filename := uuid_metadata.get("filename")):
            raise Exception(f"Cannot determine file name: {uuid}")

    if not os.path.isfile(item_filename):
        if directory and not os.path.isfile(item_filename := os.path.join(directory, item_filename)):
            raise Exception(f"File not found: {item_filename}")

    if not no_query:
        file_size = _format_file_size(_get_file_size(item_filename))
        if not yes_or_no("Upload %s (%s) to %s?" % (item_filename, file_size, server)):
            show("Aborting submission.")
            exit(1)

    upload_file_to_uuid(filename=item_filename, uuid=uuid, auth=portal.key)


def _show_detailed_results(uuid: str, metadata_bundles_bucket: str) -> None:

    print(f"----- Detailed Info -----")

    submission_results_location, submission_results = _fetch_submission_results(metadata_bundles_bucket, uuid)
    exception_results_location, exception_results = _fetch_exception_results(metadata_bundles_bucket, uuid)

    if not submission_results and not exception_results:
        print(f"Neither submission nor exception results found!")
        print(f"-> {submission_results_location}")
        print(f"-> {exception_results_location}")
        return

    if submission_results:
        print(f"From: {submission_results_location}")
        print(yaml.dump(submission_results))

    if exception_results:
        print("Exception during schema ingestion processing:")
        print(f"From: {exception_results_location}")
        print(exception_results)


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
                      validate_local_only: bool = False, upload_folder: Optional[str] = None,
                      subfolders: bool = False, exit_immediately_on_errors: bool = False, verbose: bool = False) -> int:
    errors_exist = False
    if validate_local_only:
        PRINT(f"\n> Validating {'ONLY ' if validate_local_only else ''}file locally because" +
              f" --validate-local{'-only' if validate_local_only else ''} specified: {ingestion_filename}")
    structured_data = StructuredDataSet.load(ingestion_filename, portal, autoadd=autoadd)
    if verbose:
        PRINT(f"\n> Parsed JSON:")
        _print_json_with_prefix(structured_data.data, "  ")
    errors_exist = not _validate_data(structured_data, portal, ingestion_filename)
    PRINT(f"\n> Types submitting:")
    for type_name in sorted(structured_data.data):
        PRINT(f"  - {type_name}: {len(structured_data.data[type_name])}"
              f" object{'s' if len(structured_data.data[type_name]) != 1 else ''}")
    if (resolved_refs := structured_data.resolved_refs):
        PRINT(f"\n> Resolved object (linkTo) references:")
        for resolved_ref in sorted(resolved_refs):
            PRINT(f"  - {resolved_ref}")
    if (ref_errors := structured_data.ref_errors):
        errors_exist = True
        PRINT(f"\n> ERROR: Unresolved object (linkTo) references:")
        for ref_error in ref_errors:
            PRINT(f"  - {_format_issue(ref_error, ingestion_filename)}")
    if (reader_warnings := structured_data.reader_warnings):
        PRINT(f"\n> WARNING: Parser warnings:")
        for reader_warning in reader_warnings:
            PRINT(f"  - {_format_issue(reader_warning, ingestion_filename)}")
    if files := structured_data.upload_files:
        files = structured_data.upload_files_located(location=[upload_folder,
                                                               os.path.dirname(ingestion_filename)],
                                                     recursive=subfolders)
        files_found = [file for file in files if file.get("path")]
        files_not_found = [file for file in files if not file.get("path")]
        if files_found:
            PRINT(f"\n> Resolved file references:")
            for file in files_found:
                if path := file.get("path"):
                    PRINT(f"  - {file.get('type')}: {file.get('file')} -> {path}"
                          f" [{_format_file_size(_get_file_size(path))}]")
                else:
                    PRINT(f"  - {file.get('type')}: {file.get('file')} -> NOT FOUND!")
        if files_not_found:
            errors_exist = True
            PRINT(f"\n> ERROR: Unresolved file references:")
            for file in files_not_found:
                if path := file.get("path"):
                    PRINT(f"  - {file.get('type')}: {file.get('file')} -> {path}")
                else:
                    PRINT(f"  - {file.get('type')}: {file.get('file')} -> Not found!")
    _print_structured_data_status(portal, structured_data)
    PRINT()
    if exit_immediately_on_errors and errors_exist:
        PRINT("There are some errors outlined above. Please fix them before trying again. No action taken.")
        exit(1)
    if errors_exist:
        if not yes_or_no("There are some errors outlined above; do you want to continue?"):
            exit(1)
    if validate_local_only:
        exit(0 if not errors_exist else 1)


def _validate_data(structured_data: StructuredDataSet, portal: Portal, ingestion_filename: str) -> bool:
    PRINT(f"\n> Validation results:")
    pre_validation_errors = _pre_validate_data(structured_data, portal)
    if pre_validation_errors:
        for pre_validation_error in pre_validation_errors:
            print(f"  - {pre_validation_error}")
        return False
    validation_errors_exist = False
    structured_data.validate()
    if (validation_errors := structured_data.validation_errors):
        validation_errors_exist = True
        PRINT(f"\n> ERROR: Validation violations:")
        for validation_error in validation_errors:
            PRINT(f"  - {_format_issue(validation_error, ingestion_filename)}")
    else:
        PRINT(f"  - OK")
    return not validation_errors_exist


def _pre_validate_data(structured_data: StructuredDataSet, portal: Portal) -> List[str]:
    # TODO: Move this more specific "pre" validation checking to dcicutils.structured_data.
    # Just for nicer more specific (non-jsonschema) error messages for common problems.
    pre_validation_errors = []
    if not (portal and structured_data and structured_data.data):
        return pre_validation_errors
    for schema_name in structured_data.data:
        if schema_data := portal.get_schema(schema_name):
            if identifying_properties := schema_data.get(EncodedSchemaConstants.IDENTIFYING_PROPERTIES):
                identifying_properties = set(identifying_properties)
                if data := structured_data.data[schema_name]:
                    data_properties = set(data[0].keys())
                    if not data_properties & identifying_properties:
                        # No identifying properties for this object.
                        pre_validation_errors.append(f"ERROR: No identifying properties for type: {schema_name}")
            if required_properties := schema_data.get(JsonSchemaConstants.REQUIRED):
                required_properties = set(required_properties) - set("submission_centers")
                if data := structured_data.data[schema_name]:
                    data_properties = set(data[0].keys())
                    if (data_properties & required_properties) != required_properties:
                        if missing_required_properties := required_properties - data_properties:
                            # Missing required properties for this object.
                            for missing_required_property in missing_required_properties:
                                pre_validation_errors.append(
                                    f"ERROR: Missing required property ({missing_required_property})"
                                    f" for type: {schema_name}")
    return pre_validation_errors


def _print_structured_data_status(portal: Portal, structured_data: StructuredDataSet) -> None:
    PRINT("\n> Object create/update situation:")
    diffs = structured_data.compare()
    for object_type in diffs:
        print(f"  TYPE: {object_type}")
        for object_info in diffs[object_type]:
            print(f"  - OBJECT: {object_info.path}")
            if not object_info.uuid:
                print(f"    Does not exist -> Will be CREATED")
            else:
                print(f"    Already exists -> {object_info.uuid} -> Will be UPDATED", end="")
                if not object_info.diffs:
                    print(" (but NO substantive diffs)")
                else:
                    print(" (substantive DIFFs below)")
                    for diff_path in object_info.diffs:
                        if (diff := object_info.diffs[diff_path]).creating_value:
                            print(f"     CREATE {diff_path}: {diff.value}")
                        elif diff.updating_value:
                            print(f"     UPDATE {diff_path}: {diff.updating_value} -> {diff.value}")
                        elif (diff := object_info.diffs[diff_path]).deleting_value:
                            print(f"     DELETE {diff_path}: {diff.value}")


def _print_json_with_prefix(data, prefix):
    json_string = json.dumps(data, indent=4)
    json_string = f"\n{prefix}".join(json_string.split("\n"))
    PRINT(prefix, end="")
    PRINT(json_string)


def _format_issue(issue: dict, original_file: Optional[str] = None) -> str:
    def src_string(issue: dict) -> str:
        if not isinstance(issue, dict) or not isinstance(issue_src := issue.get("src"), dict):
            return ""
        show_file = original_file and (original_file.endswith(".zip") or
                                       original_file.endswith(".tgz") or original_file.endswith(".gz"))
        src_file = issue_src.get("file") if show_file else ""
        src_type = issue_src.get("type")
        src_column = issue_src.get("column")
        src_row = issue_src.get("row", 0)
        if src_file:
            src = f"{os.path.basename(src_file)}"
            sep = ":"
        else:
            src = ""
            sep = "."
        if src_type:
            src += (sep if src else "") + src_type
            sep = "."
        if src_column:
            src += (sep if src else "") + src_column
        if src_row > 0:
            src += (" " if src else "") + f"[{src_row}]"
        if not src:
            if issue.get("warning"):
                src = "Warning"
            elif issue.get("error"):
                src = "Error"
            else:
                src = "Issue"
        return src
    issue_message = None
    if issue:
        if error := issue.get("error"):
            issue_message = error
        elif warning := issue.get("warning"):
            issue_message = warning
        elif issue.get("truncated"):
            return f"Truncated result set | More: {issue.get('more')} | See: {issue.get('details')}"
    return f"{src_string(issue)}: {issue_message}" if issue_message else ""


def _define_portal(key: Optional[dict] = None, env: Optional[str] = None, server: Optional[str] = None,
                   app: Optional[str] = None, keys_file: Optional[str] = None, report: bool = False) -> Portal:
    if not app:
        app = DEFAULT_APP
        app_default = True
    else:
        app_default = False
    if not (portal := Portal(key or keys_file, env=env, server=server, app=app, raise_exception=False)).key:
        raise Exception(
            f"No portal key defined; setup your ~/.{app or 'smaht'}-keys.json file and use the --env argument.")
    if report:
        PRINT(f"Portal app name is{' (default)' if app_default else ''}: {app}")
        PRINT(f"Portal environment (in keys file) is: {portal.env}")
        PRINT(f"Portal keys file is: {portal.keys_file}")
        PRINT(f"Portal server is: {portal.server}")
        if portal.key_id and len(portal.key_id) > 2:
            PRINT(f"Portal key prefix is: {portal.key_id[:2]}******")
    return portal


def _is_accession_id(value: str) -> bool:
    return isinstance(value, str) and re.match(r"^[A-Z0-9]{12}$", value) is not None


def _extract_accession_id(value: str) -> Optional[str]:
    if isinstance(value, str):
        if value.endswith(".gz"):
            value = value[:-3]
        value, _ = os.path.splitext(value)
        if _is_accession_id(value):
            return value


def _get_file_size(file: str) -> int:
    return os.path.getsize(file)


def _format_file_size(nbytes: int) -> str:
    for unit in ["b", "Kb", "Mb", "Gb", "Tb", "Pb", "Eb", "Zb"]:
        if abs(nbytes) < 1024.0:
            return f"{nbytes:3.1f}{unit}"
        nbytes /= 1024.0
    return f"{nbytes:.1f}Yb"


def _pytesting():
    return "pytest" in sys.modules
