import os


REPOSITORY_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

if not os.path.basename(REPOSITORY_ROOT_DIR).startswith('submitr'):
    raise Exception(f"REPOSITORY_ROOT_DIR is not set right: {REPOSITORY_ROOT_DIR}")
