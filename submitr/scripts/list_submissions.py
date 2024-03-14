import argparse
import os
from dcicutils.command_utils import script_catch_errors
from ..submission import _define_portal, _print_recent_submissions


def main(simulated_args_for_testing=None):

    args = argparse.ArgumentParser(
        description="List recently submitted submissions.",
    )
    args.add_argument("--env", "-e",
                      help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    args.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    args.add_argument("--count", type=int, help="Maximum number of items to show.", default=30)
    args.add_argument("--details", action="store_true", help="Detailed output.", default=False)
    args.add_argument("--verbose", action="store_true", help="Verbose output.", default=False)
    args = args.parse_args()

    env_from_env = False
    if not args.env:
        args.env = os.environ.get("SMAHT_ENV")
        env_from_env = True

    with script_catch_errors():
        portal = _define_portal(env=args.env,
                                env_from_env=env_from_env,
                                keys_file=args.keys or os.environ.get("SMAHT_KEYS"), report=args.verbose)
        _print_recent_submissions(portal, details=args.details, verbose=args.verbose, count=args.count)


if __name__ == "__main__":
    main()
