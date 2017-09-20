# -*- coding: utf-8 -*-

import os
import shutil
import unittest
from mock import MagicMock, patch

from txclib.commands import cmd_init


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
        with patch('txclib.commands.project.Project') as project_mock:
            with patch('txclib.commands.cmd_set') as set_mock:
                cmd_init(argv, '')
                project_mock.assert_called()
                set_mock.assert_called_once_with([], os.getcwd())
        self.assertTrue(os.path.exists('./.tx'))
        self.assertTrue(os.path.exists('./.tx/config'))

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
