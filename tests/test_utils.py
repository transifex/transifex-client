import unittest
from mock import patch, MagicMock, mock_open
from urllib3.exceptions import SSLError

from txclib import utils, exceptions


# XXX: Taken from https://stackoverflow.com/a/21611963
def Any():
    """A method that will match any parameter."""
    class Any(object):
        def __eq__(self, *args):
            return True
    return Any()


class MakeRequestTestCase(unittest.TestCase):

    @patch('urllib3.PoolManager')
    def test_makes_request(self, mock_manager):
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_manager.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        utils.make_request(
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )
        mock_manager.assert_called_once_with(num_pools=1)
        mock_connection.request.assert_called_once()

    @patch('urllib3.PoolManager')
    @patch('txclib.utils.logger')
    def test_catches_ssl_error(self, mock_logger, mock_manager):
        mock_connection = MagicMock()
        mock_connection.request.side_effect = SSLError('Boom!')
        mock_manager.return_value = mock_connection

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
    @patch('urllib3.PoolManager')
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
        mock_conn.assert_called_once_with(num_pools=1)
        mock_connection.request.assert_called_once()
        mock_determine.assert_not_called()

    @patch('urllib3.PoolManager')
    def test_makes_request_404(self, mock_manager):
        response_mock = MagicMock()
        response_mock.status = 404
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_manager.return_value = mock_connection

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

    @patch('urllib3.PoolManager')
    def test_makes_request_403(self, mock_manager):
        response_mock = MagicMock()
        response_mock.status = 403
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_manager.return_value = mock_connection

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

    @patch('urllib3.PoolManager')
    def test_makes_request_401(self, mock_manager):
        response_mock = MagicMock()
        response_mock.status = 401
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_manager.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        self.assertRaises(
            exceptions.AuthenticationError,
            utils.make_request,
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )

    @patch('urllib3.PoolManager')
    def test_makes_request_connection_error(self, mock_manager):
        """Tests for common 50X connection errors."""
        for code in range(500, 506):
            mock_connection = MagicMock()
            mock_connection.request.return_value = MagicMock(status=code,
                                                             data=None)
            mock_manager.return_value = mock_connection

            host = 'http://whynotestsforthisstuff.com'
            url = '/my_test_url/'
            args = ('GET', host, url, 'a_user', 'a_pass',)
            with self.assertRaises(exceptions.TXConnectionError) as err:
                utils.make_request(*args)
            self.assertEqual(err.exception.response_code, code)

    @patch('urllib3.PoolManager')
    def test_makes_request_None(self, mock_manager):
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.data = None

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_manager.return_value = mock_connection

        host = 'http://whynotestsforthisstuff.com'
        url = '/my_test_url/'
        utils.make_request(
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )
        mock_manager.assert_called_once_with(num_pools=1)
        mock_connection.request.assert_called_once()

    @patch('urllib3.PoolManager')
    def test_url_format(self, mock_manager):
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.data = None

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_manager.return_value = mock_connection

        host = 'http://test.com/'
        url = '/path/to/we/'
        expected_url = 'http://test.com/path/to/we/'
        utils.make_request(
            'GET',
            host,
            url,
            'a_user',
            'a_pass'
        )
        mock_connection.request.assert_called_once_with('GET',
                                                        expected_url,
                                                        fields=Any(),
                                                        headers=Any())

    def test_get_current_branch_root_dir_no_git(self):
        with patch('txclib.utils.os.getcwd') as cwd_mock, \
             patch('txclib.utils.os.path.isdir') as isdir_mock:

            cwd_mock.return_value = '/usr/local/test_cli'
            isdir_mock.return_value = False
            b = utils.get_current_branch('/usr/local/test_cli')
            self.assertEqual(b, None)

    def test_get_current_branch_root_dir_with_git(self):
        data = "ref: refs/heads/test_branch\n"
        with patch('txclib.utils.os.getcwd') as cwd_mock, \
             patch('txclib.utils.os.path.isdir') as isdir_mock, \
             patch("txclib.utils.open", mock_open(read_data=data)):

            cwd_mock.return_value = '/usr/local/test_cli'
            isdir_mock.return_value = True
            b = utils.get_current_branch('/usr/local/test_cli')
            self.assertEqual(b, 'test_branch')

    def test_get_current_branch_subdir_with_git(self):
        data = "ref: refs/heads/test_branch\n"
        with patch('txclib.utils.os.getcwd') as cwd_mock, \
             patch('txclib.utils.os.path.isdir') as isdir_mock, \
             patch("txclib.utils.open", mock_open(read_data=data)):

            cwd_mock.return_value = '/usr/local/test_cli/files'
            isdir_mock.side_effects = [False, True]
            b = utils.get_current_branch('/usr/local/test_cli')
            self.assertEqual(b, 'test_branch')

    def test_get_current_branch_contains_slash(self):
        data = "ref: refs/heads/test_branch/abc\n"
        with patch('txclib.utils.os.getcwd') as cwd_mock, \
             patch('txclib.utils.os.path.isdir') as isdir_mock, \
             patch("txclib.utils.open", mock_open(read_data=data)):

            cwd_mock.return_value = '/usr/local/test_cli'
            isdir_mock.side_effects = [False, True]
            b = utils.get_current_branch('/usr/local/test_cli')
            self.assertEqual(b, 'test_branch/abc')
