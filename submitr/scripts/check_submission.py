import os
from dcicutils.command_utils import script_catch_errors
from dcicutils.common import ORCHESTRATED_APPS
from ..base import DEFAULT_APP
from ..submission import _monitor_ingestion_process, _pytesting
from .cli_utils import CustomArgumentParser

_HELP = f"""
===
check-submission [VERSION]
===
Tool to check the status of previously submitted metedata.
If the given UUID is for a validation rather than a submission
then you will have the opportunity to continue with its submission.
See: {CustomArgumentParser.HELP_URL}#check-submission
===
USAGE: check-submission UUID OPTIONS
-----
UUID: This is UUID of your submission.
===
OPTIONS:
===
--env ENVIRONMENT-NAME
  To specify your environment name; from your ~/.smaht-keys.json file.
--KEYS-FILE
  To specify an alternate credentials/keys
  file to the default ~/.smaht-keys.json file.
--directory DIRECTORY
  To specify a directory containing the files to upload;
  this directory will be search, recursively.
--directory-only
  Same as --directory but does NOT search recursively.
--output OUTPUT-FILE
  Writes all logging output to the specified file;
  and refrains from printing lengthy content to output/stdout.
--verbose
  Displays more verbose output.
--help
  Prints this documentation.
--help-web
  Opens your browser to the Web based documentation.
  {CustomArgumentParser.HELP_URL}
===
"""


def main(simulated_args_for_testing=None):

    parser = CustomArgumentParser(help=_HELP, help_url=CustomArgumentParser.HELP_URL)
    parser.add_argument('submission_uuid', nargs="?", help='UUID of previously submitted submission.')
    parser.add_argument('--app', choices=ORCHESTRATED_APPS, default=DEFAULT_APP,
                        help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--server', help="An http or https address of the server to use.", default=None)
    parser.add_argument("--env", help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    parser.add_argument('--directory', help="Directory of the upload files (if resuming submission).")
    parser.add_argument('--directory-only', help="Same as --directory but NOT recursively.", default=False)
    parser.add_argument('--output', help="Output file for results.", default=False)
    parser.add_argument('--details', action="store_true", help="More detailed output.", default=False)
    parser.add_argument('--verbose', action="store_true", help="More verbose output.", default=False)
    parser.add_argument('--timeout', help="Wait timeout for server validation/submission.")
    parser.add_argument('--debug', action="store_true", help="Debugging output.", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    if not args.submission_uuid:
        if _pytesting():
            exit(2)
        args.submission_uuid = "dummy"

    env_from_env = False
    if not args.env:
        args.env = os.environ.get("SMAHT_ENV")
        if args.env:
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
                keys_file=args.keys,
                server=args.server,
                env_from_env=env_from_env,
                show_details=(args.verbose or args.details),
                check_submission_script=True,
                verbose=args.verbose,
                debug=args.debug,
                upload_directory=upload_directory,
                upload_directory_recursive=not upload_directory_only,
                output_file=args.output,
                note="Checking Submission"
        )


if __name__ == '__main__':
    main()
