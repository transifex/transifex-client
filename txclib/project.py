import base64
import copy
import getpass
import os
import re
import urllib2
import ConfigParser
import datetime, time

from txclib.web import *
from txclib.utils import *
from txclib.urls import API_URLS
from txclib.config import OrderedRawConfigParser

class ProjectNotInit(Exception):
    pass


class Project():
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

        self.txrc = ConfigParser.RawConfigParser()
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

    def getset_host_credentials(self, host):
        """
        Read .transifexrc and report user,pass for a specific host else ask the
        user for input.
        """
        try:
            username = self.txrc.get(host, 'username')
            passwd = self.txrc.get(host, 'password')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            MSG("No entry found for host %s. Creating..." % host)
            username = raw_input("Please enter your transifex username: ")
            while (not username):
                username = raw_input("Please enter your transifex username: ")
            passwd = ''
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
        file_filter = re.sub("<sep>", os.sep, file_filter)

        self.config.set(resource, 'source_lang', source_lang)
        self.config.set(resource, 'file_filter', file_filter % {'proj': p_slug,
            'res': r_slug, 'extension': FILE_EXTENSIONS[i18n_type]})
        if host != self.config.get('main', 'host'):
            self.config.set(resource, 'host', host)
        # NOW WHAT?
        #self.config.set(resource,'source_file', ???)

    def get_resource_host(self, resource):
        """
        Returns the host that the resource is configured to use. If there is no
        such option we return the default one
        """
        if self.config.has_option(resource, 'host'):
            return self.config.get(resource, 'host')
        return self.config.get('main', 'host')

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
            file_filter = self.config.get(resource, "file_filter")
            source_lang = self.config.get(resource, "source_lang")
            expr_re = re.escape(file_filter)
            expr_re = re.sub(r"\\<lang\\>", '<lang>', expr_re)
            expr_re = re.sub(r"<lang>", '(?P<lang>[^/]+)', '.*%s$' % expr_re)
            expr_rec = re.compile(expr_re)
            for root, dirs, files in os.walk(self.root):
                for f in files:
                    f_path = os.path.join(root, f)
                    match = expr_rec.match(f_path)
                    if match:
                        lang = match.group('lang')
                        if lang != source_lang:
                            f_path = os.path.relpath(f_path, self.root)
                            tr_files.update({lang: f_path})

            for (name, value) in self.config.items(resource):
                if name.startswith("trans."):
                    lang = name.split('.')[1]
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
                return self.config.get(resource,option)
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
            p_slug, r_slug = r.split('.')
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
        force=False):
        """
        Pull all translations file from transifex server
        """
        if resources:
            resource_list = resources
        else:
            resource_list = self.get_resource_list()

        for resource in resource_list:
            project_slug, resource_slug = resource.split('.')
            files = self.get_resource_files(resource)
            slang = self.get_resource_option(resource, 'source_lang')
            sfile = self.get_resource_option(resource, 'source_file')
            host = self.get_resource_host(resource)
            file_filter = self.config.get(resource, 'file_filter')

            # Pull source file
            MSG("Pulling translations for resource %s (source: %s)" %
                (resource, sfile))

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
                    if not l['code'] in files.keys() and\
                      not l['code'] == slang:
                        new_translations.append(l['code'])

                if new_translations:
                    MSG("New translations found for the following languages: %s" %
                        ', '.join(new_translations))

            for lang in files.keys():
                local_file = files[lang]

                if not force:
                    # Check remote timestamp for file and skip update if needed
                    r = self.do_url_request('resource_stats',
                        host=host,
                        project=project_slug,
                        resource=resource_slug,
                        language=lang)

                    stats = parse_json(r)
                    if stats.has_key(lang):
                        time_format = "%Y-%m-%d %H:%M:%S"
             
                        try:
                            remote_time = time.mktime(datetime.datetime.strptime(stats[lang]['last_update'], time_format).utctimetuple())
                        except TypeError,e:
                            remote_time = None
                        local_time = time.mktime(time.gmtime(os.path.getmtime(local_file)))


                        if remote_time and remote_time < local_time:
                            MSG("Skipping '%s' translation (file: %s)." % (color_text(lang, "RED"), local_file))
                            continue

                if languages and lang not in languages:
                    continue
                if not overwrite:
                    local_file = ("%s.new" % local_file)
                MSG(" -> %s: %s" % (color_text(lang,"RED"), local_file))
                r = self.do_url_request('pull_file',
                    host=host,
                    project=project_slug,
                    resource=resource_slug,
                    language=lang)
                base_dir = os.path.split(local_file)[0]
                mkdir_p(base_dir)
                fd = open(local_file, 'w')
                fd.write(r)
                fd.close()

                # Fetch translation statistics from the server
