# -*- coding: utf-8 -*-

import os
import unittest
from mock import patch
from txclib.paths import posix_path, native_path


class PosixPathTestcase(unittest.TestCase):
    """Tests for posix paths in various systems."""

    def test_posix_path_in_unix_does_nothing(self):
        orig_path = os.path.abspath(os.getcwd())
        path = posix_path(orig_path)
        self.assertEqual(orig_path, path)

    @patch.object(os, 'sep', new='\\')
    @patch.object(os, 'altsep', new='/')
    def test_posix_path_in_windows_replaces_backslashes(self):
        orig_path = os.path.abspath(os.getcwd())
        path = orig_path.replace('/', '\\')
        self.assertEqual(orig_path, posix_path(path))


class NativePathTestCase(unittest.TestCase):
    """Tests for native paths in various systems."""

    def test_native_path_in_unix_does_nothing(self):
        orig_path = os.path.abspath(os.getcwd())
        path = native_path(orig_path)
        self.assertEqual(orig_path, path)

    @patch.object(os, 'sep', new='\\')
    @patch.object(os, 'altsep', new='/')
    def test_posix_path_in_windows_replaces_backslashes(self):
        orig_path = posix_path(os.path.abspath(os.getcwd()))
        expected_path = orig_path.replace('/', '\\')
        self.assertEqual(expected_path, native_path(orig_path))
