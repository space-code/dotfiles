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


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        "command script add -f breakafterregex.break_after_regex bar"
    )


def break_after_regex(debugger, command, result, internal_dict):
    """The function sets a regex breakpoint and prints
    output values after stepping out."""

    target = debugger.GetSelectedTarget()
    bp = target.BreakpointCreateByRegex(command)

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
