class PortalPermissionError(PermissionError):

    def __init__(self, server):
        self.server = server
        super().__init__("Your credentials were rejected by %s. Either this is not the right server,"
                         " or you need to obtain up-to-date access keys." % server)
