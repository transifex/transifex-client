import os
import shutil
import unittest
import sys
from StringIO import StringIO
from mock import patch, MagicMock, call
from txclib.commands import _set_source_file, _set_translation, cmd_pull, \
    cmd_init, cmd_set, cmd_status, cmd_help, UnInitializedError
from txclib.cmdline import main


class TestCommands(unittest.TestCase):
    def test_cmd_pull_return_exception_when_dir_not_initialized(self):
        """Test when tx is not instantiated, that proper error is thrown"""
        with self.assertRaises(UnInitializedError):
            cmd_pull([], None)

    def test_set_source_file_when_dir_not_initialized(self):
        with self.assertRaises(UnInitializedError):
            _set_source_file(path_to_tx=None, resource='dummy_resource.en',
                             lang='en', path_to_file='dummy')

    def test_set_translation_when_dir_not_initialized(self):
        with self.assertRaises(UnInitializedError):
            _set_translation(path_to_tx=None, resource="dummy_resource.md",
                             lang='en', path_to_file='invalid')


class TestStatusCommand(unittest.TestCase):
    @patch('txclib.commands.project')
    def test_status(self, mock_p):
        """Test status command"""
        mock_project = MagicMock()
        mock_project.get_chosen_resources.return_value = ['foo.bar']
        mock_project.get_resource_files.return_value = {
            "fr": "translations/foo.bar/fr.po",
            "de": "translations/foo.bar/de.po"
        }
        mock_p.Project.return_value = mock_project
        cmd_status([], None)
        mock_project.get_chosen_resources.assert_called_once_with([])
        self.assertEqual(mock_project.get_resource_files.call_count, 1)


class TestHelpCommand(unittest.TestCase):
    def test_help(self):
        out = StringIO()
        sys.stdout = out
        cmd_help([], None)
        output = out.getvalue().strip()
        self.assertTrue(
            all(
                c in output for c in
                ['delete', 'help', 'init', 'pull', 'push', 'set', 'status']
            )
        )

        # call for specific command
        with patch('txclib.commands.cmd_pull', spec=cmd_pull) as pull_mock:
            cmd_help(['pull'], None)
            pull_mock.assert_called_once_with(['--help'], None)


class TestInitCommand(unittest.TestCase):

    def setUp(self):
        self.curr_dir = os.getcwd()
        self.config_file = '.tx/config'
        os.chdir('./tests/project_dir/')

    def tearDown(self, *args, **kwargs):
        shutil.rmtree('.tx', ignore_errors=False, onerror=None)
        os.chdir(self.curr_dir)
        super(TestInitCommand, self).tearDown(*args, **kwargs)

    def test_init(self):
        argv = []
        config_text = "[main]\nhost = https://www.transifex.com\n\n"
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                set_mock.assert_called_once_with([], os.getcwd())
        self.assertTrue(os.path.exists('./.tx'))
        self.assertTrue(os.path.exists('./.tx/config'))
        self.assertEqual(open(self.config_file).read(), config_text)

    def test_init_skipsetup(self):
        argv = ['--skipsetup']
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                self.assertEqual(set_mock.call_count, 0)
        self.assertTrue(os.path.exists('./.tx'))
        self.assertTrue(os.path.exists('./.tx/config'))

    @patch('txclib.commands.utils.confirm')
    def test_init_save_N(self, confirm_mock):
        os.mkdir('./.tx')
        open('./.tx/config', 'a').close()
        argv = []
        confirm_mock.return_value = False
        with patch('txclib.commands.project.Project') as project_mock:
                cmd_init(argv, '')
                self.assertEqual(project_mock.call_count, 0)
        self.assertTrue(os.path.exists('./.tx'))
        self.assertEqual(confirm_mock.call_count, 1)

    @patch('txclib.commands.utils.confirm')
    def test_init_save_y(self, confirm_mock):
        os.mkdir('./.tx')
        open('./.tx/config', 'a').close()
        argv = []
        confirm_mock.return_value = True
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                set_mock.assert_called()
        self.assertTrue(os.path.exists('./.tx'))
        self.assertEqual(confirm_mock.call_count, 1)

    def test_init_force_save(self):
        os.mkdir('./.tx')
        argv = ['--force-save']
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                set_mock.assert_called()
        self.assertTrue(os.path.exists('./.tx'))
        self.assertTrue(os.path.exists('./.tx/config'))


