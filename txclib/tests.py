# -*- coding: utf-8 -*-

from __future__ import with_statement
import unittest
import itertools
import json
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

    def test_specifying_resources(self):
        """Test the various ways to specify resources in a project."""
        p = Project(init=False)
        resources = [
            'proj1.res1',
            'proj2.res2',
            'transifex.txn',
            'transifex.txo',
        ]
        with patch.object(p, 'get_resource_list') as mock:
            mock.return_value = resources
            cmd_args = [
                'proj1.res1', '*1*', 'transifex*', '*r*',
                '*o', 'transifex.tx?', 'transifex.txn',
            ]
            results = [
                ['proj1.res1', ],
                ['proj1.res1', ],
                ['transifex.txn', 'transifex.txo', ],
                ['proj1.res1', 'proj2.res2', 'transifex.txn', 'transifex.txo', ],
                ['transifex.txo', ],
                ['transifex.txn', 'transifex.txo', ],
                ['transifex.txn', ],
                [],
            ]

            for arg in cmd_args:
                resources = [arg]
                p.get_chosen_resources(resources)

            # wrong argument
            resources = ['*trasnifex*', ]
            self.assertRaises(Exception, p.get_chosen_resources, resources)


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


class TestProjectFilters(unittest.TestCase):
    """Test filters used to decide whether to push/pull a translation or not."""

    def setUp(self):
        super(TestProjectFilters, self).setUp()
        self.p = Project(init=False)
        self.p.minimum_perc = None
        self.p.resource = "resource"
        self.stats = {
            'en': {
                'completed': '100%', 'last_update': '2011-11-01 15:00:00',
            }, 'el': {
                'completed': '60%', 'last_update': '2011-11-01 15:00:00',
            }, 'pt': {
                'completed': '70%', 'last_update': '2011-11-01 15:00:00',
            },
        }
        self.langs = self.stats.keys()

    def test_add_translation(self):
        """Test filters for adding translations.

        We do not test here for minimum percentages.
        """
        with patch.object(self.p, "get_resource_option") as mock:
            mock.return_value = None
            should_add = self.p._should_add_translation
            for force in [True, False]:
                for lang in self.langs:
                    self.assertTrue(should_add(lang, self.stats, force))

            # unknown language
            self.assertFalse(should_add('es', self.stats))

    def test_update_translation(self):
        """Test filters for updating a translation.

        We do not test here for minimum percentages.
        """
        with patch.object(self.p, "get_resource_option") as mock:
            mock.return_value = None

            should_update = self.p._should_update_translation
            force = True
            for lang in self.langs:
                self.assertTrue(should_update(lang, self.stats, 'foo', force))

            force = False       # reminder
            local_file = 'foo'

            # unknown language
            self.assertFalse(should_update('es', self.stats, local_file))

            # no local file
            with patch.object(self.p, "_get_time_of_local_file") as time_mock:
                time_mock.return_value = None
                with patch.object(self.p, "get_full_path") as path_mock:
                    path_mock.return_value = "foo"
                    for lang in self.langs:
                        self.assertTrue(
                            should_update(lang, self.stats, local_file)
                        )

            # older local files
            local_times = [self.p._generate_timestamp('2011-11-01 14:00:59')]
            results = itertools.cycle(local_times)
            def side_effect(*args):
                return results.next()

            with patch.object(self.p, "_get_time_of_local_file") as time_mock:
                time_mock.side_effect = side_effect
                with patch.object(self.p, "get_full_path") as path_mock:
                    path_mock.return_value = "foo"
                    for lang in self.langs:
                        self.assertTrue(
                            should_update(lang, self.stats, local_file)
                        )

            # newer local files
            local_times = [self.p._generate_timestamp('2011-11-01 15:01:59')]
            results = itertools.cycle(local_times)
            def side_effect(*args):
                return results.next()

            with patch.object(self.p, "_get_time_of_local_file") as time_mock:
                time_mock.side_effect = side_effect
                with patch.object(self.p, "get_full_path") as path_mock:
                    path_mock.return_value = "foo"
                    for lang in self.langs:
                        self.assertFalse(
                            should_update(lang, self.stats, local_file)
                        )

    def test_push_translation(self):
        """Test filters for pushing a translation file."""
        with patch.object(self.p, "get_resource_option") as mock:
            mock.return_value = None

            local_file = 'foo'
            should_push = self.p._should_push_translation
            force = True
            for lang in self.langs:
                self.assertTrue(should_push(lang, self.stats, local_file, force))

            force = False       # reminder

            # unknown language
            self.assertTrue(should_push('es', self.stats, local_file))

            # older local files
            local_times = [self.p._generate_timestamp('2011-11-01 14:00:59')]
            results = itertools.cycle(local_times)
            def side_effect(*args):
                return results.next()

            with patch.object(self.p, "_get_time_of_local_file") as time_mock:
                time_mock.side_effect = side_effect
                with patch.object(self.p, "get_full_path") as path_mock:
                    path_mock.return_value = "foo"
                    for lang in self.langs:
                        self.assertFalse(
                            should_push(lang, self.stats, local_file)
                        )

            # newer local files
            local_times = [self.p._generate_timestamp('2011-11-01 15:01:59')]
            results = itertools.cycle(local_times)
            def side_effect(*args):
                return results.next()

            with patch.object(self.p, "_get_time_of_local_file") as time_mock:
                time_mock.side_effect = side_effect
                with patch.object(self.p, "get_full_path") as path_mock:
                    path_mock.return_value = "foo"
                    for lang in self.langs:
                        self.assertTrue(
                            should_push(lang, self.stats, local_file)
                        )


