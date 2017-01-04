"""
This iterates through all the projects for the experiment, compiles them
in different ways, than applies a transformation step to all the
compilation results. Then for all resulting swf files, we play them
in different contexts.
"""
import os
import re
import shutil
from subprocess import CalledProcessError, TimeoutExpired, run
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
import pickle
from base64 import b64encode
from functools import partial

from common_exp.helpers import header
from common_exp.assertions import assert_logger_running
from common_exp.constants import LOGGER_IP, SEED
from reorder_exp.constants import (PROJECTS_PATH, ORIGIN_PROJECT,
                                   SA_PLAYERS, FF_PATH, FLASH_PROFILE_ITERATIONS,
                                   HTML_WRAP_TEMPLATE, FLASH_SECS_FOR_RUN,
                                   NUM_BLOCKS, NUM_METHODS, TOTAL_CALLS, DEBUG, TEST_TARGETS)
from reorder_exp.helpers import swf_scandir, plugin_play_checker, will_entry_play, print_entry_config
from reorder_exp.assertions import (assert_no_marks, assert_players_there, assert_rabcdasm_installed)


def import_common_files(project):
    """ Use  benchmarking files from 1 location, cannot symlink """
    files = ['ISubjectWrapper.as', 'Main.as', 'ProfileResult.as']
    source_path = os.path.join(PROJECTS_PATH, project, 'src')
    for file in files:
        file_path = os.path.join(source_path, file)
        origin_path = os.path.join(PROJECTS_PATH, ORIGIN_PROJECT, 'src', file)
        if os.path.exists(file_path):
            os.remove(file_path)
        shutil.copy(origin_path, file_path)
        print('Copied ' + origin_path)


def get_projects():
    """ In theory possible to do multiple experiments at once """
    for entry in os.listdir(PROJECTS_PATH):
        fullpath = os.path.join(PROJECTS_PATH, entry)
        if os.path.isdir(fullpath):
            yield entry
        else:
            raise ValueError('Files should not be in SourceProjects: ' + (str(entry)))


def get_compile_commands(project):
    """ Will yield for this project multiple ways in which the project can be compiled with different compilers """
    compiler_paths = {
        0: '"C:\\Program Files (x86)\\Adobe\\Flex Builder 3\\sdks\\3.2.0\\bin\\mxmlc"',
        1: '"C:\\Users\\sije\\AppData\\Local\\apache_flex_4_9_1\\bin\\mxmlc"',
        2: '"C:\\Users\\sije\\AppData\\Local\\apache_flex_4_15_0\\bin\\mxmlc"',
        3: '"C:\\Users\\sije\\AppData\\Local\\FlashDevelop\\Apps\\ascsdk\\23.0.0\\bin\\mxmlc"'
    }
    compiler_names = {
        0: 'Adobe Flex Compiler (mxmlc) 3.2.0 build 3958',
        1: 'Apache Flex Compiler (mxmlc) 4.9.1 build 1447119',
        2: 'Apache Flex Compiler (mxmlc) 4.15.0 build 20160104',
        3: 'Adobe ActionScript Compiler (mxmlc) Version 2.0.0 build 354194'
    }
    enabled = [0, 3]
    compilers = {(i, compiler_paths[i]): compiler_names[i] for i in enabled}
    project_path = os.path.join(PROJECTS_PATH, project)
    # project_config = os.path.join(project_path, 'obj', project + 'Config.xml')
    source_path = os.path.join(PROJECTS_PATH, project, 'src')
    optimized_id = 0
    # For the original version there is no config to be appended, that's for the optimize step
    config = b64encode(pickle.dumps({'seed': SEED}))
    for (index, path), name in compilers.items():
        filename = '{project}_{comp_ix}_{optimized}_{config}.swf'.format(project=project, comp_ix=str(index),
                                                                         optimized=str(optimized_id),
                                                                         config=str(config, 'utf-8'))
        output_path = os.path.join(project_path, 'bin', filename)
        # '-load-config+=' + project_config,
        yield [
            path,
            '-source-path "C:\\Program Files (x86)\\FlashDevelop\\Library\\AS3\\classes"',
            '-source-path ' + source_path,
            '-define=NAMES::compiler,"\'' + str(index) + '\'"',
            '-define=NAMES::loggerHost,"\'' + LOGGER_IP + '\'"',
            '-o', output_path,
            os.path.join(source_path, 'Main.as')
        ]


