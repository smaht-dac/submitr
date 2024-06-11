import multiprocessing
import sys
from submitr.scripts.check_submission import main as main_check_submission
from submitr.scripts.get_metadata_template import main as main_get_metadata_template
from submitr.scripts.list_submissions import main as main_list_submissions
from submitr.scripts.rcloner import main as main_rcloner
from submitr.scripts.resume_uploads import main as main_resume_uploads
from submitr.scripts.submit_metadata_bundle import main as main_submit_metadata_bundle
from submitr.scripts.view_portal_object import main as main_view_portal_object

supported_commands = {
    "check-submission": main_check_submission,
    "main-get-metadata-template": main_get_metadata_template,
    "list-submissions": main_list_submissions,
    "rcloner": main_rcloner,
    "resume-uploads": main_resume_uploads,
    "submit-metadata": main_submit_metadata_bundle,
    "submit-metadata-bundle": main_submit_metadata_bundle,
    "view-portal-object": main_view_portal_object
}


def main():
    multiprocessing.freeze_support()
    if (command := sys.argv[1]) not in supported_commands:
        print(f"Unknown command: {command}")
        sys.exit(1)
    sys.argv = sys.argv[1:]
    supported_commands[command]()
    sys.exit(0)


if __name__ == "__main__":
    main()
