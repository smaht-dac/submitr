from unittest import mock

from dcicutils.common import ORCHESTRATED_APPS
from dcicutils.misc_utils import ignored
from ..base import DEFAULT_APP
from ..scripts.check_submission import main as check_submission_main
from ..scripts import check_submission as check_submission_module
from .testing_helpers import system_exit_expected


SAMPLE_GUID = '1f199b61-e7a1-4c2a-9599-cfc64f51dab7'


def test_check_submission_script():

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):
        ignored(expect_call_args)
        with mock.patch.object(check_submission_module, "_check_submit_ingestion") as mock_check_submit_ingestion:
            with system_exit_expected(exit_code=expect_exit_code):
                check_submission_main(args_in)
                raise AssertionError("check_submission_main should not exit normally.")  # pragma: no cover
            assert mock_check_submit_ingestion.call_count == (1 if expect_called else 0)

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=[SAMPLE_GUID], expect_exit_code=0, expect_called=True,
            expect_call_args={
                'submission_uuid': SAMPLE_GUID,
                'app': DEFAULT_APP,
                'server': None,
                'env': None,
            })
    sample_app = None
    for app in ORCHESTRATED_APPS:
        if app != DEFAULT_APP:
            sample_app = app
    assert sample_app, "sample_app did not get properly set."
    sample_server = 'https://some-portal'
    sample_env = 'some-env'
    test_it(args_in=['--server', sample_server, SAMPLE_GUID],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args={
                'submission_uuid': SAMPLE_GUID,
                'app': DEFAULT_APP,
                'server': sample_server,
                'env': None,
            })
    test_it(args_in=[SAMPLE_GUID, '--server', sample_server, '--app', sample_app],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args={
                'submission_uuid': SAMPLE_GUID,
                'app': sample_app,  # unadvisable but possible. documented as being only for debugging
                'server': sample_server,
                'env': None,
            })
    test_it(args_in=[SAMPLE_GUID, '--env', sample_env],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args={
                'submission_uuid': SAMPLE_GUID,
                'app': DEFAULT_APP,
                'server': None,
                'env': sample_env,
            })
