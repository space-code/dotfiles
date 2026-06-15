#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

"""
This module defines the DTHexDumpCommand class, which provides a custom LLDB command
for reading memory at a specific address and displaying it in a formatted hex dump.
"""

import lldbbase as bc


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
        return super().run(args, options)
