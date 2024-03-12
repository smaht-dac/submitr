import boto3
from botocore.exceptions import NoCredentialsError as BotoNoCredentialsError
import copy
from datetime import datetime
from functools import lru_cache
import io
import json
import os
import pytz
import re
import signal
import subprocess
import sys
import time
from tqdm import tqdm
from typing import BinaryIO, Dict, List, Optional, Tuple
import yaml

# get_env_real_url would rely on env_utils
# from dcicutils.env_utils import get_env_real_url
from dcicutils.command_utils import yes_or_no
from dcicutils.common import APP_CGAP, APP_FOURFRONT, APP_SMAHT, OrchestratedApp
from dcicutils.exceptions import InvalidParameterError
from dcicutils.file_utils import search_for_file
from dcicutils.function_cache_decorator import function_cache
from dcicutils.lang_utils import conjoined_list, disjoined_list, there_are
from dcicutils.misc_utils import (
    environ_bool, is_uuid, url_path_join, ignorable, remove_prefix, str_to_bool as asbool
)
from dcicutils.s3_utils import HealthPageKey
from dcicutils.schema_utils import EncodedSchemaConstants, JsonSchemaConstants, Schema
from dcicutils.structured_data import Portal, StructuredDataSet
from typing_extensions import Literal
from urllib.parse import urlparse
from .base import DEFAULT_APP
from .exceptions import PortalPermissionError
from .scripts.cli_utils import print_boxed
from .utils import keyword_as_title, check_repeatedly
from .output import ERASE_LINE, PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW, setup_for_output_file_option


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
        SHOW(f"Portal server recognizes you as{' (admin)' if _is_admin_user(user_record) else ''}:"
             f" {user_record['title']} ({user_record['contact_email']})")
    return user_record