def copy_and_disassemble_project(entry, config):
    """ Because assembly replaces file, do copy, then disassemble """
    bin_path = 'D:\\Studie\\Master\\ExperimentationProject\\SourceProjects\\TestLocalMethodTable\\bin'
    filename_parts = entry.name.split('_')
    if filename_parts[2] == '1':
        # Already compiled swf
        raise ValueError('Can only optimize non-optimized swf, got: {}'.format(entry.name))
    config_str = str(b64encode(pickle.dumps(config)), 'utf-8')
    print('Disassembling for config: {}'.format(str(config)))
    copy_name = '{}_{}_1_{}'.format(filename_parts[0], filename_parts[1], config_str)
    copy_swf_name = copy_name + '.swf'
    copy_swf_path = os.path.join(bin_path, copy_swf_name)
    base_file_path = copy_swf_path[:-4] + '-0'
    abc_path = base_file_path + '.abc'
    # Remove old leftover files
    if os.path.isfile(copy_swf_path):
        os.remove(copy_swf_path)
    if os.path.isfile(abc_path):
        os.remove(abc_path)
    if os.path.isdir(base_file_path):
        shutil.rmtree(base_file_path)
    shutil.copy(entry.path, copy_swf_path)
    run(['abcexport', copy_swf_path], check=True, shell=True)
    run(['rabcdasm', abc_path], check=True, shell=True)
    copy_info = (copy_name, copy_swf_name, copy_swf_path)
    return base_file_path, copy_info, abc_path


def assemble_project(base_file_path, copy_info, abc_path, remove_temp=False):
    """ Use RABCDAsm to re-assemble """
    copy_name, _, copy_swf_path = copy_info
    main_file = os.path.join(base_file_path, copy_name + '-0.main.asasm')
    main_abc = main_file[:-5] + 'abc'
    run(['rabcasm', main_file], check=True, shell=True)
    run(['abcreplace', copy_swf_path, '0', main_abc], check=True, shell=True)
    if remove_temp:
        shutil.rmtree(base_file_path)
        os.remove(abc_path)
        print('Removed intermediate files')


def optimize_test_local_method_table(entry):
    """ See inner function docstring """

    configs = []
    for i in TEST_TARGETS:
        configs.append({'seed': SEED, 'target': i})

    def inner(config):
        """ Given an equal distribution, change certain function to do 90% of calls, rest do 10% """
        limit_pattern = r'pushshort\s+(\d{3,})'
        call_pattern = r'"work(\d{1,2})"'
        # First disassemble copied swf
        base_file_path, copy_info, abc_path = copy_and_disassemble_project(entry, config)
        call_file = os.path.join(base_file_path, 'SubjectWrapper.class.asasm')
        out = []
        # Cycle over all lines, when we encounter a call to target_method, make sure the
        # next pushshort gets upped to right higher value. Bit tricky to carry
        # information over lines. Goal is to update loop upper limit, higher for
        # target method calls, lower for rest
        up_next = False
        with open(call_file) as file:
            for line in file.readlines():
                match_call = re.findall(call_pattern, line)
                if match_call:
                    up_next = match_call[0] == str(config['target'])
                    out.append(line)
                    continue
                match_loop_var = re.findall(limit_pattern, line)
                if match_loop_var:
                    if up_next:
                        # Call to target. Move 90% of total calls (which is per class)
                        # to this method
                        calls_to_target = 0.9 * TOTAL_CALLS
                        # it's split in blocks
                        new_calls = int(calls_to_target / NUM_BLOCKS)
                    else:
                        # Call to other method. All of the other methods should do 10%
                        calls_to_others = 0.1 * TOTAL_CALLS
                        calls_to_this_method = calls_to_others / (NUM_METHODS - 1)
                        # Amount for this specific block
                        new_calls = int(calls_to_this_method / NUM_BLOCKS)
                    out.append(line.replace(match_loop_var[0], str(new_calls)))
                    continue
                # Non-interesting line
                out.append(line)
        with open(call_file, 'w') as file:
            file.writelines(out)
        print('Modified (for each class) balance of {} method calls'.format(TOTAL_CALLS))
        # Now re-assemble swf and optionally delete temporary files
        remove_temp = False if DEBUG else True
        assemble_project(base_file_path, copy_info, abc_path, remove_temp)

    for config in configs:
        yield partial(inner, config)


