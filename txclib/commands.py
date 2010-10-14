# -*- coding: utf-8 -*-
"""
In this file we have all the top level commands for the transifex client.
Since we're using a way to automatically list them and execute them, when
adding code to this file you must take care of the following:
 * Added functions must begin with 'cmd_' followed by the actual name of the
   command being used in the command line (eg cmd_init)
 * The description for each function that we display to the user is read from
   the func_doc attribute which reads the doc string. So, when adding
   docstring to a new function make sure you add an oneliner which is
   descriptive and is meant to be seen by the user.
 * When including libraries, it's best if you include modules instead of
   functions because that way our function resolution will work faster and the
   chances of overlapping are minimal
 * All functions should use the OptionParser and should have a usage and
   descripition field.
"""
import os
import getpass
import re, shutil
import sys
from optparse import OptionParser
import ConfigParser
from json import loads as parse_json, dumps as compile_json

from txclib import utils, project

def cmd_get_source_file(path_to_tx):
    "Download source file from transifex server"

    usage="usage: %prog [tx_options] get_source_file"
    description="Download source file from transifex server"
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify the resource for which you want to pull"
        " the translations (defaults to all)")
    (options, args) = parser.parse_args(argv)

    raise NotImplementedError


def cmd_init(argv, path_to_tx):
    "Initialize a new transifex project."

    # Current working dir path
    usage="usage: %prog [tx_options] init <path>"
    description="This command initializes a new project for use with"\
        " transifex. It is recommended to execute this command in the"\
        " top level directory of your project so that you can include"\
        " all files under it in transifex. If no path is provided, the"\
        " current working dir will be used."
    parser = OptionParser(usage=usage, description=description)
    (options, args) = parser.parse_args(argv)

    if len(args) > 1:
        parser.error("Too many arguments were provided. Aborting...")

    if args:
        path_to_tx = args[0]
    else:
        path_to_tx = os.getcwd()

    if os.path.isdir(os.path.join(path_to_tx,".tx")):
        utils.MSG("tx: There is already a tx folder!")
        reinit = raw_input("Do you want to delete it and reinit the project? [y/N]: ")
        while (reinit != 'y' and reinit != 'Y' and reinit != 'N' and reinit != 'n' and reinit != ''):
            reinit = raw_input("Do you want to delete it and reinit the project? [y/N]: ")
        if not reinit or reinit in ['N', 'n', 'NO', 'no', 'No']:
            return
        # Clean the old settings
        # FIXME: take a backup
        else:
            rm_dir = os.path.join(path_to_tx, ".tx")
            shutil.rmtree(rm_dir)

    utils.MSG("Creating .tx folder...")
    # FIXME: decide the mode of the directory
    os.mkdir(os.path.join(path_to_tx,".tx"))

    # Handle the credentials through transifexrc
    home = os.getenv('USERPROFILE') or os.getenv('HOME')
    txrc = os.path.join(home, ".transifexrc")
    config = ConfigParser.RawConfigParser()
    # Touch the file if it doesn't exist
    if not os.path.exists(txrc):
        username = raw_input("Please enter your transifex username: ")
        while (not username):
            username = raw_input("Please enter your transifex username: ")
        # FIXME: Temporary we use basic auth, till we switch to token
        passwd = ''
        while (not passwd):
            passwd = getpass.getpass()

        utils.MSG("Creating .transifexrc file...")
        config.add_section('API credentials')
        config.set('API credentials', 'username', username)
        config.set('API credentials', 'password', passwd)
        config.set('API credentials', 'token', '')

        # Writing our configuration file to 'example.cfg'
        fh = open(txrc, 'w')
        config.write(fh)
        fh.close()
    else:
        config.read(txrc)
        username = config.get('API credentials', 'username')
        passwd = config.get('API credentials', 'password')

    # The path to the txdata file (.tx/txdata)
    txdata_file = os.path.join(path_to_tx, ".tx", "txdata")
    # Touch the file if it doesn't exist
    if not os.path.exists(txdata_file):
        utils.MSG("Creating txdata file...")
        open(txdata_file, 'w').close()

    # Get the project slug
    project_url = raw_input("Please enter your tx project url here: ")
    hostname, project_slug = utils.parse_tx_url(project_url)
    while (not hostname and not project_slug):
        project_url = raw_input("Please enter your tx project url here: ")
        hostname, project_slug = utils.parse_tx_url(project_url)

    # Check the project existence
    project_info = project.get_project_info(hostname, username, passwd, project_slug)
    if not project_info:
        # Clean the old settings 
        # FIXME: take a backup
        rm_dir = os.path.join(path_to_tx, ".tx")
        shutil.rmtree(rm_dir)
        return

    # Write the skeleton dictionary
    utils.MSG("Creating skeleton...")
    txdata = { 'resources': [],
               'meta': { 'project_slug': project_info['slug'],
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


def cmd_push(argv, path_to_tx):
    "Push local files to remote server"
    usage="usage: %prog [tx_options] push [options]"
    description="This command pushes all local files that have been added to"\
        " Transifex to the remote server. All new translations are merged"\
        " with existing ones and if a language doesn't exists then it gets"\
        " created. If you want to push the source file as well (either"\
        " because this is your first time running the client or because"\
        " you just have updated with new entries), use the -f|--force option."\
        " By default, this command will push all files which are watched by"\
        " Transifex but you can filter this per resource or/and language."
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-l","--language", action="store", dest="languages",
        default=None, help="Specify which translations you want to pull"
        " (defaults to all)")
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=None, help="Specify the resource for which you want to pull"
        " the translations (defaults to all)")
    parser.add_option("-f","--force", action="store_true", dest="force_creation",
        default=False, help="Push source files along with translations. This"
        " can create remote resources.")
    parser.add_option("--skip", action="store_true", dest="skip_errors",
        default=False, help="Don't stop on errors. Useful when pushing many"
        " files concurrently.")
    (options, args) = parser.parse_args(argv)

    force_creation = options.force_creation

    languages = options.languages.split(',') if options.languages else []
    resources = options.resources.split(',') if options.resources else []


    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    prj.push(force_creation, resources, languages)

    utils.MSG("Done.")

