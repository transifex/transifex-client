import os
import shutil
import unittest
import sys
from StringIO import StringIO
from mock import patch, MagicMock, call
from txclib.commands import _set_source_file, _set_translation, cmd_pull, \
    cmd_init, cmd_status, cmd_help, UnInitializedError


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
        self.assertEqual(open('.tx/config').read(), config_text)

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
        pull_call = call(branch='somebranch', fetchall=False, fetchsource=False,
                         force=False, languages=[], minimum_perc=None, mode=None,
                         overwrite=True, pseudo=False, resources=[], skip=False,
                         xliff=False)
        pr_instance.pull.assert_has_calls([pull_call])
