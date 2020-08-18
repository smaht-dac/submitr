import argparse
import datetime
# import io
# import json
import os
import re
import requests
# import subprocess
# import sys
import time

from dcicutils.beanstalk_utils import get_beanstalk_real_url
from dcicutils.command_utils import yes_or_no
from dcicutils.env_utils import is_cgap_env
from dcicutils.misc_utils import check_true


EPILOG = __doc__


# Programmatic output will use 'show' so that debugging statements using regular 'print' are more easily found.
def show(*args, with_time=False):
    program_output = print
    if with_time:
        hh_mm_ss = str(datetime.datetime.now().strftime("%H:%M:%S"))
        program_output(hh_mm_ss, *args)
    else:
        program_output(*args)


ACCESS_KEY_FILENAME = ".cgap-access"

KEY_ID_VAR = "SUBMIT_CGAP_ACCESS_KEY_ID"
SECRET_VAR = "SUBMIT_CGAP_SECRET_ACCESS_KEY"
DEFAULT_ENV_VAR = "SUBMIT_CGAP_DEFAULT_ENV"


def get_cgap_auth_tuple():
    key_id = os.environ.get(KEY_ID_VAR, "")
    secret = os.environ.get(SECRET_VAR, "")
    if key_id and secret:
        return key_id, secret
    raise RuntimeError("Both of the environment variables %s and %s must be set."
                       " Appropriate values can be obtained by creating an access key in your CGAP user profile."
                       % (KEY_ID_VAR, SECRET_VAR))


def get_cgap_auth_dict(server):
    auth_tuple = get_cgap_auth_tuple()
    auth_dict = {
        'key': auth_tuple[0],
        'secret': auth_tuple[1],
        'server': server,
    }
    return auth_dict


SITE_REGEXP = re.compile(
    # Note that this regular expression does NOT contain 4dnucleome.org for the same reason it requires
    # a fourfront-cgapXXX address. It is trying only to match cgap addresses, though of course it has to make an
    # exception for localhost debugging. You're on your own to make sure the right server is connected there.
    # -kmp 16-Aug-2020
    r"^(https?://localhost:[0-9]+"
    r"|https?://fourfront-cgap[a-z0-9.-]*"
    r"|https://[a-z.-]*cgap.hms.harvard.edu)/?$"
)


def resolve_site(site, env):
    check_true(not site or not env, "You may not specify both --site and --env.", error_class=SyntaxError)

    if not site and not env:
        env = os.environ.get(DEFAULT_ENV_VAR)
        if env:
            show("Defaulting to beanstalk environment '%s' because %s is set." % (env, DEFAULT_ENV_VAR))
        else:
            # Production default needs no explanation.
            env = 'fourfront-cgap'

    if env:
        try:
            # TODO: Replace with env = env_utils.full_env_name(env) when available in a future dcicutils.
            if not env.startswith('fourfront-'):
                env = 'fourfront-' + env
            assert is_cgap_env(env)
            site = get_beanstalk_real_url(env)
        except Exception:
            raise SyntaxError("The specified env is not a valid CGAP beanstalk name.")

    matched = SITE_REGEXP.match(site)
    if not matched:
        raise ValueError("The site should be 'http://localhost:<port>' or 'https://<cgap-hostname>', not: %s"
                         % site)
    site = matched.group(1)

    return site


PROGRESS_CHECK_INTERVAL = 15


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('bundle_filename', help='a local Excel filename that is the data bundle')
    parser.add_argument('--institution', '-i', help='institution identifier', default=None)
    parser.add_argument('--project', '-p', help='project identifier', default=None)
    parser.add_argument('--site', '-s', help="an http or https address of the site to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the site to use", default=None)
    args = parser.parse_args(args=simulated_args_for_testing)

    try:

        bundle_filename = args.bundle_filename
        institution = args.institution
        project = args.project

        site = resolve_site(site=args.site, env=args.env)

        if not yes_or_no("Submit %s to %s?" % (bundle_filename, site)):
            show("Aborting submission.")
            exit(1)

        auth = get_cgap_auth_tuple()

        user_url = site + "/me?format=json"
        user_record_response = requests.get(user_url, auth=auth)
        if user_record_response.status_code == 401:
            raise PermissionError("Your credentials (the access key information in environment variables %s and %s)"
                                  " were rejected by %s."
                                  " Either this is not the right site, or you need to obtain up-to-date access keys."
                                  % (KEY_ID_VAR, SECRET_VAR, site))
        user_record_response.raise_for_status()
        user_record = user_record_response.json()
        show("The site %s recognizes you as %s <%s>."
             % (site, user_record['title'], user_record['contact_email']))

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

        if not project:
            project = user_record.get('project', {}).get('@id', None)
            if not project:
                raise SyntaxError("Your user profile has no project declared,"
                                  " so you must specify a --project explicitly.")
            show("Using project:", project)

        if not os.path.exists(bundle_filename):
            raise ValueError("The file '%s' does not exist." % bundle_filename)

        post_files = {
            "datafile": open(bundle_filename, 'rb')
        }

        post_data = {
            'ingestion_type': 'data_bundle',
            'institution': institution,
            'project': project,
        }

        submission_url = site + "/submit_for_ingestion"

        res = requests.post(submission_url, auth=auth, data=post_data, files=post_files).json()

        # print(json.dumps(res, indent=2))

        uuid = res['submission_id']

        show("Bundle uploaded. Awaiting processing...", with_time=True)

        tracking_url = site + "/ingestion-submissions/" + uuid + "?format=json"

        success = False
        outcome = None
        n_tries = 8
        tries_left = n_tries
        done = False
        while tries_left > 0:
            # Pointless to hit the queue immediately, so we avoid some
            # server stress by sleeping even before the first try.
            time.sleep(PROGRESS_CHECK_INTERVAL)
            res = res = requests.get(tracking_url, auth=auth).json()
            processing_status = res['processing_status']
            done = processing_status['state'] == 'done'
            if done:
                outcome = processing_status['outcome']
                success = outcome == 'success'
                break
            else:
                show("Progress is %s. Continuing to wait..." % processing_status['progress'], with_time=True)
            tries_left -= 1

        if not done:
            show("Timed out after %d tries." % n_tries, with_time=True)
        else:
            show("Final status: %s" % outcome, with_time=True)

        def show_section(section):
            show("----- %s -----" % section.replace("_", " ").title())
            lines = res['additional_data'].get(section)
            if lines:
                for line in lines:
                    show(line)
            else:
                show("Nothing to show.")

        show_section('validation_output')

        if success:
            show_section('post_output')

            show_section('upload_info')

    except Exception as e:
        show("%s: %s" % (e.__class__.__name__, str(e)))
        exit(1)


if __name__ == '__main__':
    main()
