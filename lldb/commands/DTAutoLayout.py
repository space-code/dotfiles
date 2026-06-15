#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

"""
This module defines the HighlightLayoutIssuesCommand class, which provides an LLDB command
to visually identify UIView objects with ambiguous Auto Layout constraints.
"""

import lldbbase as bc


def commands():
    """Returns a list of custom LLDB command instances defined in this module."""
    return [DTAutoLayoutCheckCommand()]


class DTAutoLayoutCheckCommand(bc.BaseCommand):
    """
    LLDB command that highlights UIViews with Auto Layout issues by outlining them in red.
    Usage: alcheck [-c color] [-w width]
    """

    def name(self):
        """Returns the command name as it will be used in the LLDB console (alcheck)."""
        return "alcheck"

    def description(self):
        """Provides a short description of the command's purpose."""
        return "Displays Auto Layout issues by outlining ambiguous views in red"

    def options(self):
        """
        Defines the supported command-line options for the hli command.

        Available options:
        -c, --color: The border color (default: red).
        -w, --width: The border width (default: 2.0).
        """
        return [
            bc.CommandArgument(
                short="-c",
                long="--color",
                arg="color",
                type="string",
                default="red",
                help="A color name such as 'red', 'green', etc.",
            ),
            bc.CommandArgument(
                short="-w",
                long="--width",
                arg="width",
                type="CGFloat",
                default=2.0,
                help="Desired width of border.",
            ),
        ]

    def run(self, args, options):
        """
        Executes the command logic. Finds the key window and recursively
        sets borders on any views with ambiguous layout.
        """

        # Get the current key window of the application
        key_window = bc.evaluate_expression(
            "(id)[[UIApplication sharedApplication] keyWindow]"
        )

        # Start the recursive highlighting process
        set_border_on_ambiguous(key_window, options.color, options.width)


def set_border_on_ambiguous(view, color, width):
    """
    Recursively checks if a UIView and its subviews have ambiguous layout,
    and draws a border with the given color and width if they do.

    :param view: Name of the UIView variable in LLDB (as a string address)
    :param color: UIColor name as a string (e.g., "red", "blue")
    :param width: Border width (float)
    """

    # Check if the object is actually a UIView
    if not bc.evaluate_bool_expression(f"[(id){view} isKindOfClass:[UIView class]]"):
        return

    # Check if this specific view has an ambiguous layout
    if bc.evaluate_bool_expression(f"(BOOL)[{view} hasAmbiguousLayout]"):
        draw_border(view, color, width)

    # Get the list of subviews
    subviews = bc.evaluate_expression(f"(id)[{view} subviews]")
    subviews_count = int(bc.evaluate_expression(f"(int)[(id){subviews} count]"))

    # Recursively check each subview
    if subviews_count > 0:
        for i in range(subviews_count):
            subview = bc.evaluate_expression(f"(id)[{subviews} objectAtIndex:{i}]")
            set_border_on_ambiguous(subview, color, width)


def retrieve_layer(view):
    """
    Returns the CALayer of a UIView, or the layer itself if already a CALayer.
    Raises an exception if the object does not support 'layer'.

    :param view: Name of the object in LLDB (as a string address)
    :return: The layer object address (as a string)
    """

    # If it's already a CALayer, return it as is
    if bc.evaluate_bool_expression(
        f"[(id){view} isKindOfClass:(Class)[CALayer class]]"
    ):
        return view
    # If it has a layer property, retrieve it
    elif bc.evaluate_bool_expression(
        f"[(id){view} respondsToSelector:(SEL)@selector(layer)]"
    ):
        return bc.evaluate_expression(f"(CALayer *)[{view} layer]")
    else:
        raise Exception("Argument must be a CALayer, UIView, or NSView.")


def draw_border(view, color, width):
    """
    Sets a border on the given view or layer with the specified color and width.

    :param view: Name of the view or layer variable in LLDB (string address)
    :param color: UIColor name (e.g., "red", "blue")
    :param width: Border width (float)
    """

    layer = retrieve_layer(view)

    # Set the border width on the CALayer
    bc.evaluate_effect(f"[{layer} setBorderWidth:(CGFloat){width}]")

    # Set the border color on the CALayer using the requested UIColor
    bc.evaluate_effect(
        f"[{layer} setBorderColor:(CGColorRef)[(id)[UIColor {color}Color] CGColor]]"
    )
