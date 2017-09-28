import unittest
from txclib.commands import _set_source_file, _set_translation, cmd_pull, \
    UnInitializedError


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