def cmd_pull(argv, path_to_tx):
    "Pull files from remote server to local repository"
    usage="usage: %prog [tx_options] pull [options]"
    description="This command pulls all outstanding changes from the remote"\
        " Transifex server to the local repository. By default, only the"\
        " files that are watched by Transifex will be updated but if you"\
        " want to fetch the translations for new languages as well, use the"\
        " -a|--all option. (Note: new translations are saved in the .tx folder"\
        " and require the user to manually rename them and add then in "\
        " transifex using the set_translation command)."
    parser = OptionParser(usage=usage,description=description)
    parser.add_option("-l","--language", action="store", dest="languages",
        default=[], help="Specify which translations you want to pull"
        " (defaults to all)")
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify the resource for which you want to pull"
        " the translations (defaults to all)")
    parser.add_option("-a","--all", action="store_true", dest="fetchall",
        default=False, help="Fetch all translation files from server (even new"
        " ones)")
    parser.add_option("--disable-overwrite", action="store_false",
        dest="overwrite", default=True, 
        help="By default transifex will fetch new translations files and"\
            " replace existing ones. Use this flag if you want to disable"\
            " this feature")

    (options, args) = parser.parse_args(argv)

    if options.fetchall and options.languages:
        parser.error("You can't user a language filter along with the"\
            " -a|--all option")

    languages = options.languages.split(',') if options.languages else []
    resources = options.resources.split(',') if options.resources else []


    os.chdir(path_to_tx)
    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    prj.pull(languages, resources, options.overwrite, options.fetchall)
    prj.save()

    utils.MSG("Done.")


def cmd_send_source_file(argv, path_to_tx):
    "Upload source file to remote server"
    usage="usage: %prog [tx_options] send_source_file [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify the resources for which you want to push"
        " the source files (defaults to all)")

    (options, args) = parser.parse_args(argv)

    raise NotImplementedError


def _set_source_file(path_to_tx, resource, lang, path_to_file):
    """Reusable method to set source file."""

    # Chdir to the root dir
    os.chdir(path_to_tx)

    if not os.path.exists(path_to_file):
        utils.MSG("tx: File does not exist.")
        return

    # instantiate the project.Project
    prj = project.Project(path_to_tx)
    root_dir = os.path.abspath(path_to_tx)

    if root_dir not in os.path.normpath(os.path.abspath(path_to_file)):
        utils.MSG("File must be under the project root directory.")
        return

    # FIXME: Check also if the path to source file already exists.
    map_object = {}
    for r_entry in prj.txdata['resources']:
        if r_entry['resource_slug'] == resource:
            map_object = r_entry
            break

    path_to_file = os.path.relpath(path_to_file, root_dir)

    utils.MSG("Setting source file for resource %s ( %s -> %s )." % (
        resource, lang, path_to_file))
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