def _is_admin_user(user: dict) -> bool:
    return False if os.environ.get("SMAHT_NOADMIN") else ("admin" in user.get("groups", []))


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
    if portal and not _pytesting():
        for consortium in consortia:
            consortium_path = f"/Consortium/{consortium}" if not consortium.startswith("/") else consortium
            if not (consortium_object := portal.get_metadata(consortium_path)):
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
    # TODO: Need to support submits_for ...
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
    if portal and not _pytesting():
        for submission_center in submission_centers:
            submission_center_path = (
                f"/SubmissionCenter/{submission_center}"
                if not submission_center.startswith("/") else submission_center)
            if not (submission_center_object := portal.get_metadata(submission_center_path)):
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
    SHOW("\n----- %s%s -----" % (keyword_as_title(section), caveat))
    if isinstance(section_data, dict):
        if file := section_data.get("file"):
            PRINT(f"File: {file}")
        if s3_file := section_data.get("s3_file"):
            PRINT(f"S3 File: {s3_file}")
        if details := section_data.get("details"):
            PRINT(f"Details: {details}")
        for item in section_data:
            if isinstance(section_data[item], list) and section_data[item]:
                issue_prefix = ""
                if item == "reader":
                    PRINT(f"Parser Warnings:")
                    issue_prefix = "WARNING: "
                elif item == "validation":
                    PRINT(f"Validation Errors:")
                    issue_prefix = "ERROR: "
                elif item == "ref":
                    PRINT(f"Reference (linkTo) Errors:")
                    issue_prefix = "ERROR: "
                elif item == "errors":
                    PRINT(f"Other Errors:")
                    issue_prefix = "ERROR: "
                else:
                    continue
                for issue in section_data[item]:
                    if isinstance(issue, dict):
                        PRINT(f"- {issue_prefix}{_format_issue(issue, file)}")
                    elif isinstance(issue, str):
                        PRINT(f"- {issue_prefix}{issue}")
    elif isinstance(section_data, list):
        if section == "upload_info":
            for info in section_data:
                if isinstance(info, dict) and info.get("filename") and (uuid := info.get("uuid")):
                    upload_file_accession_name, upload_file_type = _get_upload_file_info(portal, uuid)
                    info["target"] = upload_file_accession_name
                    info["type"] = upload_file_type
            PRINT(yaml.dump(section_data))
        else:
            [SHOW(line) for line in section_data]
    else:  # We don't expect this, but such should be shown as-is, mostly to see what it is.
        SHOW(section_data)


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
        SHOW(f"Created {INGESTION_SUBMISSION_TYPE_NAME} (bundle) type object: {submission.get('uuid', 'not-found')}")
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
                         validate_local=False,
                         validate_local_only=False,
                         validate_remote=False,
                         validate_remote_only=False,
                         validate_remote_silent=False,
                         post_only=False,
                         patch_only=False,
                         keys_file=None,
                         show_details=False,
                         json_only=False,
                         ref_nocache=False,
                         verbose_json=False,
                         verbose=False,
                         noprogress=False,
                         output_file=None,
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

    # Setup for output to specified output file, in addition to stdout),
    # except in this case we will not output large amounts of output to stdout.
    if output_file:
        global PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW
        PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW = setup_for_output_file_option(output_file)

    portal = _define_portal(env=env, server=server, app=app, keys_file=keys_file,
                            report=not json_only or verbose, verbose=verbose)

    app_args = _resolve_app_args(institution=institution, project=project, lab=lab, award=award, app=portal.app,
                                 consortium=consortium, submission_center=submission_center)

    if portal.get("/health").status_code != 200:  # TODO: with newer version dcicutils do: if not portal.ping():
        SHOW(f"Portal credentials do not seem to work: {portal.keys_file} ({env})")
        exit(1)

    exit_immediately_on_errors = False
    user_record = _get_user_record(portal.server, auth=portal.key_pair, quiet=json_only and not verbose)
    is_admin_user = _is_admin_user(user_record)
    if not is_admin_user and not (validate_remote_only or validate_remote or validate_local or validate_local_only):
        # If user is not an admin, and no other validate related options are
        # specified, then default to server-side and client-side validation,
        # i.e. act as-if the --validate option was specified.
        validate_local = True
        validate_remote = True
        validate_remote_silent = True
        exit_immediately_on_errors = True
    if not is_admin_user or validate_local_only or (validate_remote_only and not is_admin_user):
        exit_immediately_on_errors = True

    if debug:
        PRINT(f"DEBUG: validate_local = {validate_local}")
        PRINT(f"DEBUG: validate_local_only = {validate_local_only}")
        PRINT(f"DEBUG: validate_remote = {validate_remote}")
        PRINT(f"DEBUG: validate_remote_only = {validate_remote_only}")
        PRINT(f"DEBUG: validate_remote_silent = {validate_remote_silent}")

    validation_only = validate_local_only or validate_remote_only
    validation = validation_only or validate_remote_silent

    metadata_bundles_bucket = get_metadata_bundles_bucket_from_health_path(key=portal.key)
    if not _do_app_arg_defaulting(app_args, user_record, portal, quiet=json_only and not verbose, verbose=verbose):
        pass
    if not json_only:
        PRINT(f"Submission file to {'validate' if validation_only else 'ingest'}: {ingestion_filename}")

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

    if validate_local or validate_local_only:
        _validate_locally(ingestion_filename, portal,
                          validate_local_only=validate_local_only,
                          validate_remote_only=validate_remote_only,
                          autoadd=autoadd, upload_folder=upload_folder, subfolders=subfolders,
                          exit_immediately_on_errors=exit_immediately_on_errors,
                          ref_nocache=ref_nocache, output_file=output_file, noprogress=noprogress,
                          json_only=json_only, verbose_json=verbose_json,
                          verbose=verbose, debug=debug, debug_sleep=debug_sleep)

    maybe_ingestion_type = ''
    if ingestion_type != DEFAULT_INGESTION_TYPE:
        maybe_ingestion_type = " (%s)" % ingestion_type

    if validate_remote_only:
        action_message = f"Continue with validation against {portal.server}?"
    else:
        action_message = f"Submit {ingestion_filename}{maybe_ingestion_type} to {portal.server}?"

    if not no_query:
        if not validate_remote_silent:
            if not yes_or_no(action_message):
                if validate_remote_only:
                    SHOW("Aborting validation.")
                else:
                    SHOW("Aborting submission.")
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
                                                               validate_remote_only=validate_remote_only, **app_args)

    elif submission_protocol == SubmissionProtocol.UPLOAD:

        submission_post_data = {
            'validate_only': None,  # see initiate_submission below
            'validate_first': validate_remote,
            'post_only': post_only,
            'patch_only': patch_only,
            'ref_nocache': ref_nocache,
            'autoadd': json.dumps(autoadd),
            'ingestion_directory': os.path.dirname(ingestion_filename)
        }

    else:

        raise InvalidParameterError(parameter='submission_protocol', value=submission_protocol,
                                    options=SUBMISSION_PROTOCOLS)

    def initiate_submission(first_time=True):
        nonlocal submission_post_data, validate_remote, validate_remote_only, validate_remote_silent
        submission_post_data = copy.deepcopy(submission_post_data)
        if first_time:
            submission_post_data["validate_only"] = (
                validate_remote_only or (validate_remote and validate_remote_silent))
        else:
            submission_post_data["validate_only"] = False
            submission_post_data["validate_first"] = False
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
                SHOW(message)
                if title == "Unsupported Media Type":
                    SHOW("NOTE: This error is known to occur if the server"
                         " does not support metadata bundle submission.")
            raise
        if res is None:  # pragma: no cover
            # This clause is not ordinarily entered. It handles a pathological case that we only hypothesize.
            # It does not require careful unit test coverage. -kmp 23-Feb-2022
            raise Exception("Bad JSON body in %s submission result." % response.status_code)
        return res['submission_id']

    submission_uuid = initiate_submission(first_time=True)

    """
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
            SHOW(message)
            if title == "Unsupported Media Type":
                SHOW("NOTE: This error is known to occur if the server"
                     " does not support metadata bundle submission.")
        raise

    if res is None:  # pragma: no cover
        # This clause is not ordinarily entered. It handles a pathological case that we only hypothesize.
        # It does not require careful unit test coverage. -kmp 23-Feb-2022
        raise Exception("Bad JSON body in %s submission result." % response.status_code)

    uuid = res['submission_id']
    """

    if validate_remote_silent:
        SHOW(f"Continuing with additional (server) validation: {portal.server}")
    if DEBUG_PROTOCOL:  # pragma: no cover
        SHOW(f"Created {INGESTION_SUBMISSION_TYPE_NAME} object: s3://{metadata_bundles_bucket}/{submission_uuid}",
             with_time=False)
    if verbose:
        SHOW(f"Metadata bundle upload bucket: {metadata_bundles_bucket}", with_time=False)
    if not validation:
        SHOW(f"Submission tracking ID: {submission_uuid}", with_time=False)
    else:
        SHOW(f"Validation tracking ID: {submission_uuid}", with_time=False)

    check_done, check_status, check_response = _check_submit_ingestion(
            submission_uuid, portal.server, portal.env, app=portal.app, keys_file=portal.keys_file,
            show_details=show_details, report=False, messages=True,
            validation=validation, validate_remote_silent=validate_remote_silent,
            verbose=verbose)

    if validate_remote_only:
        if check_status == "success":
            PRINT("Validation results (server): OK")
        elif validate_remote_silent:
            PRINT(f"Validation results (server): ERROR"
                  f"{f' ({check_status})' if check_status not in ['failure', 'error'] else ''}")
            if check_response and (additional_data := check_response.get("additional_data")):
                if (validation_info := additional_data.get("validation_output")) and isinstance(validation_info, list):
                    if errors := [info for info in validation_info if info.lower().startswith("error:")]:
                        for error in errors:
                            PRINT_OUTPUT("- " + error.replace("Error", "ERROR:"))
            if check_response and isinstance(other_errors := check_response.get("errors"), list):
                for error in other_errors:
                    PRINT_OUTPUT("- " + error)
        exit(0)

    if check_status == "success":
        if validation:
            SHOW("Validation results (server): OK")
            SHOW(f"Ready to continue with submission to {portal.server}: {ingestion_filename}")
            if yes_or_no("Continue with submission?"):
                submission_uuid = initiate_submission(first_time=False)
                SHOW(f"Submission tracking ID: {submission_uuid}")
                check_done, check_status, check_response = _check_submit_ingestion(
                        submission_uuid, portal.server, portal.env, app=portal.app, keys_file=portal.keys_file,
                        show_details=show_details, report=False, messages=True,
                        validation=False, validate_remote_silent=False,
                        verbose=verbose)
            else:
                exit(0)
        do_any_uploads(check_response, keydict=portal.key, ingestion_filename=ingestion_filename,
                       upload_folder=upload_folder, no_query=no_query,
                       subfolders=subfolders)
    else:
        if validate_remote_silent:
            PRINT(f"Validation results (server): ERROR"
                  f"{f' ({check_status})' if check_status not in ['failure', 'error'] else ''}")
            if check_response and (additional_data := check_response.get("additional_data")):
                if (validation_info := additional_data.get("validation_output")) and isinstance(validation_info, list):
                    if errors := [info for info in validation_info if info.lower().startswith("error:")]:
                        for error in errors:
                            PRINT_OUTPUT("- " + error.replace("Error", "ERROR:"))
            if check_response and isinstance(other_errors := check_response.get("errors"), list):
                for error in other_errors:
                    PRINT_OUTPUT("- " + error)
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


