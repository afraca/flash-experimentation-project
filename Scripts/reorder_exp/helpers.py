"""
Helpers for the experiment concerning reordering method calls
"""
import os
import requests
import requests.adapters
from time import sleep
import re
from base64 import b64decode
import pickle

from reorder_exp.constants import FLASH_PROFILE_ITERATIONS, FLASH_SECS_FOR_RUN, SA_PLAYERS
from common_exp.constants import REQ_TIMEOUT
from common_exp.helpers import url_helper


def swf_scandir(path):
    """ Normal scandir, but only find swf files compiled by this script """
    pat = r'_\d_\d_'
    for entry in os.scandir(path):
        matches = re.findall(pat, entry.name)
        if matches and entry.name.endswith('.swf'):
            yield entry


def plugin_play_checker(mac_config=None, timeout_limit_factor=1):
    """ We lose control when spawning browser, here we keep checking for updates and move on when appropriate """
    done = False
    timeout_count = 0
    # Adjust to runtime (seconds)
    timeout_limit = int(timeout_limit_factor * FLASH_PROFILE_ITERATIONS * FLASH_SECS_FOR_RUN)
    timeout = REQ_TIMEOUT
    # cross-network is flaky at the moment...
    if mac_config is not None:
        timeout *= 20
        session = requests.session()
        adapter = requests.adapters.HTTPAdapter(max_retries=20)
        session.mount('http://', adapter)
        requester = session
    else:
        requester = requests
    while not done:
        response = requester.get(url_helper('asktabdone'), timeout=timeout)
        done = response.status_code == 200 and response.text == '1'
        timeout_count += 1
        if timeout_count == timeout_limit:
            print('Plugin play timed out, moving on')
            done = True
            # We know it will never end in this situation, and was spawned by Selenium
            if mac_config is not None and mac_config['old_compiler']:
                mac_config['driver'].close()
        if not done:
            msg = 'Waiting 1s for update, cur count: {}, max: {}'
            print(msg.format(timeout_count, timeout_limit))
            sleep(1)
    # Register we've seen mark and moving on
    if timeout_count != timeout_limit:
        print('Seen done-marker, moving on')
    requester.get(url_helper('unmark'), timeout=timeout)


def will_entry_play(entry, sa_name=None):
    """ Simple wrapper for will_it_play """
    name_parts = entry.name.split('_')
    compiler_id = int(name_parts[1])
    return will_it_play(compiler_id, sa_name)


def will_it_play(compiler_id, sa_name=None):
    """ Known some combinations will not work """
    # Oldest compiler with new plugin will not work
    if sa_name is None and compiler_id == 0:
        return False
    # Old player will not play files from newest compiler
    if sa_name == SA_PLAYERS[0] and compiler_id == 3:
        return False
    return True


def did_it_play(compiler_id, version, versions):
    """ For writing results, annoying to merge with will_it_play with different version etc """
    # Oldest compiler with new plugin will not work
    is_plugin = versions[version][0] == 0
    if is_plugin and compiler_id == 0:
        return False
    # Old player will not play files from newest compiler
    if versions[version][1] == 0 and compiler_id == 3:
        return False
    return True


def get_config_from_entry(entry):
    """ Common to get some information for displaying progress etc """
    parts = entry.name.split('_')
    b64_config = parts[3][:-4]
    config = pickle.loads(b64decode(b64_config))
    return config


def print_entry_config(entry):
    """ Simple wrapper """
    config = get_config_from_entry(entry)
    print('(config: {})'.format(str(config)))