def cmd_set_source_file(argv, path_to_tx):
    "Assign a source file to a specific resource"

    usage="usage: %prog [tx_options] set_source_file [options] <file>"
    description="Assign a file as the source file of a specific resource"\
        " The source language for this file is considered to be English(en)"\
        " if no other is provided. These settings are kept in the local conf"\
        " file and are used to keep in sync the server with the repository."
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-l","--language", action="store", dest="slang",
        default="en", help="Source languages of the source file (defaults to 'en')")
    parser.add_option("-r","--resource", action="store", dest="resource_slug",
        default=None, help="Specify resource name")

    (options, args) = parser.parse_args(argv)

    if not options.resource_slug:
        parser.error("You must specify a resource using the -r|--resource"
            " option.")

    resource = options.resource_slug
    lang = options.slang

    if len(args) != 1:
        parser.error("Please specify a file")

    if not utils.valid_slug(resource):
        parser.error("Invalid characters in resource slug. Valid characters"
            " include [_-\w].")

    # Calculate relative path
    path_to_file = os.path.relpath(args[0], path_to_tx)
    _set_source_file(path_to_tx, resource, lang, path_to_file)
    utils.MSG("Done.")


def _set_translation(path_to_tx, resource, lang, path_to_file):
    """Reusable method to set translation file."""
    # instantiate the project.Project
    prj = project.Project(path_to_tx)

    root_dir = os.path.abspath(path_to_tx)

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


    utils.MSG("Updating resource %s ( %s -> %s )." % (
        resource, lang, path_to_file))
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
    

def cmd_set_translation(argv, path_to_tx):
    "Assign translation files to a resource"

    usage="usage: %prog [tx_options] set_translation [options] <file>"
    description="Assign a file as the translation file of a specific resource"\
        " in a given language. These info is stored in a configuration file"\
        " and is used for synchronization between the server and the local"\
        " repository"
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("-l","--language", action="store", dest="lang",
        default=None, help="Language of the translation file")
    parser.add_option("-r","--resource", action="store", dest="resource_slug",
        default=None, help="Specify resource name")
        
    (options, args) = parser.parse_args(argv)

    resource = options.resource_slug
    lang = options.lang

    if not resource or not lang:
        parser.error("You need to specify a resource and a language for the"
            " translation")

    if len(args) != 1:
        parser.error("Please specify a file")

    # Calculate relative path
    path_to_file = os.path.relpath(args[0], path_to_tx)
    # Chdir to the root dir
    os.chdir(path_to_tx)

    if not os.path.exists(path_to_file):
        utils.MSG("tx: File does not exist.")
        return

    _set_translation(path_to_tx, resource, lang, path_to_file)
    utils.MSG("Done.")


