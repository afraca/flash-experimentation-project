"""
The experiments share some code in generating the testcases.
"""

from itertools import repeat
from random import shuffle, seed
import requests
import requests.adapters

import common_exp.templates as templates
from common_exp.constants import LOGGER_IP, SEED, REQ_TIMEOUT


def url_helper(path):
    """ requests likes proper urls """
    return 'http://' + LOGGER_IP + ':5000/' + path


def get_classes(num_classes, num_sub_classes):
    """ Creates class names """
    for i in range(1, num_classes + 1):
        yield 'C' + str(i)
        for j in range(1, num_sub_classes + 1):
            yield 'C' + str(i) + str(j)


def get_call_vars(classnames, vart_templ=None):
    """ Before blocks of calling methods, we need variables """
    content = templates.LOOPVART
    template = templates.VART if vart_templ is None else vart_templ
    for classname in classnames:
        content += template.format(classname=classname)
    print('Done')
    return content


def get_class_content(classname, extending, num_methods, fun_templ=None, class_templ=None):
    """ A single class declaration """
    methodbodies = ''
    extends = ' extends ' + classname[:-1] if extending else ''
    override = 'override ' if extending else ''
    assert num_methods % 2 == 0
    for k in range(1, num_methods + 1):
        # Subclasses will override even methods
        if extending and k % 2 != 0:
            continue
        method = 'work' + str(k)
        # Unique string, partly for debug purposes
        uniq = 's' + str(k)
        template = templates.FUNCTIONT if fun_templ is None else fun_templ
        methodbodies += '\n'
        methodbodies += template.format(override=override, name=method, classname=classname, s2=uniq)
    template = templates.CLASST if class_templ is None else class_templ
    return template.format(classname=classname, extends=extends, methodbodies=methodbodies)


def get_call_block(classname, k, limit):
    """ A for-loop calling certain method """
    method = 'work' + str(k)
    return templates.CALLT.format(classname=classname, method=method, limit=limit)


def get_call_blocks(classname, num_methods, total_calls, num_blocks, debug=False, call_templ=None):
    """The file section where all the methods are called, split up in blocks and randomized """
    # Note that total_calls is actually per class!
    if not debug:
        assert total_calls >= 100 * 1000
    calls_per_method = total_calls // num_methods
    if not debug:
        assert calls_per_method > 100
    assert calls_per_method % num_blocks == 0
    calls_per_block = calls_per_method // num_blocks
    # We want a representation of the 'blocks', where each block
    # belongs to a certain method
    blocks = [repeat(method, num_blocks) for method in range(1, num_methods + 1)]
    # It's list of lists, e.g. [[1,1,1,1], [2,2,2,2] etc] , flatten for easier use
    flat_blocks = [item for sublist in blocks for item in sublist]
    if not debug:
        # Reproducible randomness
        seed(SEED)
        shuffle(flat_blocks)
    out = ''
    for index in flat_blocks:
        method = 'work' + str(index)
        template = templates.CALLT if call_templ is None else call_templ
        out += template.format(limit=calls_per_block, classname=classname, method=method)
    return out


def header(contents):
    """ For pretty output """
    line = '----------'
    print(line, contents, line, sep="\n")


def get_requester_and_timeout(mac_run=False):
    """ Local network communication currently quite flaky... """
    timeout = REQ_TIMEOUT
    if mac_run:
        timeout *= 20
        session = requests.session()
        adapter = requests.adapters.HTTPAdapter(max_retries=20)
        session.mount('http://', adapter)
        requester = session
    else:
        requester = requests
    return requester, timeout
