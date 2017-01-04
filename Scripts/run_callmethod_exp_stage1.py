"""
Stage1 is generating callmethod_0.as with all classes and calls
Execute in Windows

See run_callmethod_exp_stage2 for stage2
"""

from pathlib import Path

from common_exp.helpers import get_classes, get_call_vars, get_class_content, get_call_blocks, header
from common_exp.templates import CALLT

DEBUG = False

# Virtual Machine will mount this separately
OUT_DIR = Path.cwd().parent / 'AvmshellTests'
OUT_NAME = 'callmethod_0.as'

if not DEBUG:
    NUM_CLASSES = 8
    NUM_SUB_CLASSES = NUM_CLASSES
    NUM_METHODS = 50
    TOTAL_CALLS = 400 * 1000
    NUM_BLOCKS = 4
else:
    NUM_CLASSES = 1
    NUM_SUB_CLASSES = NUM_CLASSES
    NUM_METHODS = 4
    TOTAL_CALLS = 10
    NUM_BLOCKS = 1

PRINT_CALLT = """
for (i = 0; i < {limit}; i++)
{{
    print(_{classname}.{method}());
}}
"""


def main():
    """ Create one big file, see module doc"""
    contents = ''
    header('Gathering class declarations')
    # For subclass division
    assert NUM_METHODS % 2 == 0
    classes = list(get_classes(NUM_CLASSES, NUM_SUB_CLASSES))
    for classname in classes:
        extending = len(classname) == 3
        contents += get_class_content(classname, extending, NUM_METHODS)
    header('Gathering call var declarations')
    contents += get_call_vars(classes)
    header('Gathering call block declarations')
    call_templ = PRINT_CALLT if DEBUG else CALLT
    for classname in classes:
        contents += get_call_blocks(classname, NUM_METHODS, TOTAL_CALLS, NUM_BLOCKS, DEBUG, call_templ=call_templ)
    file_path = str(OUT_DIR / OUT_NAME)
    header('Writing file')
    with open(file_path, 'w') as file:
        file.writelines(contents)


if __name__ == '__main__':
    main()