class TestProjectPull(unittest.TestCase):
    """Test bits & pieces of the pull method."""

    def setUp(self):
        super(TestProjectPull, self).setUp()
        self.p = Project(init=False)
        self.p.minimum_perc = None
        self.p.resource = "resource"
        self.p.host = 'foo'
        self.p.project_slug = 'foo'
        self.p.resource_slug = 'foo'
        self.stats = {
            'en': {
                'completed': '100%', 'last_update': '2011-11-01 15:00:00',
            }, 'el': {
                'completed': '60%', 'last_update': '2011-11-01 15:00:00',
            }, 'pt': {
                'completed': '70%', 'last_update': '2011-11-01 15:00:00',
            },
        }
        self.langs = self.stats.keys()
        self.files = dict(zip(self.langs, itertools.repeat(None)))
        self.details = {'available_languages': []}
        for lang in self.langs:
            self.details['available_languages'].append({'code': lang})
        self.slang = 'en'
        self.lang_map = {}

    def test_new_translations(self):
        """Test finding new transaltions to add."""
        with patch.object(self.p, 'do_url_request') as resource_mock:
            resource_mock.return_value = json.dumps(self.details)
            files_keys = self.langs
            new_trans = self.p._new_translations_to_add
            for force in [True, False]:
                res = new_trans(
                    self.files, self.slang, self.lang_map, self.stats, force
                )
                self.assertEquals(res, [])

            with patch.object(self.p, '_should_add_translation') as filter_mock:
                filter_mock.return_value = True
                for force in [True, False]:
                    res = new_trans(
                        {'el': None}, self.slang, self.lang_map, self.stats, force
                    )
                    self.assertEquals(res, ['pt'])
                for force in [True, False]:
                    res = new_trans(
                        {}, self.slang, self.lang_map, self.stats, force
                    )
                    self.assertEquals(res, ['el', 'pt'])

                files = {}
                files['pt_PT'] = None
                lang_map = {'pt': 'pt_PT'}
                for force in [True, False]:
                    res = new_trans(
                        files, self.slang, lang_map, self.stats, force
                    )
                    self.assertEquals(res, ['el'])
