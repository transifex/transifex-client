# -*- coding: utf-8 -*-
#!/usr/bin/env python

# FIXME: move this to a separate file!
# There are placeholder args: the first is the hostname and the others are
# the corresponding params of the url
API_URLS = {
    'project_get' : '%(hostname)s/api/project/%(project)s/',
    'get_resources': '%(hostname)s/api/project/%(project)s/resources/',
    'push_source': '%(hostname)s/api/storage/'  #'%(hostname)s/api/project/%(project)s/files/',
}


HELP = """
Transifex client application

usage: tx [--version] [-h|--help] [-d|--debug] [-p|--path_to_tx] COMMAND ARGS

COMMAND can be one of the following:

get_source_file   Fetch only the source file of a specific resource.
init              Create a local instance of a transifex project.
push              Update remote resources with the local file content.
pull              Fetch all files (source, translation) from server.
send_source_file  Update the source strings of a specific remote resource.
set_source_file   Assign a source file to a project resource locally.
set_translation   Assign a translation file to a project resource locally.
status            Show the current configuration status.


See 'tx help COMMAND' for more information on a specific command.
"""

DEBUG = False
AUTHENTICATION = 'HTTPAUTHBASIC'


import base64
import ConfigParser
import getpass
import getopt
import httplib
import os
import re
import shutil
import sys
import urllib2

from json import loads as parse_json, dumps as compile_json

from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers


reload(sys) # WTF? Otherwise setdefaultencoding doesn't work

# When we open file with f = codecs.open we specifi FROM what encoding to read
# This sets the encoding for the strings which are created with f.read()
sys.setdefaultencoding('utf-8')


class ProjectNotInit(Exception):
    pass


class Project():
    """
    Represents an association between the local and remote project instances.
    """

    def __init__(self):
        """
        Initialize the Project attributes.
        """
        # The path to the root of the project, where .tx lives!
        self.root = find_dot_tx()
        if not self.root:
            print "Cannot find any .tx directory!"
            print "Run 'tx init' to initialize your project first!"
            raise ProjectNotInit()

        # The path to the txdata file (.tx/txdata)
        self.txdata_file = os.path.join(self.root, ".tx", "txdata")
        # Touch the file if it doesn't exist
        if not os.path.exists(self.txdata_file):
            print "Cannot find the txdata file (.tx/txdata)!"
            print "Run 'tx init' to fix this!"
            raise ProjectNotInit()

        # The dictionary which holds the txdata parameters after deser/tion.
        # Read the txdata in memory
        self.txdata = {}
        try:
            self.txdata = parse_json(open(self.txdata_file).read())
        except Exception, err:
            print "WARNING: Cannot open/parse .tx/txdata file", err
            print "Run 'tx init' to fix this!"
            raise ProjectNotInit()


    def create_resource(self):
        pass


    def validate_txdata(self):
        """
        To ensure the json structure is correctly formed.
        """
        pass


    def save(self):
        """
        Store the txdata dictionary in the .tx/txdata file of the project.
        """
        fh = open(self.txdata_file,"w")
        fh.write(compile_json(self.txdata, indent=4))
        fh.close()


    def get_project_slug(self):
        return self.txdata['meta']['project_slug']


    def get_full_path(self, relpath):
        if relpath[0] == "/":
            return relpath
        else:
            return os.path.join(self.root, relpath)


    def push(self, force=False):
        """
        Push all the resources
        """

        raw = self.do_url_request('get_resources',
                                  project=self.get_project_slug())
        remote_resources = parse_json(raw)

        local_resources = self.txdata['resources']
        for remote_resource in remote_resources:
            name = remote_resource['name']
            for i, resource in enumerate(local_resources):
                if name in resource['resource_name'] :
                    del(local_resources[i])

        if local_resources != [] and not force:
            print "Following resources are not available on remote machine:", ", ".join([i['resource_name'] for i in local_resources])
            print "Use -f to force creation of new resources"
            exit(1)
        else:
            for resource in self.txdata['resources']:
                # Push source file
                print "Pushing source file %s" % resource['source_file']
                self.do_url_request('push_source', multipart=True,
                     files=[( "%s_%s" % (resource['resource_name'],
                                         resource['source_lang']),
                             self.get_full_path(resource['source_file']))],
                     project=self.get_project_slug())

                # Push translation files one by one
                for lang, f_obj in resource['translations'].iteritems():
                    print "Pushing %s to %s" % (lang, f_obj['file'])
                    self.do_url_request('push_source', multipart=True,
                         files=[( "%s_%s" % (resource['resource_name'],
                                             lang),
                                 self.get_full_path(f_obj['file']))],
                         project=self.get_project_slug())


    def do_url_request(self, api_call, multipart=False, data=None, files=[],
                       **kwargs):
        """
        Issues a url request.
        """
        # Read the credentials from the config file (.transifexrc)
        home = os.getenv('USERPROFILE') or os.getenv('HOME')
        txrc = os.path.join(home, ".transifexrc")
        config = ConfigParser.RawConfigParser()

        if not os.path.exists(txrc):
            print "Cannot find the ~/.transifexrc!"
            raise ProjectNotInit()

        # FIXME do some checks :)
        config.read(txrc)
        username = config.get('API credentials', 'username')
        passwd = config.get('API credentials', 'password')
        token = config.get('API credentials', 'token')
        hostname = config.get('API credentials', 'hostname')

        # Create the Url
        kwargs['hostname'] = hostname
        url = API_URLS[api_call] % kwargs

        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, hostname, username,passwd)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_manager)

        opener = None
        headers = None
        req = None
        if multipart:
            # Register the streaming http handlers with urllib2
            opener = register_openers()
            opener.add_handler(auth_handler)

            file_params = []
            # iterate through 2-tuples
            for f in files:
                file_params.append(MultipartParam.from_file(f[0], f[1]))
            # headers contains the necessary Content-Type and Content-Length
            # data is a generator object that yields the encoded parameters
            data, headers = multipart_encode(file_params)
            req = urllib2.Request(url=url, data=data, headers=headers)
            # FIXME: This is used till we have a fix from Chris.
            base64string = base64.encodestring('%s:%s' % (username, passwd))[:-1]
            authheader =  "Basic %s" % base64string
            req.add_header("Authorization", authheader)
        else:
            opener = urllib2.build_opener(auth_handler)
            urllib2.install_opener(opener)
            req = urllib2.Request(url=url, data=data)

        fh = urllib2.urlopen(req)
        raw = fh.read()
        fh.close()
        return raw


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
        print "Transifex instance:", hostname
        print "Project slug:", project
        return hostname, project
    else:
        print "tx: Malformed url given!"
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
        print "tx: The given project does not exist."
        print "Check your url and try again."
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