def _get_recent_submissions(portal: Portal, count: int = 30) -> List[dict]:
    if submissions := portal.get_metadata(f"/search/?type=IngestionSubmission&sort=-date_created&from=0&limit={count}"):
        if submissions := submissions.get("@graph"):
            return submissions
    return []


def _print_recent_submissions(portal: Portal, count: int = 30, message: Optional[str] = None,
                              details: bool = False, verbose: bool = False) -> bool:
    lines = []
    if submissions := _get_recent_submissions(portal, count):
        if message:
            PRINT(message)
        lines.append("===")
        lines.append("Recent Submissions [COUNT]")
        lines.append("===")
        for submission in submissions:
            if verbose:
                PRINT()
                _print_submission_summary(portal, submission)
                continue
            submission_uuid = submission.get("uuid")
            submission_created = submission.get("date_created")
            line = f"{submission_uuid}: {_format_portal_object_datetime(submission_created)}"
            if asbool(submission.get("parameters", {}).get("validate_only")):
                line += f" | V"
            else:
                line += f" | S"
            if details and (submission_file := submission.get("parameters", {}).get("datafile")):
                line += f" | {submission_file}"
            lines.append(line)
        if not verbose:
            lines.append("===")
            print_boxed(lines, right_justified_macro=("[COUNT]", lambda: f"Showing: {len(submissions)}"))
        return True
    return False


def _check_submit_ingestion(uuid: str, server: str, env: str, keys_file: Optional[str] = None,
                            app: Optional[OrchestratedApp] = None,
                            show_details: bool = False,
                            validation: bool = False, validate_remote_silent: bool = False,
                            verbose: bool = False,
                            report: bool = True, messages: bool = False) -> Tuple[bool, str, dict]:

    if app is None:  # Better to pass explicitly, but some legacy situations might require this to default
        app = DEFAULT_APP

    portal = _define_portal(env=env, server=server, app=app, report=report)

    if not _pytesting():
        if not (uuid_metadata := portal.get_metadata(uuid)):
            message = f"Submission ID not found: {uuid}" if uuid != "dummy" else "No submission ID specified."
            if _print_recent_submissions(portal, message=message):
                return
            raise Exception(f"Cannot find object given uuid: {uuid}")
        if not portal.is_schema_type(uuid_metadata, INGESTION_SUBMISSION_TYPE_NAME):
            undesired_type = portal.get_schema_type(uuid_metadata)
            raise Exception(f"Given ID is not an {INGESTION_SUBMISSION_TYPE_NAME} type: {uuid} ({undesired_type})")

    action = "validation" if validation else "ingestion"
    if validation:
        SHOW(f"Waiting for validation results ...")
    else:
        SHOW(f"Checking {action} for submission ID: %s ..." % uuid, with_time=False)

    def check_ingestion_progress():
        return _check_ingestion_progress(uuid, keypair=portal.key_pair, server=portal.server)

    # Check the ingestion processing repeatedly, up to ATTEMPTS_BEFORE_TIMEOUT times,
    # and waiting PROGRESS_CHECK_INTERVAL seconds between each check.
    [check_done, check_status, check_response] = (
        check_repeatedly(check_ingestion_progress,
                         wait_seconds=PROGRESS_CHECK_INTERVAL,
                         repeat_count=ATTEMPTS_BEFORE_TIMEOUT,
                         messages=messages, action=action, verbose=verbose)
    )

    if not check_done:
        command_summary = _summarize_submission(uuid=uuid, server=server, env=env, app=portal.app)
        SHOW(f"Exiting after check processing timeout using {command_summary!r}.")
        exit(1)

    """
    SHOW("Final status: %s" % check_status.title(), with_time=True)

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
    """

    if not validate_remote_silent and not _pytesting():
        _print_submission_summary(portal, check_response)

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
        **other_args  # validate_remote_only, and any of institution, project, lab, or award that caller gave us
    }
    return submission_post_data


