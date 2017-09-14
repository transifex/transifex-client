import os
import inquirer
from slugify import slugify
from txclib.api import Api
from txclib.project import Project
from txclib.log import logger
from txclib.parsers import set_parser


def validate_source_file(answers, path):
    return os.path.isfile(os.path.abspath(path))


def validate_expression(answers, expression):
    return '<lang>' in expression

TEXTS = {
    "source_file": {
        "type": inquirer.Text,
        "description": ("""
The Transifex Client syncs files between your local directory and Transifex.
The mapping configuration between the two is stored in a file called .tx/config
in your current directory. For more information, visit
https://docs.transifex.com/client/set/.
"""),
        "error": ("No file was found in that path. Please correct the path "
                  "or make sure a file exists in that location."),
        "processing": "",
        "message": "Enter a path to your local source file"
    },
    "expression": {
        "type": inquirer.Text,
        "description": ("""
Next, we’ll need a path expression pointing to the location of the
translation files (whether they exist yet or not) associated with
the source file ‘locale/en/main.yml’. You should use <lang> as a
wildcard for the language code.
"""),
        "error": "The path expression doesn’t contain the <lang> placeholder.",
        "message": "Enter a path expression"
    },
    "formats": {
        "type": inquirer.List,
        "description": ("""
Here’s a list of the supported file formats. For more information,
check our docs at https://docs.transifex.com/formats/.
"""),
        "error": "",
        "message": "Select the file format type",
    },
    "organization": {
        "type": inquirer.List,
        "description": ("""
You’ll now choose a project in a Transifex organization to sync with your
local files.
You belong to these organizations in Transifex:
"""),
        "error": ("""
You don’t have any projects in the ‘Waze’ organization. To create a new
project, head to https://www.transifex.com/waze/add.  Once you’ve created
a project, you can continue.
"""),
        "message": "Select the organization",
    },
    "projects": {
        "type": inquirer.List,
        "description": ("""We found these projects in your organization."""),
        "error": "",
        "message": "Select project",
    },
}

epilog = """
The Transifex Client syncs files between your local directory and Transifex.
The mapping configuration between the two is stored in a file called
.tx/config in your current directory. For more information, visit
https://docs.transifex.com/client/set/.
"""


class Wizard(object):
    DEFAULTS = {'host': 'http://127.0.0.1:8000', }

    def __init__(self, path_to_tx):
        username, token_or_password = Project(path_to_tx).\
            getset_host_credentials(self.DEFAULTS['host'])
        self.api = Api(username=username, password=token_or_password)

    def get_organizations(self):
        try:
            organizations = self.api.get('organizations')
        except Exception as e:
            logger.error(unicode(e))
            exit(1)
        return [(o['name'], o['slug']) for o in organizations]

    def get_projects_for_org(self, organization):
        try:
            return self.api.get('projects', organization=organization)
        except Exception as e:
            logger.error(unicode(e))
            exit(1)

    def get_formats(self, filename):
        _, extension = os.path.splitext(filename)
        try:
            formats = self.api.get('formats')
        except Exception as e:
            logger.error(unicode(e))
            exit(1)

        def display_format(v):
            return '{} - {}'.format(v['description'], v['file-extensions'])

        formats = [(display_format(v), k) for k, v in formats.items()
                   if extension in v['file-extensions']]
        return formats

    def run(self):
        """
        Runs the interactive wizard for `tx set` command and populates the
        parser's options with the user input. Options `local` and `execute`
        are by default True when interactive wizard is run.

        Returns: the populated (options, args) tuple.
        """

        options, args = set_parser().parse_args()
        options.local = True
        options.execute = True
        logger.info(TEXTS['source_file']['description'])

        ans = inquirer.prompt([
            inquirer.Text('source_file',
                          message=TEXTS['source_file']['message'],
                          validate=validate_source_file)
        ])
        options.source_file = ans['source_file']

        logger.info(TEXTS['expression']['description'])
        ans = inquirer.prompt([
            inquirer.Text('expression',
                          message=TEXTS['expression']['message'],
                          validate=validate_expression)
        ])
        args.append(ans['expression'])

        formats = self.get_formats(os.path.basename(options.source_file))
        logger.info(TEXTS['formats']['description'])
        ans = inquirer.prompt([
            inquirer.List('i18n_type', message=TEXTS['formats']['message'],
                          choices=formats)
        ])
        options.i18n_type = ans['i18n_type']

        organizations = self.get_organizations()
        logger.info(TEXTS['organization']['description'])
        ans = inquirer.prompt([
            inquirer.List('organization',
                          message=TEXTS['organization']['message'],
                          choices=organizations)
        ])

        projects = []
        first_time = True
        while len(projects) == 0:
            if not first_time:
                inquirer.Text(
                    message="Hit Enter to try selecting a project again:")

            projects = self.get_projects_for_org(ans['organization'])
            create_project = ("Create new project (show instructions)...",
                              'tx:new_project')
            project = None
            if projects:
                p_choices = [(p['name'], p['slug']) for p in projects]
                logger.info(TEXTS['projects']['description'])
                first_time = False
                ans = inquirer.prompt([
                    inquirer.List('project',
                                  message=TEXTS['projects']['message'],
                                  choices=p_choices + [create_project])
                    ])
                if ans['project'] == 'tx:new_project':
                    logger.info("To create a new project, head to "
                                "https://www.transifex.com/{}/add. Once "
                                "you’ve created the project, you can continue."
                                "".format(ans['organization']))
                else:
                    project = [p for p in projects
                               if p['slug'] == ans['project']][0]
                    options.source_language = project['source_language_code']
                    project_slug = ans['project']

        if not project:
            return (options, args)

        resource_slug = slugify(os.path.basename(options.source_file))
        options.resource = '{}.{}'.format(project_slug, resource_slug)

        return options, args
