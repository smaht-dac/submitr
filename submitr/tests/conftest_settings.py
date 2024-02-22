import os


os.environ.pop("SMAHT_ENV", None)
os.environ.pop("SMAHT_KEYS", None)
os.environ.pop("SMAHT_NOADMIN", None)

REPOSITORY_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

if not os.path.basename(REPOSITORY_ROOT_DIR).startswith('submitr'):
    raise Exception(f"REPOSITORY_ROOT_DIR is not set right: {REPOSITORY_ROOT_DIR}")
