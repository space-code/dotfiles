"""
LLDB Memory Stack Logging Script

This script provides an LLDB command (`msl`) to retrieve and process stack traces
for memory allocations and deallocations. It allows debugging memory-related issues
by analyzing the most recent memory accesses. The script also includes an alias
for enabling stack logging in LLDB.'
"""

import optparse
import shlex
import sbt
import lldb


def __lldb_init_module(debugger, internal_dict):
    """
    Initializes the LLDB module by adding a new command script.

    This function registers the `msl` command and an alias for enabling stack logging
    """
    debugger.HandleCommand("command script add -f msl.handle_command msl")
    debugger.HandleCommand(
        "command alias enable_logging expression -lobjc -O -- extern void turn_on_stack_logging(int); turn_on_stack_logging(1);"
    )


def handle_command(debugger, command, result, internal_dict):
    """
    msl will produce the stack trace of the most recent deallocations or allocations.
    Make sure to either call enable_logging or set MallocStackLogging environment variable
    """

    command_args = shlex.split(command)
    parser = generate_option_parser()

    try:
        (options, args) = parser.parse_args(command_args)
    except:
        result.SetError(parser.usage)
        return

    clean_command = args[0]
    process = debugger.GetSelectedTarget().GetProcess()
    frame = process.GetSelectedThread().GetSelectedFrame()
    target = debugger.GetSelectedTarget()

    script = generate_script(clean_command, options)
    sbval = frame.EvaluateExpression(script, generate_options())

    if sbval.error.fail:
        result.AppendMessage(str(sbval.error))
        return

    val = lldb.value(sbval)
    addresses = []

    for i in range(val.count.sbvalue.unsigned):
        address = val.address[i].sbvalue.unsigned
        sbaddr = target.ResolveLoadAddress(address)
        load_addr = sbaddr.GetLoadAddress(target)
        addresses.append(load_addr)

    if options.resymbolicate:
        ret_string = sbt.process_stack_trace_string_from_addresses(addresses, target)
    else:
        ret_string = process_stack_trace_string_from_addresses(addresses, target)

    free_expr = "free(" + str(val.addresses.sbvalue.unsigned) + ")"

    frame.EvaluateExpression(free_expr, generate_options())
    result.AppendMessage(ret_string)


def process_stack_trace_string_from_addresses(frame_addresses, target):
    """
    Generates a human-readable stack trace from memory addresses.

    Args:
        frame_addresses (list): A list of memory addresses representing stack frames.
        target (lldb.SBTarget): The LLDB target for resolving addresses.

    Returns:
        str: A formatted stack trace string.
    """

    frame_string = ""
    for index, frame_addr in enumerate(frame_addresses):
        addr = target.ResolveLoadAddress(frame_addr)
        symbol = addr.symbol
        name = symbol.name
        offset_str = ""
        offset = addr.GetLoadAddress(target) - addr.symbol.addr.GetLoadAddress(target)
        if offset > 0:
            offset_str = "+ {}".format(offset)

        frame_string += f"frame # {index:<2}: {hex(addr.GetLoadAddress(target))} {addr.module.file.basename}`{name} {offset_str}\n"

    return frame_string


def generate_options():
    """
    Generates expression evaluation options for LLDB.

    Returns:
        lldb.SBExpressionOptions: Configured expression options for evaluation.
    """
    expr_options = lldb.SBExpressionOptions()
    expr_options.SetUnwindOnError(True)
    expr_options.SetLanguage(lldb.eLanguageTypeObjC_plus_plus)
    expr_options.SetCoerceResultToId(True)
    expr_options.SetGenerateDebugInfo(True)
    return expr_options


def generate_script(addr, options):
    """
    Generates an LLDB script to retrieve memory stack traces from a given address.

    Args:
        addr (str): The memory address to analyze.
        options (optparse.Values): Parsed command-line options.

    Returns:
        str: The generated script to execute in LLDB.
    """

    script = "  mach_vm_address_t addr = (mach_vm_address_t)" + str(addr) + ";\n"
    script += r"""
typedef struct $LLDBStackAddress {
    mach_vm_address_t *addresses;
    uint32_t count = 0;
} $LLDBStackAddress;

  $LLDBStackAddress stackaddress;
  mach_vm_address_t address = (mach_vm_address_t)addr;
  void * task = mach_task_self_;
  stackaddress.addresses = (mach_vm_address_t *)calloc(100, sizeof(mach_vm_address_t));
  __mach_stack_logging_get_frames(task, address, stackaddress.addresses, 100, &stackaddress.count);
  stackaddress
  """
    return script


def generate_option_parser():
    """
    Creates an option parser for the `msl` command.

    Returns:
        optparse.OptionParser: The configured option parser.
    """

    usage = "usage: %prog [options] 0xaddrE55"
    parser = optparse.OptionParser(usage=usage, prog="msl")
    parser.add_option(
        "-r",
        "--resymbolicate",
        action="store_true",
        default=False,
        dest="resymbolicate",
        help="Resymbolicate Stripped out Objective-C code",
    )
    return parser
