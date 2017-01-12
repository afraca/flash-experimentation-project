"""
Figure out all configurations, fetch from database rows for these configurations, calculate statistics, write csv
"""

import statistics
import csv
import sqlite3
from pathlib import Path
from itertools import product
import json
import numpy as np
import matplotlib.pyplot as plt

from reorder_exp.constants import TEST_TARGETS
from reorder_exp.helpers import did_it_play

ROOT_PATH = Path.cwd().parent
DB_PATH = ROOT_PATH / 'logfile.db'
CONNECTION = sqlite3.connect(str(DB_PATH))
CURSOR = CONNECTION.cursor()

# Items: (seed, target_method)
SEEDS = [42 ** 2, 42 ** 3]
CONFIGS = product(SEEDS, TEST_TARGETS)

# { version : (standalone, short_key} }
VERSIONS = {
    'WIN 9,0,280,0': (1, 0),
    'WIN 23,0,0,185': (1, 1),
    'WIN 24,0,0,186': (0, 2),
    'MAC 24,0,0,186': (0, 3),
}


def include_row(row, seed, target):
    """ Cannot like with callmethod results simply alter query... """
    row_config = json.loads(row[5])
    if row_config is None:
        # Should not happen...
        return False
    if 'seed' not in row_config:
        return False
    # Now the interesting parts
    if 'target' not in row_config:
        # This is a non-optimized run result
        return row_config['seed'] == seed
    # By careful observation, we have some other outliers
    if row[6] == 27145:
        return False
    # Optimized run result
    return row_config['seed'] == seed and row_config['target'] == target


def raw_results(seed, target):
    """ _ """
    results = {}
    with CONNECTION:
        for row in CURSOR.execute('SELECT compiler, version, standalone, optimized, elapsed, config, id FROM log'):
            if not include_row(row, seed, target):
                continue
            key = (row[0], row[1], row[2], row[3])
            if key in results:
                results[key].append(row[4])
            else:
                # Explicit discard of first row: they are always outlier, see report
                results[key] = []  # [row[4]]
    return results


def possible_keys():
    """ Some combinations disallowed """
    compilers = [0, 3]
    optimized = [0, 1]
    standalone = [0, 1]
    versions = sorted(VERSIONS.keys(), key=lambda v: VERSIONS[v][1])
    for combination in product(compilers, versions, standalone, optimized):
        comb_version_is_sa = VERSIONS[combination[1]][0] == 1
        if comb_version_is_sa and combination[2] == 0:
            continue
        if not comb_version_is_sa and combination[2] == 1:
            continue
        yield combination


def calc_statistics(raw_results):
    """ Averages and standard deviation for the results """
    results = {}
    for key in possible_keys():
        results[key] = {}
        if key in raw_results.keys():
            results[key]['avg'] = statistics.mean(raw_results[key])
            results[key]['std'] = statistics.stdev(raw_results[key], results[key]['avg'])
            results[key]['n'] = len(raw_results[key])
        else:
            results[key]['avg'] = None
            results[key]['std'] = None
            results[key]['n'] = None

    return results


def sub_stats_from_stats(stats):
    """ _ """
    if stats['avg'] is None:
        avg = '-'
        std = '-'
        n = '-'
    else:
        avg = '{:.2f}'.format(stats['avg'])
        std = '{:.2f}'.format(stats['std'])
        n = stats['n']
    return avg, std, n


def write(results, seed, target):
    """ Create csv file with results for certain seed and target """
    filename = 'reorder_results_seed{}_target{}.csv'.format(seed, target)
    with open(str(ROOT_PATH / 'Results' / filename), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['compiler', 'version', 'standalone', 'optimized', 'avg', 'std', 'n'])
        for key in possible_keys():
            (compiler, version, standalone, optimized) = key
            short_version = VERSIONS[version][1]
            avg, std, n = sub_stats_from_stats(results[key])
            writer.writerow([compiler, short_version, standalone, optimized, avg, std, n])