def _cmd_get_source_file():
    pass


def _cmd_init(argv, path_to_tx=None):
    """
    Initialize the tx client folder. 
    
    The .tx folder is created by default to the CWD!
    """
    # Current working dir path
    root = os.getcwd()

    if path_to_tx:
        if not os.path.exists(path_to_tx):
            print "tx: The path to root directory does not exist!"
            return

        path = find_dot_tx(path_to_tx)
        if path:
            print "tx: There is already a tx folder!"
            reinit = raw_input("Do you want to delete it and reinit the project? [y/N]:")
            while (reinit != 'y' and reinit != 'Y' and reinit != 'N' and reinit != 'n' and reinit != ''):
                reinit = raw_input("Do you want to delete it and reinit the project? [y/N]:")
            if not reinit or reinit == 'N':
                return
            # Clean the old settings
            # FIXME: take a backup
            else:
                rm_dir = os.path.join(path, ".tx")
                shutil.rmtree(rm_dir)

        root = path_to_tx
        print "Creating .tx folder ..."
        # FIXME: decide the mode of the directory
        os.mkdir(os.path.join(path_to_tx,".tx"))

    else:
        path = find_dot_tx(root)
        if path:
            print "tx: There is already a tx folder!"
            reinit = raw_input("Do you want to delete it and reinit the project? [y/N]:")
            while (reinit != 'y' and reinit != 'Y' and reinit != 'N' and reinit != 'n' and reinit != ''):
                reinit = raw_input("Do you want to delete it and reinit the project? [y/N]:")
            if not reinit or reinit == 'N':
                return
            # Clean the old settings 
            # FIXME: take a backup
            else:
                rm_dir = os.path.join(path, ".tx")
                shutil.rmtree(rm_dir)

        print "Creating .tx folder ..."
        # FIXME: decide the mode of the directory
        os.mkdir(os.path.join(os.getcwd(), ".tx"))
    print "Done."

    # Handle the credentials through transifexrc
    home = os.getenv('USERPROFILE') or os.getenv('HOME')
    txrc = os.path.join(home, ".transifexrc")
    config = ConfigParser.RawConfigParser()
    # Touch the file if it doesn't exist
    if not os.path.exists(txrc):
        username = raw_input("Please enter your transifex username :")
        while (not username):
            username = raw_input("Please enter your transifex username :")
        # FIXME: Temporary we use basic auth, till we switch to token
        passwd = ''
        while (not passwd):
            passwd = getpass.getpass()

        print "Creating .transifexrc file ..."
        config.add_section('API credentials')
        config.set('API credentials', 'username', username)
        config.set('API credentials', 'password', passwd)
        config.set('API credentials', 'token', '')

        # Writing our configuration file to 'example.cfg'
        fh = open(txrc, 'w')
        config.write(fh)
        fh.close()
    else:
        print "Read .transifexrc file ..."
        # FIXME do some checks :)
        config.read(txrc)
        username = config.get('API credentials', 'username')
        passwd = config.get('API credentials', 'password')
        token = config.get('API credentials', 'token')
    print "Done."


    # The path to the txdata file (.tx/txdata)
    txdata_file = os.path.join(root, ".tx", "txdata")
    # Touch the file if it doesn't exist
    if not os.path.exists(txdata_file):
        print "Creating txdata file ..."
        open(txdata_file, 'w').close()
        print "Done."

    # Get the project slug
    project_url = raw_input("Please enter your tx project url here :")
    hostname, project_slug = parse_tx_url(project_url)
    while (not hostname and not project_slug):
        project_url = raw_input("Please enter your tx project url here :")
        hostname, project_slug = parse_tx_url(project_url)

    # Check the project existence
    project_info = get_project_info(hostname, username, passwd, project_slug)
    if not project_info:
        # Clean the old settings 
        # FIXME: take a backup
        rm_dir = os.path.join(root, ".tx")
        shutil.rmtree(rm_dir)
        return

    # Write the skeleton dictionary
    print "Creating skeleton ..."
    txdata = { 'resources': [],
               'meta': { 'project_name': project_info['name'],
                         'project_slug': project_info['slug'],
                         'last_push': None} 
             }
    fh = open(txdata_file,"w")
    fh.write(compile_json(txdata, indent=4))
    fh.close()

    # Writing hostname for future usages
    config.read(txrc)
    config.set('API credentials', 'hostname', hostname)
    fh = open(txrc, 'w')
    config.write(fh)
    fh.close()
    print "Done."


