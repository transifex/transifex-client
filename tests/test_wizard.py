# -*- coding: utf-8 -*-

import unittest
from mock import patch, MagicMock

from six import assertRaisesRegex

from txclib.wizard import Wizard


@patch('txclib.wizard.Api')
class WizardCase(unittest.TestCase):
    def setUp(self, *args, **kwargs):
        with patch('txclib.wizard.Project') as project_mock:
            with patch('txclib.wizard.Api'):
                instance_mock = MagicMock()
                instance_mock.getset_host_credentials.return_value = \
                    'foo', 'bar'
                project_mock.return_value = instance_mock
                self.wizard = Wizard('/foo/bar/tmp')
        super(WizardCase, self).setUp(*args, **kwargs)

    def test_get_organizations(self, api_mock):
        self.wizard.api.get.return_value = [
            {
                "name": "Transifex",
                "slug": "transifex",
            },
            {
                "name": "Dunder Mifflin",
                "slug": "dunder-mifflin",
            }
        ]
        orgs = self.wizard.get_organizations()
        self.assertEqual(
            orgs,
            [("dunder-mifflin", "Dunder Mifflin"), ("transifex", "Transifex")]
        )

    def test_get_projects_excludes_archived(self, api_mock):
        self.wizard.api.get.return_value = [
            {
                "name": "project 1",
                "slug": "project-1",
                "archived": False
            },
            {
                "name": "project 2",
                "slug": "project-2",
                "archived": True
            }
        ]
        projects = self.wizard.get_projects_for_org('org_slug')
        self.assertEqual(
            projects,
            [
                {
                    "archived": False,
                    "name": "project 1",
                    "slug": "project-1"
                }
            ]
        )

    def test_get_formats_with_extension(self, api_mock):
        self.wizard.api.get.return_value = {
            "INI": {
                "mimetype": "text/plain",
                "file-extensions": ".ini",
                "description": "Joomla INI File"
            },
            "SRT": {
                "mimetype": "text/plain",
                "file-extensions": ".srt",
                "description": "SubRip subtitles"
            }
        }
        formats = self.wizard.get_formats('test.srt')
        self.assertEqual(formats, [("SRT", "SubRip subtitles - .srt")])

    def test_get_formats_without_extension(self, api_mock):
        self.wizard.api.get.return_value = {
            "INI": {
                "mimetype": "text/plain",
                "file-extensions": ".ini",
                "description": "Joomla INI File"
            },
            "SRT": {
                "mimetype": "text/plain",
                "file-extensions": ".srt",
                "description": "SubRip subtitles"
            }
        }
        formats = self.wizard.get_formats('test')
        self.assertEqual(
            formats,
            [("INI", "Joomla INI File - .ini"),
             ("SRT", "SubRip subtitles - .srt")]
        )

    def test_unsupported_formats(self, api_mock):
        self.wizard.api.get.return_value = {
            "INI": {
                "mimetype": "text/plain",
                "file-extensions": ".ini",
                "description": "Joomla INI File"
            },
            "SRT": {
                "mimetype": "text/plain",
                "file-extensions": ".srt",
                "description": "SubRip subtitles"
            }
        }
        error_msg = "No formats found for this file"
        with assertRaisesRegex(self, Exception, error_msg):
            self.wizard.get_formats('test.srt.txt')
        with assertRaisesRegex(self, Exception, error_msg):
            self.wizard.get_formats('test.init')
        with assertRaisesRegex(self, Exception, error_msg):
            self.wizard.get_formats('test.txt')

    @patch('txclib.wizard.os.path.isfile')
    def test_run(self, api_mock, isfile_mock):
        isfile_mock.return_value = True

        # list of return values of Api.get for consecutive calls
        self.wizard.api.get.side_effect = [
            {
                "INI": {
                    "mimetype": "text/plain",
                    "file-extensions": ".ini",
                    "description": "Joomla INI File"
                },
                "SRT": {
                    "mimetype": "text/plain",
                    "file-extensions": ".srt",
                    "description": "SubRip subtitles"
                }
            },
            [
                {
                    "name": "Test Org",
                    "slug": "test-org",
                }
            ],
            [
                {
                    "name": "project 1",
                    "source_language": {"code": "en", "name": "English"},
                    "slug": "project-1",
                    "archived": False
                }
            ]
        ]
        with patch('txclib.wizard.input_prompt') as iprompt_mock, \
                patch('txclib.wizard.choice_prompt') as cprompt_mock:

            iprompt_mock.side_effect = ["test_file", "translations/<lang>.txt"]
            cprompt_mock.side_effect = ['INI', 'test-org', "project-1"]
            options = self.wizard.run()

            expected_options = {
                'source_file': 'test_file',
                'expression': 'translations/<lang>.txt',
                'i18n_type': 'INI',
                'source_language': 'en',
                'resource': 'project-1.test-file',
            }
            self.assertDictEqual(options, expected_options)
