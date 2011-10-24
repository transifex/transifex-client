# -*- coding: utf-8 -*-


import unittest
from txclib.project import Project


class TestProject(unittest.TestCase):

    def test_extract_fields(self):
        """Test the functions that extract a field from a stats object."""
        stats = {
            'completed': '80%',
            'last_update': '00:00',
            'foo': 'bar',
        }
        self.assertEqual(
            stats['completed'], '%s%%' % Project._extract_completed(stats)
        )
        self.assertEqual(stats['last_update'], Project._extract_updated(stats))