def _cmd_push(argv, path_to_tx=None):
    """
    Push to the server all the local files included in the txdata json structure.
    """
    force_creation = False
    try:
        opts, args = getopt.getopt(argv, "f", ["force"])
    except getopt.GetoptError:
        usage('push')
        return
    for opt, arg in opts:
        if opt in ("-f", "--force"):
            force_creation = True


    # instantiate the Project
    project = Project()
    project.push(force_creation)

    print "Done."



def _cmd_pull(argv, path_to_tx=None):
    pass


def _cmd_send_source_file(argv, path_to_tx=None):
    pass


def _cmd_set_source_file(argv, path_to_tx=None):
    """
    Point a source file to the txdata file.
    
    This file will be committed to the server when the 'tx push' command will be
    called.
    """
    resource = None
    lang = None
    try:
        opts, args = getopt.getopt(argv, "r:l:", ["resource=", "lang="])
    except getopt.GetoptError:
        usage('set_source_file')
        return
    for opt, arg in opts:
        if opt in ("-r", "--resource"):
            resource = arg
        elif opt in ("-l", "--lang"):
            lang = arg

    if not resource:
        print "tx: Resource argument must be given, use -r|--resource"
        return
    elif not lang:
        print "tx: Language argument must be given, use -l|--lang"
        return

    # If no path provided show the usage and exit
    if len(args) != 1:
        usage()
        sys.exit(2)

    path_to_file = args[0]
    if not os.path.exists(path_to_file):
        print "tx: File does not exist."
        return

    # instantiate the Project
    project = Project()

    # FIXME: Check also if the path to source file already exists.
    map_object = {}
    for r_entry in project.txdata['resources']:
        if r_entry['resource_name'] == resource:
            map_object = r_entry
            break

    print "Updating txdata file ..."
    if map_object:
        map_object['source_file'] = path_to_file
        map_object['source_lang'] = lang
    else:
        project.txdata['resources'].append({
              'resource_name': resource,
              'source_file': path_to_file,
              'source_lang': lang,
              'translations': {},
            })
    project.save()
    print "Done."


