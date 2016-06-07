import unittest
from mock import patch, MagicMock
from urllib3.exceptions import SSLError

from txclib import utils


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
