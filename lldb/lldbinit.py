#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

import lldb
import os

def __lldb_init_module(debugger, internal_dict):
    file_path = os.path.realpath(__file__)
    dir_name = os.path.dirname(file_path)
    commands_direcory = os.path.join(dir_name, "commands")
    load_python_scripts_dir(commands_direcory)

def load_python_scripts_dir(dir_name):
    this_files_basename = os.path.basename(__file__)
    cmd = ''
    for file in os.listdir(dir_name):
        if file.endswith('.py'):
            cmd = 'command script import '
        elif file.endswith('.txt'):
            cmd = 'command source -e0 -s1 '
        else: 
            continue

        if file != this_files_basename:
            fullpath = dir_name + '/' + file
            lldb.debugger.HandleCommand(cmd + fullpath)
