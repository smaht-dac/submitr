import io
import os
import json


ACCESS_KEY_FILENAME = ".cgap-access"

KEY_ID_VAR = "SUBMIT_CGAP_ACCESS_KEY_ID"
SECRET_VAR = "SUBMIT_CGAP_SECRET_ACCESS_KEY"
DEFAULT_ENV_VAR = "SUBMIT_CGAP_DEFAULT_ENV"


class CGAPPermissionError(PermissionError):

    def __init__(self, server):
        self.server = server
        super().__init__("Your credentials (the access key information in environment variables %s and %s)"
                         " were rejected by %s."
                         " Either this is not the right server, or you need to obtain up-to-date access keys."
                         % (KEY_ID_VAR, SECRET_VAR, server))


def get_cgap_auth_tuple():
    key_id = os.environ.get(KEY_ID_VAR, "")
    secret = os.environ.get(SECRET_VAR, "")
    if key_id and secret:
        return key_id, secret
    raise RuntimeError("Both of the environment variables %s and %s must be set."
                       " Appropriate values can be obtained by creating an access key in your CGAP user profile."
                       % (KEY_ID_VAR, SECRET_VAR))


def get_cgap_auth_dict(server):
    auth_tuple = get_cgap_auth_tuple()
    return auth_tuple_to_cgap_auth_dict(auth_tuple, server)


def auth_tuple_to_cgap_auth_dict(auth_tuple, server):
    auth_dict = {
        'key': auth_tuple[0],
        'secret': auth_tuple[1],
        'server': server,
    }
    return auth_dict


def cgap_auth_to_tuple(auth_dict):
    return (auth_dict['key'], auth_dict['secret'])


KEYPAIRS_FILENAME = '.cgap-keypairs.json'


def get_cgap_keypairs():
    with io.open(KEYPAIRS_FILENAME) as keyfile:
        keys = json.load(keyfile)
        return keys


def get_cgap_keypair(bs_env=None):
    """
    Gets the appropriate auth info for talking to a given beanstalk environment.

    Args:
        bs_env: the name of a beanstalk environment

    Returns:
        Auth information.
        The auth is probably a keypair, though we might change this to include a JWT token in the the future.
    """

    keypairs = get_cgap_keypairs()
    keypair = tuple(keypairs.get(bs_env or 'fourfront-cgaplocal'))
    if not keypair:
        raise RuntimeError("Missing credential in keypairs file %s for %s." % (KEYPAIRS_FILENAME, bs_env))
    return keypair