def _print_submission_summary(portal: Portal, result: dict) -> None:
    if not result:
        return
    lines = []
    errors = []
    validation_info = None
    submission_type = "Submission"
    if submission_parameters := result.get("parameters", {}):
        if submission_validation := asbool(submission_parameters.get("validate_only")):
            submission_type = "Validation"
        if submission_file := submission_parameters.get("datafile"):
            lines.append(f"Submission File: {submission_file}")
    if submission_uuid := result.get("uuid"):
        lines.append(f"{submission_type} ID: {submission_uuid}")
    if date_created := _format_portal_object_datetime(result.get("date_created"), True):
        lines.append(f"{submission_type} Time: {date_created}")
    if submission_validation:
        lines.append(f"Validation Only: Yes")
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
    if processing_status := result.get("processing_status"):
        summary_lines = []
        if state := processing_status.get("state"):
            summary_lines.append(f"State: {state.title()}")
        if progress := processing_status.get("progress"):
            summary_lines.append(f"Progress: {progress.title()}")
        if outcome := processing_status.get("outcome"):
            summary_lines.append(f"Outcome: {outcome.title()}")
        if validation_info:
            if status := [info for info in validation_info if info.lower().startswith("status")]:
                summary_lines.append(status[0])
            pass
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
                    summary_lines.append(f"S3: {s3_data_bucket}")
                summary_lines.append(f"S3 Data: {s3_data_file}")
        if s3_details_file := [info for info in validation_info if info.lower().startswith("details: ")]:
            s3_details_file = s3_details_file[0][9:]
            if (rindex := s3_details_file.rfind("/")) > 0:
                s3_details_bucket = s3_details_file[5:rindex] if s3_details_file.startswith("s3://") else ""
                s3_details_file = s3_details_file[rindex + 1:]
                if s3_details_bucket != s3_data_bucket:
                    summary_lines.append(f"S3 Bucket: {s3_details_bucket}")
                summary_lines.append(f"S3 Details: {s3_details_file}")
        if summary_lines:
            lines.append("===")
            lines += summary_lines
    if additional_data:
        if upload_files := additional_data.get("upload_info"):
            for upload_file in upload_files:
                upload_file_uuid = upload_file.get("uuid")
                upload_file_name = upload_file.get("filename")
                upload_file_accession_name, upload_file_type = _get_upload_file_info(portal, upload_file_uuid)
                lines.append("===")
                lines.append(f"Upload File: {upload_file_name}")
                lines.append(f"Upload File ID: {upload_file_uuid}")
                if upload_file_accession_name:
                    lines.append(f"Upload File Accession Name: {upload_file_accession_name}")
                if upload_file_type:
                    lines.append(f"Upload File Type: {upload_file_type}")
    if lines:
        lines = ["===", "SMaHT Submission Summary [UUID]", "==="] + lines + ["==="]
        if errors:
            lines += ["ERRORS ITEMIZED BELOW ...", "==="]
        print_boxed(lines, right_justified_macro=("[UUID]", lambda: submission_uuid))
        if errors:
            for error in errors:
                PRINT(error.replace("Error", "ERROR:"))


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
        raise Exception(f"Given ID is not an {INGESTION_SUBMISSION_TYPE_NAME} type: {uuid} ({undesired_type})")

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

    if not _pytesting():
        PRINT("")
        _print_submission_summary(portal, res)


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
            SHOW("Uploads: None")

    # New March 2023 ...

    if show_validation_output and _get_section(result, 'validation_output'):
        _show_section(result, 'validation_output')

    if show_processing_status and result.get('processing_status'):
        SHOW("\n----- Processing Status -----")
        state = result['processing_status'].get('state')
        if state:
            SHOW(f"State: {state.title()}")
        outcome = result['processing_status'].get('outcome')
        if outcome:
            SHOW(f"Outcome: {outcome.title()}")
        progress = result['processing_status'].get('progress')
        if progress:
            SHOW(f"Progress: {progress.title()}")

    if show_datafile_url and result.get('parameters'):
        datafile_url = result['parameters'].get('datafile_url')
        if datafile_url:
            SHOW("----- DataFile URL -----")
            SHOW(datafile_url)


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
                SHOW("No uploads attempted.")


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
            raise Exception(f"Given ID not found: {uuid}")

    if not portal.is_schema_type(response, INGESTION_SUBMISSION_TYPE_NAME):

        # Subsume function of upload-item-data into resume-uploads for convenience.
        if portal.is_schema_type(response, FILE_TYPE_NAME):
            _upload_item_data(item_filename=uuid, uuid=None, server=portal.server,
                              env=portal.env, directory=upload_folder, no_query=no_query, app=app, report=False)
            return

        undesired_type = portal.get_schema_type(response)
        raise Exception(f"Given ID is not an {INGESTION_SUBMISSION_TYPE_NAME} type: {uuid} ({undesired_type})")

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
        SHOW("Uploading %s to: %s" % (source, target))
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
        # SHOW("Upload duration: %.2f seconds" % duration)
        SHOW(f"Upload of {os.path.basename(source)}: OK -> {'%.1f' % duration} seconds")


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
        SHOW("Creating FileOther type object ...")
    response = Portal(auth).post_metadata(object_type=schema_name, data=post_item)
    if DEBUG_PROTOCOL:  # pragma: no cover
        type_object_message = f" {response.get('@graph', [{'uuid': 'not-found'}])[0].get('uuid', 'not-found')}"
        SHOW(f"Created FileOther type object: {type_object_message}")

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
                SHOW(f"No upload attempted for file {file_name} because multiple copies"
                     f" were found in folder {folder}: {', '.join(file_paths)}.")
            else:
                SHOW(f"Upload file not found: {file_name}")
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
                    SHOW("OK, not uploading it.")
                    perform_upload = False
            if perform_upload:
                try:
                    result = function(*args, **kwargs)
                except Exception as e:
                    SHOW("%s: %s" % (e.__class__.__name__, e))
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
                SHOW(f"No upload attempted for file {extra_file_name} because multiple"
                     f" copies were found in folder {folder}: {', '.join(extra_file_paths)}.")
            else:
                SHOW(f"Upload file not found: {extra_file_name}")
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
            SHOW("Aborting submission.")
            exit(1)

    upload_file_to_uuid(filename=item_filename, uuid=uuid, auth=portal.key)


