import lldb


def lldb_commands():
    """Returns a list of the LLDB commands."""
    return []


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        "command script add -f auto_layout_trace.auto_layout_trace alt"
    )