def write_combined_csv(seed, targets, all_results):
    """ Just reuse previously calculated averages """
    targets_combined = '-'.join(map(str, targets))
    filename = 'reorder_results_seed{}_targets{}.csv'.format(seed, targets_combined)
    with open(str(ROOT_PATH / 'Results' / filename), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        header = ['compiler', 'version', 'standalone', 'optimized']
        for _ in targets:
            header += ['avg', 'std', 'n']
        writer.writerow(header)
        for key in possible_keys():
            (compiler, version, standalone, optimized) = key
            short_version = VERSIONS[version][1]
            row = [compiler, short_version, standalone, optimized]
            for target in targets:
                stats = all_results[(seed, target)][key]
                avg, std, n = sub_stats_from_stats(stats)
                row += [avg, std, n]
            writer.writerow(row)


def plot_all_targets(seed, all_results):
    """ Create visual plot to compare how targets influence performance """
    for key in possible_keys():
        (compiler, version, standalone, optimized) = key
        # Non-optimized gets included manually in optimized analysis
        if optimized == 0:
            continue
        # Known some combinations will not have results at all
        if not did_it_play(compiler, version, VERSIONS):
            continue
        short_version = VERSIONS[version][1]
        tmp_results = []
        for target in TEST_TARGETS:
            stats = all_results[(seed, target)][key]
            avg, std, n = sub_stats_from_stats(stats)
            tmp_results.append((target, avg, std))
        # The non-optimized results are not different per target here
        non_optimized_key = (compiler, version, standalone, 0)
        non_optimized_stats = all_results[(seed, TEST_TARGETS[0])][non_optimized_key]
        avg, std, n = sub_stats_from_stats(non_optimized_stats)
        tmp_results.append(('Default', avg, std))
        # For debug message declared here
        filename = 'reorder_seed{}_comp{}_version{}'.format(seed, compiler, short_version)
        try:
            # No big differences makes sorting useless
            if False:
                sorted_results = sorted(tmp_results, key=lambda e: float(e[1]))
            else:
                sorted_results = tmp_results
            groups = [str(e[0]) for e in sorted_results]
            results = [float(e[1]) for e in sorted_results]
            stdevs = [float(e[2]) for e in sorted_results]
            ind = np.arange(len(groups))
        except ValueError:
            print('Missing target information to create {}.png/eps'.format(filename))
            continue
        actual_plotting(groups, results, stdevs, ind, compiler, short_version, filename)


def actual_plotting(groups, results, stdevs, ind, compiler, short_version, filename):
    """ Well... the actual plotting here """
    plt.figure()
    plt.bar(ind, results, width=0.35, align='center', color='r', yerr=stdevs, zorder=3)
    # x-axis
    plt.xticks(ind, groups)
    x_label = 'Compiler={},Version={}'.format(compiler, short_version)
    plt.xlabel(x_label)
    plt.autoscale(True, 'x', tight=True)
    plt.rc('font', size=8)
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=90)
    # y-axis
    plt.ylabel('Avg runtime (ms)')
    # Fix tick interval y axis
    y_start = 0
    y_end = max(results) * 1.1
    y_stepsize = 25 if max(results) < 1000 else 250
    plt.yticks(np.arange(y_start, y_end, y_stepsize))
    plt.grid(zorder=0)
    # Filename without extension
    filepath = ROOT_PATH / 'Results' / filename
    plt.savefig(str(filepath) + '.eps')
    plt.savefig(str(filepath) + '.png', dpi=600)
    print('Wrote file {}'.format(filename + '.png/eps'))


def main():
    """ See module docstring """
    all_results = {}
    steps = {
        'csv': False,
        'plot': True
    }
    for seed, target in CONFIGS:
        raw = raw_results(seed, target)
        # Combine rows for mean and stdev
        results = calc_statistics(raw)
        if steps['csv']:
            write(results, seed, target)
        all_results[(seed, target)] = results
    # Combined csv should include only part of results
    for seed in SEEDS:
        write_combined_csv(seed, [1, 25, 50], all_results)
        if steps['plot']:
            plot_all_targets(seed, all_results)


if __name__ == '__main__':
    main()
