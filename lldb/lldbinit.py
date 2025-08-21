#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import os
import sys
import lldb
import optparse


def __lldb_init_module(debugger, internal_dict):
    """
    LLDB entry point — this function is automatically called when the script
    is imported.

    It locates the base directory, loads `.txt` LLDB settings,
    and imports Python command scripts from the `commands/` folder.
    """
    base_dir = os.path.dirname(os.path.realpath(__file__))
    commands_dir = os.path.join(base_dir, "commands")

    load_settings(base_dir)
    load_commands_from(commands_dir)


def load_settings(dir_path: str):
    """
    Loads all `.txt` files in the given directory as LLDB scripts.

    This allows you to define LLDB aliases, settings, and custom behavior
    in plain text files that are sourced on load.
    """
    for file in os.listdir(dir_path):
        if file.endswith(".txt"):
            full_path = os.path.join(dir_path, file)
            lldb.debugger.HandleCommand(f'command source -e0 -s1 "{full_path}"')


def load_commands_from(commands_dir: str):
    """
    Dynamically loads all Python command scripts from the `commands/` directory.

    Each Python file is imported as a module using `importlib`, and any objects
    returned by its `commands()` function are registered with LLDB.
    """
    for file in os.listdir(commands_dir):
        if file.endswith(".py"):
            path = os.path.join(commands_dir, file)
            module_name = f"lldb_command_{file[:-3]}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            if hasattr(module, "commands"):
                for command in module.commands():
                    register_command(command, module.__name__, path)


def register_command(command, module_name, file_path):
    """
    Registers a command object with LLDB.

    - Wraps the command into a function LLDB can execute.
    - Stores it in `sys.modules[module_name]._loadedFunctions`.
    - Creates a named Python reference via `script ...` so LLDB can find it.
    - Adds the command to LLDB via `command script add`.
    """
    key = f"{file_path}_{command.name()}"
    function_name = f"__{command.name().replace('-', '_')}"

    def run_command(debugger, input_str, exe_ctx, result, _):
        with redirect_stdout(result), redirect_stderr(result):
            command.result = result
            command.context = exe_ctx

            split_input = command.lex(input_str)

            options = command.options()

            if len(options) == 0:
                if "--" not in split_input:
                    split_input.insert(0, "--")

            parser = generate_option_parser(command)

            try:
                (options, args) = parser.parse_args(split_input)
            except:
                result.SetError(parser.usage)
                return

            if len(args) > len(command.args()):
                overhead = len(args) - len(command.args())
                head = args[: overhead + 1]
                args = [" ".join(head)] + args[-overhead:]

            if validate_args(args=args, command=command):
                command.run(args, options)

    run_command.__doc__ = help_for_command(command)

    # pylint: disable=protected-access
    if not hasattr(sys.modules[module_name], "_loadedFunctions"):
        sys.modules[module_name]._loadedFunctions = {}

    sys.modules[module_name]._loadedFunctions[key] = run_command
    # pylint: enable=protected-access

    lldb.debugger.HandleCommand(
        f"script {function_name} = sys.modules['{module_name}']._loadedFunctions['{key}']"
    )

    lldb.debugger.HandleCommand(
        f"command script add --function {function_name} {command.name()}"
    )


def help_for_command(command) -> str:
    """
    Returns the first line of the command's description.

    Used as inline help text in LLDB for `command script add`.
    """
    return command.description().splitlines()[0]


def generate_option_parser(command):
    """
    Gets the return register as a string for lldb
    based upon the hardware
    """

    usage = "usage: %prog [options]"

    parser = optparse.OptionParser(usage=usage, prog="bar")

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
    - Ensures required arguments are present.
    - Fills in missing optional arguments with their default values.
    - Prints usage instructions if required arguments are missing.

    Parameters:
        args (list): List of arguments passed by the user.
        command (object): Command object that defines expected arguments.

    Returns:
        True if arguments are valid, otherwise None (after printing error message).
    """
    if len(args) < len(command.args()):
        default_args = [arg.default for arg in command.args()]
        default_args_to_append = default_args[len(args) :]

        index = len(args)

        for default_arg in default_args_to_append:
            if not default_arg:
                arg = command.args()[index]
                print("Whoops! You are missing the <" + arg.argName + "> argument.")
                print("\nUsage: " + usage_for_command(command))
                return
            index += 1

        args.extend(default_args_to_append)

    return True


def usage_for_command(command):
    """
    Generates a usage string for a command.
    Required arguments are shown without brackets.
    Optional arguments (with defaults) are shown inside brackets.

    Example:
        command.name() == "copy"
        args == [source, destination, overwrite (default=False)]
        usage → "copy source destination [overwrite]"

    Parameters:
        command (object): Command object with name() and args().

    Returns:
        str: Usage string for the command.
    """
    usage = command.name()
    for arg in command.args():
        if arg.default:
            usage += " [" + arg.argName + "]"
        else:
            usage += " " + arg.argName

    return usage
