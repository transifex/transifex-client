import os
import shutil
import unittest
import sys
from StringIO import StringIO
from mock import patch, MagicMock
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

    @patch('txclib.commands.inquirer')
    def test_init(self, inquirer_mock):
        argv = []
        prompt_mock = MagicMock(return_value={'host': 'somehost'})
        inquirer_mock.prompt = prompt_mock
        config_text = "[main]\nhost = https://somehost\n\n"
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                set_mock.assert_called_once_with([], os.getcwd())
        self.assertTrue(os.path.exists('./.tx'))
        self.assertTrue(os.path.exists('./.tx/config'))
        self.assertEqual(open('.tx/config').read(), config_text)

    @patch('txclib.commands.inquirer')
    def test_init_skipsetup(self, inquirer_mock):
        argv = ['--skipsetup']
        prompt_mock = MagicMock(return_value={'host': 'somehost'})
        inquirer_mock.prompt = prompt_mock
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                self.assertEqual(set_mock.call_count, 0)
        self.assertTrue(os.path.exists('./.tx'))
        self.assertTrue(os.path.exists('./.tx/config'))

    @patch('txclib.commands.inquirer')
    def test_init_save_N(self, inquirer_mock):
        os.mkdir('./.tx')
        argv = []
        prompt_mock = MagicMock(return_value={'reinit': False})
        inquirer_mock.prompt = prompt_mock
        with patch('txclib.commands.project.Project') as project_mock:
                cmd_init(argv, '')
                self.assertEqual(project_mock.call_count, 0)
        self.assertTrue(os.path.exists('./.tx'))
        self.assertEqual(prompt_mock.call_count, 1)

    @patch('txclib.commands.inquirer')
    def test_init_save_y(self, inquirer_mock):
        os.mkdir('./.tx')
        argv = []
        prompt_mock = MagicMock(
            return_value={'host': 'somehost', 'reinit': True}
        )
        inquirer_mock.prompt = prompt_mock
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                set_mock.assert_called()
        self.assertTrue(os.path.exists('./.tx'))
        self.assertEqual(prompt_mock.call_count, 2)

    @patch('txclib.commands.inquirer')
    def test_init_force_save(self, inquirer_mock):
        os.mkdir('./.tx')
        argv = ['--force-save']
        prompt_mock = MagicMock(return_value={'host': 'somehost'})
        inquirer_mock.prompt = prompt_mock
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                set_mock.assert_called()
        self.assertTrue(os.path.exists('./.tx'))
        self.assertTrue(os.path.exists('./.tx/config'))
        self.assertEqual(prompt_mock.call_count, 1)