def _show_detailed_results(uuid: str, metadata_bundles_bucket: str) -> None:

    PRINT(f"----- Detailed Info -----")

    submission_results_location, submission_results = _fetch_submission_results(metadata_bundles_bucket, uuid)
    exception_results_location, exception_results = _fetch_exception_results(metadata_bundles_bucket, uuid)

    if not submission_results and not exception_results:
        PRINT(f"Neither submission nor exception results found!")
        PRINT(f"-> {submission_results_location}")
        PRINT(f"-> {exception_results_location}")
        return

    if submission_results:
        PRINT(f"From: {submission_results_location}")
        PRINT(yaml.dump(submission_results))

    if exception_results:
        PRINT("Exception during schema ingestion processing:")
        PRINT(f"From: {exception_results_location}")
        PRINT(exception_results)


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
                      validate_local_only: bool = False, validate_remote_only: bool = False,
                      upload_folder: Optional[str] = None,
                      subfolders: bool = False, exit_immediately_on_errors: bool = False,
                      ref_nocache: bool = False, output_file: Optional[str] = None,
                      json_only: bool = False, noprogress: bool = False,
                      verbose_json: bool = False, verbose: bool = False, quiet: bool = False,
                      debug: bool = False, debug_sleep: Optional[str] = None) -> int:

    # N.B. This same bit of code is in smaht-portal; not sure best way to share;
    # It really should not go in dcicutils (structured_data) as this know pretty
    # specific details about our (SMaHT) schemas, namely, submitted_id and accession.
    def ref_lookup_strategy(type_name: str, schema: dict, value: str) -> (int, Optional[str]):
        #
        # FYI: Note this situation WRT object lookups ...
        #
        # /{submitted_id}                # NOT FOUND
        # /UnalignedReads/{submitted_id} # OK
        # /SubmittedFile/{submitted_id}  # OK
        # /File/{submitted_id}           # NOT FOUND
        #
        # /{accession}                   # OK
        # /UnalignedReads/{accession}    # NOT FOUND
        # /SubmittedFile/{accession}     # NOT FOUND
        # /File/{accession}              # OK
        #
        def ref_validator(schema: Optional[dict],
                          property_name: Optional[str], property_value: Optional[str]) -> Optional[bool]:
            """
            Returns False iff the type represented by the given schema, can NOT be referenced by
            the given property name with the given property value, otherwise returns None.

            For example, if the schema is for the UnalignedReads type and the property name
            is accession, then we will return False iff the given property value is NOT a properly
            formatted accession ID. Otherwise, we will return None, which indicates that the
            caller (in dcicutils.structured_data.Portal.ref_exists) will continue executing
            its default behavior, which is to check other ways in which the given type can NOT
            be referenced by the given value, i.e. it checks other identifying properties for
            the type and makes sure any patterns (e.g. for submitted_id or uuid) are ahered to.

            The goal (in structured_data) being to detect if a type is being referenced in such
            a way that cannot possibly be allowed, i.e. because none of its identifying types
            are in the required form (if indeed there any requirements). Note that it is guaranteed
            that the given property name is indeed an identifying property for the given type.
            """
            if property_format := schema.get("properties", {}).get(property_name, {}).get("format"):
                if (property_format == "accession") and (property_name == "accession"):
                    if not _is_accession_id(property_value):
                        return False
            return None

        if not schema and value:
            nonlocal portal
            if not (schema := portal.get_schema(type_name)):
                return Portal.LOOKUP_DEFAULT, ref_validator
        if value and (schema_properties := schema.get("properties")):
            if schema_properties.get("accession") and _is_accession_id(value):
                # Case: lookup by accession (only by root).
                return Portal.LOOKUP_ROOT, ref_validator
            elif schema_property_info_submitted_id := schema_properties.get("submitted_id"):
                if schema_property_pattern_submitted_id := schema_property_info_submitted_id.get("pattern"):
                    if re.match(schema_property_pattern_submitted_id, value):
                        # Case: lookup by submitted_id (only by specified type).
                        return Portal.LOOKUP_SPECIFIED_TYPE, ref_validator
        return Portal.LOOKUP_DEFAULT, ref_validator

    start = time.time()

    if True:

        def handle_control_c(signum, frame):
            PRINT('INTERRUPT')
            if not yes_or_no("CTRL-C: You have interrupted this process. Do you want to continue?"):
                exit(1)
            PRINT('CONTINUE')

        total_rows = 0
        processed_rows = 0
        last_progress_message = ""

        def progress(nrows: int,
                     nsheets: int,
                     nrefs_total: Optional[int] = None,
                     nrefs_resolved: Optional[int] = None,
                     nrefs_unresolved: Optional[int] = None,
                     nlookups: Optional[int] = None,
                     ncachehits: Optional[int] = None,
                     ref_invalid: Optional[int] = None) -> None:
            nonlocal total_rows, processed_rows, last_progress_message
            if nrows > 0:
                if total_rows == 0:
                    if nsheets > 0:
                        message = (
                            f"Parsing submission file which has{' only' if nsheets == 1 else ''}"
                            f" {nsheets} sheet{'s' if nsheets != 1 else ''} and a total of {nrows} rows.")
                    else:
                        message = f"Parsing submission file which has a total of {nrows} rows."
                    PRINT_STDOUT(message)
                total_rows += nrows
            elif nrows < 0:
                processed_rows += -nrows
            message = (
                f"Rows: {total_rows} | "
                f"Parsed: {processed_rows} | "
                f"Remaining: {total_rows - processed_rows}")
            if nrefs_total is not None:
                message += f" ‖ Refs: {nrefs_total}"
                # if nrefs_resolved is not None:
                #     message += f" | Resolved: {nrefs_resolved}"
                if nrefs_unresolved is not None:
                    message += f" | Unresolved: {nrefs_unresolved}"
                if nlookups is not None:
                    message += f" | Lookups: {nlookups}"
                if ref_invalid is not None:
                    message += f" | Invalid: {ref_invalid}"
                if ncachehits is not None and ncachehits > 0:
                    message += f" | Cache Hits: {ncachehits}"
            message += f" ‖ {'%.1f' % (time.time() - start)}s"
            message += f" | {(float(processed_rows) / float(max(total_rows, 1)) * 100):.1f}%"
            last_progress_message = f"{message}"
            PRINT_STDOUT(f"{ERASE_LINE}{last_progress_message}\r", end="")

        signal.signal(signal.SIGINT, handle_control_c)

        if verbose:
            PRINT("Starting preliminary validation.")

        structured_data = StructuredDataSet(None, portal, autoadd=autoadd,
                                            ref_lookup_strategy=ref_lookup_strategy,
                                            ref_lookup_nocache=ref_nocache,
                                            progress=progress if not noprogress else None,
                                            debug_sleep=debug_sleep)
        structured_data._load_file(ingestion_filename)
        if not noprogress:
            PRINT(last_progress_message)

        signal.signal(signal.SIGINT, signal.SIG_DFL)

    else:
        structured_data = StructuredDataSet.load(ingestion_filename, portal, autoadd=autoadd,
                                                 ref_lookup_strategy=ref_lookup_strategy,
                                                 ref_lookup_nocache=ref_nocache,
                                                 debug_sleep=debug_sleep)
    if debug:
        duration = time.time() - start
        PRINT_OUTPUT(f"Preliminary validation complete (results below): {'%.1f' % duration} seconds")
        PRINT_OUTPUT(f"Reference total count: {structured_data.ref_total_count}")
        PRINT_OUTPUT(f"Reference total found count: {structured_data.ref_total_found_count}")
        PRINT_OUTPUT(f"Reference total not found count: {structured_data.ref_total_notfound_count}")
        PRINT_OUTPUT(f"Reference exists cache hit count: {structured_data.ref_exists_cache_hit_count}")
        PRINT_OUTPUT(f"Reference exists cache miss count: {structured_data.ref_exists_cache_miss_count}")
        PRINT_OUTPUT(f"Reference exists internal count: {structured_data.ref_exists_internal_count}")
        PRINT_OUTPUT(f"Reference exists external count: {structured_data.ref_exists_external_count}")
        PRINT_OUTPUT(f"Reference lookup cache hit count: {structured_data.ref_lookup_cache_hit_count}")
        PRINT_OUTPUT(f"Reference lookup cache miss count: {structured_data.ref_lookup_cache_miss_count}")
        PRINT_OUTPUT(f"Reference lookup count: {structured_data.ref_lookup_count}")
        PRINT_OUTPUT(f"Reference lookup found count: {structured_data.ref_lookup_found_count}")
        PRINT_OUTPUT(f"Reference lookup not found count: {structured_data.ref_lookup_notfound_count}")
        PRINT_OUTPUT(f"Reference lookup error count: {structured_data.ref_lookup_error_count}")
        PRINT_OUTPUT(f"Reference invalid identifying property count:"
                     f" {structured_data.ref_invalid_identifying_property_count}")
    if json_only:
        PRINT_OUTPUT(json.dumps(structured_data.data, indent=4))
        exit(1)
    if verbose_json:
        PRINT_OUTPUT(f"Parsed JSON:")
        PRINT_OUTPUT(json.dumps(structured_data.data, indent=4))
    validation_okay = _validate_data(structured_data, portal, ingestion_filename, upload_folder, recursive=subfolders)
    if validation_okay:
        PRINT("Validation results (preliminary): OK")
    if verbose:
        _print_structured_data_verbose(portal, structured_data,
                                       ingestion_filename, upload_folder=upload_folder,
                                       recursive=subfolders, validate_remote_only=validate_remote_only)
    elif not quiet:
        _print_structured_data_status(portal, structured_data,
                                      validate_remote_only=validate_remote_only,
                                      report_updates_only=True, debug=debug)
    if exit_immediately_on_errors and not validation_okay:
        if output_file:
            PRINT(f"There are some preliminary ERRORs outlined in the output file: {output_file}")
        else:
            PRINT(f"\nThere are some preliminary ERRORs outlined above.")
        PRINT(f"Please fix them before trying again. No action taken.")
        exit(1)
    if not validation_okay:
        question_suffix = " with validation" if validate_local_only or validate_remote_only else ""
        if not yes_or_no(f"There are some preliminary errors outlined above;"
                         f" do you want to continue{question_suffix}?"):
            exit(1)
    if validate_local_only:
        exit(0 if validation_okay else 1)
    # if verbose:
    #     PRINT()


