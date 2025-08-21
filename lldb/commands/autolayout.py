#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

import lldbbase as bc


def commands():
    """Return a list of custom LLDB commands registered in the plugin"""
    return [HighlightLayoutIssuesCommand()]


class HighlightLayoutIssuesCommand(bc.BaseCommand):
    """LLDB command that highlights UIViews with Auto Layout issues by outlining them in red."""

    def name(self):
        """The command name used in LLDB (e.g. (lldb) hli)"""
        return "hli"

    def description(self):
        """Displays Auto Layout issues by outlining ambiguous views in red"""
        return "Displays Auto Layout issues by outlining ambiguous views in red"

    def options(self):
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
        Objective-C / Swift runtime code that finds all ambiguous layout views
        and highlights them with a red border
        """

        key_window = bc.evaluate_expression(
            "(id)[[UIApplication sharedApplication] keyWindow]"
        )
        set_border_on_ambiguous(key_window, options.color, options.width)


def set_border_on_ambiguous(view, color, width):
    """
    Recursively checks if a UIView and its subviews have ambiguous layout,
    and draws a border with the given color and width if they do.

    :param view: Name of the UIView variable in LLDB (as a string)
    :param color: UIColor name as a string (e.g., "red", "blue")
    :param width: Border width (float)
    """

    if not bc.evaluate_bool_expression(f"[(id){view} isKindOfClass:[UIView class]]"):
        return

    if bc.evaluate_bool_expression(f"(BOOL)[{view} hasAmbiguousLayout]"):
        draw_border(view, color, width)

    subviews = bc.evaluate_expression(f"(id)[{view} subviews]")
    subviews_count = int(bc.evaluate_expression(f"(int)[(id){subviews} count]"))

    if subviews_count > 0:
        for i in range(subviews_count):
            subview = bc.evaluate_expression(f"(id)[{subviews} objectAtIndex:{i}]")
            set_border_on_ambiguous(subview, color, width)


def retrieve_layer(view):
    """
    Returns the CALayer of a UIView, or the layer itself if already a CALayer.
    Raises an exception if the object does not support 'layer'.

    :param view: Name of the object in LLDB (as a string)
    :return: The layer object (as a string)
    """

    if bc.evaluate_bool_expression(
        f"[(id){view} isKindOfClass:(Class)[CALayer class]]"
    ):
        return view
    elif bc.evaluate_bool_expression(
        f"[(id){view} respondsToSelector:(SEL)@selector(layer)]"
    ):
        return bc.evaluate_expression(f"(CALayer *)[{view} layer]")
    else:
        raise Exception("Argument must be a CALayer, UIView, or NSView.")


def draw_border(view, color, width):
    """
    Sets a border on the given view or layer with the specified color and width.

    :param view: Name of the view or layer variable in LLDB (string)
    :param color: UIColor name (e.g., "red", "blue")
    :param width: Border width (float)
    """

    layer = retrieve_layer(view)
    bc.evaluate_effect(f"[{layer} setBorderWidth:(CGFloat){width}]")
    bc.evaluate_effect(
        f"[{layer} setBorderColor:(CGColorRef)[(id)[UIColor {color}Color] CGColor]]"
    )
