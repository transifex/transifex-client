import os
import time
import unittest
import six
from mock import patch, MagicMock, Mock, mock_open
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

        # In case the http proxy variable exists but is empty,
        # it shouldn't break things
        with patch.dict(os.environ, {'http_proxy': ''}):
            utils.make_request(
                'GET',
                host,
                url,
                'a_user',
                'a_pass'
            )
            mock_manager.assert_called_with(num_pools=1)
            self.assertEqual(mock_connection.request.call_count, 2)

        # In case the https proxy variable exists but is empty,
        # it shouldn't break things
        with patch.dict(os.environ, {'https_proxy': ''}):
            utils.make_request(
                'GET',
                host,
                url,
                'a_user',
                'a_pass'
            )
            mock_manager.assert_called_with(num_pools=1)
            self.assertEqual(mock_connection.request.call_count, 3)

    @patch('urllib3.ProxyManager')
    def test_makes_request_with_proxy(self, mock_manager):
        response_mock = MagicMock()
        response_mock.status = 200
        response_mock.data = 'test_data'

        mock_connection = MagicMock()
        mock_connection.request.return_value = response_mock
        mock_manager.return_value = mock_connection
        url = '/my_test_url/'

        # Test http
        host = 'http://whynotestsforthisstuff.com'
        with patch.dict(os.environ, {'http_proxy': 'proxy.host:333'}):
            utils.make_request(
                'GET',
                host,
                url,
                'a_user',
                'a_pass'
            )
            mock_manager.assert_called_once_with(num_pools=1,
                                                 proxy_headers=Any(),
                                                 proxy_url='http://proxy.host:333')
            mock_connection.request.assert_called_once()

        # Test https
        host = 'https://whynotestsforthisstuff.com'
        with patch.dict(os.environ, {'https_proxy': 'proxy.host:333'}):
            utils.make_request(
                'GET',
                host,
                url,
                'a_user',
                'a_pass'
            )
            mock_manager.assert_called_with(num_pools=1,
                                            proxy_headers=Any(),
                                            proxy_url='https://proxy.host:333',
                                            ca_certs=Any(),
                                            cert_reqs=Any())
            self.assertEqual(mock_connection.request.call_count, 2)

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


class ProjectFilesTestCase(unittest.TestCase):

    def test_project_files_scanning(self):
        """
        Test that the project files filter works as expected.
        """
        # XXX: This testcase depends on the current file structure

        # Test with a valid expression on directory-level
        expressions = ["tests/project_dir/test_expressions/<lang>/test.txt",
                       "./tests/project_dir/test_expressions/<lang>/test.txt"]

        for expr in expressions:
            langs = []
            for file, lang in utils.get_project_files(os.getcwd(), expr):
                langs.append(lang)
                self.assertTrue(file.endswith("{}/test.txt".format(lang)))
            self.assertListEqual(sorted(langs), sorted(["en", "es"]))

        # Test with a valid expression on file-level with different prefixes
        expressions = ["tests/project_dir/test_expressions/bulk/1.<lang>.po",
                       "tests/project_dir/test_expressions/bulk/2_<lang>.po",
                       "tests/project_dir/test_expressions/bulk/3 <lang>.po"]

        for expr in expressions:
            langs = []
            for file, lang in utils.get_project_files(os.getcwd(), expr):
                langs.append(lang)
                self.assertTrue(file.endswith("{}.po".format(lang)))
            self.assertListEqual(sorted(langs), sorted(["en_SE", "en"]))

        # Test with an invalid expression that doesn't contain <lang>
        expression = "tests/project_dir/test_expressions/bulk/1.en.po"
        msg = r"File filter (.*) does not contain"

        with six.assertRaisesRegex(self, exceptions.MalformedConfigFile, msg):
            for file, lang in utils.get_project_files(os.getcwd(), expression):
                pass

class GitUtilsTestCase(unittest.TestCase):

    def test_fetch_timestamp_from_git_tree(self):
        # A bit meta, lets try to get the timestamp of the
        # current file
        epoch_ts = utils.get_git_file_timestamp(
            os.path.dirname(os.path.abspath(__file__))
        )
        self.assertIsNotNone(epoch_ts)

    def test_git_timestamp_is_parsable(self):
        # A bit meta, lets try to get the timestamp of the
        # current file
        epoch_ts = utils.get_git_file_timestamp(
            os.path.dirname(os.path.abspath(__file__))
        )
        parsed_ts = time.mktime(time.gmtime(epoch_ts))
        self.assertIsNotNone(parsed_ts)

    def test_uses_authorized_date(self):
        commit = Mock()
        commit.authored_date = 1590969254
        commit.committed_date = 1590970456
        with patch('txclib.utils.git.Repo') as repo:
            repo.return_value.iter_commits.return_value = [commit]
            epoch_ts = utils.get_git_file_timestamp('any')
        self.assertEqual(1590969254, epoch_ts)
