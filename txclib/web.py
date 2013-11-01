# -*- coding: utf-8 -*-

import platform
from txclib import get_version


def user_agent_identifier():
    """Return the user agent for the client."""
    client_info = (get_version(), platform.system(), platform.machine())
    return "txclient/%s (%s %s)" % client_info
