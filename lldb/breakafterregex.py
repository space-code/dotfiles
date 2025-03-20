"""
LLDB Breakpoint Script for Stepping Out After a Regex Match

This script provides an LLDB command to set a breakpoint using a
regular expression and automatically step out of the function when
the breakpoint is hit. It captures and prints the returned object
from the function after stepping out.

Usage:
(lldb) bar <regex>
"""

import lldb
import optparse
import shlex


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        "command script add -f breakafterregex.break_after_regex bar"
    )


def break_after_regex(debugger, command, result, internal_dict):
    """The function sets a regex breakpoint and prints
    output values after stepping out."""

    command = command.replace("\\", "\\\\")
    command_args = shlex.split(command, posix=False)

    parser = generate_option_parser()

    try:
        (options, args) = parser.parse_args(command_args)
    except:
        result.SetError(parser.usage)
        return

    target = debugger.GetSelectedTarget()

    clean_command = shlex.split(args[0])[0]

    if options.non_regex:
        bp = target.BreakpointCreateByName(clean_command, options.module)
    else:
        bp = target.BreakpointCreateByRegex(clean_command, options.module)

    if not bp.IsValid() or bp.num_locations == 0:
        result.AppendWarning("Breakpoint isn't valid or hasn't found any hits.")
    else:
        result.AppendWarning(f"{bp}")

    bp.SetScriptCallbackFunction("breakafterregex.breakpoint_handler")


def breakpoint_handler(frame, bp_loc, dict):
    """The function called when the reguar expression
    breakpoint gets triggered"""

    thread = frame.GetThread()
    process = thread.GetProcess()
    debugger = process.GetTarget().GetDebugger()

    # Grabs the name of the parent function.
    function_name = frame.GetFunctionName()

    # Waits until the StepOut method complete.
    debugger.SetAsync(False)

    thread.StepOut()

    output = evaluate_returned_object(debugger, thread, function_name)

    if output is not None:
        print(output)

    return False


def evaluate_returned_object(debugger, thread, function_name):
    """Grabs the reference from the return register
    and returns a string from evaluated value."""

    res = lldb.SBCommandReturnObject()

    interpreter = debugger.GetCommandInterpreter()
    target = debugger.GetSelectedTarget()
    frame = thread.GetSelectedFrame()
    parent_function_name = frame.GetFunctionName()

    expression = f"expression -lobjc -O -- {get_register_string(target)}"

    interpreter.HandleCommand(expression, res)

    if res.HasResult():
        output = (
            f"{'*' * 80}{chr(10)}"
            f"breakpoint: {chr(10)}"
            f"object: {function_name}{chr(10)}"
            f"stopped: {res.GetOutput().replace(f'{chr(10)}', '')}{chr(10)}"
            f"{parent_function_name}{chr(10)}"
        )

        return output
    else:
        return None


def get_register_string(target):
    """Gets the return as a string for lldb
    based upon the hardware"""

    triple_name = target.GetTriple()

    if "x86_64" in triple_name:
        return "$rax"
    elif "i386" in triple_name:
        return "$eax"
    elif "arm64" in triple_name:
        return "$x0"

    raise Exception("Unknown hardware.")


def generate_option_parser():
    """Gets the return register as a string for lldb
    based upon the hardware"""
    usage = "usage: %prog [options] breakpoint_query\n" + "Use 'bar -h' for option desc"

    parser = optparse.OptionParser(usage=usage, prog="bar")

    parser.add_option(
        "-n",
        "--non_regex",
        action="store_true",
        default=False,
        dest="non_regex",
        help="Use a non-regex breakpoint instead",
    )

    parser.add_option(
        "-m",
        "--module",
        action="store",
        default=None,
        dest="module",
        help="Filter a breakpoint by only searching within a specified Module",
    )

    return parser
