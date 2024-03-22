import argparse
import os
from dcicutils.command_utils import script_catch_errors
from dcicutils.common import ORCHESTRATED_APPS
from ..base import DEFAULT_APP
from ..submission import _monitor_ingestion_process, _pytesting


EPILOG = __doc__


def main(simulated_args_for_testing=None):

    args = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Check previously submitted submission.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    args.add_argument('submission_uuid', nargs="?", help='UUID of previously submitted submission.')
    args.add_argument('--app', choices=ORCHESTRATED_APPS, default=DEFAULT_APP,
                      help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                           f" Normally this should not be given.")
    args.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    args.add_argument("--env", "-e",
                      help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    args.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    args.add_argument('--directory', '-d', help="Directory of the upload files (if resuming submission).")
    args.add_argument('--directory-only', help="Same as --directory but NOT recursively.", default=False)
    args.add_argument('--details', action="store_true", help="More detailed output.", default=False)
    args.add_argument('--timeout', help="Wait timeout for server validation/submission.")
    args.add_argument('--verbose', action="store_true", help="More verbose output.", default=False)
    args.add_argument('--debug', action="store_true", help="Debugging output.", default=False)
    args = args.parse_args(args=simulated_args_for_testing)

    if not args.submission_uuid:
        if _pytesting():
            exit(2)
        args.submission_uuid = "dummy"

    env_from_env = False
    if not args.env:
        args.env = os.environ.get("SMAHT_ENV")
        env_from_env = True

    # We would we want to specify an upload directy for checks-submissions?
    # Because if the check is for a server validation "submission" which on which
    # we previously timed out waiting for (via submit-metadata-bundler) this
    # command will give the user the option of continueing on with the submission.
    upload_directory = None
    upload_directory_only = True
    if args.directory:
        upload_directory = args.directory
        upload_directory_only = False
    if args.directory_only:
        upload_directory = args.directory_only
        upload_directory_only = True

    if upload_directory and not os.path.isdir(upload_directory):
        print(f"Directory does not exist: {upload_directory}")
        exit(1)

    if args.timeout:
        if not args.timeout.isdigit():
            args.timeout = None
        else:
            args.timeout = int(args.timeout)

    with script_catch_errors():
        return _monitor_ingestion_process(
                args.submission_uuid,
                env=args.env,
                keys_file=args.keys or os.environ.get("SMAHT_KEYS"),
                server=args.server,
                env_from_env=env_from_env,
                show_details=(args.verbose or args.details),
                check_submission_script=True,
                verbose=args.verbose,
                debug=args.debug,
                upload_directory=upload_directory,
                upload_directory_recursive=not upload_directory_only,
                note="Checking Submission"
        )


if __name__ == '__main__':
    main()
