# -*- coding: utf-8 -*-
import base64
import copy
import getpass
import os
import re
import urllib2
import datetime, time
import ConfigParser

from txclib.web import *
from txclib.utils import *
from txclib.urls import API_URLS
from txclib.config import OrderedRawConfigParser, Flipdict

class ProjectNotInit(Exception):
    pass


class Project(object):
    """
    Represents an association between the local and remote project instances.
    """

    def __init__(self, path_to_tx=None):
        """
        Initialize the Project attributes.
        """
        # The path to the root of the project, where .tx lives!
        self.root = path_to_tx or find_dot_tx()
        if not self.root:
            MSG("Cannot find any .tx directory!")
            MSG("Run 'tx init' to initialize your project first!")
            raise ProjectNotInit()

        # The path to the config file (.tx/config)
        self.config_file = os.path.join(self.root, ".tx", "config")
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

        self.config.set(resource, 'source_lang', source_lang)
        self.config.set(resource, 'file_filter', file_filter % {'proj': p_slug,
            'res': r_slug, 'extension': FILE_EXTENSIONS[i18n_type]})
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
        fetchsource=False, force=False, skip=False):
        """
        Pull all translations file from transifex server
        """
        if resources:
            resource_list = resources
        else:
            resource_list = self.get_resource_list()

        for resource in resource_list:
            self.resource = resource
            project_slug, resource_slug = resource.split('.')
            files = self.get_resource_files(resource)
            slang = self.get_resource_option(resource, 'source_lang')
            sfile = self.get_resource_option(resource, 'source_file')
            lang_map = self.get_resource_lang_mapping(resource)
            host = self.get_resource_host(resource)

            try:
                r = self.do_url_request(
                    'resource_stats', host=host, project=project_slug,
                    resource=resource_slug
                )
                stats = parse_json(r)
            except Exception,e:
                stats = {}

            # remove mapped lanaguages from local file listing
            for l in lang_map.flip:
                if l in files:
                    del files[l]

            try:
                file_filter = self.config.get(resource, 'file_filter')
            except ConfigParser.NoOptionError:
                file_filter = None

            # Pull source file
            pull_languages = []
            new_translations = []

            if fetchall:
                timestamp = time.time()
                raw = self.do_url_request('resource_details',
                    host=host,
                    project=project_slug,
                    resource=resource_slug)

                details = parse_json(raw)
                langs = details['available_languages']

                for l in langs:
                    code = l['code']
                    if not code in files.keys() and\
                      not code == slang and\
                      not (code in lang_map and lang_map[code] in files.keys()):
                        if self._should_add_translation(l['code'], stats, force):
                            new_translations.append(code)

                if new_translations:
                    MSG("New translations found for the following languages: %s" %
                        ', '.join(new_translations))

            if not languages:
                pull_languages.extend(files.keys())
            else:
                f_langs = files.keys()
                for l in languages:
                    if l not in f_langs and not (l in lang_map and lang_map[l] in f_langs):
                        if self._should_add_translation(l['code'], stats, force):
                            new_translations.append(l)
                    else:
                        if l in lang_map.keys():
                            l = lang_map[l]
                        pull_languages.append(l)

            if fetchsource:
                if sfile and slang not in pull_languages:
                    pull_languages.append(slang)
                elif slang not in new_translations:
                    new_translations.append(slang)

            if pull_languages:
                MSG("Pulling translations for resource %s (source: %s)" %
                    (resource, sfile))

            for lang in pull_languages:
                local_lang = lang
                if lang in lang_map.values():
                    remote_lang = lang_map.flip[lang]
                else:
                    remote_lang = lang
                if languages and lang not in pull_languages:
                    continue
                if lang != slang:
                    local_file = files[lang] or files[lang_map[lang]]
                else:
                    local_file = sfile

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
                    r = self.do_url_request('pull_file',
                        host=host,
                        project=project_slug,
                        resource=resource_slug,
                        language=remote_lang)
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
                    r = self.do_url_request('pull_file',
                        host=host,
                        project=project_slug,
                        resource=resource_slug,
                        language=remote_lang)

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
        if resources:
            resource_list = resources
        else:
            resource_list = self.get_resource_list()

        for resource in resource_list:
            push_languages = []
            project_slug, resource_slug = resource.split('.')
            files = self.get_resource_files(resource)
            slang = self.get_resource_option(resource, 'source_lang')
            sfile = self.get_resource_option(resource, 'source_file')
            lang_map = self.get_resource_lang_mapping(resource)
            host = self.get_resource_host(resource)

            MSG("Pushing translations for resource %s:" % resource)

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
                    r = self.do_url_request('push_file', host=host, multipart=True,
                            files=[( "%s;%s" % (resource_slug, slang),
                            self.get_full_path(sfile))],
                            method="POST",
                            project=project_slug)
                    r = parse_json(r)
                    uuid = r['files'][0]['uuid']
                    self.do_url_request('extract_source',
                        host=host,
                        data=compile_json({"uuid":uuid,"slug":resource_slug}),
                        encoding='application/json',
                        method="POST",
                        project=project_slug)
                except Exception, e:
                    if not skip:
                        raise e
                    else:
                        MSG(e)
            else:
                try:
                    self.do_url_request('resource_details', host=host,
                        project=project_slug, resource=resource_slug)
                except Exception, e:
                    try:
                        code = e.code
                    except:
                        raise e
                    if e.code == 404:
                        ERRMSG("Resource %s doesn't exist on the server. Use the"
                            " --source option to create it." % resource)
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

                # Push translation files one by one
                for lang in push_languages:
                    local_lang = lang
                    if lang in lang_map.values():
                        remote_lang = lang_map.flip[lang]
                    else:
                        remote_lang = lang

                    local_file = files[local_lang]

                    if not force:
                        try:
                            r = self.do_url_request('resource_stats',
                                host=host,
                                project=project_slug,
                                resource=resource_slug,
                                language=remote_lang)

                            # Check remote timestamp for file and skip update if needed
                            stats = parse_json(r)
                            time_format = "%Y-%m-%d %H:%M:%S"
                            remote_time = time.mktime(
                                datetime.datetime(
                                    *time.strptime(
                                        stats[remote_lang]['last_update'], time_format)[0:5]
                                ).utctimetuple()
                            )
                        except Exception, e:
                            remote_time = None

                        local_time = self._get_time_of_local_file(self.get_full_path(local_file))
                        if local_time is not None:
                            if remote_time and remote_time > local_time:
                                MSG("Skipping '%s' translation (file: %s)." % (color_text(lang, "RED"), local_file))
                                continue

                    MSG("Pushing '%s' translations (file: %s)" % (color_text(remote_lang, "RED"), local_file))
                    try:
                        r = self.do_url_request('push_file', host=host, multipart=True,
                            files=[( "%s;%s" % (resource_slug, remote_lang),
                            self.get_full_path(local_file))],
                            method="POST",
                            project=project_slug)
                        r = parse_json(r)
                        uuid = r['files'][0]['uuid']
                        self.do_url_request('extract_translation',
                            host=host,
                            data=compile_json({"uuid":uuid}),
                            encoding='application/json',
                            method="PUT",
                            project=project_slug,
                            resource=resource_slug,
                            language=remote_lang)
                    except Exception, e:
                        if not skip:
                            raise e
                        else:
                            ERRMSG(e)

    def delete(self, resources=[], languages=[], skip=False):
        """Delete translations."""
        if not resources:
            resources = self.get_resource_list()
        for resource in resources:
            delete_languages = []
            files = self.get_resource_files(resource)
            project_slug, resource_slug = resource.split('.')
            lang_map = self.get_resource_lang_mapping(resource)
            host = self.get_resource_host(resource)


            if languages:
                MSG("Deleting translations for resource %s:" % resource)
                for language in languages:
                    try:
                        r = self.do_url_request(
                            'delete_translation', host=host,
                            project=project_slug, resource=resource_slug,
                            language=language, method="DELETE"
                        )
                        MSG(
                            "Deleted language %s from resource %s in project %s." % (
                                language, resource_slug, project_slug
                            ))
                    except Exception, e:
                        MSG(
                            "ERROR: Unable to delete translation %s.%s.%s" % (
                                project_slug, resource_slug, language
                            ))
                        if not skip:
                            raise
            else:
                try:
                    r = self.do_url_request(
                        'resource_details', host=host, project=project_slug,
                        resource=resource_slug, method="DELETE"
                    )
                    MSG("Deleted resource %s in project %s." % (
                            resource_slug, project_slug
                    ))
                except Exception, e:
                    MSG(
                        "ERROR: Unable to delete resource %s.%s" % (
                            project_slug, resource_slug
                        ))
                    if not skip:
                        raise

    def do_url_request(self, api_call, host=None, multipart=False, data=None,
                       files=[], encoding=None, method="GET", **kwargs):
        """
        Issues a url request.
        """
        # Read the credentials from the config file (.transifexrc)
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
        if force:
            return True
        try:
            lang_stats = stats[lang]
        except KeyError, e:
            # TODO log messages
            return False

        if local_file is not None:
            remote_update = self._extract_updated(lang_stats)
            if not self._remote_is_newer(remote_update, local_file):
                return False

        return self._satisfies_min_translated(lang_stats)

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
        minimum_percent = int(
            self.get_resource_option(self.resource, 'minimum') or 0
        )
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
        if remote_time is None:
            return False
        remote_time = self._generate_timestamp(remote_update)
        local_time = self._get_time_of_local_file(
            self.get_full_path(local_file)
        )
        if local_time is not None and remote_time < local_time:
            return False

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
