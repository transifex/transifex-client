# -*- coding: utf-8 -*-

import unittest
from mock import MagicMock, patch

from txclib.api import Api


class ApiTestCase(unittest.TestCase):

    @patch('txclib.utils.get_api_domains')
    @patch('requests.get')
    def test_resolve_api_call(self, requests_mock, domains_mock):
        token = 'blabla'
        domains_mock.return_value = {
            'hostname': 'https://www.foo.bar',
            'api_hostname': 'https://api.foo.bar'
        }
        response_mock = MagicMock()
        response_mock.json.return_value = {"some": "json data"}
        response_mock.links = {}
        requests_mock.return_value = response_mock
        api = Api(token=token)
        api.get('formats')
        self.assertEqual(
            requests_mock.call_args[0][0],
            'https://www.foo.bar/api/2/formats/',
        )
        requests_mock.reset_mock()
        requests_mock.return_value = response_mock
        api.get('organizations')
        self.assertEqual(
            requests_mock.call_args[0][0],
            'https://api.foo.bar/organizations/',
        )

    @patch('txclib.utils.get_api_domains')
    @patch('requests.get')
    def test_pagination(self, requests_mock, domains_mock):
        token = 'blabla'
        domains_mock.return_value = {
            'hostname': 'https://www.foo.bar',
            'api_hostname': 'https://api.foo.bar'
        }
        first_response_mock = MagicMock()
        first_response_mock.json.return_value = [{"key1": "json data"}]
        first_response_mock.links = {
            'next': {'url': 'https://www.foo.bar/api/2/formats/?page=2'}}
        second_response_mock = MagicMock()
        second_response_mock.json.return_value = [{"key2": "json data"}]
        second_response_mock.links = {}
        requests_mock.side_effect = [
            first_response_mock,
            second_response_mock
        ]
        api = Api(token=token)
        data = api.get('formats')
        self.assertEqual(
            requests_mock.call_args_list[0][0][0],
            'https://www.foo.bar/api/2/formats/',
        )
        self.assertEqual(
            requests_mock.call_args_list[1][0][0],
            'https://www.foo.bar/api/2/formats/?page=2',
        )
        self.assertEqual(data, [
            {"key1": "json data"},
            {"key2": "json data"}
        ])

    def test_invalid_call(self):
        api = Api(token='blabla')
        with self.assertRaises(Exception):
            api.get('invalid')