def _cmd_set_translation(argv, path_to_tx=None):
    """
    Create a ref for a translation file in the txdata file.
    
    This file will be committed to the server when the 'tx push' command will be
    called.
    """
    resource = None
    lang = None
    try:
        opts, args = getopt.getopt(argv, "r:l:", ["resource=", "lang="])
    except getopt.GetoptError:
        usage('set_translation')
        return
    for opt, arg in opts:
        if opt in ("-r", "--resource"):
            resource = arg
        elif opt in ("-l", "--lang"):
            lang = arg

    if not resource:
        print "tx: Resource argument must be given, use -r|--resource"
        return
    elif not lang:
        print "tx: Language argument must be given, use -l|--lang"
        return

    # If no path provided show the usage and exit
    if len(args) != 1:
        usage()
        sys.exit(2)

    path_to_file = args[0]
    if not os.path.exists(path_to_file):
        print "tx: File does not exist."
        return

    # instantiate the Project
    project = Project()

    map_object = {}
    for r_entry in project.txdata['resources']:
        if r_entry['resource_name'] == resource:
            map_object = r_entry
            break

    if not map_object:
        print "tx: You should first run 'set_source_file' to map the source file."
        return

    if lang == map_object['source_lang']:
        print "tx: You cannot set translation file for the source language."
        print "Source languages contain the strings which will be translated!"
        return

    print "Updating txdata file ..."
    if map_object['translations'].has_key(lang):
        for key, value in map_object['translations'][lang].items():
            if value == path_to_file:
                print "tx: The file already exists in the specific resource."
                return
        map_object['translations'][lang]['file'] = path_to_file
    else:
        # Create the language file list
        map_object['translations'][lang] = {'file' : path_to_file}
    project.save()
    print "Done."


def _cmd_status(argv, path_to_tx=None):
    pass


def usage(cmd=None):
    """
    Explain the usage of the tx client commands.
    """
    # TODO: Implement all the command specific documentation.
    print HELP


def main(argv):
    """
    Here we parse the flags (short, long) and we instantiate the classes.
    """
    DEBUG = False
    path_to_tx = None
    extra_opts = []
    try:
        opts, args = getopt.getopt(argv, "vhd",
            ["version", "help", "debug", "path_to_tx="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-v", "--version"):
            print "Transifex Client Version 0.1"
            sys.exit()
        elif opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-d", "--debug"):
            DEBUG = True
        elif opt in ("--path_to_tx"):
            path_to_tx = arg

    # If no commands provided show the usage and exit
    if len(args) == 0:
        usage()
        sys.exit(2)

    cmd = args[0]
    print "Command : %s" % cmd
    try:
        if cmd == 'get_source_file':
            _cmd_get_source_file(args[1:], path_to_tx)
        elif cmd == 'init':
            _cmd_init(args[1:], path_to_tx)
        elif cmd == 'push':
            _cmd_push(args[1:], path_to_tx)
        elif cmd == 'pull':
            _cmd_pull(args[1:], path_to_tx)
        elif cmd == 'send_source_file':
            _cmd_send_source_file(args[1:], path_to_tx)
        elif cmd == 'set_source_file':
            _cmd_set_source_file(args[1:], path_to_tx)
        elif cmd == 'set_translation':
            _cmd_set_translation(args[1:], path_to_tx)
        elif cmd == 'status':
            _cmd_status(args[1:], path_to_tx)
        else:
            print "tx: '%s' is not a tx-command. See 'tx --help'." % cmd
            sys.exit(2)
    except:
        if DEBUG:
            raise
        sys.exit()


# Run baby :) ... run
if __name__ == "__main__":
    # sys.argv[0] is the name of the script that we’re running.
    main(sys.argv[1:])
