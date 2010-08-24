import os
import getpass
import shutil
from optparse import OptionParser
import ConfigParser
from json import loads as parse_json, dumps as compile_json

from txclib import utils, project

def cmd_get_source_file():
    """
    Fetch source file from remote server
    """

    usage="usage: %prog [tx_options] get_source_file"
    parser = OptionParser(usage=usage)
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify the resource for which you want to pull"
        " the translations (defaults to all)")
    (options, args) = parser.parse_args(argv)

    pass


def cmd_init(argv, path_to_tx=None):
    """
    Initialize the tx client folder. 
    
    The .tx folder is created by default to the CWD!
    """
    # Current working dir path
    root = os.getcwd()


    usage="usage: %prog [tx_options] init"
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args(argv)


    if path_to_tx:
        if not os.path.exists(path_to_tx):
            utils.MSG("tx: The path to root directory does not exist!")
            return

        path = path_to_tx or utils.find_dot_tx(path_to_tx)
        if path:
            utils.MSG("tx: There is already a tx folder!")
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
        utils.MSG("Creating .tx folder ...")
        # FIXME: decide the mode of the directory
        os.mkdir(os.path.join(path_to_tx,".tx"))

    else:
        path = path_to_tx or utils.find_dot_tx(root)
        if path:
            utils.MSG("tx: There is already a tx folder!")
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

        utils.MSG("Creating .tx folder ...")
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

    utils.MSG("Creating .transifexrc file ...")
    config.add_section('API credentials')
    config.set('API credentials', 'username', username)
    config.set('API credentials', 'password', passwd)
    config.set('API credentials', 'token', '')

    # Writing our configuration file to 'example.cfg'
    fh = open(txrc, 'w')
    config.write(fh)
    fh.close()
#    else:
#        utils.MSG("Read .transifexrc file ...")
#        # FIXME do some checks :)
#        config.read(txrc)
#        username = config.get('API credentials', 'username')
#        passwd = config.get('API credentials', 'password')
#        token = config.get('API credentials', 'token')


    # The path to the txdata file (.tx/txdata)
    txdata_file = os.path.join(root, ".tx", "txdata")
    # Touch the file if it doesn't exist
    if not os.path.exists(txdata_file):
        utils.MSG("Creating txdata file ...")
        open(txdata_file, 'w').close()


    # Get the project slug
    project_url = raw_input("Please enter your tx project url here :")
    hostname, project_slug = utils.parse_tx_url(project_url)
    while (not hostname and not project_slug):
        project_url = raw_input("Please enter your tx project url here :")
        hostname, project_slug = utils.parse_tx_url(project_url)

    # Check the project existence
    project_info = project.get_project_info(hostname, username, passwd, project_slug)
    if not project_info:
        # Clean the old settings 
        # FIXME: take a backup
        rm_dir = os.path.join(root, ".tx")
        shutil.rmtree(rm_dir)
        return

    # Write the skeleton dictionary
    utils.MSG("Creating skeleton ...")
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
    utils.MSG("Done.")


def cmd_push(argv, path_to_tx=None):
    """
    Push to the server all the local files included in the txdata json structure.
    """
    usage="usage: %prog [tx_options] push [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-l","--language", action="store", dest="languages",
        default=[], help="Specify which translations you want to pull"
        " (defaults to all)")
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify the resource for which you want to pull"
        " the translations (defaults to all)")
    parser.add_option("-f","--force", action="store_true", dest="force_creation",
        default=False, help="Push source files along with translations. This"
        " can create remote resources.")
    parser.add_option("--skip", action="store_true", dest="skip_errors",
        default=False, help="Don't stop on errors. Useful when pushing many"
        " files concurrently.")
    (options, args) = parser.parse_args(argv)

    force_creation = options.force_creation


    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    prj.push(force_creation)

    utils.MSG("Done.")



def cmd_pull(argv, path_to_tx=None):
    """
    Pull files from remote instance
    """
    usage="usage: %prog [tx_options] pull [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-l","--language", action="store", dest="languages",
        default=[], help="Specify which translations you want to pull"
        " (defaults to all)")
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify the resource for which you want to pull"
        " the translations (defaults to all)")
    parser.add_option("-a","--all", action="store_true", dest="fetchall",
        default=False, help="Fetch all translation files from server (even new"
        " ones)")

    (options, args) = parser.parse_args()

    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    prj.pull()

    utils.MSG("Done.")


