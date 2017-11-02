import unittest
import sys
from StringIO import StringIO
from mock import patch, MagicMock
from txclib.commands import _set_source_file, _set_translation, cmd_pull, \
    UnInitializedError, cmd_help, cmd_status


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