#                r = self.do_url_request('resource_stats',
#                    project=self.get_project_slug(),
#                    resource=resource['resource_slug'],
#                    language=lang)
#
#                stats = parse_json(r)
#
#                for res in self.config['resources']:
#                    if res['resource_slug'] == resource['resource_slug']:
#                        res['translations'][lang].update({
#                            'completed': stats[lang]['completed']})
#

            if new_translations:
                trans_dir = os.path.join(self.root, ".tx", resource)
                if not os.path.exists(trans_dir):
                    os.mkdir(trans_dir)

                MSG("Pulling new translations for source file %s" % sfile)
                for lang in new_translations:
                    local_file = os.path.join(self.root,
                        re.sub('<lang>', lang, file_filter))

                    MSG(" -> %s: %s" % (color_text(lang, "RED"), local_file))
                    r = self.do_url_request('pull_file',
                        host=host,
                        project=project_slug,
                        resource=resource_slug,
                        language=lang)

                    base_dir = os.path.split(local_file)[0]
                    mkdir_p(base_dir)
                    fd = open(local_file, 'w')
                    fd.write(r)
                    fd.close()


    def push(self, source=False, force=False, resources=[], languages=[], skip=False):
        """
        Push all the resources
        """
        if resources:
            resource_list = resources
        else:
            resource_list = self.get_resource_list()

        for resource in resource_list:
            project_slug, resource_slug = resource.split('.')
            files = self.get_resource_files(resource)
            slang = self.get_resource_option(resource, 'source_lang')
            sfile = self.get_resource_option(resource, 'source_file')
            host = self.get_resource_host(resource)

            MSG("Pushing translations for resource %s:" % resource_slug)

            if source:
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

            # Push translation files one by one
            for lang in files.keys():
                local_file = files[lang]
                if languages and lang not in languages:
                    continue

                if not force:
                    # Check remote timestamp for file and skip update if needed
                    r = self.do_url_request('resource_stats',
                        host=host,
                        project=project_slug,
                        resource=resource_slug,
                        language=lang)

                    stats = parse_json(r)
                    time_format = "%Y-%m-%d %H:%M:%S"
                    try:
                        remote_time = time.mktime(datetime.datetime.strptime(stats[lang]['last_update'], time_format).utctimetuple())
                    except TypeError, e:
                        remote_time = None
                    local_time = time.mktime(time.gmtime(os.path.getmtime(local_file)))

                    if remote_time and remote_time > local_time:
                        MSG("Skipping '%s' translation (file: %s)." % (color_text(lang, "RED"), local_file))
                        continue

                MSG("Pushing '%s' translations (file: %s)" % (color_text(lang, "RED"), local_file))
                try:
                    r = self.do_url_request('push_file', host=host, multipart=True,
                        files=[( "%s;%s" % (resource_slug, lang),
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
                        language=lang)
                except Exception, e:
                    if not skip:
                        raise e
                    else:
                        ERRMSG(e)


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
        url = API_URLS[api_call] % kwargs

        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, hostname, username, passwd)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_manager)

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
            opener = urllib2.build_opener(auth_handler)
            urllib2.install_opener(opener)
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
                raise Exception(e)
            else:
                # For other requests, we should print the message as well
                raise Exception("%s: %s" % (e.code, e.read()))

        except urllib2.URLError, e:
            error = e.args[0]
            raise Exception("%s: %s" % (error[0], error[1]))

        raw = fh.read()
        fh.close()
        return raw

