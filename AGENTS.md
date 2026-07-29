# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.

## Tests

`make test` runs unit tests (`pytest -m "not integration"`); `make test-integration` runs the
rclone tests that really talk to AWS S3 and Google Cloud Storage. The `integration` marker is
applied per-file via `pytestmark` (see `submitr/tests/integration/`), and `pytest.ini` declares it.

AWS auth for CI is GitHub OIDC (`aws-actions/configure-aws-credentials`) in every workflow. **Do not
reintroduce long-lived AWS access keys.**

Part of what the rclone tests exercise is minting scoped, short-lived credentials for one
bucket/key, mirroring how smaht-portal issues upload credentials
(`encoded_core.types.file.external_creds`). **`sts:GetFederationToken` cannot be used for that under
OIDC** — AWS only lets an IAM user or the account root user call it, so a role session cannot
(https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_sts-comparison.html). So
`AwsS3._generate_temporary_credentials` uses `sts:AssumeRoleWithWebIdentity` instead whenever web
identity federation is available, passing the same inline session policy (same intersection
semantics, and it needs no caller credentials); it falls back to `GetFederationToken` for
command-line use with an IAM user. This is why the workflow needs `id-token: write` and passes
`AWS_OIDC_ROLE_ARN` through to the test step.

Relatedly, anything needing the AWS account number must use `sts:GetCallerIdentity`, not
`iam:GetUser` — the latter has no answer for a role session.

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
