import json
import os
import pytest

from dcicutils.qa_utils import MockFileSystem
from unittest import mock
from .test_base import default_env_for_testing
from .. import base as base_module
from ..auth import (
    keypair_to_keydict, keydict_to_keypair, get_cgap_keydicts,
    get_keypair_for_env, get_keydict_for_env,
    get_keydict_for_server, get_keypair_for_server,
)
from ..base import LOCAL_PSEUDOENV, PRODUCTION_SERVER, PRODUCTION_ENV, KeyManager
from ..exceptions import CGAPEnvKeyMissing, CGAPServerKeyMissing


def test_keydict_to_keypair():

    assert keydict_to_keypair({'key': 'foo', 'secret': 'bar', 'server': 'baz'}) == ('foo', 'bar')


def test_keypair_to_keydict():

    assert keypair_to_keydict(('foo', 'bar'), server='baz') == {
        'key': 'foo',
        'secret': 'bar',
        'server': 'baz',
    }


def test_get_cgap_keydicts_missing():

    mfs = MockFileSystem()

    with mock.patch.object(os.path, "exists", mfs.exists):

        assert get_cgap_keydicts() == {}  # When missing, it appears empty


def test_get_keypair_keydict_and_keydicts():

    missing_env = 'fourfront-cgapwolf'
    missing_server = "http://localhost:6666"

    cgap_pair = ('key000', 'secret000')

    cgap_dict = {
        'key': cgap_pair[0],
        'secret': cgap_pair[1],
        'server': PRODUCTION_SERVER,
    }

    cgap_foo_env = 'fourfront-cgapfoo'

    cgap_foo_pair = ('key123', 'secret123')

    cgap_foo_server = 'https://foo.cgap.hms.harvard.edu'

    cgap_foo_dict = {
        'key': cgap_foo_pair[0],
        'secret': cgap_foo_pair[1],
        'server': cgap_foo_server,
    }

    cgap_local_pair = ('key456', 'secret456')

    cgap_local_server = 'http://localhost:8000'

    cgap_local_dict = {
        'key': cgap_local_pair[0],
        'secret': cgap_local_pair[1],
        'server': cgap_local_server,
    }

    # The content of the keydict file will be a dictionary like:
    #   {
    #       'fourfront-cgap': {
    #           'key': 'key1',
    #           'secret': 'somesecret1',
    #           'server': 'https://cgap.hms.harvard.edu'
    #       },
    #       'fourfront-cgapfoo': {
    #           'key': 'key2',
    #           'secret': 'somesecret2',
    #           'server': 'http://fourfront-cgapfoo.whatever.aws.com'
    #       },
    #       'fourfront-cgaplocal': {
    #           'key': 'key3',
    #           'secret': 'somesecret3',
    #           'server': 'http://localhost:8000'
    #       }
    #   }
    expected_content = {
        cgap_foo_env: cgap_foo_dict,
        LOCAL_PSEUDOENV: cgap_local_dict,
        PRODUCTION_ENV: cgap_dict,
    }

    mfs = MockFileSystem(files={
        KeyManager.keydicts_filename():
            json.dumps(expected_content)
    })

    with mock.patch("io.open", mfs.open):
        with mock.patch("os.path.exists", mfs.exists):
            assert get_cgap_keydicts() == expected_content

            def test_it(override_default_env, default_pair_expected, default_dict_expected):

                with default_env_for_testing(override_default_env):

                    assert get_keypair_for_env(PRODUCTION_ENV) == cgap_pair
                    assert get_keypair_for_env(cgap_foo_env) == cgap_foo_pair
                    assert get_keypair_for_env(LOCAL_PSEUDOENV) == cgap_local_pair
                    assert get_keypair_for_env(None) == default_pair_expected
                    assert get_keypair_for_env() == default_pair_expected

                    with pytest.raises(CGAPEnvKeyMissing):
                        get_keypair_for_env(missing_env)

                    assert get_keydict_for_env(PRODUCTION_ENV) == cgap_dict
                    assert get_keydict_for_env(cgap_foo_env) == cgap_foo_dict
                    assert get_keydict_for_env(LOCAL_PSEUDOENV) == cgap_local_dict
                    assert get_keydict_for_env(None) == default_dict_expected
                    assert get_keydict_for_env() == default_dict_expected

                    assert get_keypair_for_server(PRODUCTION_SERVER) == cgap_pair
                    assert get_keypair_for_server(cgap_foo_server) == cgap_foo_pair
                    assert get_keypair_for_server(cgap_local_server) == cgap_local_pair
                    assert get_keypair_for_server(None) == default_pair_expected
                    assert get_keypair_for_server() == default_pair_expected

                    with pytest.raises(CGAPServerKeyMissing):
                        get_keypair_for_server(missing_server)

                    assert get_keydict_for_server(PRODUCTION_SERVER) == cgap_dict
                    assert get_keydict_for_server(cgap_foo_server) == cgap_foo_dict
                    assert get_keydict_for_server(cgap_local_server) == cgap_local_dict
                    assert get_keydict_for_server(None) == default_dict_expected
                    assert get_keydict_for_server() == default_dict_expected

            # If no override given, production env (fourfront-cgap) is default default.
            test_it(override_default_env=None,
                    default_pair_expected=cgap_pair,
                    default_dict_expected=cgap_dict)

            test_it(override_default_env=PRODUCTION_ENV,
                    default_pair_expected=cgap_pair,
                    default_dict_expected=cgap_dict)

            test_it(override_default_env=base_module.LOCAL_PSEUDOENV,
                    default_pair_expected=cgap_local_pair,
                    default_dict_expected=cgap_local_dict)

            test_it(override_default_env=cgap_foo_env,
                    default_pair_expected=cgap_foo_pair,
                    default_dict_expected=cgap_foo_dict)
