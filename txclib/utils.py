import os, sys, re, errno
try:
    from json import loads as parse_json, dumps as compile_json
except ImportError:
    from simplejson import loads as parse_json, dumps as compile_json
import urllib2 # This should go and instead use do_url_request everywhere

from urls import API_URLS

# This is a mapping between i18n types supported on Transifex and related file
# extensions of the translation files.
FILE_EXTENSIONS = {
    'PO': 'po',
    'QT': 'ts',
}

def MSG(msg, verbose=1):
    """
    STDOUT logging function
    """
    if verbose:
        sys.stdout.write('%s\n' % msg)

def ERRMSG(msg, verbosity=1):
    """
    STDERR logging function
    """
    sys.stderr.write('%s\n' % msg)

def find_dot_tx(path = os.path.curdir, previous = None):
    """
    Return the path where .tx folder is found.

    The 'path' should be a DIRECTORY.
    This process is functioning recursively from the current directory to each 
    one of the ancestors dirs.
    """
    if path == previous:
        return None
    joined = os.path.join(path, ".tx")
    if os.path.isdir(joined):
        return path
    else:
        return find_dot_tx(os.path.dirname(path), path)


TX_URLS = {
    'resource': '(?P<hostname>https?://(\w|\.|:)+)/projects/p/(?P<project>(\w|-)+)/resource/(?P<resource>(\w|-)+)/?$',
    'release': '(?P<hostname>https?://(\w|\.|:)+)/projects/p/(?P<project>(\w|-)+)/r/(?P<release>(\w|-)+)/?$',
    'project': '(?P<hostname>https?://(\w|\.|:)+)/projects/p/(?P<project>(\w|-)+)/?$',
}

def parse_tx_url(url):
    """
    Try to match given url to any of the valid url patterns specified in
    TX_URLS. If not match is found, we raise exception
    """
    for type in TX_URLS.keys():
        pattern = TX_URLS[type]
        m = re.match(pattern, url)
        if m:
            return type, m.groupdict()

    raise Exception("tx: Malformed url given!")

def get_release_details(hostname, username, passwd, project_slug, release_slug):
    """
    Get remote release info through the API
    """
    url = API_URLS['release_details'] % {'hostname': hostname,
        'project': project_slug, 'release': release_slug}
    opener = get_opener(hostname, username, passwd)
    urllib2.install_opener(opener)
    req = urllib2.Request(url=url)
    try:
        fh = urllib2.urlopen(req)
        raw = fh.read()
        fh.close()
        remote_project = parse_json(raw)
    except urllib2.HTTPError:
        raise Exception("tx: The given release does not exist.")

    return remote_project

def get_resource_details(hostname, username, passwd, project_slug, resource_slug):
    """
    Get remote resource info through the API
    """
    url = API_URLS['resource_details'] % {'hostname': hostname,
        'project': project_slug, 'resource': resource_slug}
    opener = get_opener(hostname, username, passwd)
    urllib2.install_opener(opener)
    req = urllib2.Request(url=url)
    try:
        fh = urllib2.urlopen(req)
        raw = fh.read()
        fh.close()
        remote_project = parse_json(raw)
    except urllib2.HTTPError:
        raise Exception("tx: The given resource does not exist.")

    return remote_project

def get_project_details(hostname, username, passwd, project_slug):
    """
    Get the tx project info through the API.

    This function can also be used to check the existence of a project.
    """
    url = API_URLS['project_details'] % {'hostname':hostname, 'project':project_slug}
    opener = get_opener(hostname, username, passwd)
    urllib2.install_opener(opener)
    req = urllib2.Request(url=url)
    try:
        fh = urllib2.urlopen(req)
        raw = fh.read()
        fh.close()
        remote_project = parse_json(raw)
    except urllib2.HTTPError:
        raise Exception("tx: The given project does not exist.")
    except urllib2.URLError, e:
        error = e.args[0]
        raise Exception("%s" % error[1])

    return remote_project


def get_opener(host, username, passwd):
    """
    Return an auth opener to use with the urlopen requests.
    """
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, host, username,passwd)
    auth_handler = urllib2.HTTPBasicAuthHandler(password_manager)
    opener = urllib2.build_opener(auth_handler)
    return opener


def valid_slug(slug):
    """
    Check if a slug contains only valid characters.

    Valid chars include [-_\w]
    """
    if re.match("^[A-Za-z0-9_-]*$", slug):
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
                name.split("cmd_")[1]:fn
            })

    return command_table

def exec_command(command, *args, **kwargs):
    """
    Execute given command
    """
    commands = discover_commands()
    commands[command](*args,**kwargs)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError, exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise



# Stuff for command line colored output

COLORS = (
    'BLACK', 'RED', 'GREEN', 'YELLOW',
    'BLUE', 'MAGENTA', 'CYAN', 'WHITE'
)

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
        return '\033[{0};{1}m{2}\033[0m'.format(
            int(bold), COLORS.index(color_name) + 30, text)
    else:
        return text
