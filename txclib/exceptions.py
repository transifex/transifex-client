# -*- coding: utf-8 -*-

"""
Exception classes for the tx client.
"""


class UnInitializedError(Exception):
    """The project directory has not been initialized."""


class UnknownCommandError(Exception):
    """The provided command is not supported."""


class MalformedConfigFile(Exception):
    pass


class InvalidAuthenticationCredentials(Exception):
    pass


class ProjectAlreadyInitialized(Exception):
    pass

# HTTP exceptions
class HttpNotFound(Exception):
    pass


class HttpNotAuthorized(Exception):
    pass
