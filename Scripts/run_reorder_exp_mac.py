"""
Download compiled swf's, play all in browser.
"""

import requests
from pathlib import Path
from zipfile import ZipFile
import os
import re
from subprocess import run
from sys import platform, version_info
from selenium import webdriver

from common_exp.constants import LOGGER_IP, REQ_TIMEOUT
from common_exp.assertions import assert_logger_running
from reorder_exp.constants import HTML_WRAP_TEMPLATE, FLASH_PROFILE_ITERATIONS, FLASH_SECS_FOR_RUN
from reorder_exp.helpers import plugin_play_checker, get_config_from_entry
from reorder_exp.assertions import assert_no_marks

SWF_LOCATION = 'https://vps924.directvps.nl/owncloud/index.php/s/ERPQbIyJQDUffZW/download'
ZIP_NAME = 'all_swfs.zip'


def mac_assertions():
    """ Prevent accidental running in dev env elsewhere, and accidental invoking with py2"""
    assert platform == 'darwin'
    assert version_info >= (3, 0)


def entry_for_old_compiler(entry):
    """ When opening swf from old compiler in tab, it will not end, take precautions """
    parts = entry.name.split('_')
    # Assuming formatted like name_compiler_optimized_base64.swf
    return parts[1] == '0'


def download_swf_zip():
    """ There is a zip with all swf's somewhere, get all files from that """
    response = requests.get(SWF_LOCATION, timeout=REQ_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError('Could not get .zip for swfs')
    zip_path = Path.cwd().parent / ZIP_NAME
    with open(str(zip_path), 'wb') as file:
        for chunk in response:
            file.write(chunk)
    with ZipFile(str(zip_path)) as swf_zip:
        print('Extracting all swf files from zip')
        swf_zip.extractall(str(Path.cwd().parent))


def get_projects():
    """ _ """
    pat = r'(\S+)\_\d\_\d'
    swf_dir = str(Path.cwd().parent)
    for entry in os.scandir(swf_dir):
        if not entry.name.endswith('.swf'):
            continue
        # Assuming formatted like name_d_d_base64configstring.swf
        matches = re.findall(pat, entry.name)
        if matches:
            project = matches[0]
        else:
            project = entry.name
            print('Warning, malformed name detected')
        yield (project, entry)


def write_html_wrapper(project, entry):
    """ Create simple html file which embeds swf file """
    html_name = 'wrap-' + entry.name[:-3] + 'html'
    contents = HTML_WRAP_TEMPLATE.format(host=LOGGER_IP, swf_file=entry.name)
    out_path = Path.cwd().parent / html_name
    config = get_config_from_entry(entry)
    print('Writing html wrapper for ' + project)
    print('Config: {}'.format(str(config)))
    with open(str(out_path), 'w') as file:
        file.writelines(contents)


def play(project, entry):
    """ Make browser open html file, tricky with swf files from old compiler (Selenium required) """
    html_name = 'wrap-' + entry.name[:-3] + 'html'
    out_path = Path.cwd().parent / html_name
    timeout = FLASH_PROFILE_ITERATIONS * FLASH_SECS_FOR_RUN
    from_old_compiler = entry_for_old_compiler(entry)
    check_config = {}
    if not from_old_compiler:
        run(['open', str(out_path)], timeout=timeout)
    else:
        file_url = 'file://' + str(out_path)
        # Need Flash to trust files from directory, but Chrome Driver from Selenium has no memory
        # Use normal Chrome Flash player
        options = webdriver.ChromeOptions()
        plugin_path = '~/Library/Application Support/Google/Chrome/PepperFlash/24.0.0.186/PepperFlashPlayer.plugin'
        options.add_argument(
            '--ppapi-flash-path={}'.format(plugin_path))
        options.add_argument('--ppapi-flash-version=24.0.0.186')
        options.add_argument('--user-data-dir=~/Library/Application Support/Google/Chrome/Default')
        dr = webdriver.Chrome(chrome_options=options)
        dr.get(file_url)
        check_config['old_compiler'] = True
        check_config['driver'] = dr
    plugin_play_checker(check_config, timeout_limit_factor=0.5)


def main():
    """ See module docstring """
    mac_assertions()
    assert_logger_running(mac_run=True)
    assert_no_marks(mac_run=True)
    steps = {
        'download': False,
        'write': True,
        'play': True
    }
    if steps['download']:
        download_swf_zip()
    for project, entry in get_projects():
        if steps['write']:
            write_html_wrapper(project, entry)
        if steps['play']:
            play(project, entry)
    print('Done')


if __name__ == '__main__':
    main()