class TestPullCommand(unittest.TestCase):
    @patch('txclib.utils.get_current_branch')
    @patch('txclib.commands.logger')
    @patch('txclib.commands.project.Project')
    def test_pull_with_branch_no_git_repo(self, project_mock, log_mock, bmock):
        bmock.return_value = None
        pr_instance = MagicMock()
        project_mock.return_value = pr_instance
        with self.assertRaises(SystemExit):
            cmd_pull(['--branch'], '.')
        log_mock.error.assert_called_once_with(
            "You specified the --branch option but current "
            "directory does not seem to belong in any git repo.")
        assert pr_instance.pull.call_count == 0

    @patch('txclib.utils.get_current_branch')
    @patch('txclib.commands.logger')
    @patch('txclib.commands.project.Project')
    def test_pull_only_branchname_option(self, project_mock, log_mock, bmock):
        bmock.return_value = None
        pr_instance = MagicMock()
        project_mock.return_value = pr_instance
        with self.assertRaises(SystemExit):
            cmd_pull(['--branchname', 'somebranch'], '.')
        log_mock.error.assert_called_once_with(
            "--branchname options should be used along with "
            "the --branch option."
        )
        assert pr_instance.pull.call_count == 0

    @patch('txclib.utils.get_current_branch')
    @patch('txclib.commands.logger')
    @patch('txclib.commands.project.Project')
    def test_pull_with_branch_and_branchname_option(
        self, project_mock, log_mock, bmock
    ):
        pr_instance = MagicMock()
        project_mock.return_value = pr_instance
        bmock.return_value = None
        cmd_pull(['--branch', '--branchname', 'somebranch'], '.')
        assert pr_instance.pull.call_count == 1
        pull_call = call(
            branch='somebranch', fetchall=False, fetchsource=False,
            force=False, languages=[], minimum_perc=None, mode=None,
            overwrite=True, pseudo=False, resources=[], skip=False, xliff=False
        )
        pr_instance.pull.assert_has_calls([pull_call])


