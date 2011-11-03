# -*- coding: utf-8 -*-


import unittest
import itertools
from mock import patch
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


class TestProjectMinimumPercent(unittest.TestCase):
    """Test the minimum-perc option."""

    def setUp(self):
        super(TestProjectMinimumPercent, self).setUp()
        self.p = Project(init=False)
        self.p.minimum_perc = None
        self.p.resource = "resource"


    def test_cmd_option(self):
        """Test command-line option."""
        self.p.minimum_perc = 20
        results = itertools.cycle([80, 90 ])
        def side_effect(*args):
            return results.next()

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(self.p._satisfies_min_translated({'completed': '12%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '20%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '30%'}))

    def test_global_only(self):
        """Test only global option."""
        results = itertools.cycle([80, None ])
        def side_effect(*args):
            return results.next()

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(self.p._satisfies_min_translated({'completed': '70%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '80%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '90%'}))

    def test_local_lower_than_global(self):
        """Test the case where the local option is lower than the global."""
        results = itertools.cycle([80, 70 ])
        def side_effect(*args):
            return results.next()

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(self.p._satisfies_min_translated({'completed': '60%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '70%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '80%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '90%'}))

    def test_local_higher_than_global(self):
        """Test the case where the local option is lower than the global."""
        results = itertools.cycle([60, 70 ])
        def side_effect(*args):
            return results.next()

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(self.p._satisfies_min_translated({'completed': '60%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '70%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '80%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '90%'}))

    def test_local_only(self):
        """Test the case where the local option is lower than the global."""
        results = itertools.cycle([None, 70 ])
        def side_effect(*args):
            return results.next()

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(self.p._satisfies_min_translated({'completed': '60%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '70%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '80%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '90%'}))

    def test_no_option(self):
        """"Test the case there is nothing defined."""
        results = itertools.cycle([None, None ])
        def side_effect(*args):
            return results.next()

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertTrue(self.p._satisfies_min_translated({'completed': '0%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '10%'}))
            self.assertTrue(self.p._satisfies_min_translated({'completed': '90%'}))
