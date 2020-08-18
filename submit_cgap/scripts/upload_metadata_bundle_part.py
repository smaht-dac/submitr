import argparse
# import datetime
# import io
# import json
# import os
# import re
# import requests
# import subprocess
# import sys
# import time

from dcicutils.command_utils import yes_or_no
from .submit_metadata_bundle import resolve_site, show, get_cgap_auth_dict


EPILOG = __doc__


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

    site = resolve_site(site=args.site, env=args.env)

    auth_dict = get_cgap_auth_dict(site)

    if not yes_or_no("Upload %s to %s?" % (part_filename, site)):
        show("Aborting submission.")
        exit(1)

    raise NotImplementedError("This is not yet implemented.")

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
