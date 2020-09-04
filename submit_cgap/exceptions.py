from .base import KEYDICTS_FILENAME


class CGAPPermissionError(PermissionError):

    def __init__(self, server):
        self.server = server
        super().__init__("Your credentials were rejected by %s. Either this is not the right server,"
                         " or you need to obtain up-to-date access keys." % server)


class CGAPKeyMissing(RuntimeError):

    def __init__(self, context, keyfile=KEYDICTS_FILENAME):
        self.context = context
        super().__init__("Missing credential in file %s for %s." % (keyfile, context))


class CGAPEnvKeyMissing(CGAPKeyMissing):

    def __init__(self, env, keyfile=KEYDICTS_FILENAME):
        self.env = env
        super().__init__(context="beanstalk environment %s" % env, keyfile=keyfile)


class CGAPServerKeyMissing(CGAPKeyMissing):

    def __init__(self, server, keyfile=KEYDICTS_FILENAME):
        self.server = server
        super().__init__(context="server %s" % server, keyfile=keyfile)
