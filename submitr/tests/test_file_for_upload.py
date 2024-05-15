import os
import tempfile
from dcicutils.file_utils import create_random_file, get_file_size, compute_file_md5
from dcicutils.misc_utils import create_uuid
from dcicutils.tmpfile_utils import remove_temporary_directory, temporary_directory
from submitr.file_for_upload import FilesForUpload
from submitr.rclone import RCloneConfigGoogle
from unittest.mock import patch as mock_patch

TMPDIR = None


def setup_module():
    global TMPDIR
    TMPDIR = tempfile.mkdtemp()


def teardown_module():
    global TMPDIR
    remove_temporary_directory(TMPDIR)


class Mock_RCloneConfigGoogle(RCloneConfigGoogle):

    @staticmethod
    def create_for_testing(self, file):
        return Mock_RCloneConfigGoogle(file)

    def __init__(self, file):
        self._file = file

    def path_exists(self, path):
        return os.path.isfile(path)

    def file_size(self, file):
        get_file_size(file)

    def file_checksum(self, file):
        return compute_file_md5(file)


def test_file_for_upload_b():

    with temporary_directory() as tmpdir:
        config_google = Mock_RCloneConfigGoogle("asdf")
        # assert config_google.path_exists("dummy") is True

    with mock_patch("submitr.rclone.RCloneConfigGoogle") as MockedRCloneConfigGoogle:
        with temporary_directory() as tmpdir:

            config_google = MockedRCloneConfigGoogle.return_value
            config_google.path_exists.return_value = True
            config_google.file_size.return_value = 1023
            assert config_google.path_exists("dummy") is True
            assert config_google.file_size("dummy") == 1023

            upload_file_a = os.path.join(tmpdir, "some_file_a.fastq")
            upload_file_b = os.path.join(tmpdir, "some_file_b.fastq")
            upload_file_a_uuid = create_uuid()
            upload_file_b_uuid = create_uuid()

            files = [{"filename": upload_file_a, "uuid": upload_file_a_uuid},
                     {"filename": upload_file_b, "uuid": upload_file_b_uuid}]
            ffu = FilesForUpload.assemble(files,
                                          main_search_directory=tmpdir,
                                          main_search_directory_recursively=True,
                                          config_google=config_google)
            print(ffu)
            # assert ffu[0].found_google is True

    config_google = RCloneConfigGoogle()
    with mock_patch.object(RCloneConfigGoogle, "path_exists") as mocked_config_path_google_exists:
        with temporary_directory() as tmpdir:
            mocked_config_path_google_exists.return_value = True
            assert config_google.path_exists("dummy") is True

            upload_file_a = os.path.join(tmpdir, "some_file_a.fastq")
            upload_file_b = os.path.join(tmpdir, "some_file_b.fastq")
            upload_file_a_uuid = create_uuid()
            upload_file_b_uuid = create_uuid()

            files = [{"filename": upload_file_a, "uuid": upload_file_a_uuid},
                     {"filename": upload_file_b, "uuid": upload_file_b_uuid}]
            ffu = FilesForUpload.assemble(files,
                                          main_search_directory=tmpdir,
                                          main_search_directory_recursively=True,
                                          config_google=config_google)
            # assert ffu[0].found_google is True
        pass


def test_file_for_upload_a():

    with temporary_directory() as tmpdir:
        upload_file_a = os.path.join(tmpdir, "some_file_a.fastq")
        upload_file_b = os.path.join(tmpdir, "some_file_b.fastq")
        upload_file_a_uuid = create_uuid()
        upload_file_b_uuid = create_uuid()
        files = [{"filename": upload_file_a, "uuid": upload_file_a_uuid},
                 {"filename": upload_file_b, "uuid": upload_file_b_uuid}]
        ffu = FilesForUpload.assemble(files,
                                      main_search_directory=tmpdir,
                                      main_search_directory_recursively=True)
        assert ffu[0].found is False
        assert ffu[1].found is False

    with temporary_directory() as tmpdir:
        upload_file_a_size = 1024
        upload_file_a_dup_size = 1024
        upload_file_b_size = 2048
        dir_a = tmpdir
        os.makedirs(dir_b := os.path.join(tmpdir, "some_subdir"))
        upload_file_a = create_random_file(os.path.join(dir_a, "some_file_a.fastq"), nbytes=upload_file_a_size)
        upload_file_b = create_random_file(os.path.join(dir_a, "some_file_b.fastq"), nbytes=upload_file_b_size)
        upload_file_a_dup = create_random_file(os.path.join(dir_b, "some_file_a.fastq"), nbytes=upload_file_a_dup_size)
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
        assert ffu[0].path == upload_file_a
        assert ffu[0].size == upload_file_a_size
        assert ffu[0].found_local is True
        assert ffu[0].found_local_multiple is True
        assert ffu[0].path_local == upload_file_a
        assert ffu[0].path_local_multiple == [upload_file_a, upload_file_a_dup]
        assert ffu[0].size_local == upload_file_a_size
        assert ffu[0].found_google is False
        assert ffu[0].path_google is None
        assert ffu[0].ignore is False
        assert ffu[0].resume_upload_command(env="some_env") == f"resume-uploads --env some_env {upload_file_a_uuid}"

        assert ffu[1].found is True
        assert ffu[1].path == upload_file_b
        assert ffu[1].size == upload_file_b_size
        assert ffu[1].found_local is True
        assert ffu[1].found_local_multiple is False
        assert ffu[1].path_local == upload_file_b
        assert ffu[1].path_local_multiple is None
        assert ffu[1].size_local == upload_file_b_size
        assert ffu[1].found_google is False
        assert ffu[1].path_google is None
        assert ffu[1].ignore is False
        assert ffu[1].resume_upload_command(env="some_env") == f"resume-uploads --env some_env {upload_file_b_uuid}"
