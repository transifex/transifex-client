import os, sys, re, errno
from json import loads as parse_json, dumps as compile_json
import urllib2 # This should go and instead use do_url_request everywhere

from urls import API_URLS

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
    sys.stderr.write('--> ERROR: %s\n' % msg)

def find_dot_tx(path = os.getcwd()):
    """
    Return the path where .tx folder is found.
    
    The 'path' should be a DIRECTORY.
    This process is functioning recursively from the current directory to each 
    one of the ancestors dirs.
    """
    if path == "/":
        return None
    joined = os.path.join(path, ".tx")
    if os.path.isdir(joined):
        return path
    else:
        return find_dot_tx(os.path.dirname(path))

def parse_tx_url(url):
    m = re.match("(?P<hostname>https?://(\w|\.|:)+)/projects/p/(?P<project>(\w|-)+)/?", url)
    if m:
        hostname = m.group('hostname')
        project = m.group('project')
        MSG("Transifex instance: %s" % hostname)
        MSG("Project slug: %s" % project)
        return hostname, project
    else:
        MSG("tx: Malformed url given!")
        return None, None


def get_project_info(hostname, username, passwd, project_slug):
    """
    Get the tx project info through the API.
    
    This function can also be used to check the existence of a project.
    """
    url = API_URLS['project_get'] % {'hostname':hostname, 'project':project_slug}
    opener = get_opener(hostname, username, passwd)
    urllib2.install_opener(opener)
    req = urllib2.Request(url=url)
    try:
        fh = urllib2.urlopen(req)
        raw = fh.read()
        fh.close()
        remote_project = parse_json(raw)
        return remote_project
    except urllib2.HTTPError:
        raise
        MSG("tx: The given project does not exist.")
        MSG("Check your url and try again.")
    return None
#    remote_project = parse_json(raw)


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
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

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
