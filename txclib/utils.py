from __future__ import unicode_literals
import os
import sys
import re
import errno
import ssl
import urllib3

try:
    from json import loads as parse_json, dumps as compile_json
except ImportError:
    from simplejson import loads as parse_json, dumps as compile_json

from email.parser import Parser
from urllib3.exceptions import SSLError
from urllib3.packages import six
from urllib3.packages.six.moves import input
from txclib.urls import API_URLS
from txclib.exceptions import UnknownCommandError
from txclib.paths import posix_path, native_path, posix_sep
from txclib.web import user_agent_identifier, certs_file
from txclib.log import logger


class HttpNotFound(Exception):
    pass


def get_base_dir():
    """PyInstaller Run-time Operation.

    http://pythonhosted.org/PyInstaller/#run-time-operation
    """
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        basedir = os.path.join(sys._MEIPASS, 'txclib')
    else:
        # we are running in a normal Python environment
        basedir = os.path.dirname(os.path.abspath(__file__))
    return basedir


def find_dot_tx(path=os.path.curdir, previous=None):
    """Return the path where .tx folder is found.

    The 'path' should be a DIRECTORY.
    This process is functioning recursively from the current directory to each
    one of the ancestors dirs.
    """
    path = os.path.abspath(path)
    if path == previous:
        return None
    joined = os.path.join(path, ".tx")
    if os.path.isdir(joined):
        return path
    else:
        return find_dot_tx(os.path.dirname(path), path)


#################################################
# Parse file filter expressions and create regex

def regex_from_filefilter(file_filter, root_path=os.path.curdir):
    """Create proper regex from <lang> expression."""
    # Force expr to be a valid regex expr (escaped) but keep <lang> intact
    expr_re = re.escape(
        posix_path(os.path.join(root_path, native_path(file_filter)))
    )
    expr_re = expr_re.replace("\\<lang\\>", '<lang>').replace(
        '<lang>', '([^%(sep)s]+)' % {'sep': re.escape(posix_sep)})

    return "^%s$" % expr_re


TX_URLS = {
    'resource': '(?P<hostname>https?://(\w|\.|:|-)+)/projects/p/(?P<project>(\w|-)+)/resource/(?P<resource>(\w|-)+)/?$',  # noqa
    'project': '(?P<hostname>https?://(\w|\.|:|-)+)/projects/p/(?P<project>(\w|-)+)/?$',  # noqa
}


def parse_tx_url(url):
    """
    Try to match given url to any of the valid url patterns specified in
    TX_URLS. If not match is found, we raise exception
    """
    for type_ in list(TX_URLS.keys()):
        pattern = TX_URLS[type_]
        m = re.match(pattern, url)
        if m:
            return type_, m.groupdict()
    raise Exception(
        "tx: Malformed url given."
        " Please refer to our docs: http://bit.ly/txcconfig"
    )


def determine_charset(response):
    content_type = response.headers.get('content-type', None)
    if content_type:
        message = Parser().parsestr("Content-type: %s" % content_type)
        for charset in message.get_charsets():
            if charset:
                return charset
    return "utf-8"


def make_request(method, host, url, username, password, fields=None,
                 skip_parse=False):
    charset = None
    if host.lower().startswith('https://'):
        connection = urllib3.connection_from_url(
            host,
            cert_reqs=ssl.CERT_REQUIRED,
            ca_certs=certs_file()
        )
    else:
        connection = urllib3.connection_from_url(host)
    headers = urllib3.util.make_headers(
        basic_auth='{0}:{1}'.format(username, password),
        accept_encoding=True,
        user_agent=user_agent_identifier(),
        keep_alive=True
    )
    r = None
    try:
        r = connection.request(method, url, headers=headers, fields=fields)
        data = r.data
        if not skip_parse:
            charset = determine_charset(r)
            if isinstance(data, bytes):
                data = data.decode(charset)
        if r.status < 200 or r.status >= 400:
            if r.status == 404:
                raise HttpNotFound(data)
            else:
                raise Exception(data)
        return data, charset
    except SSLError:
        logger.error("Invalid SSL certificate")
        raise
    finally:
        if r is not None:
            r.close()


def get_details(api_call, username, password, *args, **kwargs):
    """
    Get the tx project info through the API.

    This function can also be used to check the existence of a project.
    """
    url = API_URLS[api_call] % kwargs
    try:
        data, charset = make_request(
            'GET', kwargs['hostname'], url, username, password
        )
        return parse_json(data)
    except Exception as e:
        logger.debug(six.u(str(e)))
        raise


def valid_slug(slug):
    """
    Check if a slug contains only valid characters.

    Valid chars include [-_\w]
    """
    try:
        a, b = slug.split('.')
    except ValueError:
        return False
    else:
        if re.match("^[A-Za-z0-9_-]*$", a) and re.match("^[A-Za-z0-9_-]*$", b):
            return True
        return False


def discover_commands():
    """
    Inspect commands.py and find all available commands
    """
    import inspect
    from txclib import commands

    command_table = {}
    fns = inspect.getmembers(commands, inspect.isfunction)

    for name, fn in fns:
        if name.startswith("cmd_"):
            command_table.update({
                name.split("cmd_")[1]: fn
            })

    return command_table


def exec_command(command, *args, **kwargs):
    """
    Execute given command
    """
    commands = discover_commands()
    try:
        cmd_fn = commands[command]
    except KeyError:
        raise UnknownCommandError
    cmd_fn(*args, **kwargs)


def mkdir_p(path):
    try:
        if path:
            os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def confirm(prompt='Continue?', default=True):
    """
    Prompt the user for a Yes/No answer.

    Args:
        prompt: The text displayed to the user ([Y/n] will be appended)
        default: If the default value will be yes or no
    """
    valid_yes = ['Y', 'y', 'Yes', 'yes', ]
    valid_no = ['N', 'n', 'No', 'no', ]
    if default:
        prompt = prompt + '[Y/n]'
        valid_yes.append('')
    else:
        prompt = prompt + '[y/N]'
        valid_no.append('')

    ans = input(prompt)
    while (ans not in valid_yes and ans not in valid_no):
        ans = input(prompt)

    return ans in valid_yes


# Stuff for command line colored output

COLORS = [
    'BLACK', 'RED', 'GREEN', 'YELLOW',
    'BLUE', 'MAGENTA', 'CYAN', 'WHITE'
]

DISABLE_COLORS = False


def color_text(text, color_name, bold=False):
    """
    This command can be used to colorify command line output. If the shell
    doesn't support this or the --disable-colors options has been set, it just
    returns the plain text.

    Usage:
        print "%s" % color_text("This text is red", "RED")
    """
    if color_name in COLORS and not DISABLE_COLORS:
        return '\033[%s;%sm%s\033[0m' % (
            int(bold), COLORS.index(color_name) + 30, text)
    else:
        return text


def files_in_project(curpath):
    """
    Iterate over the files in the project.

    Return each file under ``curpath`` with its absolute name.
    """
    visited = set()
    for root, dirs, files in os.walk(curpath, followlinks=True):
        root_realpath = os.path.realpath(root)

        # Don't visit any subdirectory
        if root_realpath in visited:
            del dirs[:]
            continue

        for f in files:
            yield os.path.realpath(os.path.join(root, f))

        visited.add(root_realpath)

        # Find which directories are already visited and remove them from
        # further processing
        removals = list(
            d for d in dirs
            if os.path.realpath(os.path.join(root, d)) in visited
        )
        for removal in removals:
            dirs.remove(removal)
