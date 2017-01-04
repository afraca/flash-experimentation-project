"""
Stage2 is on Linux.

    Compile with asc.jar:
    java -jar avmplus/utils/asc.jar -AS3 (-optimize) -import avmplus/generated/builtin.abc callmethod_0.as

    Disassemble
    Change to use right `callmethod` opcode
    Assemble
    (output file callmethod_1.abc)

    time avmp/bin-release/shell/avmshell (-Djitordie) callmethod_0.abc
    time avmp/bin-release/shell/avmshell (-Djitordie) callmethod_1.abc

"""
from sys import version_info
from platform import system

# Prevent accidentally running in py2 on Ubuntu
assert version_info >= (3, 0)
assert system() == 'Linux'

from subprocess import run
from pathlib import Path
from shutil import copy, rmtree
from os import remove
import resource
import re
import requests
from time import sleep
import pickle
from base64 import b64encode

from common_exp.helpers import header
from common_exp.assertions import assert_logger_running
from common_exp.constants import LOGGER_IP, SEED
from callmethod_exp.constants import (SOURCE_PATH, RABCDASM_PATH, ASC_PATH,
                                      BUILTINS_PATH, AVM_SHELL_PATH, NUM_RUMS, DEBUG,
                                      EXP_CONFIGS)


def pre_clean():
    """ Remove previously generated files to avoid errors """
    for entry in SOURCE_PATH.iterdir():
        if entry.is_dir():
            rmtree(str(entry))
            print('Removed old folder ' + str(entry))
        else:
            remove(str(entry))
            print('Removed old file ' + str(entry))


def copy_src():
    """ Because of read-only for shared folder move over file"""
    input_file = str(Path.cwd().parent / 'sf_AvmshellTests' / 'callmethod_0.as')
    output_dir = str(SOURCE_PATH)
    copy(input_file, output_dir)
    print('Copy done')


def compile_as(compile_flags):
    """ Simple compile with asc.jar """
    input_file = str(SOURCE_PATH / 'callmethod_0.as')
    # -strict
    cmd = ['java', '-jar', str(ASC_PATH), '-AS3'] + compile_flags + ['-import', str(BUILTINS_PATH), input_file]
    print('Compiling with: {}'.format(' '.join(cmd)))
    run(cmd)
    print('Compilation done')


def copy_bytecode():
    """ Because re-assembly overwrites file we copy early and edit that one """
    input_file = str(SOURCE_PATH / 'callmethod_0.abc')
    output_file = str(SOURCE_PATH / 'callmethod_1.abc')
    copy(input_file, output_file)
    print('Copy for for bytecode edit done')


def disassemble():
    """ Because re-assembly overwrites file we copy early and edit that one """
    input_file = str(SOURCE_PATH / 'callmethod_1.abc')
    dasm_path = str(RABCDASM_PATH / 'rabcdasm')
    run([dasm_path, input_file])
    print('Disassemble done')


def optimize():
    """ Replace all work{i} with callmethod {i} """
    script_name = 'script_0.script.asasm'
    script_path = SOURCE_PATH / 'callmethod_1' / script_name
    regex = r'callproperty\s+Multiname\(\"work(\d\d?)'
    with open(str(script_path)) as file:
        contents = file.readlines()
    with open(str(script_path), 'w') as file:
        for line in contents:
            matches = re.findall(regex, line)
            if matches:
                replacement = (matches[0] if not DEBUG else '50') + '\n'
                line = 'callmethod {}, 0'.format(replacement)
            file.write(line)
    print('Updating to `callmethod` calls done')


def assemble():
    """ Use assembly tool to update swf file with optimized code """
    asm_path = str(RABCDASM_PATH / 'rabcasm')
    file = str(SOURCE_PATH / 'callmethod_1/callmethod_1.main.asasm')
    run([asm_path, file])
    print('Assemble done')


def run_shell(optimized, runs, run_flags):
    """ Run swf file with avmshell """
    if not optimized:
        file = str(SOURCE_PATH / 'callmethod_0.abc')
    else:
        file = str(SOURCE_PATH / 'callmethod_1.abc')
    results = []
    run_parts = [str(AVM_SHELL_PATH)] + run_flags + [file]
    print('Run config = {}'.format(str(run_flags)))
    for iteration in range(runs):
        print('Iteration {} of {}'.format(iteration + 1, runs))
        # Thanks http://stackoverflow.com/a/13933797
        usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
        run(run_parts)
        usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
        user_time = usage_end.ru_utime - usage_start.ru_utime
        system_time = usage_end.ru_stime - usage_start.ru_stime
        max_rss = usage_end.ru_maxrss
        ix_rss = usage_end.ru_ixrss
        id_rss = usage_end.ru_idrss
        result = {
            'utime': user_time,
            'stime': system_time,
            'maxrss': max_rss,
            'ixrss': ix_rss,
            'idrss': id_rss
        }
        results.append(result)
    return results


def process_results(results, optimized, compile_flags, run_flags):
    """ Get the results in the database """
    config = b64encode(pickle.dumps((compile_flags, run_flags)))
    for result in results:
        logger = 'http://{}:5000/callmethod'.format(LOGGER_IP)
        payload = {
            'optimized': 1 if optimized else 0,
            'utime': result['utime'],
            'stime': result['stime'],
            'maxrss': result['maxrss'],
            'ixrss': result['ixrss'],
            'idrss': result['idrss'],
            'seed': SEED,
            'config': config
        }
        print('Sending result...')
        response = requests.get(logger, params=payload)
        if response.status_code != 200:
            raise Exception(response.text)
        # Logger sometimes stalls when requests come too fast
        sleep(0.2)
    print('Done logging results to DB')


def main():
    """ See module documentation """
    for compile_flags, run_flags in EXP_CONFIGS:
        header('Asserting requirements')
        assert_logger_running()
        pre_clean()
        header('Copying files to own linux folder')
        copy_src()
        header('Compiling .as file')
        compile_as(compile_flags)
        header('Copying for bytecode edit')
        copy_bytecode()
        header('Disassembling')
        disassemble()
        header('Optimizing')
        optimize()
        header('Re-assembling')
        assemble()
        header('Running non-optimized {}x'.format(NUM_RUMS))
        results_0 = run_shell(False, NUM_RUMS, run_flags)
        header('Running optimized {}x'.format(NUM_RUMS))
        results_1 = run_shell(True, NUM_RUMS, run_flags)
        header('Doing things with timing results')
        process_results(results_0, False, compile_flags, run_flags)
        process_results(results_1, True, compile_flags, run_flags)


if __name__ == '__main__':
    main()
