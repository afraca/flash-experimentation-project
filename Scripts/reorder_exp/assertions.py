"""
Helpers for the experiment concerning reordering method calls
"""

import os
from subprocess import run, PIPE
import reorder_exp.constants as constants
from common_exp.helpers import url_helper, get_requester_and_timeout


def assert_rabcdasm_installed():
    """ rabcdasm required for optimizing """
    try:
        # No arguments given will pollute stderr
        run('rabcdasm', stderr=PIPE)
    except FileNotFoundError:
        raise AssertionError('RABCDAsm not installed')


def assert_players_there():
    """ Cannot launch what's not there """
    exp_path = os.path.dirname(constants.PROJECTS_PATH)
    for name in constants.SA_PLAYERS:
        full_player_path = os.path.join(exp_path, 'players', name)
        if not os.path.isfile(full_player_path):
            raise KeyError('Player ' + name + ' not found')


def assert_no_marks(mac_run=False):
    """ Begin with no "done" markers in the database """
    # This is more of a preparing step, than an assertion...
    requester, timeout = get_requester_and_timeout(mac_run)
    requester.get(url_helper('unmark'), timeout=timeout)