def cmd_auto_find(argv, path_to_tx):
    "Automatically identify translation files."

    """
    This command goes through all files in this directory and its
    subdirectories and tries to find matches to the expression given.
    
    The expression should contain '<lang>' to identify the language, or, if
    the --regex option is defined, should be a full regular expression.
     
    By default, the command will print `set_source_lang` and `set_translation`
    commands, which you can examine and run manually. If --execute is
    specified, the commands will be executed.
    """

    usage="usage: %prog [tx_options] auto_find -r <resource> -l <language> [options] '<expression>'"
    description=("Walk through all files in subdirectories for files matching "
        "<expression> and auto-associate them with a language. You may "
        "use the keyword '<lang>' in your expression to signify the language "
        "locale, for example: 'po/<lang>.po'. Alternatively, you may use a "
        "full-powered regular expression with --regex.")

    parser = OptionParser(usage=usage, description=description)
    # Mandatory
    parser.add_option("-r","--resource", action="store", dest="resource_slug",
        default=None, help="Specify resource name")
    # Optional
    parser.add_option("-e","--execute", action="store_true", dest="execute",
        default=False, help="Execute the commands instead of just printing them.")
    parser.add_option("-E","--regex", action="store_true", dest="regex",
        default=False, help="Set if the expression is a POSIX regex.")
    parser.add_option("-l","--language", action="store", dest="slang",
        default="en", help="The language of the source file (default: 'en')")
    parser.add_option("-n","--no-source", action="store_true", dest="nosource",
        default=False, help="Disable searching for a source file.")
    (options, args) = parser.parse_args(argv)

    resource = options.resource_slug
    source_language = options.slang
    execute = options.execute

    if not resource:
        parser.error("Please specify a resource.")
    if len(args) != 1:
        parser.error("Please specify an expression.")

    expr = args[0]
    expr_re = '.*%s.*' % expr
    if not options.regex:
        # Force expr to be a valid regex expr (escaped) but keep <lang> intact
        expr_re = re.escape(expr)
        expr_re = re.sub(r"\\<lang\\>", '<lang>', expr_re)
        expr_re = re.sub(r"<lang>", '(?P<lang>[^/]+)', '.*%s.*' % expr_re)
    expr_rec = re.compile(expr_re)

    # The path everything will be relative to
    curpath = '.'

    if not execute:
        utils.MSG("Only printing the commands which will be run if the "
                  "--execute switch is specified.")

    # First, let's construct a dictionary of all matching files.
    # Note: Only the last matching file of a language will be stored.
    source_file = None
    translation_files = {}
    for root, dirs, files in os.walk(curpath):
        for f in files:
            f_path = os.path.join(root, f)
            match = expr_rec.match(f_path)
            if match:
                lang = match.group('lang')
                if lang == source_language:
                    source_file = f_path
                else:
                    translation_files[lang] = f_path

    # The set_source_file commands needs to be handled first.
    # If source file search is enabled, go ahead and find it:
    if not options.nosource:
        if not source_file:
            parser.error(
"Could not find a source language file. Please run set_source_language\n"
"manually and then re-run this command with the --no-source switch")
    
        if execute:
            _set_source_file(path_to_tx, resource, source_language, source_file)
        else:
            utils.MSG('\ntx set_source_lang -r %(res)s -l %(lang)s %(file)s\n' % {
                'res': resource,
                'lang': source_language,
                'file': source_file})

    # Now let's handle the translation files.
    for (lang, f_path) in sorted(translation_files.items()):
        if execute:
            _set_translation(path_to_tx, resource, lang, f_path)
        else:
            utils.MSG('tx set_translation -r %(res)s -l %(lang)s %(file)s' % {
                'res': resource,
                'lang': lang,
                'file': f_path})
    utils.MSG("Done.")


def cmd_status(argv, path_to_tx):
    "Print status of current project"

    usage="usage: %prog [tx_options] status [options]"
    description="Prints the status of the current project by reading the"\
        " data in the configuration file."
    parser = OptionParser(usage=usage,description=description)
    parser.add_option("-r","--resource", action="store", dest="resources",
        default=[], help="Specify resources")

    (options, args) = parser.parse_args(argv)

    prj = project.Project(path_to_tx)

    resources = len(prj.txdata['resources'])
    for id, res in enumerate(prj.txdata['resources']):
        utils.MSG("%s -> %s (%s of %s)" % (prj.txdata['meta']['project_slug'],
            res['resource_slug'], id+1, resources))
        utils.MSG("Translation Files:")
        utils.MSG(" - %s: %s (%s)" % (utils.color_text(res['source_lang'], "RED"),
            res['source_file'], utils.color_text("source", "YELLOW")))
        for tr in sorted(res['translations'].keys()):
            perc = "pull needed"
            if res['translations'][tr].has_key('completed'):
                perc = "%s" % res['translations'][tr]['completed']
            utils.MSG(" - %s: %s [%s]" % (utils.color_text(tr, "RED"), res['translations'][tr]['file'],
                utils.color_text(perc,"GREEN")))

        utils.MSG("")

def cmd_help(argv, path_to_tx):
    "List all available commands"

    usage="usage: %prog help command"
    description="Lists all available commands in the transifex command"\
        " client. If a command is specified, the help page of the specific"\
        " command is displayed instead."

    parser = OptionParser(usage=usage, description=description)

    (options, args) = parser.parse_args(argv)

    if len(args) > 1:
        parser.error("Multiple arguments received. Exiting...")

    # Get all commands
    fns = utils.discover_commands()

    # Print help for specific command
    if len(args) == 1:
        try:
            fns[argv[0]](['--help'], path_to_tx)
        except KeyError:
            utils.ERRMSG("Command %s not found" % argv[0])
    # or print summary of all commands

    # the code below will only be executed if the KeyError exception is thrown
    # becuase in all other cases the function called with --help will exit
    # instead of return here
    keys = fns.keys()
    keys.sort()


    utils.MSG("Transifex command line client.\n")
    utils.MSG("Available commands are:")
    for key in keys:
        utils.MSG("  %-15s\t%s" % (key, fns[key].func_doc))


    utils.MSG("\nFor more information run %s command --help" % sys.argv[0])
