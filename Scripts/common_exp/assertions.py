"""
Pre-run assertions.
"""

from common_exp.constants import LOGGER_IP, REQ_TIMEOUT
from common_exp.helpers import url_helper, get_requester_and_timeout


def assert_logger_running(mac_run=False):
    """ Without it no use of running """
    error_msg = 'Logger not running on ' + LOGGER_IP + ':5000'
    requester, timeout = get_requester_and_timeout(mac_run)
    try:
        response = requester.get(url_helper('ping'), timeout=REQ_TIMEOUT)
    except Exception:
        raise AssertionError(error_msg)
    if response.status_code != 200:
        raise AssertionError(error_msg)