def get_optimizing_funcs(project):
    """ This should yield for every swf a function which should make an optimized version """
    hardcoded_funcs = {'TestLocalMethodTable': optimize_test_local_method_table}
    bin_path = os.path.join(PROJECTS_PATH, project, 'bin')
    # Call list because we modify directory while iterating
    for entry in list(swf_scandir(bin_path)):
        # There can be old files left
        match_old_optimized = re.findall(r'\d_1_', entry.name)
        if match_old_optimized:
            continue
        if project in hardcoded_funcs:
            for optimizing_func in hardcoded_funcs[project](entry):
                yield optimizing_func
        else:
            configs = [None]
            for config in configs:
                config_filepart = b64encode(pickle.dumps(config))

                def copy():
                    """ Default: copy """
                    # format {project}_{comp_id}_{optimized}_{config}.swf
                    project = entry.name.split('_')[0]
                    comp_id = entry.name.split('_')[1]
                    new_name = project + '_{comp_id}_1_{config}.swf'.format(comp_id=comp_id,
                                                                            config=str(config_filepart, 'utf-8'))
                    # Not exposed directly, chop off filename from full path
                    entry_dir = entry.path[:-(len(entry.name))]
                    new_path = os.path.join(entry_dir, new_name)
                    shutil.copy(entry.path, new_path)

                yield copy


def get_play_commands(project):
    """ Every swf should be played by all players and plugins """
    bin_path = os.path.join(PROJECTS_PATH, project, 'bin')
    exp_path = os.path.dirname(PROJECTS_PATH)
    # Call list because we modify directory while iterating
    entries = list(swf_scandir(bin_path))
    for entry in entries:
        for name in SA_PLAYERS:
            if not will_entry_play(entry, name):
                print('Invalid combo: Skipping player {} playing {}'.format(name, entry.name))
                continue
            full_player_path = os.path.join(exp_path, 'players', name)

            def play_with_sa():
                """ _ """
                timeout = FLASH_PROFILE_ITERATIONS * FLASH_SECS_FOR_RUN
                print('Player ' + name + ' playing ' + entry.name)
                print_entry_config(entry)
                print('(timeout={}*{}s)'.format(FLASH_PROFILE_ITERATIONS, FLASH_SECS_FOR_RUN))
                try:
                    run([full_player_path, entry.path], timeout=timeout)
                except TimeoutExpired:
                    print('Player timed out')

            yield play_with_sa
        if will_entry_play(entry):
            yield get_play_with_plugin(entry, bin_path)
        else:
            print('Invalid combo: Skipping FF playing {}'.format(entry.name))


def get_play_with_plugin(entry, bin_path):
    """ See inner function docstring """

    def inner():
        """ Write swf file which includes swf, then open it with browser """
        html_file = 'wrap-' + entry.name[:-3] + 'html'
        out_path = os.path.join(bin_path, html_file)
        contents = HTML_WRAP_TEMPLATE.format(host=LOGGER_IP, swf_file=entry.name)
        with open(out_path, 'w') as file:
            file.writelines(contents)
        try:
            print('FF opening ' + html_file)
            print_entry_config(entry)
            run([FF_PATH, out_path], shell=True, check=True)
        except CalledProcessError as error:
            # It will always error it seems, but sometimes ok
            if error.returncode != 1 or error.output is not None:
                raise
        plugin_play_checker()

    return inner


def zip_swfs(projects):
    """ Find all swf's for all projects, gather in 1 zip file """
    location = Path.cwd().parent / 'all_swfs.zip'
    zipf = ZipFile(str(location), 'w', ZIP_DEFLATED)
    for project in projects:
        bin_path = os.path.join(PROJECTS_PATH, project, 'bin')
        for entry in swf_scandir(bin_path):
            zipf.write(entry.path, entry.name)
    zipf.close()


def main():
    """ See module docstring """
    header('Asserting requirements')
    assert_logger_running()
    assert_no_marks()
    assert_rabcdasm_installed()
    assert_players_there()

    skip_projects = [ORIGIN_PROJECT]
    steps = {'importing': True,
             'compiling': True,
             'optimizing': True,
             'playing': True,
             'zipping': True}
    for project in get_projects():
        if project in skip_projects:
            continue

        if project != ORIGIN_PROJECT and steps['importing']:
            header('importing main classes')
            import_common_files(project)

        if steps['compiling']:
            header('Compiling')
            for compile_command_parts in get_compile_commands(project):
                print(' '.join(compile_command_parts) + '\n')
                run(' '.join(compile_command_parts), shell=True)

        if steps['optimizing']:
            header('Optimizing')
            for optimizer in get_optimizing_funcs(project):
                optimizer()

        if steps['playing']:
            header('Playing!')
            for play_func in get_play_commands(project):
                play_func()

    if steps['zipping']:
        header('Zipping all swf files')
        zip_swfs(get_projects())

    header('Done')


if __name__ == '__main__':
    main()
