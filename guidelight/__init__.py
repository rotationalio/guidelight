"""
A library for developing task-oriented AI systems that integrate with Endeavor.
"""

##########################################################################
## Module Info
##########################################################################

# Import the version number at the top level
from .version import __version_info__, get_version
from dotenv import load_dotenv

from .client import Client
from .endeavor import Endeavor

##########################################################################
## Package Version
##########################################################################

__version__ = get_version(short=True)

__all__ = ["Client", "Endeavor", "__version__", "__version_info__", "client", "connect"]


##########################################################################
## Primary API Entry Point
##########################################################################

def client(url=None, client_id=None, client_secret=None, auth_url=None, timeout=None):
    """
    Create and authenticate a low-level API client.

    Use this entry point when direct access to an endpoint is required. For the
    high-level SDK, use :func:`connect` instead.
    """
    if url is None or client_id is None or client_secret is None or auth_url is None:
        load_dotenv()

    transport = Client(
        url=url,
        client_id=client_id,
        client_secret=client_secret,
        auth_url=auth_url,
        timeout=timeout,
    )
    transport._pre_flight(require_authentication=True)
    return transport


def connect(url=None, client_id=None, client_secret=None, auth_url=None, timeout=None):
    """
    Create an authenticated high-level Endeavor SDK with the specified URL and API
    key material. If not specified, this function will first load any .env files in
    the local path, then attempt to configure the client from the environment.

    Parameters
    ----------
    url : str
        The URL of your Endeavor server (e.g. https://guidelight.dev). If not
        set, it is discovered from the $ENDEAVOR_URL environment variable.

    client_id : str
        The Client ID from your API Key to access your Endeavor server. If not set, it
        is discovered from the $ENDEAVOR_CLIENT_ID environment variable.

    client_secret : str
        The Client Secret from your API Key to access your Endeavor server. If not set,
        it is discovered from the $ENDEAVOR_CLIENT_SECRET environment variable.

    auth_url : str
        The URL of your authentication server (e.g. https://auth.guidelight.dev). If not
        set, it is discovered from the $ENDEAVOR_AUTH_URL environment variable and falls
        back to the url specified otherwise.

    timeout : float
        The number of seconds to wait for a response until error.
    """

    transport = client(
        url=url,
        client_id=client_id,
        client_secret=client_secret,
        auth_url=auth_url,
        timeout=timeout,
    )
    return Endeavor(transport)