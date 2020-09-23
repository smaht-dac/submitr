import io
import json
import os

from . import base as base_module
from .base import KeyManager
from .exceptions import CGAPEnvKeyMissing, CGAPServerKeyMissing


def keypair_to_keydict(auth_tuple, server):
    auth_dict = {
        'key': auth_tuple[0],
        'secret': auth_tuple[1],
        'server': server,
    }
    return auth_dict


def keydict_to_keypair(auth_dict):
    return (
        auth_dict['key'],
        auth_dict['secret']
    )


def get_cgap_keydicts():
    if not os.path.exists(KeyManager.keydicts_filename()):
        return {}
    with io.open(KeyManager.keydicts_filename()) as keyfile:
        keys = json.load(keyfile)
        return keys


def get_keydict_for_env(env=None):
    """
    Gets the appropriate auth info for talking to a given beanstalk environment.

    Args:
        env: the name of a beanstalk environment

    Returns:
        Auth information as a dict with keys 'key', 'secret', and 'server'.
    """

    keydicts = get_cgap_keydicts()
    keydict = keydicts.get(env
                           # For testing, we sometimes bind base_module.DEFAULT_ENV so we must make sure
                           # to pick up the value of DEFAULT_ENV indirectly through that module
                           # rather than importing the variable directly, which would complicate mocking.
                           # -kmp 4-Sep-2020
                           or base_module.DEFAULT_ENV)
    if not keydict:
        raise CGAPEnvKeyMissing(env=env, keyfile=KeyManager.keydicts_filename())
    return keydict


def get_keypair_for_env(env=None):
    """
    Gets the appropriate auth info for talking to a given beanstalk environment.

    Args:
        env: the name of a beanstalk environment

    Returns:
        Auth information as a (key, secret) tuple.
    """

    return keydict_to_keypair(get_keydict_for_env(env=env))


def get_keydict_for_server(server=None):
    """
    Gets the appropriate auth info for talking to a given beanstalk environment.

    Args:
        server: the name of a server

    Returns:
        Auth information.
        The auth is a keypair, though we might change this to include a JWT token in the the future.
    """
    if server is None:
        # The values of keydict_for_server(None) and keydict_for_env(None) should match,
        # and since we don't know what server we're looking for anyway,
        # let's just look it up the other way and be done...
        return get_keydict_for_env()

    keydicts = get_cgap_keydicts()
    server_to_find = server.rstrip('/')
    for keydict in keydicts.values():
        if keydict['server'].rstrip('/') == server_to_find:
            return keydict
    raise CGAPServerKeyMissing(server=server, keyfile=KeyManager.keydicts_filename())


def get_keypair_for_server(server=None):
    return keydict_to_keypair(get_keydict_for_server(server=server))
