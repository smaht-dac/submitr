from .base import KeyManager


class CGAPPermissionError(PermissionError):

    def __init__(self, server):
        self.server = server
        super().__init__("Your credentials were rejected by %s. Either this is not the right server,"
                         " or you need to obtain up-to-date access keys." % server)


class CGAPKeyMissing(RuntimeError):

    def __init__(self, context, keyfile=KeyManager.keydicts_filename()):
        self.context = context
        super().__init__("Missing credential in file %s for %s." % (keyfile, context))


class CGAPEnvKeyMissing(CGAPKeyMissing):

    def __init__(self, env, keyfile=KeyManager.keydicts_filename()):
        self.env = env
        super().__init__(context="beanstalk environment %s" % env, keyfile=keyfile)


class CGAPServerKeyMissing(CGAPKeyMissing):

    def __init__(self, server, keyfile=KeyManager.keydicts_filename()):
        self.server = server
        super().__init__(context="server %s" % server, keyfile=keyfile)
