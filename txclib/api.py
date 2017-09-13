import six
import requests

from requests.auth import HTTPBasicAuth

from txclib.utils import parse_json
from txclib.urls import API_URLS, HOSTNAMES
from txclib.log import logger


class Api(object):

    USERNAME = 'api'
    VALID_CALLS = ['projects', 'organizations', 'formats']

    @classmethod
    def map_paths_to_hostnames(cls):
        return {
            path: hostname for hostname, paths in HOSTNAMES.items()
            for path in paths

        }

    def __init__(self, token=None, username=None, password=None):
        self.hostnames = self.map_paths_to_hostnames()
        if token:
            self.token = token
            self.username = self.USERNAME
        elif username and password:
            self.token = password
            self.username = username
        else:
            logger.error("Authorization credentials are missing. Make sure "
                         "that you have run `tx init` to setup your "
                         "credentials.")

    def get(self, api_call, *args, **kwargs):
        """
        Performs the GET api call specified by api_call and
        parses the response
        """
        # mock response
        if api_call not in self.VALID_CALLS:
            raise Exception(
                "Tried to perform unsupported api call {}".format(
                    api_call
                )
            )

        hostname = self.hostnames[api_call]
        url = API_URLS[api_call] % kwargs
        url = "{}{}".format(hostname, url)

        try:
            response = requests.get(
                url, auth=HTTPBasicAuth(self.USERNAME, self.token)
            )
            all_data = parse_json(response.content)
        except Exception as e:
            logger.debug(six.u(str(e)))
            raise

        next_page = response.links.get('next')
        while next_page:
            try:
                response = requests.get(
                    next_page['url'],
                    auth=HTTPBasicAuth(self.USERNAME, self.token)
                )
                all_data.extend(parse_json(response.content))
                next_page = response.links.get('next')
            except Exception as e:
                logger.debug(six.u(str(e)))
                raise
        return all_data
