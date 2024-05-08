from unittest import mock
import os
from dcicutils.file_utils import create_random_file
from dcicutils.misc_utils import create_uuid
from dcicutils.tmpfile_utils import temporary_directory
from submitr.file_for_upload import FileForUpload, FilesForUpload

def test_file_for_upload():
    with temporary_directory() as tmpdir:
        upload_file_a_size = 1024
        upload_file_a_duplicate_size = 1024
        upload_file_b_size = 2048
        dir_a = tmpdir
        os.makedirs(dir_b := os.path.join(tmpdir, "some_subdir"))
        upload_file_a = create_random_file(os.path.join(dir_a, "some_file_a.fastq"), nbytes=upload_file_a_size)
        upload_file_b = create_random_file(os.path.join(dir_a, "some_file_b.fastq"), nbytes=upload_file_b_size)
        upload_file_a_duplicate = create_random_file(os.path.join(dir_b, "some_file_a.fastq"))
        upload_file_a_uuid = create_uuid()
        upload_file_b_uuid = create_uuid()
        assert os.path.isfile(upload_file_a)
        assert os.path.isfile(upload_file_b)
        files = [{"filename": upload_file_a, "uuid": upload_file_a_uuid},
                 {"filename": upload_file_b, "uuid": upload_file_b_uuid}]
        ffu = FilesForUpload.assemble(files,
                                      main_search_directory=tmpdir,
                                      main_search_directory_recursively=True)
        assert ffu[0].found is True
        assert ffu[0].found_locally is True
        assert ffu[0].found_locally_multiple is True
        assert ffu[0].found_in_google is False
        assert ffu[0].path == upload_file_a
        assert ffu[0].local_path == upload_file_a
        assert ffu[0].local_paths == [upload_file_a, upload_file_a_duplicate]
        assert ffu[0].local_size == upload_file_a_size
        assert ffu[0].size == upload_file_a_size
        assert ffu[0].ignore is False
        assert ffu[0].resume_upload_command(env="some_env") == f"resume-uploads --env some_env {upload_file_a_uuid}"

        assert ffu[1].found is True
        assert ffu[1].found_locally is True
        assert ffu[1].found_locally_multiple is False
        assert ffu[1].found_in_google is False
        assert ffu[1].path == upload_file_b
        assert ffu[1].local_path == upload_file_b
        assert ffu[1].local_paths is None
        assert ffu[1].local_size == upload_file_b_size
        assert ffu[1].size == upload_file_b_size
        assert ffu[1].ignore is False
        assert ffu[1].resume_upload_command(env="some_env") == f"resume-uploads --env some_env {upload_file_b_uuid}"
