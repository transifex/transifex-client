# -*- coding: utf-8 -*-

import os
import unittest
import itertools
try:
    import json
except ImportError:
    import simplejson as json
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from functools import wraps
from mock import Mock, patch, mock_open
from collections import namedtuple
from os.path import dirname
from sys import modules, version_info

from txclib.exceptions import AuthenticationError, TXConnectionError
from txclib.project import (Project, DEFAULT_PULL_URL)

from txclib.config import Flipdict
from txclib import utils


class TestProject(unittest.TestCase):

    @patch('txclib.utils.find_dot_tx')
    def test_get_tx_dir_path(self, m_find_dot_tx):
        """Test _get_tx_dir_path function"""
        expected_path = '/tmp/'
        m_find_dot_tx.return_value = expected_path
        path = utils.get_tx_dir_path(path_to_tx=None)
        self.assertEqual(path, expected_path)
        m_find_dot_tx.assert_called_once_with()

        expected_path = '/opt/'
        path = utils.get_tx_dir_path(path_to_tx=expected_path)
        self.assertEqual(path, expected_path)
        # make sure it has not been called twice
        m_find_dot_tx.assert_called_once_with()

    @patch('os.path.exists')
    def test_get_config_file_path(self, m_exists):
        """Test get_config_file_path function"""
        m_exists.return_value = True
        utils.get_config_file_path('/tmp/')
        m_exists.assert_called_once_with('/tmp/.tx/config')

        m_exists.return_value = False
        with self.assertRaises(utils.ProjectNotInit):
            utils.get_config_file_path('/tmp/')

    @patch('txclib.config.configparser')
    def test_getset_host_credentials(self, m_parser):
        p = Project(init=False)
        # let suppose a token has been set at the config
        dummy_token = 'salala'
        p.txrc = m_parser
        p.txrc.add_section = Mock()
        p.txrc.set = Mock()
        p.txrc.get = Mock()
        p.txrc.get.side_effect = ['api', dummy_token, None, None]
        p.txrc_file = '/tmp'
        username, password = p.getset_host_credentials('test')
        self.assertEqual(username, 'api')
        self.assertEqual(password, dummy_token)

        # let's try to get credentials for someone without
        # a token
        p.txrc.get.side_effect = [
            'username',
            'passw0rdz'
        ]
        username, password = p.getset_host_credentials('test')
        self.assertEqual(username, 'username')
        self.assertEqual(password, 'passw0rdz')

    @patch('txclib.project.input')
    @patch('txclib.config.configparser')
    def test_getset_host_credentials_no_transifexrc(
            self, m_parser, m_input):
        p = Project(init=False)
        # let suppose a token has been set at the config
        dummy_token = 'salala'
        p.txrc = m_parser
        p.save = Mock()
        p.validate_credentials = Mock(return_value=True)
        p.txrc_file = '/tmp'
        p.txrc.get.side_effect = configparser.NoSectionError('test')
        m_input.return_value = dummy_token
        username, password = p.getset_host_credentials('test')
        self.assertEqual(username, 'api')
        self.assertEqual(password, dummy_token)
        self.assertEqual(p.txrc.set.call_count, 2)
        self.assertEqual(m_input.call_count, 1)
        p.save.assert_called()

    @patch('txclib.project.input')
    @patch('txclib.config.configparser')
    @patch.dict(os.environ, {'TX_TOKEN': 'environment_value'})
    def test_getset_host_credentials_env_variable(
            self, m_parser, m_input):
        p = Project(init=False)
        p.txrc = m_parser
        p.save = Mock()
        p.txrc_file = '/tmp'
        p.txrc.has_section.side_effect = [False]
        username, password = p.getset_host_credentials('test')
        self.assertEqual(username, 'api')
        self.assertEqual(password, 'environment_value')
        self.assertEqual(p.txrc.set.call_count, 2)
        # no input will be asked, password will be used by environment variable
        self.assertEqual(m_input.call_count, 0)
        p.save.assert_called()

    @patch('txclib.project.input')
    @patch('txclib.config.configparser')
    @patch.dict(os.environ, {'TX_TOKEN': 'environment_value'})
    def test_getset_host_credentials_env_variable_first_time(
            self, m_parser, m_input):
        p = Project(init=False)
        p.txrc = m_parser
        p.save = Mock()
        p.txrc_file = '/tmp'
        p.txrc.has_section.side_effect = [False]
        username, password = p.getset_host_credentials('test')
        self.assertEqual(username, 'api')
        self.assertEqual(password, 'environment_value')
        # ensure that we have set host in the txrc_file, even though TX_TOKEN
        # exists
        self.assertEqual(p.txrc.set.call_count, 2)
        p.save.assert_called()

    @patch('txclib.config.configparser')
    @patch("txclib.project.logger")
    @patch.dict(os.environ, {'TX_TOKEN': 'environment_value'})
    def test_getset_host_credentials_both_token_and_env(
            self, m_logger, m_parser):
        p = Project(init=False)
        p.txrc = m_parser
        p.save = Mock()
        p.txrc_file = '/tmp'
        p.txrc.has_section.side_effect = [False]
        username, password = p.getset_host_credentials('test', token='demo')
        self.assertEqual(username, 'api')
        self.assertEqual(password, 'environment_value')
        # ensure that we did not make additional calls to set the token in the
        # txrc file
        self.assertEqual(p.txrc.set.call_count, 2)
        p.save.assert_called()
        self.assertEqual(m_logger.warning.call_count, 1)

    @patch('txclib.project.utils.confirm')
    @patch('txclib.config.configparser')
    def test_getset_host_credentials_update_transifexrc(
            self, m_parser, m_input):
        p = Project(init=False)
        dummy_token = 'salala'
        p.txrc = m_parser
        p.save = Mock()
        p.txrc_file = '/tmp'
        p.validate_credentials = Mock(return_value=True)
        p.txrc.get.side_effect = [
            'foo', 'bar'
        ]
        # transifexrc does not get updated if credentials are the same
        username, password = p.getset_host_credentials(
            'test', username='foo', password='bar'
        )
        self.assertEqual(username, 'foo')
        self.assertEqual(password, 'bar')
        self.assertEqual(p.txrc.set.call_count, 0)
        self.assertEqual(m_input.call_count, 0)
        self.assertEqual(p.save.call_count, 0)

        # transifexrc is not updated if confirm is no
        p.txrc.get.side_effect = [
            'foo', 'bar'
        ]
        m_input.return_value = False
        username, password = p.getset_host_credentials('test',
                                                       token=dummy_token)
        self.assertEqual(username, 'api')
        self.assertEqual(password, dummy_token)
        self.assertEqual(p.txrc.set.call_count, 0)
        self.assertEqual(m_input.call_count, 1)
        self.assertEqual(p.save.call_count, 0)

        # transifexrc is not updated if confirm is yes
        p.txrc.get.side_effect = [
            'foo', 'bar'
        ]
        m_input.return_value = True
        m_input.reset_mock()
        username, password = p.getset_host_credentials('test',
                                                       token=dummy_token)
        self.assertEqual(username, 'api')
        self.assertEqual(password, dummy_token)
        self.assertEqual(p.txrc.set.call_count, 2)
        self.assertEqual(m_input.call_count, 1)
        p.save.assert_called()

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
                ['proj1.res1', 'proj2.res2', 'transifex.txn', 'transifex.txo', ],  # noqa
                ['transifex.txo', ],
                ['transifex.txn', 'transifex.txo', ],
                ['transifex.txn', ],
                [],
            ]

            for i, arg in enumerate(cmd_args):
                resources = [arg]
                self.assertEqual(p.get_chosen_resources(resources), results[i])

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
        results = itertools.cycle([80, 90])

        def side_effect(*args):
            return next(results)

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(
                self.p._satisfies_min_translated({'completed': '12%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '20%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '30%'})
            )

    def test_global_only(self):
        """Test only global option."""
        results = itertools.cycle([80, None])

        def side_effect(*args):
            return next(results)

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(
                self.p._satisfies_min_translated({'completed': '70%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '80%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '90%'})
            )

    def test_local_lower_than_global(self):
        """Test the case where the local option is lower than the global."""
        results = itertools.cycle([80, 70])

        def side_effect(*args):
            return next(results)

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(
                self.p._satisfies_min_translated({'completed': '60%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '70%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '80%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '90%'})
            )

    def test_local_higher_than_global(self):
        """Test the case where the local option is lower than the global."""
        results = itertools.cycle([60, 70])

        def side_effect(*args):
            return next(results)

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(
                self.p._satisfies_min_translated({'completed': '60%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '70%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '80%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '90%'})
            )

    def test_local_only(self):
        """Test the case where the local option is lower than the global."""
        results = itertools.cycle([None, 70])

        def side_effect(*args):
            return next(results)

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertFalse(
                self.p._satisfies_min_translated({'completed': '60%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '70%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '80%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '90%'})
            )

    def test_no_option(self):
        """"Test the case there is nothing defined."""
        results = itertools.cycle([None, None])

        def side_effect(*args):
            return next(results)

        with patch.object(self.p, "get_resource_option") as mock:
            mock.side_effect = side_effect
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '0%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '10%'})
            )
            self.assertTrue(
                self.p._satisfies_min_translated({'completed': '90%'})
            )


class TestProjectFilters(unittest.TestCase):
    """
    Test filters used to decide whether to push/pull a translation or not.
    """

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
        self.langs = list(self.stats.keys())

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
                return next(results)

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
                return next(results)

            with patch.object(self.p, "_get_time_of_local_file") as time_mock:
                time_mock.side_effect = side_effect
                with patch.object(self.p, "get_full_path") as path_mock:
                    path_mock.return_value = "foo"
                    for lang in self.langs:
                        self.assertFalse(
                            should_update(lang, self.stats, local_file)
                        )

    def test_push_translation(self):
        """
        Test filters for pushing a translation file.
        """
        with patch.object(self.p, "get_resource_option") as mock:
            mock.return_value = None

            local_file = 'foo'
            should_push = self.p._should_push_translation
            force = True
            for lang in self.langs:
                self.assertTrue(
                    should_push(
                        lang, self.stats, local_file, force
                    )
                )

            force = False  # reminder

            # unknown language
            self.assertTrue(should_push('es', self.stats, local_file))

            # older local files
            local_times = [self.p._generate_timestamp('2011-11-01 14:00:59')]
            results = itertools.cycle(local_times)

            def side_effect(*args):
                return next(results)

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
                return next(results)

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
        self.langs = list(self.stats.keys())
        self.files = dict(list(zip(self.langs, itertools.repeat(None))))
        self.details = {'available_languages': []}
        for lang in self.langs:
            self.details['available_languages'].append({'code': lang})
        self.slang = 'en'
        self.lang_map = Flipdict()

    def test_new_translations(self):
        """Test finding new translations to add."""
        with patch.object(self.p, 'do_url_request') as resource_mock:
            resource_mock.return_value = json.dumps(self.details), "utf-8"
            new_trans = self.p._new_translations_to_add
            for force in [True, False]:
                res = new_trans(
                    self.files, self.slang, self.lang_map, self.stats, force
                )
                self.assertEqual(res, set([]))

            with patch.object(self.p,
                              '_should_add_translation') as filter_mock:
                filter_mock.return_value = True
                for force in [True, False]:
                    res = new_trans(
                        {'el': None}, self.slang, self.lang_map, self.stats,
                        force
                    )
                    self.assertEqual(res, set(['pt']))
                for force in [True, False]:
                    res = new_trans(
                        {}, self.slang, self.lang_map, self.stats, force
                    )
                    self.assertEqual(res, set(['el', 'pt']))

                files = {}
                files['pt_PT'] = None
                lang_map = {'pt': 'pt_PT'}
                for force in [True, False]:
                    res = new_trans(
                        files, self.slang, lang_map, self.stats, force
                    )
                    self.assertEqual(res, set(['el']))

    def test_get_pseudo_file(self):
        slang = 'en'
        resource = 'adriana'
        file_filter = 'adriana/<lang>.po'

        pseudo_file = self.p._get_pseudo_file(slang, resource, file_filter)

        self.assertEqual(pseudo_file, 'adriana/en_pseudo.po')

    def test_languages_to_pull_empty_initial_list(self):
        """Test determining the languages to pull, when the initial
        list is empty.
        """
        languages = []
        force = False

        res = self.p._languages_to_pull(
            languages, self.files, self.lang_map, self.stats, force
        )
        existing = res[0]
        new = res[1]
        self.assertEqual(existing, set(['el', 'en', 'pt']))
        self.assertFalse(new)

        del self.files['el']
        self.files['el-gr'] = None
        self.lang_map['el'] = 'el-gr'
        res = self.p._languages_to_pull(
            languages, self.files, self.lang_map, self.stats, force
        )
        existing = res[0]
        new = res[1]
        self.assertEqual(existing, set(['el', 'en', 'pt']))
        self.assertFalse(new)

    def test_languages_to_pull_with_initial_list(self):
        """Test determining the languages to pull, then there is a
        language selection from the user.
        """
        languages = ['el', 'en']
        self.lang_map['el'] = 'el-gr'
        del self.files['el']
        self.files['el-gr'] = None
        force = False

        with patch.object(self.p, '_should_add_translation') as mock:
            mock.return_value = True
            res = self.p._languages_to_pull(
                languages, self.files, self.lang_map, self.stats, force
            )
            existing = res[0]
            new = res[1]
            self.assertEqual(existing, set(['en', 'el-gr', ]))
            self.assertFalse(new)

            mock.return_value = False
            res = self.p._languages_to_pull(
                languages, self.files, self.lang_map, self.stats, force
            )
            existing = res[0]
            new = res[1]
            self.assertEqual(existing, set(['en', 'el-gr', ]))
            self.assertFalse(new)

            del self.files['el-gr']
            mock.return_value = True
            res = self.p._languages_to_pull(
                languages, self.files, self.lang_map, self.stats, force
            )
            existing = res[0]
            new = res[1]
            self.assertEqual(existing, set(['en', ]))
            self.assertEqual(new, set(['el', ]))

            mock.return_value = False
            res = self.p._languages_to_pull(
                languages, self.files, self.lang_map, self.stats, force
            )
            existing = res[0]
            new = res[1]
            self.assertEqual(existing, set(['en', ]))
            self.assertEqual(new, set([]))

    def test_in_combination_with_force_option(self):
        """Test the minimum-perc option along with -f."""
        with patch.object(self.p, 'get_resource_option') as mock:
            mock.return_value = 70

            res = self.p._should_download('de', self.stats, None, False)
            self.assertEqual(res, False)
            res = self.p._should_download('el', self.stats, None, False)
            self.assertEqual(res, False)
            res = self.p._should_download('el', self.stats, None, True)
            self.assertEqual(res, False)
            res = self.p._should_download('en', self.stats, None, False)
            self.assertEqual(res, True)
            res = self.p._should_download('en', self.stats, None, True)
            self.assertEqual(res, True)

            with patch.object(self.p, '_remote_is_newer'):
                res = self.p._should_download('pt', self.stats, None, False)
                self.assertEqual(res, True)
                res = self.p._should_download('pt', self.stats, None, True)
                self.assertEqual(res, True)

            with patch.object(utils, 'get_git_file_timestamp') as ts_mock:
                # Note that the test needs an existing file path
                # The current test (__file__) is the only file
                # we're sure will exist and won't change

                # Old timestamp (1990)
                ts_mock.return_value = 640124371
                res = self.p._should_download(
                    'pt', self.stats, os.path.abspath(__file__), False,
                    use_git_timestamps=True
                )
                self.assertEqual(res, True)

                # "Recent" timestamp (in the future - 2100)
                ts_mock.return_value = 4111417171
                res = self.p._should_download(
                    'pt', self.stats, os.path.abspath(__file__), False,
                    use_git_timestamps=True
                )
                self.assertEqual(res, False)

    def test_get_url_by_pull_mode(self):
        self.assertEqual(
            'pull_sourceastranslation_file',
            self.p._get_url_by_pull_mode(mode='sourceastranslation')
        )
        self.assertEqual(
            DEFAULT_PULL_URL,
            self.p._get_url_by_pull_mode(mode='invalid mode')
        )
        self.assertEqual(
            DEFAULT_PULL_URL,
            self.p._get_url_by_pull_mode(mode=None)
        )

    def fixture_mocked_project(func):
        """A mock object with main os and http operations mocked"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            app_dir = dirname(modules['txclib'].__file__)
            config_file = app_dir + "/../tests/templates/config"
            transifex_file = app_dir + "/../tests/templates/transifexrc"
            with patch("txclib.utils.encode_args") as mock_encode_args, \
                patch("txclib.utils.determine_charset")\
                    as mock_determine_charset, \
                    patch("txclib.utils.get_transifex_file",
                          return_value=transifex_file) \
                    as mock_get_transifex_file, \
                    patch("txclib.utils.get_config_file_path",
                          return_value=config_file) \
                    as mock_get_config_file_path, \
                    patch("txclib.utils.save_txrc_file") \
                    as mock_save_txrc_file, \
                    patch("txclib.project.Project._get_stats_for_resource") \
                    as mock_get_stats_for_resource:

                # Create fake https response
                def encode_args(*args, **kwargs):
                    struct = namedtuple("response", "data status close")
                    return struct(status=401, data="mock_response",
                                  close=Mock())
                mock_determine_charset.return_value = "utf-8"
                mock_encode_args.return_value = encode_args

                # Mock configuration files
                p = Project(init=False)
                p._init(path_to_tx=app_dir + "/../templates")

                kwargs['mock_project'] = p
                kwargs['mocks'] = {
                    'mock_determine_charset': mock_determine_charset,
                    "mock_encode_args": mock_encode_args,
                    "mock_get_config_file_path": mock_get_config_file_path,
                    "mock_get_stats_for_resource": mock_get_stats_for_resource,
                    "mock_get_transifex_file": mock_get_transifex_file,
                    "mock_save_txrc_file": mock_save_txrc_file
                }
                return func(*args, **kwargs)
        return wrapper

    @fixture_mocked_project
    @patch("txclib.project.logger.error")
    def test_pull_raises_authentication_exception(self, mock_logger, **kwargs):
        project = kwargs['mock_project']
        with self.assertRaises(AuthenticationError):
            project.pull()
            mock_logger.assert_called_once_with(
                Project.AUTHENTICATION_FAILED_MESSAGE)

    @fixture_mocked_project
    @patch('txclib.project.Project.do_url_request')
    def test_pull_with_branch_pulls_from_right_resource(self, m, **kwargs):
        m.return_value = ('{"i18n_type": "PO"}', '')
        project = kwargs['mock_project']
        project.pull(branch='somebranch')
        self.assertDictEqual(project.url_info, {
            'host': 'https://fake.com',
            'project': 'example',
            'resource': 'somebranch--enpo'
        })

    @fixture_mocked_project
    @patch('txclib.project.Project.do_url_request')
    def test_push_with_branch_pushes_to_right_resource(self, m, **kwargs):
        m.return_value = ('{"i18n_type": "PO"}', '')
        project = kwargs['mock_project']
        project.push(source=True, branch='somebranch')
        self.assertDictEqual(project.url_info, {
            'host': 'https://fake.com',
            'project': 'example',
            'resource': 'somebranch--enpo'
        })

    @fixture_mocked_project
    @patch('txclib.project.Project.do_url_request')
    def test_push_with_branch_weird_characters_are_handled(self, m, **kwargs):
        m.return_value = ('{"i18n_type": "PO"}', '')
        project = kwargs['mock_project']
        project.push(source=True, branch='some/b**r:a&n!ch')
        self.assertDictEqual(project.url_info, {
            'host': 'https://fake.com',
            'project': 'example',
            'resource': 'some-b-r-a-n-ch--enpo'
        })

    @fixture_mocked_project
    @patch("txclib.project.logger.error")
    def test_push_raises_authentication_exception(self, mock_logger, **kwargs):
        project = kwargs['mock_project']
        with self.assertRaises(AuthenticationError):
            project.push()

    @fixture_mocked_project
    @patch("txclib.project.logger.error")
    def test_delete_raises_authentication_exception(self, mock_logger,
                                                    **kwargs):
        project = kwargs['mock_project']
        with self.assertRaises(AuthenticationError):
            project.delete()

    @fixture_mocked_project
    @patch("txclib.project.logger.error")
    @patch("txclib.utils.make_request")
    def test_pull_raises_connection_exception(self, mock_request, mock_logger,
                                              **kwargs):
        """Test that all connection errors are properly handled."""
        project = kwargs["mock_project"]
        response = 502
        msg = "Failed with code %d" % response
        mock_request.side_effect = TXConnectionError(msg, code=response)
        with self.assertRaises(TXConnectionError):
            project.pull()

    @fixture_mocked_project
    @patch("txclib.project.logger.error")
    @patch("txclib.utils.make_request")
    def test_push_raises_connection_exception(self, mock_request, mock_logger,
                                              **kwargs):
        """Test that all connection errors are properly handled."""
        project = kwargs["mock_project"]
        response = 500
        msg = "Failed with code %d" % response
        mock_request.side_effect = TXConnectionError(msg, code=response)
        with self.assertRaises(TXConnectionError):
            project.push()

    @fixture_mocked_project
    @patch('txclib.utils.queue_request')
    @patch('txclib.utils.make_request')
    @patch('txclib.project.Project._resource_exists')
    def test_push_async(self, mock_exists, mock_request, mock_queue, **kwargs):
        mock_queue.return_value = None
        mock_request.return_value = ('{"i18n_type": "PO"}', '')
        mock_exists.return_value = True
        project = kwargs['mock_project']
        patch_open = ("builtins.open" if version_info.major > 2
                      else "__builtin__.open")
        with patch(patch_open, mock_open(read_data="")):
            project.push(source=True, parallel=True)
            self.assertEqual(mock_queue.call_count, 1)

            project.push(translations=True, parallel=True)
            self.assertEqual(mock_queue.call_count, 1)

            project.pull(parallel=True)
            self.assertEqual(mock_queue.call_count, 1)


class TestFormats(unittest.TestCase):
    """Tests for the supported formats."""

    def setUp(self):
        self.p = Project(init=False)

    def test_extensions(self):
        """Test returning the correct extension for a format."""
        sample_formats = {
            'PO': {'file-extensions': '.po, .pot'},
            'QT': {'file-extensions': '.ts'},
        }
        extensions = ['.po', '.ts', '', ]
        with patch.object(self.p, "do_url_request") as mock:
            mock.return_value = json.dumps(sample_formats), "utf-8"
            for (type_, ext) in zip(['PO', 'QT', 'NONE', ], extensions):
                extension = self.p._extension_for(type_)
                self.assertEqual(extension, ext)


class TestOptions(unittest.TestCase):
    """Test the methods related to parsing the configuration file."""

    def setUp(self):
        self.p = Project(init=False)

    def test_get_option(self):
        """Test _get_option method."""
        with patch.object(self.p, 'get_resource_option') as rmock:
            with patch.object(self.p, 'config', create=True) as cmock:
                rmock.return_value = 'resource'
                cmock.has_option.return_value = 'main'
                cmock.get.return_value = 'main'
                self.assertEqual(self.p._get_option(None, None), 'resource')
                rmock.return_value = None
                cmock.has_option.return_value = 'main'
                cmock.get.return_value = 'main'
                self.assertEqual(self.p._get_option(None, None), 'main')
                cmock.has_option.return_value = None
                self.assertIs(self.p._get_option(None, None), None)


class TestConfigurationOptions(unittest.TestCase):
    """Test the various configuration options."""

    def test_i18n_type(self):
        p = Project(init=False)
        i18n_type = 'PO'
        with patch.object(p, 'config', create=True) as config_mock:
            p.set_i18n_type([], i18n_type)
            calls = config_mock.method_calls
            self.assertEqual('set', calls[0][0])
            self.assertEqual('main', calls[0][1][0])
            p.set_i18n_type(['transifex.txo'], 'PO')
            calls = config_mock.method_calls
            self.assertEqual('set', calls[0][0])
            p.set_i18n_type(['transifex.txo', 'transifex.txn'], 'PO')
            calls = config_mock.method_calls
            self.assertEqual('set', calls[0][0])
            self.assertEqual('set', calls[1][0])


class TestStats(unittest.TestCase):
    """Test the access to the stats objects."""

    def setUp(self):
        self.stats = Mock()
        self.stats.__getitem__ = Mock()
        self.stats.__getitem__.return_value = '12%'

    def test_field_used_per_mode(self):
        """Test the fields used for each mode."""
        Project._extract_completed(self.stats, 'translate')
        self.stats.__getitem__.assert_called_with('completed')
        Project._extract_completed(self.stats, 'reviewed')
        self.stats.__getitem__.assert_called_with('reviewed_percentage')
