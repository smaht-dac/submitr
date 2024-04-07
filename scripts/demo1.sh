#!/bin/bash
# ----------------------------------------------------------------------------------------------------
  THIS_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
# ----------------------------------------------------------------------------------------------------
#
# Demo script for SMaHT ingestion submission (submitr/submit-metadata-bundle).
# Don't forget to set you AWS credentials so upload works, e.g.: use_test_creds smaht-wolf 

TEST_FILE=test_submission_from_doug_20231106.xlsx
TEST_FILE_DIR=$THIS_DIR/../testdata/demo
TEST_FILE_PATH=`realpath $TEST_FILE_DIR/$TEST_FILE`

echo submit-metadata-bundle $TEST_FILE_PATH --env smaht-local --submit $*
      submit-metadata-bundle $TEST_FILE_PATH --env smaht-local --submit $*