def _validate_data(structured_data: StructuredDataSet, portal: Portal, ingestion_filename: str,
                   upload_folder: str, recursive: bool) -> bool:
    nerrors = 0

    if initial_validation_errors := _validate_initial(structured_data, portal):
        nerrors += len(initial_validation_errors)

    if ref_validation_errors := _validate_references(structured_data, ingestion_filename):
        nerrors += len(ref_validation_errors)

    if file_validation_errors := _validate_files(structured_data, ingestion_filename, upload_folder, recursive):
        nerrors += len(file_validation_errors)

    structured_data.validate()
    if data_validation_errors := structured_data.validation_errors:
        nerrors += len(data_validation_errors)

    if nerrors > 0:
        PRINT_OUTPUT("Validation results (preliminary): ERROR")

    if initial_validation_errors:
        PRINT_OUTPUT(f"- Initial errors: {len(initial_validation_errors)}")
        for error in initial_validation_errors:
            PRINT_OUTPUT(f"- ERROR: {error}")

    if ref_validation_errors:
        PRINT_OUTPUT(f"- Reference errors: {len(ref_validation_errors)}")
        for error in ref_validation_errors:
            PRINT_OUTPUT(f"  - ERROR: {error}")

    if file_validation_errors:
        PRINT_OUTPUT("- File reference errors: {len(file_validation_errors)}")
        for error in file_validation_errors:
            PRINT_OUTPUT(f"  - ERROR: {error}")

    if data_validation_errors:
        PRINT_OUTPUT("- Data errors: {len(data_validation_errors)}")
        for error in data_validation_errors:
            PRINT_OUTPUT(f"  - ERROR: {error}")

    return not (nerrors > 0)


