# -*- coding: utf-8 -*-
"""Tests for txclib.config helpers."""

import unittest

from txclib.config import Flipdict


class FlipdictPopTestCase(unittest.TestCase):
    def test_pop_existing_key_keeps_flip_in_sync(self):
        mapping = Flipdict({'a': 'b'})
        self.assertEqual('b', mapping.pop('a'))
        self.assertEqual({}, dict(mapping))
        self.assertEqual({}, dict(mapping.flip))

    def test_pop_missing_key_with_default_returns_default(self):
        mapping = Flipdict({'a': 'b'})
        self.assertIsNone(mapping.pop('missing', None))
        # Neither side of the mapping may be disturbed.
        self.assertEqual({'a': 'b'}, dict(mapping))
        self.assertEqual({'b': 'a'}, dict(mapping.flip))

    def test_pop_missing_key_without_default_raises_keyerror(self):
        mapping = Flipdict({'a': 'b'})
        with self.assertRaises(KeyError):
            mapping.pop('missing')


if __name__ == '__main__':
    unittest.main()
