# -*- coding: utf-8 -*-

import os
import platform
from pkg_resources import resource_filename, resource_string
from txclib import get_version


def user_agent_identifier():
    """Return the user agent for the client."""
    client_info = (get_version(), platform.system(), platform.machine())
    return "txclient/%s (%s %s)" % client_info


def certs_file():
    if platform.system() == 'Windows':
        # Workaround py2exe and resource_filename incompatibility.
        # Store the content in the filesystem permanently.
        app_dir = os.path.join(
            os.getenv('appdata', os.path.expanduser('~')), 'transifex-client'
        )
        if not os.path.exists(app_dir):
            os.mkdir(app_dir)
        ca_file = os.path.join(app_dir, 'cacert.pem')
        if not os.path.exists(ca_file):
            content = resource_string(__name__, 'cacert.pem')
            with open(ca_file, 'w') as f:
                f.write(content)
        return ca_file
    else:
        POSSIBLE_CA_BUNDLE_PATHS = [
            # Red Hat, CentOS, Fedora and friends
            # (provided by the ca-certificates package):
            '/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem',
            '/etc/ssl/certs/ca-bundle.crt',
            '/etc/pki/tls/certs/ca-bundle.crt',
            # Ubuntu, Debian, and friends
            # (provided by the ca-certificates package):
            '/etc/ssl/certs/ca-certificates.crt',
            # FreeBSD (provided by the ca_root_nss package):
            '/usr/local/share/certs/ca-root-nss.crt',
            # openSUSE (provided by the ca-certificates package),
            # the 'certs' directory is the
            # preferred way but may not be supported by the SSL module,
            # thus it has 'ca-bundle.pem'
            # as a fallback (which is generated from pem files in the
            # 'certs' directory):
            '/etc/ssl/ca-bundle.pem',
        ]
        for path in POSSIBLE_CA_BUNDLE_PATHS:
            if os.path.exists(path):
                return path
        return resource_filename(__name__, 'cacert.pem')