def _validate_references(structured_data: StructuredDataSet, ingestion_filename: str) -> List[str]:
    ref_validation_errors = []
    if (ref_errors := structured_data.ref_errors):
        for ref_error in ref_errors:
            ref_validation_errors.append(f"{_format_issue(ref_error, ingestion_filename)}")
    return ref_validation_errors


def _validate_files(structured_data: StructuredDataSet, ingestion_filename: str,
                    upload_folder: str, recursive: bool) -> List[str]:
    file_validation_errors = []
    if files := structured_data.upload_files_located(location=[upload_folder, os.path.dirname(ingestion_filename)],
                                                     recursive=recursive):
        if files_not_found := [file for file in files if not file.get("path")]:
            for file in files_not_found:
                file_validation_errors.append(f"{file.get('type')}: {file.get('file')} -> Not found")
    return file_validation_errors


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
                                   upload_folder: str, recursive: bool, validate_remote_only: bool = False) -> None:
    if (reader_warnings := structured_data.reader_warnings):
        PRINT_OUTPUT(f"\n> Parser WARNINGS:")
        for reader_warning in reader_warnings:
            PRINT_OUTPUT(f"  - {_format_issue(reader_warning, ingestion_filename)}")
    PRINT_OUTPUT(f"\n> Types submitting:")
    for type_name in sorted(structured_data.data):
        PRINT_OUTPUT(f"  - {type_name}: {len(structured_data.data[type_name])}"
                     f" object{'s' if len(structured_data.data[type_name]) != 1 else ''}")
    if resolved_refs := structured_data.resolved_refs:
        PRINT_OUTPUT(f"\n> Resolved object (linkTo) references:")
        for resolved_ref in sorted(resolved_refs):
            PRINT_OUTPUT(f"  - {resolved_ref}")
    if files := structured_data.upload_files_located(location=[upload_folder, os.path.dirname(ingestion_filename)],
                                                     recursive=recursive):
        PRINT_OUTPUT(f"\n> Resolved file references:")
        nfiles_output = 0
        if files_found := [file for file in files if file.get("path")]:
            for file in files_found:
                nfiles_output += 1
                path = file.get("path")
                PRINT_OUTPUT(f"  - {file.get('type')}: {file.get('file')} -> {path}"
                             f" [{_format_file_size(_get_file_size(path))}]")
        if nfiles_output > 0:
            PRINT_OUTPUT()
    _print_structured_data_status(portal, structured_data,
                                  validate_remote_only=validate_remote_only, report_updates_only=True)


