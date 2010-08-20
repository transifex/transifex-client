import os
import getpass
import shutil
import getopt
import ConfigParser
from json import loads as parse_json, dumps as compile_json

from txclib.utils import *
from txclib.project import *

def cmd_get_source_file():
    pass


def cmd_init(argv, path_to_tx=None):
    """
    Initialize the tx client folder. 
    
    The .tx folder is created by default to the CWD!
    """
    # Current working dir path
    root = os.getcwd()

    if path_to_tx:
        if not os.path.exists(path_to_tx):
            MSG("tx: The path to root directory does not exist!")
            return

        path = find_dot_tx(path_to_tx)
        if path:
            MSG("tx: There is already a tx folder!")
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
        MSG("Creating .tx folder ...")
        # FIXME: decide the mode of the directory
        os.mkdir(os.path.join(path_to_tx,".tx"))

    else:
        path = find_dot_tx(root)
        if path:
            MSG("tx: There is already a tx folder!")
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

        MSG("Creating .tx folder ...")
        # FIXME: decide the mode of the directory
        os.mkdir(os.path.join(os.getcwd(), ".tx"))

    # Handle the credentials through transifexrc
    home = os.getenv('USERPROFILE') or os.getenv('HOME')
    txrc = os.path.join(home, ".transifexrc")
    config = ConfigParser.RawConfigParser()
    # Touch the file if it doesn't exist
#    if not os.path.exists(txrc):
    username = raw_input("Please enter your transifex username :")
    while (not username):
        username = raw_input("Please enter your transifex username :")
    # FIXME: Temporary we use basic auth, till we switch to token
    passwd = ''
    while (not passwd):
        passwd = getpass.getpass()

    MSG("Creating .transifexrc file ...")
    config.add_section('API credentials')
    config.set('API credentials', 'username', username)
    config.set('API credentials', 'password', passwd)
    config.set('API credentials', 'token', '')

    # Writing our configuration file to 'example.cfg'
    fh = open(txrc, 'w')
    config.write(fh)
    fh.close()
#    else:
#        MSG("Read .transifexrc file ...")
#        # FIXME do some checks :)
#        config.read(txrc)
#        username = config.get('API credentials', 'username')
#        passwd = config.get('API credentials', 'password')
#        token = config.get('API credentials', 'token')


    # The path to the txdata file (.tx/txdata)
    txdata_file = os.path.join(root, ".tx", "txdata")
    # Touch the file if it doesn't exist
    if not os.path.exists(txdata_file):
        MSG("Creating txdata file ...")
        open(txdata_file, 'w').close()


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
    MSG("Creating skeleton ...")
    txdata = { 'resources': [],
               'meta': { 'root_dir': os.path.abspath(root),
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
    MSG("Done.")


def cmd_push(argv, path_to_tx=None):
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

    MSG("Done.")



def cmd_pull(argv, path_to_tx=None):

    # instantiate the Project
    project = Project()
    project.pull()

    MSG("Done.")


def cmd_send_source_file(argv, path_to_tx=None):
    pass


def cmd_set_source_file(argv, path_to_tx=None):
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
            if not valid_slug(arg):
                raise Exception("Valid characters for resource slugs are [-_\w]")
            resource = arg
        elif opt in ("-l", "--lang"):
            lang = arg

    if not resource:
        MSG("tx: Resource argument must be given, use -r|--resource")
        return
    elif not lang:
        MSG("tx: Language argument must be given, use -l|--lang")
        return

    # If no path provided show the usage and exit
    if len(args) != 1:
        usage()
        sys.exit(2)

    path_to_file = args[0]
    if not os.path.exists(path_to_file):
        MSG("tx: File does not exist.")
        return

    # instantiate the Project
    project = Project()
    root_dir = project.txdata['meta']['root_dir']

    if root_dir not in os.path.normpath(os.path.abspath(path_to_file)):
        MSG("File must be under the project root directory.")
        return

    # FIXME: Check also if the path to source file already exists.
    map_object = {}
    for r_entry in project.txdata['resources']:
        if r_entry['resource_slug'] == resource:
            map_object = r_entry
            break

    MSG("Updating txdata file ...")
    path_to_file = os.path.relpath(path_to_file, project.txdata['meta']['root_dir'])
    if map_object:
        map_object['source_file'] = path_to_file
        map_object['source_lang'] = lang
    else:
        project.txdata['resources'].append({
              'resource_slug': resource,
              'source_file': path_to_file,
              'source_lang': lang,
              'translations': {},
            })
    project.save()
    MSG("Done.")


def cmd_set_translation(argv, path_to_tx=None):
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
        MSG("tx: Resource argument must be given, use -r|--resource")
        return
    elif not lang:
        MSG("tx: Language argument must be given, use -l|--lang")
        return

    # If no path provided show the usage and exit
    if len(args) != 1:
        usage()
        sys.exit(2)

    path_to_file = args[0]
    if not os.path.exists(path_to_file):
        MSG("tx: File does not exist.")
        return

    # instantiate the Project
    project = Project()

    root_dir = project.txdata['meta']['root_dir']

    if root_dir not in os.path.normpath(os.path.abspath(path_to_file)):
        MSG("File must be under the project root directory.")
        return



    map_object = {}
    for r_entry in project.txdata['resources']:
        if r_entry['resource_slug'] == resource:
            map_object = r_entry
            break

    if not map_object:
        MSG("tx: You should first run 'set_source_file' to map the source file.")
        return

    if lang == map_object['source_lang']:
        MSG("tx: You cannot set translation file for the source language.")
        MSG("Source languages contain the strings which will be translated!")
        return

    MSG("Updating txdata file ...")
    path_to_file = os.path.relpath(path_to_file, root_dir)
    if map_object['translations'].has_key(lang):
        for key, value in map_object['translations'][lang].items():
            if value == path_to_file:
                MSG("tx: The file already exists in the specific resource.")
                return
        map_object['translations'][lang]['file'] = path_to_file
    else:
        # Create the language file list
        map_object['translations'][lang] = {'file' : path_to_file}
    project.save()
    MSG("Done.")


def cmd_status(argv, path_to_tx=None):
    pass
