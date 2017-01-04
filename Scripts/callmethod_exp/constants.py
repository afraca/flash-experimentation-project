"""
Constants specific for the callmethod experiment. This is stage2 specific.
"""
from pathlib import Path
from itertools import product

DEBUG = False

EXP_PATH = Path.home() / 'ExperimentationProject'
SOURCE_PATH = EXP_PATH / 'CallmethodTmp'
RABCDASM_PATH = EXP_PATH / 'RABCDAsm'
ASC_PATH = EXP_PATH / 'avmplus' / 'utils' / 'asc.jar'
BUILTINS_PATH = EXP_PATH / 'avmplus' / 'generated' / 'builtin.abc'
AVM_SHELL_PATH = EXP_PATH / 'avmplus' / 'bin-release' / 'shell' / 'avmshell'

NUM_RUMS = 10 if not DEBUG else 2

COMPILE_FLAGS = [['-optimize'], []]
RUN_FLAGS = [['-Djitordie'], []]
EXP_CONFIGS = product(COMPILE_FLAGS, RUN_FLAGS)
