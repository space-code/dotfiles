"""
LLDB Lookup Command Script

This script defines a custom LLDB command called `lookup` that allows users to query
symbols in the currently loaded target. It provides options to display additional
information such as load addresses and module summaries.
"""

import lldb
import shlex
import optparse


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        'command script add -o -f lookup.handle_command lookup -h "Short documentation here"'
    )


def handle_command(debugger, command, exe_ctx, result, internal_dict):
    """
    Handles the execution of the 'lookup' command.

    Parses the user-provided command, retrieves matching global functions
    from the LLDB target, and formats the output accordingly.
    """

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

    clean_command = shlex.split(args[0])[0]
    target = debugger.GetSelectedTarget()

    context_list = target.FindGlobalFunctions(clean_command, 0, lldb.eMatchTypeRegex)

    mdict = generate_module_dictionary(context_list)
    output = generate_output(mdict, options, target)

    result.AppendMessage(output)


def generate_option_parser():
    """
    Generates an option parser for the 'lookup' command.

    Defines the command-line options that users can specify when executing 'lookup'.

    Returns:
    - An optparse.OptionParser instance configured with available options.
    """

    usage = "usage: %prog [options] code_to_query"
    parser = optparse.OptionParser(usage=usage, prog="lookup")

    parser.add_option(
        "-l",
        "--load_address",
        action="store_true",
        default=False,
        dest="load_address",
        help="Show the load addresses for a particular hit",
    )

    parser.add_option(
        "-s",
        "--module_summary",
        action="store_true",
        default=False,
        dest="module_summary",
        help="Only show the amount of queries in the module",
    )
    return parser


def generate_module_dictionary(context_list):
    """
    Creates a dictionary that maps module file paths to their corresponding function contexts.

    Groups function lookup results by the module they belong to.

    Parameters:
    - context_list: A list of LLDB function context objects.

    Returns:
    - A dictionary where keys are module file paths and values are lists of function contexts.
    """
    mdict = {}
    for context in context_list:
        key = context.module.file.fullpath

        if not key in mdict:
            mdict[key] = []

        mdict[key].append(context)

    return mdict


def generate_output(mdict, options, target):
    """
    Generates formatted output for the lookup results.

    Iterates through the module dictionary and formats the function information
    according to user-specified options.

    Parameters:
    - mdict: A dictionary mapping module names to lists of function contexts.
    - options: Parsed command-line options.
    - target: The LLDB target being debugged.

    Returns:
    - A formatted string containing the lookup results.
    """
    output = ""
    separator = "*" * 60 + "\n"

    for key in mdict:
        count = len(mdict[key])
        first_item = mdict[key][0]

        module_name = first_item.module.file.basename

        if options.module_summary:
            output += f"{count} hits in {module_name}\n"
            continue

        output += f"{separator}{count} hits in {module_name}\n{separator}"

        for context in mdict[key]:
            query = ""

            if options.load_address:
                start = context.symbol.addr.GetLoadAddress(target)
                end = context.symbol.end_addr.GetLoadAddress(target)

                start_hex = "0x" + format(start, "012x")
                end_hex = "0x" + format(end, "012x")

                query += f"[{start_hex}-{end_hex}]\n"

            query += context.symbol.name
            query += "\n\n"
            output += query
    return output