def _print_structured_data_status(portal: Portal, structured_data: StructuredDataSet,
                                  validate_remote_only: bool = False,
                                  report_updates_only: bool = False, debug: bool = False) -> None:

    def define_progress_callback(debug: bool = False) -> None:
        bar = None
        ntypes = 0
        nobjects = 0
        ncreates = 0
        nupdates = 0
        nlookups = 0
        # started = time.time()
        def handle_control_c(signum, frame):  # noqa
            if yes_or_no("\nCTRL-C: You have interrupted this process. Do you want to TERMINATE processing?"):
                if bar:
                    bar.close()
                PRINT("Premature exit.")
                exit(1)
            PRINT_STDOUT("Continuing ...")
        def progress_report(status: dict) -> None:  # noqa
            nonlocal bar, ntypes, nobjects, ncreates, nupdates, nlookups, debug
            increment = 1
            if status.get("start"):
                signal.signal(signal.SIGINT, handle_control_c)
                ntypes = status.get("types")
                nobjects = status.get("objects")
                PRINT(f"Analyzing submission file which has {ntypes} type{'s' if ntypes != 1 else ''}"
                      f" and {nobjects} object{'s' if nobjects != 1 else ''}.")
                bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} | {rate_fmt} | {elapsed}{postfix} | ETA: {remaining} "
                bar = tqdm(total=nobjects, desc="Calculating", dynamic_ncols=True, bar_format=bar_format, unit="")
                return
            elif status.get("finish"):
                if bar:
                    bar.close()
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                return
            elif status.get("create"):
                ncreates += increment
                nlookups += status.get("lookups") or 0
                bar.update(increment)
            elif status.get("update"):
                nupdates += increment
                nlookups += status.get("lookups") or 0
                bar.update(increment)
            # duration = time.time() - started
            # nprocessed = ncreates + nupdates
            # rate = nprocessed / duration
            # nremaining = nobjects - nprocessed
            # duration_remaining = (nremaining / rate) if rate > 0 else 0
            message = (
                f"▶ Items: {nobjects} | Checked: {ncreates + nupdates}"
                f" ‖ Creates: {ncreates} | Updates: {nupdates} | Lookups: {nlookups}")
            # if debug:
            #    message += f" | Rate: {rate:.1f}%"
            message += " | Progress"
            bar.set_description(message)
        return progress_report

    diffs = structured_data.compare(progress=define_progress_callback())

    ncreates = 0
    nupdates = 0
    nsubstantive_updates = 0
    for object_type in diffs:
        for object_info in diffs[object_type]:
            if object_info.uuid:
                if object_info.diffs:
                    nsubstantive_updates += 1
                ncreates += 1
            else:
                nupdates += 1

    to_or_which_would = "to" if not validate_remote_only else "which would"

    if ncreates > 0:
        if nupdates > 0:
            message = f"Objects {to_or_which_would} be -> Created: {ncreates} | Updated: {nupdates}"
            if nsubstantive_updates == 0:
                message += " (but no substantive differences)"
        else:
            message = f"Objects {to_or_which_would} be created: {ncreates}"
    elif nupdates:
        message = f"Objects {to_or_which_would} be updated: {nupdates}"
        if nsubstantive_updates == 0:
            message += " (but no substantive differences)"
    else:
        message = "No objects to create or update."
        return

    if report_updates_only and nsubstantive_updates == 0:
        PRINT(f"{message}")
        return
    else:
        PRINT(f"{message} (details below) ...")

    will_or_would = "Will" if not validate_remote_only else "Would"

    PRINT()
    for object_type in sorted(diffs):
        PRINT(f"  TYPE: {object_type}")
        for object_info in diffs[object_type]:
            PRINT(f"  - OBJECT: {object_info.path}")
            if not object_info.uuid and not report_updates_only:
                PRINT(f"    Does not exist -> {will_or_would} be CREATED")
            else:
                message = f"    Already exists -> {object_info.uuid} -> {will_or_would} be UPDATED"
                if not object_info.diffs:
                    message += " (but NO substantive diffs)"
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
    PRINT()


def _print_json_with_prefix(data, prefix):
    json_string = json.dumps(data, indent=4)
    json_string = f"\n{prefix}".join(json_string.split("\n"))
    PRINT_OUTPUT(prefix, end="")
    PRINT_OUTPUT(json_string)


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
                   app: Optional[str] = None, keys_file: Optional[str] = None,
                   report: bool = False, verbose: bool = False) -> Portal:
    if not app:
        app = DEFAULT_APP
        app_default = True
    else:
        app_default = False
    if not (portal := Portal(key or keys_file, env=env, server=server, app=app, raise_exception=False)).key:
        raise Exception(
            f"No portal key defined; setup your ~/.{app or 'smaht'}-keys.json file and use the --env argument.")
    if report:
        if verbose:
            PRINT(f"Portal app name is{' (default)' if app_default else ''}: {app}")
        PRINT(f"Portal environment (in keys file) is: {portal.env}")
        PRINT(f"Portal keys file is: {portal.keys_file}")
        PRINT(f"Portal server is: {portal.server}")
        if portal.key_id and len(portal.key_id) > 2:
            PRINT(f"Portal key prefix is: {portal.key_id[:2]}******")
    return portal


@lru_cache(maxsize=1)
def _get_consortia(portal: Portal) -> List[str]:
    results = []
    if consortia := portal.get_metadata("/consortia"):
        consortia = sorted(consortia.get("@graph", []), key=lambda key: key.get("identifier"))
        for consortium in consortia:
            if ((consortium_name := consortium.get("identifier")) and
                (consortium_uuid := consortium.get("uuid"))):  # noqa
                results.append({"name": consortium_name, "uuid": consortium_uuid})
    return results


@lru_cache(maxsize=1)
def _get_submission_centers(portal: Portal) -> List[str]:
    results = []
    if submission_centers := portal.get_metadata("/submission-centers"):
        submission_centers = sorted(submission_centers.get("@graph", []), key=lambda key: key.get("identifier"))
        for submission_center in submission_centers:
            if ((submission_center_name := submission_center.get("identifier")) and
                (submission_center_uuid := submission_center.get("uuid"))):  # noqa
                results.append({"name": submission_center_name, "uuid": submission_center_uuid})
    return results


def _is_accession_id(value: str) -> bool:
    # See smaht-portal/.../schema_formats.py
    return isinstance(value, str) and re.match(r"^SMA[1-9A-Z]{9}$", value) is not None
    # return isinstance(value, str) and re.match(r"^[A-Z0-9]{12}$", value) is not None


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


def _format_portal_object_datetime(value: str, verbose: bool = False) -> Optional[str]:  # noqa
    try:
        dt = datetime.fromisoformat(value).replace(tzinfo=pytz.utc)
        tzlocal = datetime.now().astimezone().tzinfo
        if verbose:
            return dt.astimezone(tzlocal).strftime(f"%-I:%M %p %Z | %A, %B %-d, %Y")
        else:
            return dt.astimezone(tzlocal).strftime(f"%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return None


def _pytesting():
    return "pytest" in sys.modules
