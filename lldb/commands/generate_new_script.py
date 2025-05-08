#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

import lldb
import shlex
import optparse
import os
from stat import *

# Register a new LLDB command named '__generate_script'
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        'command script add -o -f generate_new_script.generate_new_script __generate_script -h "generates new LLDB script"')

# Generates a new LLDB script when the '__generate_script' command is executed.
def generate_new_script(debugger, command, ext_ctx, result, internal_dict):
    '''
    Generates a new script in the same directory as this file.
    Can generate function styled scripts or class styled scripts.
    '''

    command_args = shlex.split(command, posix=False)
    parser = generate_option_parser()

    try:
        (options, args) = parser.parse_args(command_args)
    except:
        result.SetError(parser.usage)
        return
    
    if not args:
        result.SetError('Expects a filename. Usage __generate_script filename')
        return

    clean_command = ('').join(args)
    file_path = str(os.path.splitext(os.path.join(os.path.dirname(__file__), clean_command))[0] + '.py')

    if os.path.isfile(file_path):
        result.SetError('There already exists a file named "{}", please remove the file at "{}" first'.format(clean_command, file_path))
        return
    
    script = generate_function_file(clean_command, options)

    create_or_touch_filepath(file_path, script)
    os.system('open -R ' + file_path)

    result.AppendMessage('Opening \"{}\"...'.format(file_path))

# Create a new file for the script.
def create_or_touch_filepath(filepath, script):
    file = open(filepath, "w")
    file.write(script)
    file.flush()
    st = os.stat(filepath)
    os.chmod(filepath, st.st_mode | S_IEXEC)
    file.close()

# Generate a function file.
def generate_function_file(filename, options):
    resolved_name = options.command_name if options.command_name else filename
    script = r'''

import lldb
import os
import argparse

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
    '''
    script += '\'command script add -o -f {}.handle_command {} -h "{}"\')'.format(filename, resolved_name, "Short documentation here")
    script += r'''

def handle_command(debugger, command, exe_ctx, result, internal_dict):
    ''' 
    script += "\'\'\'\n    Documentation for how to use " + resolved_name + " goes here \n    \'\'\'"
    
    script += r'''

    command_args = command.split()
    parser = generate_option_parser()
    options = []
    args = []
    if len(command_args):
        try:
            (options, args) = parser.parse_args(command_args)
        except:
            result.SetError(parser.usage)
            return

    # Uncomment if you are expecting at least one argument
    # clean_command = shlex.split(args[0])[0]
    '''

    script += "result.AppendMessage('Hello! the " + resolved_name + " command is working!')"
    script += r'''


def generate_option_parser():
    usage = "usage: %prog [options] TODO Description Here :]"
    parser = argparse.ArgumentParser(usage=usage, prog="''' + resolved_name + r'''")
    parser.add_argument("-m", "--module",
                      action="store",
                      default=None,
                      dest="module",
                      help="This is a placeholder option to show you how to use options with strings")
    parser.add_argument("-c", "--check_if_true",
                      action="store_true",
                      default=False,
                      dest="store_true",
                      help="This is a placeholder option to show you how to use options with bools")
    return parser
    '''
    return script

# Generates the option parser.
def generate_option_parser():
    usage = "usage: %prog [options] nameofscript"
    parser = optparse.OptionParser(usage=usage, prog="__generate_script")

    parser.add_option(
        "-n", "--command_name",
        action="store",
        default=None,
        dest="command_name",
        help="By default, the script will use filename for the LLDB command. This will override the command name to a name your choosing."
    )

    return parser
