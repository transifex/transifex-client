import unittest
from mock import Mock, patch
from txclib.commands import cmd_init, DEFAULT_TRANSIFEX_URL, \
    _get_host_from_options
from txclib.exceptions import ProjectAlreadyInitialized
from txclib.project import Project
from txclib.parsers import init_parser
from os import getcwd
from os.path import join


class TestCommands(unittest.TestCase):
    @patch("txclib.commands.logger")
    @patch("txclib.commands.Project")
    @patch("txclib.commands._create_config_file")
    @patch("txclib.commands._create_tx_path")
    @patch("txclib.commands.isdir")
    def test_cmd_init_when_tx_path_not_exists(
        self,
        mock_os_path_isdir,
        mock_create_tx_path,
        mock_create_config_file,
        mock_init_project,
        mock_logger  # mock logger to supress output
    ):
        """Test cmd_init in interactive mode, in case the config dir is not
        created yet
        """
        mock_os_path_isdir.return_value = False
        mock_create_tx_path.return_value = True
        mock_create_config_file.return_value = True
        # mock creation of project
        mock_project = Project(init=False)
        mock_project.getset_host_credentials = Mock()
        mock_project.save = Mock()
        mock_init_project.return_value = mock_project

        cmd_init(["--host", DEFAULT_TRANSIFEX_URL], "dummy_path")
        mock_os_path_isdir.assert_called_once_with(join(getcwd(), ".tx"))
        mock_create_tx_path.assert_called_once_with(getcwd())
        mock_create_config_file.assert_called_once_with(
            join(getcwd(), ".tx", "config"),
            DEFAULT_TRANSIFEX_URL
        )

    @patch("txclib.commands.logger")
    @patch("txclib.commands.confirm")
    @patch("txclib.commands.isdir")
    def test_cmd_init_interactive_when_tx_path_exists_and_not_save_optionwith_user_input_proceed(  # noqa
            self,
            mock_os_path_isdir,
            mock_utils_confirm,
            mock_logger  # mock logger to supress output
    ):
        """Test cmd_init in interactive mode, without force save option,
        in case the config dir is created the user should be asked
        to confirm overwrite. Stop if negative user input
        """
        # if user input  is negative, execution stops
        mock_os_path_isdir.return_value = True
        mock_utils_confirm.return_value = False

        cmd_init([], "dummy_path")
        mock_os_path_isdir.assert_called_once_with(join(getcwd(), ".tx"))
        mock_utils_confirm.assert_called_once()


    @patch("txclib.commands.logger")
    @patch("txclib.commands.Project")
    @patch("txclib.commands._create_config_file")
    @patch("txclib.commands._create_tx_path")
    @patch("txclib.commands.confirm")
    @patch("txclib.commands.isdir")
    def test_cmd_init_interactive_when_path_exists_and_not_save_option_with_user_input_proceed(  # noqa
            self,
            mock_os_path_isdir,
            mock_utils_confirm,
            mock_create_tx_path,
            mock_create_config_file,
            mock_init_project,
            mock_logger  # mock logger to supress output
    ):
        """Test cmd_init in interactive mode, without force save option,
        in case the config dir is created, the user should be asked
        to confirm overwrite. Proceed if positive user input
        """
        # if user input is positive, then proceed
        mock_os_path_isdir.return_value = True
        mock_utils_confirm.return_value = True

        mock_create_tx_path.return_value = True
        mock_create_config_file.return_value = True
        # mock creation of project
        mock_project = Project(init=False)
        mock_project.getset_host_credentials = Mock()
        mock_project.save = Mock()
        mock_init_project.return_value = mock_project

        cmd_init(["--host", DEFAULT_TRANSIFEX_URL], "dummy_path")
        mock_create_tx_path.assert_called_once_with(getcwd(), overwrite=True)


    @patch("txclib.commands.logger")
    @patch("txclib.commands.Project")
    @patch("txclib.commands._create_config_file")
    @patch("txclib.commands._create_tx_path")
    @patch("txclib.commands.isdir")
    def test_cmd_init_when_tx_path_exists_and_assume_yes_and_force_save(
            self,
            mock_os_path_isdir,
            mock_create_tx_path,
            mock_create_config_file,
            mock_init_project,
            mock_logger  # mock logger to supress output
    ):
        """Test cmd_init in non-interactive mode with force save option, should
        create overwrite configuration files
        """
        # if user input is positive, then proceed
        mock_os_path_isdir.return_value = True

        mock_create_tx_path.return_value = True
        mock_create_config_file.return_value = True
        # mock creation of project
        mock_project = Project(init=False)
        mock_project.getset_host_credentials = Mock()
        mock_project.save = Mock()
        mock_init_project.return_value = mock_project

        cmd_init(["--force-save","-y","--host", DEFAULT_TRANSIFEX_URL],
                 "dummy_path")
        mock_create_tx_path.assert_called_once_with(getcwd(), overwrite=True)


    @patch("txclib.commands.isdir")
    def test_cmd_init_when_tx_path_exists_and_assume_yes_option(
        self,
        mock_os_path_exists
    ):
        """Test cmd_init in non-interactive mode, in case the config dir is
        already created, then exception should be raised
        """
        mock_os_path_exists.return_value = True
        with self.assertRaises(ProjectAlreadyInitialized):
            cmd_init(["-y"], "dummy_path")


    @patch("txclib.commands.input")
    def test_get_host_from_options(self, mock_input):
        # Test when host is not provided by options, should ask input
        parser = init_parser()
        (options, args) = parser.parse_args([])
        mock_input.return_value = 'www.foo.com'

        self.assertEqual('https://www.foo.com', _get_host_from_options(options))
        mock_input.assert_called()

        # Test when host is not provided by options, and user input is None
        mock_input.return_value = ''

        self.assertEqual(DEFAULT_TRANSIFEX_URL, _get_host_from_options(options))
        mock_input.assert_called()

        # Test when host is provided by options
        (options, args) = parser.parse_args(["--host", "www.foo.com"])
        self.assertEqual('https://www.foo.com', _get_host_from_options(options))

        # Test when host is provided by options
        (options, args) = parser.parse_args(["--host", "www.foo.com"])
        self.assertEqual('https://www.foo.com', _get_host_from_options(options))

        # Test when host is not provided and in non-interactive mode
        (options, args) = parser.parse_args(["-y"])
        self.assertEqual(DEFAULT_TRANSIFEX_URL, _get_host_from_options(options))

        # Test when http host is already provided
        (options, args) = parser.parse_args(["--host", "http://www.foo.com"])
        self.assertEqual('http://www.foo.com', _get_host_from_options(options))