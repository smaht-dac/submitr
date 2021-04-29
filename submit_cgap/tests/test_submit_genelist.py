import pytest

from dcicutils.misc_utils import ignored
from dcicutils.qa_utils import override_environ
from unittest import mock
from ..base import KeyManager
from ..scripts.submit_genelist import main as submit_genelist_main
from ..scripts import submit_genelist as submit_genelist_module


INGESTION_TYPE = "genelist"


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
def test_submit_metadata_bundle_script(keyfile):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):

        with override_environ(CGAP_KEYS_FILE=keyfile):
            with mock.patch.object(submit_genelist_module,
                                   "submit_any_ingestion") as mock_submit_any_ingestion:
                try:
                    # Outside of the call, we will always see the default filename for cgap keys
                    # but inside the call, because of a decorator, the default might be different.
                    # See additional test below.
                    assert KeyManager.keydicts_filename() == KeyManager.DEFAULT_KEYDICTS_FILENAME

                    def mocked_submit_genelist(*args, **kwargs):
                        ignored(args, kwargs)
                        # We don't need to test this function's actions because we test its call args below.
                        # However, we do need to run this one test from the same dynamic context,
                        # so this is close enough.
                        assert KeyManager.keydicts_filename() == (keyfile or KeyManager.DEFAULT_KEYDICTS_FILENAME)

                    mock_submit_any_ingestion.side_effect = mocked_submit_genelist
                    submit_genelist_main(args_in)
                    mock_submit_any_ingestion.assert_called_with(**expect_call_args)
                except SystemExit as e:
                    assert e.code == expect_exit_code
                assert mock_submit_any_ingestion.call_count == (1 if expect_called else 0)

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some-file'], expect_exit_code=0, expect_called=True, expect_call_args={
        'ingestion_filename': 'some-file',
        'ingestion_type': INGESTION_TYPE,
        'env': None,
        'server': None,
        'institution': None,
        'project': None,
        'validate_only': False,
    })
    expect_call_args = {
        'ingestion_filename': 'some-file',
        'ingestion_type': INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        'institution': "some-institution",
        'project': "some-project",
        'validate_only': True,
    }
    test_it(args_in=["--env", "some-env", "--institution", "some-institution",
                     "-s", "some-server", "-v", "-p", "some-project",
                     "some-file"],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=["some-file", "--env", "some-env", "--institution", "some-institution",
                     "-s", "some-server", "--validate-only", "-p", "some-project"],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
