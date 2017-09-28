import os
import inquirer
from txclib import messages
from slugify import slugify
from txclib.api import Api
from txclib.project import Project
from txclib.log import logger
from txclib.parsers import set_parser


def validate_source_file(answers, path):
    return os.path.isfile(os.path.abspath(path))


def validate_expression(answers, expression):
    return '<lang>' in expression


class Wizard(object):

    def __init__(self, path_to_tx):
        p = Project(path_to_tx)
        self.host = p.config.get('main', 'host')
        username, token_or_password = p.getset_host_credentials(self.host)
        self.api = Api(username=username, password=token_or_password,
                       host=self.host, path_to_tx=p.txrc_file)

    def get_organizations(self):
        try:
            organizations = self.api.get('organizations')
        except Exception as e:
            logger.error(unicode(e))
            exit(1)
        return [(o['name'], o['slug']) for o in organizations]

    def get_projects_for_org(self, organization):
        try:
            projects = self.api.get('projects', organization=organization)
        except Exception as e:
            logger.error(unicode(e))
            exit(1)
        return [p for p in projects if not p['archived']]

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

        TEXTS = messages.TEXTS
        options, args = set_parser().parse_args([])
        options.local = True
        options.execute = True
        logger.info(TEXTS['source_file']['description'])

        ans = inquirer.prompt([
            inquirer.Text('source_file',
                          message=TEXTS['source_file']['message'],
                          validate=validate_source_file)
        ], raise_keyboard_interrupt=True)
        options.source_file = ans['source_file']

        logger.info(
            TEXTS['expression']['description'].format(
                source_file=options.source_file
            )
        )
        ans = inquirer.prompt([
            inquirer.Text('expression',
                          message=TEXTS['expression']['message'],
                          validate=validate_expression)
        ], raise_keyboard_interrupt=True)
        args.append(ans['expression'])

        formats = self.get_formats(os.path.basename(options.source_file))
        logger.info(TEXTS['formats']['description'])
        ans = inquirer.prompt([
            inquirer.List('i18n_type', message=TEXTS['formats']['message'],
                          choices=formats)
        ], raise_keyboard_interrupt=True)
        options.i18n_type = ans['i18n_type']

        organizations = self.get_organizations()
        logger.info(TEXTS['organization']['description'])
        org_answer = inquirer.prompt([
            inquirer.List('organization',
                          message=TEXTS['organization']['message'],
                          choices=organizations)
        ], raise_keyboard_interrupt=True)

        projects = []
        first_time = True
        create_project = ("Create new project (show instructions)...",
                          'tx:new_project')
        project = None
        while not project:
            if not first_time:
                inquirer.prompt([inquirer.Text(
                    'retry',
                    message="Hit Enter to try selecting a project again")
                ], raise_keyboard_interrupt=True)

            projects = self.get_projects_for_org(org_answer['organization'])
            p_choices = [(p['name'], p['slug']) for p in projects]
            if projects:
                logger.info(TEXTS['projects']['description'])
            else:
                logger.info("We found no projects in this organization!")
            first_time = False
            ans = inquirer.prompt([
                inquirer.List(
                    'project',
                    message=TEXTS['projects']['message'].format(self.host),
                    choices=p_choices + [create_project]
                )
            ], raise_keyboard_interrupt=True)
            if ans['project'] == 'tx:new_project':
                logger.info(
                    messages.create_project_instructions.format(
                        org=org_answer['organization'])
                )
            else:
                project = [p for p in projects
                           if p['slug'] == ans['project']][0]
                options.source_language = project['source_language_code']
                project_slug = project['slug']

        resource_slug = slugify(unicode(os.path.basename(options.source_file)))
        options.resource = '{}.{}'.format(project_slug, resource_slug)

        return (options, args)
