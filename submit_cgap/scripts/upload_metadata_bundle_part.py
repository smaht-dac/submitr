import argparse
# import datetime
import io
import json
import os
# import re
# import requests
import subprocess
# import sys
import time

from dcicutils import ff_utils
from dcicutils.misc_utils import PRINT
from dcicutils.qa_utils import override_environ
from dcicutils.command_utils import yes_or_no
from .submit_metadata_bundle import resolve_site, show, get_cgap_auth_dict


EPILOG = __doc__


KEYPAIRS_FILENAME = '.cgap-keypairs.json'


def get_cgap_keypairs():
    with io.open(KEYPAIRS_FILENAME) as keyfile:
        keys = json.load(keyfile)
        return keys


def get_cgap_keypair(bs_env=None):
    """
    Gets the appropriate auth info for talking to a given beanstalk environment.

    Args:
        bs_env: the name of a beanstalk environment

    Returns:
        Auth information.
        The auth is probably a keypair, though we might change this to include a JWT token in the the future.
    """
    keypairs = get_cgap_keypairs()
    keypair = keypairs.get(bs_env or 'cgap-local')
    if not keypair:
        raise RuntimeError("Missing credential in keypairs file %s for %s." % (KEYPAIRS_FILENAME, bs_env))


def execute_prearranged_upload(path, *, upload_credentials):
    """
    This performs a file upload using special credentials received from ff_utils.patch_metadata.

    :param path: the name of a local file to upload
    :param upload_credentials: a dictionary of credentials to be used for the upload,
        containing the keys 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', and 'AWS_SECURITY_TOKEN'.
    """

    try:
        env = dict(os.environ,
                   AWS_ACCESS_KEY_ID=upload_credentials['AccessKeyId'],
                   AWS_SECRET_ACCESS_KEY=upload_credentials['SecretAccessKey'],
                   AWS_SECURITY_TOKEN=upload_credentials['SessionToken'])
    except Exception as e:
        raise("Upload specification is not in good form. %s: %s" % (e.__class__.__name__, e))

    PRINT("Uploading file.")
    start = time.time()
    try:
        subprocess.check_call(['aws', 's3', 'cp', '--only-show-errors', path, upload_credentials['upload_url']], env=env)
    except subprocess.CalledProcessError as e:
        PRINT("Upload failed with exit code %d" % e.returncode)
    else:
        end = time.time()
        duration = end - start
        PRINT("Uploaded in %.2f seconds" % duration)


def upload_file_to_uuid(filename, *, uuid, auth):
    """
    Upload file to a target environment.

    :param upload_specification: a dictionary containing a 'filename' and 'uuid',
        identifying the file to upload and the item into which it is to be uploaded.
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


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle part",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('part_filename', help='a local Excel filename that is the part file')
    parser.add_argument('--uuid', '-u', help='uuid identifier', default=None)
    parser.add_argument('--site', '-s', help="an http or https address of the site to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the site to use", default=None)
    args = parser.parse_args(args=simulated_args_for_testing)

    part_filename = args.part_filename
    uuid = args.uuid

    site = resolve_site(site=args.site, env=args.env)

    auth_dict = get_cgap_auth_dict(site)

    # print("auth_dict=", json.dumps(auth_dict, indent=2))

    if not yes_or_no("Upload %s to %s?" % (part_filename, site)):
        show("Aborting submission.")
        exit(1)

    upload_file_to_uuid(filename=part_filename, uuid=uuid, auth=auth_dict)


# TODO: Borrow from the following? -kmp 18-Aug-2020
#
#   This is stuff Submit4DN does that may or may not be useful to us.
#   To be removed if it doesn't get used.  And anyway, all this upload stuff belongs
#   in the SubmitCGAP repo at some point. It's just easier to debug here for now.
#   -kmp 9-Aug-2020
#
#
#     def get_upload_creds(file_id, connection):  # pragma: no cover
#         url = "%s/upload/" % (file_id)
#         req = ff_utils.post_metadata({}, url, key=connection.key)
#         return req['@graph'][0]['upload_credentials']
#
#
# def upload_file(creds, path):  # pragma: no cover
#     # Source: Submit4DN
#
#     ####################
#     # POST file to S3
#     env = os.environ.copy()  # pragma: no cover
#     try:
#         env.update({
#             'AWS_ACCESS_KEY_ID': creds['AccessKeyId'],
#             'AWS_SECRET_ACCESS_KEY': creds['SecretAccessKey'],
#             'AWS_SECURITY_TOKEN': creds['SessionToken'],
#         })
#     except Exception as e:
#         raise("Didn't get back s3 access keys from file/upload endpoint.  Error was %s" % str(e))
#     # ~10s/GB from Stanford - AWS Oregon
#     # ~12-15s/GB from AWS Ireland - AWS Oregon
#     print("Uploading file.")
#     start = time.time()
#     try:
#         subprocess.check_call(['aws', 's3', 'cp', '--only-show-errors', path, creds['upload_url']], env=env)
#     except subprocess.CalledProcessError as e:
#         # The aws command returns a non-zero exit code on error.
#         print("Upload failed with exit code %d" % e.returncode)
#         sys.exit(e.returncode)
#     else:
#         end = time.time()
#         duration = end - start
#         print("Uploaded in %.2f seconds" % duration)
