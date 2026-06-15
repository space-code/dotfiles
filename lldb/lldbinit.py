#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

"""
This script serves as the main entry point for loading custom LLDB commands.
It dynamically imports Python scripts from the 'commands/' directory and
sources LLDB aliases and settings from '.txt' files.
"""

from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import os
import sys
import lldb
import optparse


def __lldb_init_module(debugger, internal_dict):
    """
    LLDB entry point — this function is automatically called when the script
    is imported into LLDB.

    It locates the base directory, loads `.txt` LLDB settings,
    and imports Python command scripts from the `commands/` folder.
    """
    base_dir = os.path.dirname(os.path.realpath(__file__))
    commands_dir = os.path.join(base_dir, "commands")

    # Load aliases and settings from text files
    load_settings(base_dir)

    # Load custom Python commands
    load_commands_from(commands_dir)


def load_settings(dir_path: str):
    """
    Loads all `.txt` files in the given directory as LLDB scripts.

    This allows you to define LLDB aliases, settings, and custom behavior
    in plain text files that are sourced on load using 'command source'.
    """
    for file in os.listdir(dir_path):
        if file.endswith(".txt"):
            full_path = os.path.join(dir_path, file)
            # -e0: don't stop on error, -s1: silent mode
            lldb.debugger.HandleCommand(f'command source -e0 -s1 "{full_path}"')


def load_commands_from(commands_dir: str):
    """
    Dynamically loads all Python command scripts from the `commands/` directory.

    Each Python file is imported as a module using `importlib`. If the module
    defines a `commands()` function, its return values (command instances)
    are registered with LLDB.
    """
    if not os.path.exists(commands_dir):
        return

    for file in os.listdir(commands_dir):
        if file.endswith(".py"):
            path = os.path.join(commands_dir, file)
            module_name = f"lldb_command_{file[:-3]}"

            # Dynamic module loading
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Register each command returned by module.commands()
            if hasattr(module, "commands"):
                for command in module.commands():
                    register_command(command, module.__name__, path)


def register_command(command, module_name, file_path):
    """
    Registers a command object with LLDB.

    - Wraps the command's run logic into a function LLDB can execute.
    - Uses optparse to handle command-line options.
    - Redirects stdout/stderr to LLDB's result object.
    - Registers the command via `command script add`.
    """
    key = f"{file_path}_{command.name()}"
    function_name = f"__{command.name().replace('-', '_')}"

    def run_command(debugger, input_str, exe_ctx, result, _):
        """Wrapper function that LLDB actually calls."""
        with redirect_stdout(result), redirect_stderr(result):
            # Populate command context
            command.result = result
            command.context = exe_ctx

            # Tokenize input
            split_input = command.lex(input_str)

            # Ensure parser doesn't get confused by missing '--'
            options = command.options()
            if len(options) == 0:
                if "--" not in split_input:
                    split_input.insert(0, "--")

            # Parse arguments and options
            parser = generate_option_parser(command)
            try:
                (options, args) = parser.parse_args(split_input)
            except Exception:
                result.SetError(parser.usage)
                return

            # Handle positional argument gathering (if more than expected)
            if len(args) > len(command.args()):
                overhead = len(args) - len(command.args())
                head = args[: overhead + 1]
                args = [" ".join(head)] + args[-overhead:]

            # Validate and execute
            if validate_args(args=args, command=command):
                command.run(args, options)

    # Set docstring for LLDB help system
    run_command.__doc__ = help_for_command(command)

    # Store the function in the module so it's not garbage collected
    # pylint: disable=protected-access
    if not hasattr(sys.modules[module_name], "_loadedFunctions"):
        sys.modules[module_name]._loadedFunctions = {}

    sys.modules[module_name]._loadedFunctions[key] = run_command
    # pylint: enable=protected-access

    # Create a global reference in Python script environment
    lldb.debugger.HandleCommand(
        f"script {function_name} = sys.modules['{module_name}']._loadedFunctions['{key}']"
    )

    # Add the command to LLDB
    lldb.debugger.HandleCommand(
        f"command script add --function {function_name} {command.name()}"
    )


def help_for_command(command) -> str:
    """
    Returns the first line of the command's description.
    Used as inline help text in LLDB.
    """
    return command.description().splitlines()[0]


def generate_option_parser(command):
    """
    Generates an optparse.OptionParser based on the command's options.
    """
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage, prog=command.name())

    for argument in command.options():
        if argument.boolean:
            parser.add_option(
                argument.shortName,
                argument.longName,
                dest=argument.argName,
                help=argument.help,
                action=("store_false" if argument.default else "store_true"),
            )
        else:
            parser.add_option(
                argument.shortName,
                argument.longName,
                dest=argument.argName,
                help=argument.help,
                default=argument.default,
            )

    return parser


def validate_args(args, command):
    """
    Validates the arguments provided to a command.
    Ensures required arguments are present and fills in defaults for optional ones.
    """
    if len(args) < len(command.args()):
        default_args = [arg.default for arg in command.args()]
        default_args_to_append = default_args[len(args) :]

        index = len(args)

        for default_arg in default_args_to_append:
            if not default_arg:
                arg = command.args()[index]
                print(f"Whoops! You are missing the <{arg.argName}> argument.")
                print(f"\nUsage: {usage_for_command(command)}")
                return
            index += 1

        args.extend(default_args_to_append)

    return True


def usage_for_command(command):
    """
    Generates a usage string for a command based on its arguments.
    """
    usage = command.name()
    for arg in command.args():
        if arg.default:
            usage += f" [{arg.argName}]"
        else:
            usage += f" {arg.argName}"

    return usage
