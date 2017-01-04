"""
Create classes, subclasses, and file that calls all methods from all classes
"""
import os
import re

from common_exp.templates import CALL_BOILERPLATE_PRE, CALL_BOILERPLATE_POST
from common_exp.helpers import (get_class_content, get_call_blocks, get_classes, get_call_vars)

from reorder_exp.constants import (NUM_BASE_CLASSES, NUM_SUB_CLASSES,
                                   NUM_METHODS, TOTAL_CALLS, NUM_BLOCKS, DEBUG)

LOCATIONS = [
    'D:\\Studie\\Master\\ExperimentationProject\\SourceProjects\\TestLocalMethodTable\\src'
]


def delete_old_classes(location):
    """ Delete existing classfiles, not the subject wrapper """
    class_pattern = r'C\d+.as'
    for entry in os.scandir(location):
        if entry.is_dir():
            continue
        if re.match(class_pattern, entry.name):
            print('Removing ' + entry.name)
            os.remove(entry.path)


def write_classes(location, classes):
    """ Classes and subclasses are written, with certain amount of methods """
    for classname in classes:
        extending = len(classname) == 3
        contents = get_class_content(classname, extending, NUM_METHODS)
        class_location = os.path.join(location, classname + '.as')
        description = 'sub' if extending else 'base'
        print('Writing {} class {}'.format(description, classname))
        with open(class_location, 'w') as file:
            file.write(contents)


def write_calling_file(location, classes):
    """'Write wrapper file that calls every method of every class """
    out = get_call_vars(classes)
    for classname in classes:
        out += get_call_blocks(classname, NUM_METHODS, TOTAL_CALLS, NUM_BLOCKS, DEBUG)
    out = CALL_BOILERPLATE_PRE + out + CALL_BOILERPLATE_POST
    location = os.path.join(location, 'SubjectWrapper.as')
    with open(location, 'w') as file:
        file.write(out)


def main():
    """ See module docstring """
    classes = list(get_classes(NUM_BASE_CLASSES, NUM_SUB_CLASSES))
    for location in LOCATIONS:
        delete_old_classes(location)
        write_classes(location, classes)
        write_calling_file(location, classes)


if __name__ == '__main__':
    main()
