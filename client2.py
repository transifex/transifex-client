# -*- coding: utf-8 -*-
#!/usr/bin/env python

# FIXME: move this to a separate file!
# There are placeholder args: the first is the hostname and the others are
# the corresponding params of the url
API_URLS = {
    'project_get' : '%s/api/project/%s/'
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
import getopt
import httplib
import os
import re
import shutil
import sys
import urllib2
from json import loads as parse_json, dumps as compile_json

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

        # The path to the configuration file (.tx/config)
        self.config_file = os.path.join(self.root, ".tx", "config")
        # Touch the file if it doesn't exist
        if not os.path.exists(self.config_file):
            print "Cannot find the configuration file (.tx/config)!"
            print "Run 'tx init' to fix this!"
            raise ProjectNotInit()

        # The dictionary which holds the configuration parameters after deser/tion.
        # Read the configuration in memory
        self.config = {}
        try:
            self.config = parse_json(open(self.config_file).read())
        except Exception, err:
            print "WARNING: Cannot open/parse .tx/config file", err
            print "Run 'tx init' to fix this!"
            raise ProjectNotInit()


    def create_resource(self):
        pass


    def validate_config(self):
        """
        To ensure the json structure is correctly formed.
        """
        pass

    def save(self):
        """
        Store the config dictionary in the .tx/config file of the project.
        """
        fh = open(self.config_file,"w")
        fh.write(compile_json(self.config, indent=4))
        fh.close()


def post_multipart(host, selector, fields, files):
    """
    Post a number of files to the server and return the output.
    """
    def encode_multipart_formdata(fields, files):
        LIMIT = '----------lImIt_of_THE_fIle_eW_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: application/octet-stream')
            L.append('')
            L.append(value)
        L.append('--' + LIMIT + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % LIMIT
        return content_type, body
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    buf = h.file.read()
    if errcode == 500:
        print buf
    return buf


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
    m = re.match("(?P<hostname>https?://(\w|\.|:)+)/projects/p/(?P<project>(\w|-)+)/", url)
    if m:
        hostname = m.group('hostname')
        project = m.group('project')
        print "Transifex instance:", hostname
        print "Project slug:", project
        return hostname, project
    else:
        print "tx: Malformed url given!"
        return None, None


def get_project_info(hostname, project_slug):
    """
    Get the tx project info through the API.
    
    This function can also be used to check the existence of a project.
    """
    url = API_URLS['project_get'] % (hostname, project_slug)
    try:
        fh = urllib2.urlopen(url)
        raw = fh.read()
        fh.close()
        remote_project = parse_json(raw)
        return remote_project
    except urllib2.HTTPError:
        print "tx: The given project does not exist."
        print "Check your url and try again."
    return None
#    remote_project = parse_json(raw)


def _cmd_get_source_file():
    pass


def _cmd_init(argv, path_to_tx=None):
    """
    Initialize the tx client folder. 
    
    The .tx folder is created by default to the CWD!
    """

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

    # The path to the txrc file (.tx/txrc)
    txrc = os.path.join(root, ".tx", "txrc")
    # Touch the file if it doesn't exist
    if not os.path.exists(txrc):
        print "Creating txrc file ..."
        open(txrc, 'w').close()
        print "Done."

    # The path to the configuration file (.tx/config)
    config_file = os.path.join(root, ".tx", "config")
    # Touch the file if it doesn't exist
    if not os.path.exists(config_file):
        print "Creating config file ..."
        open(config_file, 'w').close()
        print "Done."

    # Get the project slug
    project_url = raw_input("Please enter your tx project url here :")
    hostname, project_slug = parse_tx_url(project_url)
    while (not hostname and not project_slug):
        project_url = raw_input("Please enter your tx project url here :")
        hostname, project_slug = parse_tx_url(project_url)

    # Check the project existence
    project_info = get_project_info(hostname, project_slug)
    if not project_info:
        # Clean the old settings 
        # FIXME: take a backup
        rm_dir = os.path.join(root, ".tx")
        shutil.rmtree(rm_dir)
        return

    # Write the skeleton dictionary
    print "Creating skeleton ..."
    config = { 'resources': [],
               'meta': { 'project_name': project_info['name'],
                         'project_slug': project_info['slug'],
                         'last_push': None} 
             }
    fh = open(config_file,"w")
    fh.write(compile_json(config, indent=4))
    fh.close()
    print "Done."

def _cmd_push(argv, path_to_tx=None):
    pass


def _cmd_pull(argv, path_to_tx=None):
    pass


def _cmd_send_source_file(argv, path_to_tx=None):
    pass


def _cmd_set_source_file(argv, path_to_tx=None):
    """
    Point a source file to the configuration file.
    
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
    for r_entry in project.config['resources']:
        if r_entry['resource_name'] == resource:
            map_object = r_entry
            break

    print "Updating config file ..."
    if map_object:
        map_object['source_file'] = path_to_file
        map_object['source_lang'] = lang
    else:
        project.config['resources'].append({
              'resource_name': resource,
              'source_file': path_to_file,
              'source_lang': lang,
              'translations': {},
            })
    project.save()
    print "Done."

def _cmd_set_translation(argv, path_to_tx=None):
    """
    Create a ref for a translation file in the configuration file.
    
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
    for r_entry in project.config['resources']:
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

    print "Updating config file ..."
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
            global _debug
            _debug = 1
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
        raise
#        sys.exit()


# Run baby :) ... run
if __name__ == "__main__":
    # sys.argv[0] is the name of the script that we’re running.
    main(sys.argv[1:])
