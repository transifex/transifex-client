import base64
import copy
import os
import urllib2
import ConfigParser

from txclib.web import *
from txclib.utils import *
from txclib.urls import API_URLS

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

        # The path to the txdata file (.tx/txdata)
        self.txdata_file = os.path.join(self.root, ".tx", "txdata")
        # Touch the file if it doesn't exist
        if not os.path.exists(self.txdata_file):
            MSG("Cannot find the txdata file (.tx/txdata)!")
            MSG("Run 'tx init' to fix this!")
            raise ProjectNotInit()

        # The dictionary which holds the txdata parameters after deser/tion.
        # Read the txdata in memory
        self.txdata = {}
        try:
            self.txdata = parse_json(open(self.txdata_file).read())
        except Exception, err:
            MSG("WARNING: Cannot open/parse .tx/txdata file", err)
            MSG("Run 'tx init' to fix this!")
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

    def pull(self, languages=[], resources=[], overwrite=True, fetchall=False):
        """
        Pull all translations file from transifex server
        """
        raw = self.do_url_request('get_resources',
            project=self.get_project_slug())

        remote_resources = parse_json(raw)

        for resource in self.txdata['resources']:
            # Push source file
            MSG("Pulling translations for source file %s" % resource['source_file'])

            new_translations = []
            if fetchall:
                raw = self.do_url_request('get_resource_details',
                    project=self.get_project_slug(),
                    resource=resource['resource_slug'])

                details = parse_json(raw)
                langs = details['available_languages']
                for l in langs:
                    if not l['code'] in resource['translations'].keys() and\
                      not l['code'] == resource['source_lang']:
                        new_translations.append(l['code'])

                if new_translations:
                    MSG("New translations found for the following languages: %s" %
                        ', '.join(new_translations))

            for lang, f_obj in resource['translations'].iteritems():
                if resources and resource['resource_slug'] not in resources:
                    continue
                if languages and lang not in languages:
                    continue
                local_file = f_obj['file']
                if not overwrite:
                    local_file = ("%s.new" % local_file)
                MSG(" -> %s: %s" % (lang, local_file))
                r = self.do_url_request('pull_file',
                    project=self.get_project_slug(),
                    resource=resource['resource_slug'],
                    language=lang)
                fd = open(local_file, 'w')
                fd.write(r)

            if new_translations:
                trans_dir = os.path.join(self.root, ".tx", resource['resource_slug'])
                if not os.path.exists(trans_dir):
                    os.mkdir(trans_dir)

                MSG("Pulling new translations for source file %s" % resource['source_file'])
                for lang in new_translations:
                    local_file = os.path.join(trans_dir, '%s_translation' % lang)
                    MSG(" -> %s: %s" % (lang, local_file))
                    r = self.do_url_request('pull_file',
                        project=self.get_project_slug(),
                        resource=resource['resource_slug'],
                        language=lang)
                    fd = open(local_file, 'w')
                    fd.write(r)

    def push(self, force=False, resources=[], languages=[]):
        """
        Push all the resources
        """
        raw = self.do_url_request('get_resources',
                  project=self.get_project_slug())

        remote_resources = parse_json(raw)

        local_resources = copy.copy(self.txdata['resources'])
        for remote_resource in remote_resources:
            name = remote_resource['slug']
            for i, resource in enumerate(local_resources):
                if name in resource['resource_slug'] :
                    del(local_resources[i])

        if local_resources and not force:
            MSG("Following resources are not available on remote machine:", ", ".join([i['resource_slug'] for i in local_resources]))
            MSG("Use -f to force creation of new resources")
            exit(1)
        else:
            for resource in self.txdata['resources']:
                if force:
                    if resources and resource['resource_slug'] not in resources:
                        continue
                    # Push source file
                    MSG("Pushing source file (%s)" % resource['source_file'])
                    r = self.do_url_request('push_file', multipart=True,
                            files=[( "%s;%s" % (resource['resource_slug'],
                                             resource['source_lang']),
                                 self.get_full_path(resource['source_file']))],
                            method="POST",
                            project=self.get_project_slug())
                    r = parse_json(r)
                    uuid = r['files'][0]['uuid']
                    self.do_url_request('extract_source',
                        data=compile_json({"uuid":uuid,"slug":resource['resource_slug']}),
                        encoding='application/json',
                        method="POST",
                        project=self.get_project_slug())
                else: 
                    MSG("Pushing translations for resource %s" % resource['resource_slug'])

                # Push translation files one by one
                for lang, f_obj in resource['translations'].iteritems():
                    if languages and lang not in languages:
                        continue
                    MSG("Pushing '%s' translations (file: %s)" % (lang, f_obj['file']))
                    r = self.do_url_request('push_file', multipart=True,
                         files=[( "%s;%s" % (resource['resource_slug'],
                                             lang),
                                 self.get_full_path(f_obj['file']))],
                        method="POST",
                        project=self.get_project_slug())
                    r = parse_json(r)
                    uuid = r['files'][0]['uuid']

                    self.do_url_request('extract_translation',
                        data=compile_json({"uuid":uuid}),
                        encoding='application/json',
                        method="PUT",
                        project=self.get_project_slug(),
                        resource=resource['resource_slug'],
                        language=lang)

    def do_url_request(self, api_call, multipart=False, data=None,
                       files=[], encoding=None, method="GET", **kwargs):
        """
        Issues a url request.
        """
        # Read the credentials from the config file (.transifexrc)
        home = os.getenv('USERPROFILE') or os.getenv('HOME')
        txrc = os.path.join(home, ".transifexrc")
        config = ConfigParser.RawConfigParser()

        if not os.path.exists(txrc):
            MSG("Cannot find the ~/.transifexrc!")
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

            opener = urllib2.build_opener(MultipartPostHandler)

            for info,filename in files:
                data = { "resource" : info.split(';')[0],
                         "language" : info.split(';')[1],
                         "uploaded_file" :  open(filename,'rb') }

            req = RequestWithMethod(url=url, method=method, data=data)

            urllib2.install_opener(opener)
        else:
            opener = urllib2.build_opener(auth_handler)
            urllib2.install_opener(opener)
            req = RequestWithMethod(url=url, data=data, method=method)
            if encoding:
                req.add_header("Content-Type",encoding)

        base64string = base64.encodestring('%s:%s' % (username, passwd))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)

        try:
            fh = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            raise Exception("%s: %s" % (e.code, e.read()))
        except urllib2.URLError, e:
            error = e.args[0]
            raise Exception("%s: %s" % (error[0], error[1]))

        raw = fh.read()
        fh.close()
        return raw


