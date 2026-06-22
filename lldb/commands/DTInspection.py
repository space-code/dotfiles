#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

"""
This module defines the DTHexDumpCommand class, which provides a custom LLDB command
for reading memory at a specific address and displaying it in a formatted hex dump.
"""

import lldbbase as bc
import lldb


def commands():
    """
    Returns a list of custom LLDB command instances defined in this module.
    The registration logic in lldbinit.py calls this function.
    """
    return [DTHexDumpCommand()]


class DTHexDumpCommand(bc.BaseCommand):
    """
    A custom LLDB command that performs a hex dump of memory at a given address.
    Usage: hex_dump <address> [-c count] [-o offset]
    """

    def name(self):
        """Returns the command name as it will be used in the LLDB console."""
        return "hex_dump"

    def description(self):
        """Returns a short description of the command's functionality."""
        return "Read data from the specific address and return formatted output."

    def options(self):
        """
        Defines the supported command-line options for the hex_dump command.

        Available options:
        -c, --count: Number of bytes to read (default: 16).
        -o, --offset: Starting offset from the provided address (default: 0).
        """
        return [
            bc.CommandArgument(
                short="-c",
                long="--count",
                arg="count",
                type="string",
                default="16",
                help="The number of bytes to read from memory.",
            ),
            bc.CommandArgument(
                short="-o",
                long="--offset",
                arg="offset",
                type="string",
                default="0",
                help="The memory offset (in bytes) to start reading from.",
            ),
        ]

    def run(self, args, options):
        """
        The main execution logic for the command.

        Parameters:
            args: Positional arguments (the memory address).
            options: Parsed command-line options (count, offset).
        """

        if not args:
            print("error: target address is missing. Example: hex_dump $x0")
            return

        target = lldb.debugger.GetSelectedTarget()
        process = target.GetProcess()

        if not process or not process.IsValid():
            print("error: valid active process not found")
            return

        thread = process.GetSelectedThread()
        frame = thread.GetSelectedFrame() if thread else None

        raw_address = args[0]
        base_address = None

        if frame and frame.IsValid() and raw_address.startswith("$"):
            reg_name = raw_address[1:]
            register = frame.FindRegister(reg_name)

            if register.IsValid():
                base_address = register.GetValueAsUnsigned()

        if base_address is None:
            if frame and frame.IsValid():
                expr_value = frame.EvaluateExpression(raw_address)
            else:
                expr_value = target.EvaluateExpression(raw_address)

            if not expr_value.IsValid() or expr_value.GetError().Fail():
                err_desc = (
                    expr_value.GetError().GetCString()
                    if expr_value.IsValid()
                    else "invalid expression"
                )
                print(
                    f"error: unable to resolve address expression {raw_address}: {err_desc}"
                )
                return

            base_address = expr_value.GetValueAsUnsigned()

        if base_address is None or base_address == 0:
            print(f"error: unable to resolve address expression {raw_address}")
            return

        try:
            count = int(options.count, 0)
            offset = int(options.offset, 0)
        except ValueError:
            print("error: parameters -c (count) and -o (offset) must be integers")
            return

        target_address = base_address + offset

        error = lldb.SBError()
        bytes_data = process.ReadMemory(target_address, count, error)

        if error.Fail() or bytes_data is None:
            print(
                f"error: failed to read memory at 0x{target_address:02x} {error.GetCString()}"
            )
            return

        print(
            "\nAddress            00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  ASCII"
        )
        print("-" * 80)

        for i in range(0, len(bytes_data), 16):
            chunk = bytes_data[i : i + 16]
            current_addr = target_address + i

            hex_strings = [f"{b:02x}" for b in chunk]

            if len(hex_strings) > 8:
                hex_part = " ".join(hex_strings[:8]) + "  " + " ".join(hex_strings[8:])
            else:
                hex_part = " ".join(hex_strings)

            hex_part = hex_part.ljust(48)

            ascii_chars = []

            for b in chunk:
                byte_val = b if isinstance(b, int) else ord(b)

                if 32 <= byte_val <= 126:
                    ascii_chars.append(chr(byte_val))
                else:
                    ascii_chars.append(".")

            ascii_part = "".join(ascii_chars)

            print(f"0x{current_addr:016x}  {hex_part}  {ascii_part}")

        print("")