class TestSetCommand(unittest.TestCase):

    def setUp(self):
        self.curr_dir = os.getcwd()
        os.chdir('./tests/project_dir/')
        os.mkdir('.tx')
        self.path_to_tx = os.getcwd()
        self.config_file = '.tx/config'
        open(self.config_file, "w").write('[main]\nhost = https://foo.var\n')

    def tearDown(self, *args, **kwargs):
        shutil.rmtree('.tx', ignore_errors=False, onerror=None)
        os.chdir(self.curr_dir)
        super(TestSetCommand, self).tearDown(*args, **kwargs)

    def test_bare_set_too_few_arguments(self):
        with self.assertRaises(SystemExit):
            args = ["-r", "project1.resource1"]
            cmd_set(args, None)

    def test_bare_set_source_no_file(self):
        with self.assertRaises(SystemExit):
            args = ["-r", "project1.resource1", '--is-source', '-l', 'en']
            cmd_set(args, None)

        with self.assertRaises(Exception):
            args = ['-r', 'project1.resource1', '--source', '-l', 'en',
                    'noexistent-file.txt']
            cmd_set(args, self.path_to_tx)

    def test_bare_set_source_file(self):
        expected = ("[main]\nhost = https://foo.var\n\n[project1.resource1]\n"
                    "source_file = test.txt\nsource_lang = en\n\n")
        args = ["-r", "project1.resource1", '--source', '-l', 'en', 'test.txt']
        cmd_set(args, self.path_to_tx)
        with open(self.config_file) as config:
            self.assertEqual(config.read(), expected)

        # set translation file for de
        expected = ("[main]\nhost = https://foo.var\n\n[project1.resource1]\n"
                    "source_file = test.txt\nsource_lang = en\n"
                    "trans.de = translations/de.txt\n\n")
        args = ["-r", "project1.resource1", '-l', 'de', 'translations/de.txt']
        cmd_set(args, self.path_to_tx)
        with open(self.config_file) as config:
            self.assertEqual(config.read(), expected)

    def test_auto_locale_no_expression(self):
        with self.assertRaises(SystemExit):
            args = ["auto-local", "-r", "project1.resource1",
                    '--source-language', 'en']
            cmd_set(args, self.path_to_tx)

    def test_auto_locale(self):
        expected = "[main]\nhost = https://foo.var\n"
        args = ["auto-local", "-r", "project1.resource1", '--source-language',
                'en', 'translations/<lang>/test.txt']
        cmd_set(args, self.path_to_tx)
        with open(self.config_file) as config:
            self.assertEqual(config.read(), expected)

    def test_auto_locale_execute(self):
        expected = ("[main]\nhost = https://foo.var\n\n[project1.resource1]\n"
                    "file_filter = translations/<lang>/test.txt\n"
                    "source_file = translations/en/test.txt\n"
                    "source_lang = en\n\n")

        args = ["auto-local", "-r", "project1.resource1", '--source-language',
                'en', '--execute', 'translations/<lang>/test.txt']
        cmd_set(args, self.path_to_tx)
        with open(self.config_file) as config:
            self.assertEqual(config.read(), expected)

    def test_auto_remote_invalid_url(self):
        # no project_url
        args = ["auto-remote"]
        with self.assertRaises(SystemExit):
            cmd_set(args, self.path_to_tx)

        # invalid project_url
        args = ["auto-remote", "http://some.random.url/"]
        with self.assertRaises(Exception):
            cmd_set(args, self.path_to_tx)

    @patch('txclib.utils.get_details')
    def test_auto_remote_project(self, get_details_mock):
        # change the host to tx
        open(self.config_file, "w").write(
            '[main]\nhost = https://www.transifex.com\n'
        )
        expected = ("[main]\nhost = https://www.transifex.com\n\n"
                    "[proj.resource_1]\n"
                    "file_filter = translations/proj.resource_1/<lang>.txt\n"
                    "source_lang = fr\ntype = TXT\n\n[proj.resource_2]\n"
                    "file_filter = translations/proj.resource_2/<lang>.txt\n"
                    "source_lang = fr\ntype = TXT\n\n")
        get_details_mock.side_effect = [
            # project details
            {
                'resources': [
                    {'slug': 'resource_1', 'name': 'resource 1'},
                    {'slug': 'resource_2', 'name': 'resource 2'}
                ]
            },
            # resources details
            {
                'source_language_code': 'fr',
                'i18n_type': 'TXT',
                'slug': 'resource_1',
            }, {
                'source_language_code': 'fr',
                'i18n_type': 'TXT',
                'slug': 'resource_2',
            }
        ]
        args = ["auto-remote", "https://www.transifex.com/test-org/proj/"]
        cmd_set(args, self.path_to_tx)
        with open(self.config_file) as config:
            self.assertEqual(config.read(), expected)

    def test_bulk_missing_options(self):
        with self.assertRaises(SystemExit):
            args = ["bulk"]
            cmd_set(args, self.path_to_tx)

        with self.assertRaises(SystemExit):
            args = ["bulk", "-p", "test-project"]
            cmd_set(args, self.path_to_tx)

        with self.assertRaises(SystemExit):
            args = ["bulk", "-p", "test-project", "--source-file-dir",
                    "translations", "--source-language", "en", "--t", "TXT",
                    "--file-extension", ".txt"]
            cmd_set(args, self.path_to_tx)

    def test_bulk(self):
        expected = ("[main]\nhost = https://foo.var\n\n"
                    "[test-project.translations_en_test]\n"
                    "file_filter = translations/<lang>/en/test.txt\n"
                    "source_file = translations/en/test.txt\n"
                    "source_lang = en\ntype = TXT\n\n")
        args = ["bulk", "-p", "test-project", "--source-file-dir",
                "translations", "--source-language", "en", "-t", "TXT",
                "--file-extension", ".txt", "--execute",
                "translations/<lang>/{filepath}/{filename}{extension}"]
        cmd_set(args, self.path_to_tx)
        with open(self.config_file) as config:
            self.assertEqual(config.read(), expected)


class TestMainCommand(unittest.TestCase):
    def test_call_tx_with_no_command(self):
        with self.assertRaises(SystemExit):
            main(['tx'])

    def test_call_tx_with_invalid_command(self):
        with self.assertRaises(SystemExit):
            main(['tx', 'random'])