def cmd_send_source_file(argv, path_to_tx=None):
    """
    Send source file to the server
    """
    usage="usage: %prog [tx_options] send_source_file [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify the resources for which you want to push"
        " the source files (defaults to all)")

    (options, args) = parser.parse_args()

    pass


def cmd_set_source_file(argv, path_to_tx=None):
    """
    Point a source file to the txdata file.
    
    This file will be committed to the server when the 'tx push' command will be
    called.
    """
    resource = None
    lang = None

    usage="usage: %prog [tx_options] set_source_file [options] <file>"
    parser = OptionParser(usage=usage)
    parser.add_option("-s","--source-language", action="store", dest="slang",
        default="en", help="Source languages of the source file (defaults to 'en')")
    parser.add_option("-r","--resource", action="store", dest="resource_slug",
        default=None, help="Specify resource name")

    (options, args) = parser.parse_args()

    if not options.resource_slug:
        parser.error("You must specify a resource using the -r|--resource"
            " option.")

    resource = options.resource_slug
    lang = options.slang

    if len(args) != 1:
        parser.error("Please specify a file")

    path_to_file = args[0]
    if not os.path.exists(path_to_file):
        utils.MSG("tx: File does not exist.")
        return

    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    root_dir = prj.txdata['meta']['root_dir']

    if root_dir not in os.path.normpath(os.path.abspath(path_to_file)):
        utils.MSG("File must be under the project root directory.")
        return

    # FIXME: Check also if the path to source file already exists.
    map_object = {}
    for r_entry in prj.txdata['resources']:
        if r_entry['resource_slug'] == resource:
            map_object = r_entry
            break

    utils.MSG("Updating txdata file ...")
    path_to_file = os.path.relpath(path_to_file, prj.txdata['meta']['root_dir'])
    if map_object:
        map_object['source_file'] = path_to_file
        map_object['source_lang'] = lang
    else:
        prj.txdata['resources'].append({
              'resource_slug': resource,
              'source_file': path_to_file,
              'source_lang': lang,
              'translations': {},
            })
    prj.save()
    utils.MSG("Done.")


def cmd_set_translation(argv, path_to_tx=None):
    """
    Create a ref for a translation file in the txdata file.
    
    This file will be committed to the server when the 'tx push' command will be
    called.
    """

    usage="usage: %prog [tx_options] set_source_file [options] <file>"
    parser = OptionParser(usage=usage)
    parser.add_option("-s","--source-language", action="store", dest="slang",
        default=None, help="Source languages of the source file (defaults to 'en')")
    parser.add_option("-r","--resource", action="store", dest="resource_slug",
        default=None, help="Specify resource name")

    (options, args) = parser.parse_args()

    resource = options.resource_slug
    lang = options.slang

    if not resource or lang:
        parser.error("You need to specify a resource and a language for the"
            " translation")

    if len(args) != 1:
        parser.error("Please specify a file")

    path_to_file = args[0]
    if not os.path.exists(path_to_file):
        utils.MSG("tx: File does not exist.")
        return

    # instantiate the project.Project
    prj = project.Project(path_to_tx)

    root_dir = prj.txdata['meta']['root_dir']

    if root_dir not in os.path.normpath(os.path.abspath(path_to_file)):
        utils.MSG("File must be under the project root directory.")
        return



    map_object = {}
    for r_entry in prj.txdata['resources']:
        if r_entry['resource_slug'] == resource:
            map_object = r_entry
            break

    if not map_object:
        utils.MSG("tx: You should first run 'set_source_file' to map the source file.")
        return

    if lang == map_object['source_lang']:
        utils.MSG("tx: You cannot set translation file for the source language.")
        utils.MSG("Source languages contain the strings which will be translated!")
        return

    utils.MSG("Updating txdata file ...")
    path_to_file = os.path.relpath(path_to_file, root_dir)
    if map_object['translations'].has_key(lang):
        for key, value in map_object['translations'][lang].items():
            if value == path_to_file:
                utils.MSG("tx: The file already exists in the specific resource.")
                return
        map_object['translations'][lang]['file'] = path_to_file
    else:
        # Create the language file list
        map_object['translations'][lang] = {'file' : path_to_file}
    prj.save()
    utils.MSG("Done.")


def cmd_status(argv, path_to_tx=None):
    """
    Print status for current project
    """
    usage="usage: %prog [tx_options] status [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify resources")

    (options, args) = parser.parse_args()

    pass
