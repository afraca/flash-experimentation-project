"""
Figure out all configurations, fetch from database rows for these configurations, calculate statistics, write csv
"""

import statistics
import csv
import sqlite3
from pathlib import Path
from itertools import product
import json

from callmethod_exp.constants import EXP_CONFIGS

ROOT_PATH = Path.cwd().parent
DB_PATH = ROOT_PATH / 'logfile.db'
CONNECTION = sqlite3.connect(str(DB_PATH))
CURSOR = CONNECTION.cursor()

SEEDS = [42 ** 2, 42 ** 3]
OPTIMIZED = [0, 1]


def possible_keys():
    for seed, config, optimized in product(SEEDS, EXP_CONFIGS, OPTIMIZED):
        yield (seed, json.dumps(config), optimized)


def raw_results(seed, config, optimized):
    """ Fetch from DB certain rows, put in nice dictionary """
    results = {
        'utime': [],
        'stime': [],
    }
    query = 'SELECT seed, optimized, config, utime, stime, maxrss, ixrss, idrss, created_at FROM callmethod WHERE seed = ? AND config = ? AND optimized = ?'
    with CONNECTION:
        for row in CURSOR.execute(query, (seed, config, optimized)):
            utime_ms = int(row[3] * 1000)
            stime_ms = int(row[4] * 1000)
            results['utime'].append(utime_ms)
            results['stime'].append(stime_ms)
    return results


def calc_statistics(raw_results):
    """ Calculate mean and standard deviation """
    results = {
        'utime': {},
        'stime': {}
    }
    for res_key, raw in raw_results.items():
        if len(raw) > 0:
            results[res_key]['avg'] = avg = statistics.mean(raw)
            results[res_key]['std'] = round(statistics.stdev(raw, avg))
            results[res_key]['n'] = len(raw)
        else:
            results[res_key] = {
                'avg': None,
                'std': None,
                'n': None,
            }
    return results


def pretty_flags(flags):
    """ Potential for better output... """
    return str(flags)


def write(results, keys):
    """ Create csv file """
    filename = 'callmethod_results.csv'
    res_keys = ['utime', 'stime']
    with open(str(ROOT_PATH / 'Results' / filename), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        header = ['seed', 'compile_flags', 'run_flags', 'optimized', 'avg_utime', 'std_utime', 'avg_stime',
                  'std_stime', 'n']
        writer.writerow(header)
        for key in keys:
            seed, config, optimized = key
            config = json.loads(config)
            row_items = [seed, pretty_flags(config[0]), pretty_flags(config[1]), optimized]
            for res_key in res_keys:
                for prop in ['avg', 'std']:
                    num = results[key][res_key][prop]
                    if num is not None:
                        row_items.append(num)
                    else:
                        row_items.append('-')
            # Should be the same
            assert results[key][res_keys[0]]['n'] == results[key][res_keys[1]]['n']
            row_items.append(results[key][res_keys[0]]['n'])
            writer.writerow(row_items)


def main():
    """ See module docstring """
    all_results = {}
    keys = list(possible_keys())
    for key in keys:
        seed, config, optimized = key
        raw = raw_results(seed, config, optimized)
        results = calc_statistics(raw)
        all_results[key] = results
    write(all_results, keys)


if __name__ == '__main__':
    main()
