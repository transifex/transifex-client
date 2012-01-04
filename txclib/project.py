# -*- coding: utf-8 -*-
import base64
import copy
import getpass
import os
import re
import fnmatch
import urllib2
import datetime, time
import ConfigParser

from txclib.web import *
from txclib.utils import *
from txclib.urls import API_URLS
from txclib.config import OrderedRawConfigParser, Flipdict
from txclib.log import logger


class ProjectNotInit(Exception):
    pass


class Project(object):
    """
    Represents an association between the local and remote project instances.
    """

    def __init__(self, path_to_tx=None, init=True):
        """
        Initialize the Project attributes.
        """
        if init:
            self._init(path_to_tx)

    def _init(self, path_to_tx=None):
        # The path to the root of the project, where .tx lives!
        self.root = path_to_tx or find_dot_tx()
        logger.debug("Path to tx is %s." % self.root)
        if not self.root:
            MSG("Cannot find any .tx directory!")
            MSG("Run 'tx init' to initialize your project first!")
            raise ProjectNotInit()

        # The path to the config file (.tx/config)
        self.config_file = os.path.join(self.root, ".tx", "config")
        logger.debug("Config file is %s" % self.config_file)
        # Touch the file if it doesn't exist
        if not os.path.exists(self.config_file):
            MSG("Cannot find the config file (.tx/config)!")
            MSG("Run 'tx init' to fix this!")
            raise ProjectNotInit()

        # The dictionary which holds the config parameters after deser/tion.
        # Read the config in memory
        self.config = OrderedRawConfigParser()
        try:
            self.config.read(self.config_file)
        except Exception, err:
            MSG("WARNING: Cannot open/parse .tx/config file", err)
            MSG("Run 'tx init' to fix this!")
            raise ProjectNotInit()


        home = os.path.expanduser("~")
        self.txrc_file = os.path.join(home, ".transifexrc")
        logger.debug(".transifexrc file is at %s" % home)
        if not os.path.exists(self.txrc_file):
            MSG("No configuration file found.")
            # Writing global configuration file
            mask = os.umask(077)
            open(self.txrc_file, 'w').close()
            os.umask(mask)

        self.txrc = OrderedRawConfigParser()
        try:
            self.txrc.read(self.txrc_file)
        except Exception, err:
            MSG("WARNING: Cannot global conf file (%s)" %  err)
            MSG("Run 'tx init' to fix this!")
            raise ProjectNotInit()


    def create_resource(self):
        pass


    def validate_config(self):
        """
        To ensure the json structure is correctly formed.
        """
        pass

    def getset_host_credentials(self, host, user=None, password=None):
        """
        Read .transifexrc and report user,pass for a specific host else ask the
        user for input.
        """
        try:
            username = self.txrc.get(host, 'username')
            passwd = self.txrc.get(host, 'password')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            MSG("No entry found for host %s. Creating..." % host)
            username = user or raw_input("Please enter your transifex username: ")
            while (not username):
                username = raw_input("Please enter your transifex username: ")
            passwd = password
            while (not passwd):
                passwd = getpass.getpass()

            MSG("Updating %s file..." % self.txrc_file)
            self.txrc.add_section(host)
            self.txrc.set(host, 'username', username)
            self.txrc.set(host, 'password', passwd)
            self.txrc.set(host, 'token', '')
            self.txrc.set(host, 'hostname', host)

        return username, passwd

    def set_remote_resource(self, resource, source_lang, i18n_type, host,
            file_filter="translations<sep>%(proj)s.%(res)s<sep><lang>.%(extension)s"):
        """
        Method to handle the add/conf of a remote resource.
        """
        if not self.config.has_section(resource):
            self.config.add_section(resource)

        p_slug, r_slug = resource.split('.')
        file_filter = file_filter.replace("<sep>", r"%s" % os.path.sep)
        self.url_info = {
            'host': host,
            'project': p_slug,
            'resource': r_slug
        }
        extension = self._extension_for(i18n_type)[1:]

        self.config.set(resource, 'source_lang', source_lang)
        self.config.set(
            resource, 'file_filter',
            file_filter % {'proj': p_slug, 'res': r_slug, 'extension': extension}
        )
        if host != self.config.get('main', 'host'):
            self.config.set(resource, 'host', host)

    def get_resource_host(self, resource):
        """
        Returns the host that the resource is configured to use. If there is no
        such option we return the default one
        """
        if self.config.has_option(resource, 'host'):
            return self.config.get(resource, 'host')
        return self.config.get('main', 'host')

    def get_resource_lang_mapping(self, resource):
        """
        Get language mappings for a specific resource.
        """
        lang_map = Flipdict()
        try:
            args = self.config.get("main", "lang_map")
            for arg in args.replace(' ', '').split(','):
                k,v = arg.split(":")
                lang_map.update({k:v})
        except ConfigParser.NoOptionError:
            pass
        except (ValueError, KeyError):
            raise Exception("Your lang map configuration is not correct.")

        if self.config.has_section(resource):
            res_lang_map = Flipdict()
            try:
                args = self.config.get(resource, "lang_map")
                for arg in args.replace(' ', '').split(','):
                    k,v = arg.split(":")
                    res_lang_map.update({k:v})
            except ConfigParser.NoOptionError:
                pass
            except (ValueError, KeyError):
                raise Exception("Your lang map configuration is not correct.")

        # merge the lang maps and return result
        lang_map.update(res_lang_map)

        return lang_map


    def get_resource_files(self, resource):
        """
        Get a dict for all files assigned to a resource. First we calculate the
        files matching the file expression and then we apply all translation
        excpetions. The resulting dict will be in this format:

        { 'en': 'path/foo/en/bar.po', 'de': 'path/foo/de/bar.po', 'es': 'path/exceptions/es.po'}

        NOTE: All paths are relative to the root of the project
        """
        tr_files = {}
        if self.config.has_section(resource):
            try:
                file_filter = self.config.get(resource, "file_filter")
            except ConfigParser.NoOptionError:
                file_filter = "$^"
            source_lang = self.config.get(resource, "source_lang")
            source_file = self.get_resource_option(resource, 'source_file') or None
            expr_re = regex_from_filefilter(file_filter, self.root)
            expr_rec = re.compile(expr_re)
            for root, dirs, files in os.walk(self.root):
                for f in files:
                    f_path = os.path.abspath(os.path.join(root, f))
                    match = expr_rec.match(f_path)
                    if match:
                        lang = match.group(1)
                        if lang != source_lang:
                            f_path = relpath(f_path, self.root)
                            if f_path != source_file:
                                tr_files.update({lang: f_path})

            for (name, value) in self.config.items(resource):
                if name.startswith("trans."):
                    lang = name.split('.')[1]
                    # delete language which has same file
                    if value in tr_files.values():
                        keys = []
                        for k, v in tr_files.iteritems():
                            if v == value:
                                keys.append(k)
                        if len(keys) == 1:
                            del tr_files[keys[0]]
                        else:
                            raise Exception("Your configuration seems wrong."\
                                " You have multiple languages pointing to"\
                                " the same file.")
                    # Add language with correct file
                    tr_files.update({lang:value})

            return tr_files

        return None

    def get_resource_option(self, resource, option):
        """
        Return the requested option for a specific resource

        If there is no such option, we return None
        """

        if self.config.has_section(resource):
            if self.config.has_option(resource, option):
                return self.config.get(resource, option)
        return None

    def get_resource_list(self, project=None):
        """
        Parse config file and return tuples with the following format

        [ (project_slug, resource_slug), (..., ...)]
        """

        resource_list= []
        for r in self.config.sections():
            if r == 'main':
                continue
            p_slug, r_slug = r.split('.', 1)
            if project and p_slug != project:
                continue
            resource_list.append(r)

        return resource_list

    def save(self):
        """
        Store the config dictionary in the .tx/config file of the project.
        """
        fh = open(self.config_file,"w")
        self.config.write(fh)
        fh.close()

        # Writing global configuration file
        mask = os.umask(077)
        fh = open(self.txrc_file, 'w')
        self.txrc.write(fh)
        fh.close()
        os.umask(mask)

    def get_full_path(self, relpath):
        if relpath[0] == "/":
            return relpath
        else:
            return os.path.join(self.root, relpath)

    def pull(self, languages=[], resources=[], overwrite=True, fetchall=False,
        fetchsource=False, force=False, skip=False, minimum_perc=0):
        """
        Pull all translations file from transifex server
        """
        self.minimum_perc = minimum_perc
        resource_list = self.get_chosen_resources(resources)

        for resource in resource_list:
            logger.debug("Handling resource %s" % resource)
            self.resource = resource
            project_slug, resource_slug = resource.split('.')
            files = self.get_resource_files(resource)
            slang = self.get_resource_option(resource, 'source_lang')
            sfile = self.get_resource_option(resource, 'source_file')
            lang_map = self.get_resource_lang_mapping(resource)
            host = self.get_resource_host(resource)
            logger.debug("Language mapping is: %s" % lang_map)
            self.url_info = {
                'host': host,
                'project': project_slug,
                'resource': resource_slug
            }
            logger.debug("URL data are: %s" % self.url_info)

            stats = self._get_stats_for_resource()

            try:
                file_filter = self.config.get(resource, 'file_filter')
            except ConfigParser.NoOptionError:
                file_filter = None

            # Pull source file
            pull_languages = set([])
            new_translations = set([])

            if fetchall:
                new_translations = self._new_translations_to_add(
                    files, slang, lang_map, stats, force
                )
                if new_translations:
                    MSG("New translations found for the following languages: %s" %
                        ', '.join(new_translations))

            existing, new = self._languages_to_pull(
                languages, files, lang_map, stats, force
            )
            pull_languages |= existing
            new_translations |= new
            logger.debug("Adding to new translations: %s" % new)

            if fetchsource:
                if sfile and slang not in pull_languages:
                    pull_languages.add(slang)
                elif slang not in new_translations:
                    new_translations.add(slang)

            if pull_languages:
                logger.debug("Pulling languages for: %s" % pull_languages)
                MSG("Pulling translations for resource %s (source: %s)" %
                    (resource, sfile))

            for lang in pull_languages:
                local_lang = lang
                if lang in lang_map.values():
                    remote_lang = lang_map.flip[lang]
                else:
                    remote_lang = lang
                if languages and lang not in pull_languages:
                    logger.debug("Skipping language %s" % lang)
                    continue
                if lang != slang:
                    local_file = files.get(lang, None) or files[lang_map[lang]]
                else:
                    local_file = sfile
                logger.debug("Using file %s" % local_file)

                kwargs = {
                    'lang': remote_lang,
                    'stats': stats,
                    'local_file': local_file,
                    'force': force,
                }
                if not self._should_update_translation(**kwargs):
                    msg = "Skipping '%s' translation (file: %s)."
                    MSG(msg % (color_text(remote_lang, "RED"), local_file))
                    continue

                if not overwrite:
                    local_file = ("%s.new" % local_file)
                MSG(" -> %s: %s" % (color_text(remote_lang,"RED"), local_file))
                try:
                    r = self.do_url_request('pull_file', language=remote_lang)
                except Exception,e:
                    if not skip:
                        raise e
                    else:
                        ERRMSG(e)
                        continue
                base_dir = os.path.split(local_file)[0]
                mkdir_p(base_dir)
                fd = open(local_file, 'wb')
                fd.write(r)
                fd.close()

            if new_translations:
                MSG("Pulling new translations for resource %s (source: %s)" %
                (resource, sfile))
                for lang in new_translations:
                    if lang in lang_map.keys():
                        local_lang = lang_map[lang]
                    else:
                        local_lang = lang
                    remote_lang = lang
                    if file_filter:
                        local_file = relpath(os.path.join(self.root,
                            file_filter.replace('<lang>', local_lang)), os.curdir)
                    else:
                        trans_dir = os.path.join(self.root, ".tx", resource)
                        if not os.path.exists(trans_dir):
                            os.mkdir(trans_dir)
                        local_file = relpath(os.path.join(trans_dir, '%s_translation' %
                            local_lang, os.curdir))

                    MSG(" -> %s: %s" % (color_text(remote_lang, "RED"), local_file))
                    r = self.do_url_request('pull_file', language=remote_lang)

                    base_dir = os.path.split(local_file)[0]
                    mkdir_p(base_dir)
                    fd = open(local_file, 'wb')
                    fd.write(r)
                    fd.close()

    def push(self, source=False, translations=False, force=False, resources=[], languages=[],
        skip=False, no_interactive=False):
        """
        Push all the resources
        """
        resource_list = self.get_chosen_resources(resources)
        for resource in resource_list:
            push_languages = []
            project_slug, resource_slug = resource.split('.')
            files = self.get_resource_files(resource)
            slang = self.get_resource_option(resource, 'source_lang')
            sfile = self.get_resource_option(resource, 'source_file')
            lang_map = self.get_resource_lang_mapping(resource)
            host = self.get_resource_host(resource)
            logger.debug("Language mapping is: %s" % lang_map)
            logger.debug("Using host %s" % host)
            self.url_info = {
                'host': host,
                'project': project_slug,
                'resource': resource_slug
            }

            MSG("Pushing translations for resource %s:" % resource)

            stats = self._get_stats_for_resource()

            if force and not no_interactive:
                answer = raw_input("Warning: By using --force, the uploaded"
                    " files will overwrite remote translations, even if they"
                    " are newer than your uploaded files.\nAre you sure you"
                    " want to continue? [y/N] ")

                if not answer in ["", 'Y', 'y', "yes", 'YES']:
                    return

            if source:
                if sfile == None:
                    ERRMSG("You don't seem to have a proper source file"
                        " mapping for resource %s. Try without the --source"
                        " option or set a source file first and then try again." %
                        resource)
                    continue
                # Push source file
                try:
                    MSG("Pushing source file (%s)" % sfile)
                    if not self._resource_exists(stats):
                        logger.info("Resource does not exist.  Creating...")
                        fileinfo = "%s;%s" % (resource_slug, slang)
                        filename = self.get_full_path(sfile)
                        self._create_resource(resource, project_slug, fileinfo, filename)
                    self.do_url_request(
                        'push_source', multipart=True, method="PUT",
                        files=[(
                                "%s;%s" % (resource_slug, slang)
                                , self.get_full_path(sfile)
                        )],
                    )
                except Exception, e:
                    if not skip:
                        raise e
                    else:
                        ERRMSG(e)
            else:
                try:
                    self.do_url_request('resource_details')
                except Exception, e:
                    code = getattr(e, 'code', None)
                    if code == 404:
                        msg = "Resource %s doesn't exist on the server."
                        logger.error(msg % resource)
                        continue

            if translations:
                # Check if given language codes exist
                if not languages:
                    push_languages = files.keys()
                else:
                    push_languages = []
                    f_langs = files.keys()
                    for l in languages:
                        if l in lang_map.keys():
                            l = lang_map[l]
                        push_languages.append(l)
                        if l not in f_langs:
                            ERRMSG("Warning: No mapping found for language code '%s'." %
                                color_text(l,"RED"))
                logger.debug("Languages to push are %s" % push_languages)

                # Push translation files one by one
                for lang in push_languages:
                    local_lang = lang
                    if lang in lang_map.values():
                        remote_lang = lang_map.flip[lang]
                    else:
                        remote_lang = lang

                    local_file = files[local_lang]

                    kwargs = {
                        'lang': remote_lang,
                        'stats': stats,
                        'local_file': local_file,
                        'force': force,
                    }
                    if not self._should_push_translation(**kwargs):
                        msg = "Skipping '%s' translation (file: %s)."
                        MSG(msg % (color_text(lang, "RED"), local_file))
                        continue

                    MSG("Pushing '%s' translations (file: %s)" % (color_text(remote_lang, "RED"), local_file))
                    try:
                        self.do_url_request(
                            'push_translation', multipart=True, method='PUT',
                            files=[(
                                    "%s;%s" % (resource_slug, remote_lang),
                                    self.get_full_path(local_file)
                            )], language=remote_lang
                        )
                        logger.debug("Translation %s pushed." % remote_lang)
                    except Exception, e:
                        if not skip:
                            raise e
                        else:
                            ERRMSG(e)

    def delete(self, resources=[], languages=[], skip=False, force=False):
        """Delete translations."""
        resource_list = self.get_chosen_resources(resources)
        for resource in resource_list:
            delete_languages = []
            files = self.get_resource_files(resource)
            project_slug, resource_slug = resource.split('.')
            lang_map = self.get_resource_lang_mapping(resource)
            host = self.get_resource_host(resource)

            self.url_info = {
                'host': host,
                'project': project_slug,
                'resource': resource_slug
            }

            project_details = parse_json(self.do_url_request('project_details',
                project = self))
            teams = project_details['teams']
            stats = self._get_stats_for_resource()

            logger.debug("URL data are: %s" % self.url_info)

            MSG("Deleting translations from resource %s:" % resource)
            if not languages:
                logger.warning("No languages specified.")
                return
            for language in languages:
                if language not in stats:
                    if not skip:
                        msg = "Skipping: %s : Translation does not exist."
                        MSG(msg % (language))
                    continue
                if not force:
                    if language in teams:
                        msg = "Skipping: %s : Unable to delete translation "\
                            "because it is associated with a team.\n"\
                            "Please use -f or --force option to delete "\
                            "this translation."
                        MSG(msg % language)
                        continue
                    if int(stats[language]['translated_entities']) > 0:
                        msg = "Skipping: %s : Unable to delete translation "\
                            "because it is not empty.\n"\
                            "Please use -f or --force option to delete this "\
                            "translation."
                        MSG(msg % language)
                        continue

                try:
                    self.do_url_request(
                        'delete_translation', language=language, method="DELETE"
                    )

                    msg = "Deleted language %s from resource %s in project %s."
                    MSG(msg % (language, resource_slug, project_slug))
                except Exception, e:
                    msg = "ERROR: Unable to delete translation %s"
                    MSG(msg % language)
                    if not skip:
                        raise

    def do_url_request(self, api_call, multipart=False, data=None,
                       files=[], encoding=None, method="GET", **kwargs):
        """
        Issues a url request.
        """
        # Read the credentials from the config file (.transifexrc)
        host = self.url_info['host']
        try:
            username = self.txrc.get(host, 'username')
            passwd = self.txrc.get(host, 'password')
            token = self.txrc.get(host, 'token')
            hostname = self.txrc.get(host, 'hostname')
        except ConfigParser.NoSectionError:
            raise Exception("No user credentials found for host %s. Edit"
                " ~/.transifexrc and add the appropriate info in there." %
                host)

        # Create the Url
        kwargs['hostname'] = hostname
        kwargs.update(self.url_info)
        url = (API_URLS[api_call] % kwargs).encode('UTF-8')

        opener = None
        headers = None
        req = None

        if multipart:
            opener = urllib2.build_opener(MultipartPostHandler)
            for info,filename in files:
                data = { "resource" : info.split(';')[0],
                         "language" : info.split(';')[1],
                         "uploaded_file" :  open(filename,'rb') }

            urllib2.install_opener(opener)
            req = RequestWithMethod(url=url, data=data, method=method)
        else:
            req = RequestWithMethod(url=url, data=data, method=method)
            if encoding:
                req.add_header("Content-Type",encoding)

        base64string = base64.encodestring('%s:%s' % (username, passwd))[:-1]
        authheader = "Basic %s" % base64string
        req.add_header("Authorization", authheader)

        try:
            fh = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            if e.code in [401, 403, 404]:
                raise e
            else:
                # For other requests, we should print the message as well
                raise Exception("Remote server replied: %s" % e.read())
        except urllib2.URLError, e:
            error = e.args[0]
            raise Exception("Remote server replied: %s" % error[1])

        raw = fh.read()
        fh.close()
        return raw


    def _should_update_translation(self, lang, stats, local_file, force=False):
        """Whether a translation should be udpated from Transifex.

        We use the following criteria for that:
        - If user requested to force the download.
        - If language exists in Transifex.
        - If the local file is older than the Transifex's file.
        - If the user requested a x% completion.

        Args:
            lang: The language code to check.
            stats: The (global) statistics object.
            local_file: The local translation file.
            force: A boolean flag.
        Returns:
            True or False.
        """
        return self._should_download(lang, stats, local_file, force)

    def _should_add_translation(self, lang, stats, force=False):
        """Whether a translation should be added from Transifex.

        We use the following criteria for that:
        - If user requested to force the download.
        - If language exists in Transifex.
        - If the user requested a x% completion.

        Args:
            lang: The language code to check.
            stats: The (global) statistics object.
            force: A boolean flag.
        Returns:
            True or False.
        """
        return self._should_download(lang, stats, None, force)

    def _should_download(self, lang, stats, local_file=None, force=False):
        """Return whether a translation should be downloaded.

        If local_file is None, skip the timestamps check (the file does
        not exist locally).
        """
        try:
            lang_stats = stats[lang]
        except KeyError, e:
            logger.debug("No lang %s in statistics" % lang)
            return False

        satisfies_min = self._satisfies_min_translated(lang_stats)
        if not satisfies_min:
            return False

        if force:
            logger.debug("Downloading translation due to -f")
            return True

        if local_file is not None:
            remote_update = self._extract_updated(lang_stats)
            if not self._remote_is_newer(remote_update, local_file):
                logger.debug("Local is newer than remote for lang %s" % lang)
                return False
        return True

    def _should_push_translation(self, lang, stats, local_file, force=False):
        """Return whether a local translation file should be
        pushed to Trasnifex.

        We use the following criteria for that:
        - If user requested to force the upload.
        - If language exists in Transifex.
        - If local file is younger than the remote file.

        Args:
            lang: The language code to check.
            stats: The (global) statistics object.
            local_file: The local translation file.
            force: A boolean flag.
        Returns:
            True or False.
        """
        if force:
            logger.debug("Push translation due to -f.")
            return True
        try:
            lang_stats = stats[lang]
        except KeyError, e:
            logger.debug("Language %s does not exist in Transifex." % lang)
            return True
        if local_file is not None:
            remote_update = self._extract_updated(lang_stats)
            if self._remote_is_newer(remote_update, local_file):
                msg  = "Remote translation is newer than local file for lang %s"
                logger.debug(msg % lang)
                return False
        return True

    def _generate_timestamp(self, update_datetime):
        """Generate a UNIX timestamp from the argument.

        Args:
            update_datetime: The datetime in the format used by Transifex.
        Returns:
            A float, representing the timestamp that corresponds to the
            argument.
        """
        time_format = "%Y-%m-%d %H:%M:%S"
        return time.mktime(
            datetime.datetime(
                *time.strptime(update_datetime, time_format)[0:5]
            ).utctimetuple()
        )

    def _get_time_of_local_file(self, path):
        """Get the modified time of the path_.

        Args:
            path: The path we want the mtime for.
        Returns:
            The time as a timestamp or None, if the file does not exist
        """
        if not os.path.exists(path):
            return None
        return time.mktime(time.gmtime(os.path.getmtime(path)))

    def _satisfies_min_translated(self, stats):
        """Check whether a translation fulfills the filter used for
        minimum translated percentage.

        Args:
            perc: The current translation percentage.
        Returns:
            True or False
        """
        cur = self._extract_completed(stats)
        option_name = 'minimum_perc'
        if self.minimum_perc is not None:
            minimum_percent = self.minimum_perc
        else:
            global_minimum = int(
                self.get_resource_option('main', option_name) or 0
            )
            resource_minimum = int(
                self.get_resource_option(
                    self.resource, option_name
                ) or global_minimum
            )
            minimum_percent = resource_minimum
        return cur >= minimum_percent

    def _remote_is_newer(self, remote_updated, local_file):
        """Check whether the remote translation is newer that the local file.

        Args:
            remote_updated: The date and time the translation was last
                updated remotely.
            local_file: The local file.
        Returns:
            True or False.
        """
        if remote_updated is None:
            logger.debug("No remote time")
            return False
        remote_time = self._generate_timestamp(remote_updated)
        local_time = self._get_time_of_local_file(
            self.get_full_path(local_file)
        )
        logger.debug(
            "Remote time is %s and local %s" % (remote_time, local_time)
        )
        if local_time is not None and remote_time < local_time:
            return False
        return True

    @classmethod
    def _extract_completed(cls, stats):
        """Extract the information for the translated percentage from the stats.

        Args:
            stats: The stats object for a language as returned by Transifex.
        Returns:
            The percentage of translation as integer.
        """
        try:
            return int(stats['completed'][:-1])
        except KeyError, e:
            return 0

    @classmethod
    def _extract_updated(cls, stats):
        """Extract the  information for the last update of a translation.

        Args:
            stats: The stats object for a language as returned by Transifex.
        Returns:
            The last update field.
        """
        try:
            return stats['last_update']
        except KeyError, e:
            return None

    def _new_translations_to_add(self, files, slang, lang_map,
                                 stats, force=False):
        """Return a list of translations which are new to the
        local installation.
        """
        new_translations = []
        timestamp = time.time()
        langs = stats.keys()
        logger.debug("Available languages are: %s" % langs)

        for lang in langs:
            lang_exists = lang in files.keys()
            lang_is_source = lang == slang
            mapped_lang_exists = (
                lang in lang_map and lang_map[lang] in files.keys()
            )
            if lang_exists or lang_is_source or mapped_lang_exists:
                continue
            if self._should_add_translation(lang, stats, force):
                new_translations.append(lang)
        return set(new_translations)

    def _get_stats_for_resource(self):
        """Get the statistics information for a resource."""
        try:
            r = self.do_url_request('resource_stats')
            logger.debug("Statistics response is %s" % r)
            stats = parse_json(r)
        except urllib2.HTTPError, e:
            logger.debug("Resource not found: %s" % e)
            stats = {}
        except Exception,e:
            logger.debug("Network error: %s" % e)
            raise
        return stats

    def get_chosen_resources(self, resources):
        """Get the resources the user selected.

        Support wildcards in the resources specified by the user.

        Args:
            resources: A list of resources as specified in command-line or
                an empty list.
        Returns:
            A list of resources.
        """
        configured_resources = self.get_resource_list()
        if not resources:
            return configured_resources

        selected_resources = []
        for resource in resources:
            found = False
            for full_name in configured_resources:
                if fnmatch.fnmatch(full_name, resource):
                    selected_resources.append(full_name)
                    found = True
            if not found:
                msg = "Specified resource '%s' does not exist."
                raise Exception(msg % resource)
        logger.debug("Operating on resources: %s" % selected_resources)
        return selected_resources

    def _languages_to_pull(self, languages, files, lang_map, stats, force):
        """Get a set of langauges to pull.

        Args:
            languages: A list of languages the user selected in cmd.
            files: A dictionary of current local translation files.
        Returns:
            A tuple of a set of existing languages and new translations.
        """
        if not languages:
            pull_languages = set([])
            pull_languages |= set(files.keys())
            mapped_files = []
            for lang in pull_languages:
                if lang in lang_map.flip:
                    mapped_files.append(lang_map.flip[lang])
            pull_languages -= set(lang_map.flip.keys())
            pull_languages |= set(mapped_files)
            return (pull_languages, set([]))
        else:
            pull_languages = []
            new_translations = []
            f_langs = files.keys()
            for l in languages:
                if l not in f_langs and not (l in lang_map and lang_map[l] in f_langs):
                    if self._should_add_translation(l, stats, force):
                        new_translations.append(l)
                else:
                    if l in lang_map.keys():
                        l = lang_map[l]
                    pull_languages.append(l)
            return (set(pull_languages), set(new_translations))

    def _extension_for(self, i18n_type):
        """Return the extension used for the specified type."""
        try:
            res = parse_json(self.do_url_request('formats'))
            return res[i18n_type]['file-extensions'].split(',')[0]
        except Exception,e:
            ERRMSG(e)
            return ''

    def _resource_exists(self, stats):
        """Check if resource exists.

        Args:
            stats: The statistics dict as returned by Tx.
        Returns:
            True, if the resource exists in the server.
        """
        return bool(stats)

    def _create_resource(self, resource, pslug, fileinfo, filename, **kwargs):
        """Create a resource.

        Args:
            resource: The full resource name.
            pslug: The slug of the project.
            fileinfo: The information of the resource.
            filename: The name of the file.
        Raises:
            URLError, in case of a problem.
        """
        multipart = True
        method = "POST"
        api_call = 'create_resource'

        host = self.url_info['host']
        try:
            username = self.txrc.get(host, 'username')
            passwd = self.txrc.get(host, 'password')
            token = self.txrc.get(host, 'token')
            hostname = self.txrc.get(host, 'hostname')
        except ConfigParser.NoSectionError:
            raise Exception("No user credentials found for host %s. Edit"
                " ~/.transifexrc and add the appropriate info in there." %
                host)

        # Create the Url
        kwargs['hostname'] = hostname
        kwargs.update(self.url_info)
        kwargs['project'] = pslug
        url = (API_URLS[api_call] % kwargs).encode('UTF-8')

        opener = None
        headers = None
        req = None

        i18n_type = self._get_option(resource, 'type')
        if i18n_type is None:
            logger.error(
                "Cannot get type for resource. Please, add it in "
                "the .tx/config file."
            )

        opener = urllib2.build_opener(MultipartPostHandler)
        data = {
            "slug": fileinfo.split(';')[0],
            "name": fileinfo.split(';')[0],
            "uploaded_file":  open(filename,'rb'),
            "i18n_type": i18n_type
        }
        urllib2.install_opener(opener)
        req = RequestWithMethod(url=url, data=data, method=method)

        base64string = base64.encodestring('%s:%s' % (username, passwd))[:-1]
        authheader = "Basic %s" % base64string
        req.add_header("Authorization", authheader)

        try:
            fh = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            if e.code in [401, 403, 404]:
                raise e
            else:
                # For other requests, we should print the message as well
                raise Exception("Remote server replied: %s" % e.read())
        except urllib2.URLError, e:
            error = e.args[0]
            raise Exception("Remote server replied: %s" % error[1])

        raw = fh.read()
        fh.close()
        return raw

    def _get_option(self, resource, option):
        """Get the value for the option in the config file.

        If the option is not in the resource section, look for it in
        the project.

        Args:
            resource: The resource name.
            option: The option the value of which we are interested in.
        Returns:
            The option value or None, if it does not exist.
        """
        value = self.get_resource_option(resource, option)
        if value is None:
            if self.config.has_option('main', option):
                return self.config.get('main', option)
        return value

