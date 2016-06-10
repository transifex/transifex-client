import unittest
from mock import patch, MagicMock
from urllib3.exceptions import SSLError

from txclib import utils, exceptions


class MakeRequestTestCase(unittest.TestCase):

    @patch('urllib3.connection_from_url')
    def test_makes_request(self, mock_connection_from_url):
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_connection_from_url.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        utils.make_request(
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )
        mock_connection_from_url.assert_called_once_with(host)
        mock_connection.request.assert_called_once()

    @patch('urllib3.connection_from_url')
    @patch('txclib.utils.logger')
    def test_catches_ssl_error(self, mock_logger, mock_connection_from_url):
        mock_connection = MagicMock()
        mock_connection.request.side_effect = SSLError('Boom!')
        mock_connection_from_url.return_value = mock_connection

        host = 'https://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        self.assertRaises(
            SSLError,
            utils.make_request,
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )
        mock_logger.error.assert_called_once_with("Invalid SSL certificate")

    @patch('txclib.utils.determine_charset')
    @patch('urllib3.connection_from_url')
    def test_makes_request_skip_decode(self, mock_conn, mock_determine):
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_conn.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        utils.make_request(
            'GET',
            host,
            url,
            'a_user',
            'a_pass',
            skip_decode=True
        )
        mock_conn.assert_called_once_with(host)
        mock_connection.request.assert_called_once()
        mock_determine.assert_not_called()

    @patch('urllib3.connection_from_url')
    def test_makes_request_404(self, mock_connection_from_url):
        response_mock = MagicMock()
        response_mock.status = 404
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_connection_from_url.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        self.assertRaises(
            exceptions.HttpNotFound,
            utils.make_request,
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )

    @patch('urllib3.connection_from_url')
    def test_makes_request_403(self, mock_connection_from_url):
        response_mock = MagicMock()
        response_mock.status = 403
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_connection_from_url.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        self.assertRaises(
            Exception,
            utils.make_request,
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )

    @patch('urllib3.connection_from_url')
    def test_makes_request_401(self, mock_connection_from_url):
        response_mock = MagicMock()
        response_mock.status = 401
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_connection_from_url.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        self.assertRaises(
            exceptions.HttpNotAuthorized,
            utils.make_request,
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )

    @patch('urllib3.connection_from_url')
    def test_makes_request_None(self, mock_connection_from_url):
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.data = None

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_connection_from_url.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        utils.make_request(
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )
        mock_connection_from_url.assert_called_once_with(host)
        mock_connection.request.assert_called_once()
