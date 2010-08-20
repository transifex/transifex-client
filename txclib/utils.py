import os, sys, re
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
        MSG("Transifex instance:", hostname)
        MSG("Project slug:", project)
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


def traceback(self, exc=None):
    '''print exception traceback if traceback printing enabled.
    only to call in exception handler. returns true if traceback
    printed.'''
    import traceback
    if self.tracebackflag:
        if exc:
            traceback.print_exception(exc[0], exc[1], exc[2])
        else:
            traceback.print_exc()
