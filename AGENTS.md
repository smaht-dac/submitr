# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.

## Tests

`make test` runs unit tests (`pytest -m "not integration"`); `make test-integration` runs the
rclone tests that really talk to AWS S3 and Google Cloud Storage. The `integration` marker is
applied per-file via `pytestmark` (see `submitr/tests/integration/`), and `pytest.ini` declares it.

**The INTEGRATION TESTS workflow cannot use GitHub OIDC for AWS; it needs an IAM user's long-term
access keys.** The harness mints scoped credentials with `sts:GetFederationToken`
(`submitr/rclone/testing/rclone_utils_for_testing_amazon.py`), deliberately mirroring how
smaht-portal issues upload credentials. AWS only lets an IAM user or the account root user call
that operation, and credentials from `AssumeRoleWithWebIdentity` explicitly cannot
(https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_sts-comparison.html). No trust
policy, role permission, bucket policy or KMS grant changes this — migrating off static keys
requires changing the harness away from `GetFederationToken` first. See the note at the top of
`.github/workflows/main-integration-tests.yml`.

Reading integration failures in GitHub Actions: because the multi-line
`GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON` secret has lines that are just `{` and `}`, Actions masks
every brace in the logs, so f-string source echoes render as `***expr***`. Don't read that as
a leaked secret or as the real error text.

## Releasing

Each PR bumps `version` in `pyproject.toml` and adds a matching `CHANGELOG.rst` entry;
`submitr/tests/test_misc.py::test_changelog_consistency` fails if the entry is missing.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
