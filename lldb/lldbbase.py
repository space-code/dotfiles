#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

"""
This module provides the foundation for creating custom LLDB commands.
It defines the BaseCommand abstract class and utility functions for
evaluating expressions within the LLDB environment.
"""

from abc import ABC, abstractmethod
import lldb
import shlex


class BaseCommand(ABC):
    """
    Abstract base class for defining custom LLDB commands.

    Subclasses must implement:
    - name(): The string used to invoke the command in LLDB.
    - description(): A help string for the command.
    - run(): The actual execution logic.
    """

    # result and context are populated by lldbinit.py before run() is called.
    result = None
    context = None

    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the command as typed in LLDB.
        Example: return "hex_dump"
        """
        pass

    @abstractmethod
    def description(self) -> str:
        """
        Returns a multiline string describing the command.
        This is used for the LLDB help system.
        """
        pass

    def args(self) -> list:
        """
        Returns a list of positional argument definitions (optional).
        Should return a list of CommandArgument objects.
        """
        return []

    def options(self) -> list:
        """
        Returns a list of supported command-line flags (optional).
        Should return a list of CommandArgument objects.
        """
        return []

    def lex(self, input_str: str) -> list:
        """
        Parses the raw input string into tokens using shell-like syntax.

        :param input_str: The raw input string from LLDB.
        :return: A list of string tokens.
        """
        return shlex.split(input_str)

    @abstractmethod
    def run(self, args: list, options: object):
        """
        Executes the command logic.

        :param args: A list of positional arguments.
        :param options: An object where attributes correspond to command-line flags.
        """
        pass


class CommandArgument:
    """
    Represents a single argument or option for a custom LLDB command.
    """

    def __init__(
        self, short="", long="", arg="", type="", help="", default="", boolean=False
    ):
        self.shortName = short  # e.g., "-c"
        self.longName = long  # e.g., "--count"
        self.argName = arg  # internal name used in the options object
        self.argType = type  # descriptive type string
        self.help = help  # help text for this argument
        self.default = default  # default value if not provided
        self.boolean = boolean  # True if the option is a toggle (no value)


def evaluate_expression_value(expression, language=lldb.eLanguageTypeObjC_plus_plus):
    """
    Evaluates an expression in the current LLDB debugging frame
    and returns the raw SBValue object.

    :param expression: The expression to evaluate.
    :param language: The language context for evaluation (default: ObjC++).
    :return: An lldb.SBValue object.
    """
    frame = (
        lldb.debugger.GetSelectedTarget()
        .GetProcess()
        .GetSelectedThread()
        .GetSelectedFrame()
    )

    options = lldb.SBExpressionOptions()
    options.SetTrapExceptions(False)
    options.SetLanguage(language)

    value = frame.EvaluateExpression(expression, options)

    error = value.GetError()
    if error.Fail():
        print(f"Error evaluating '{expression}': {error}")

    return value


def evaluate_expression(expression, language=lldb.eLanguageTypeObjC_plus_plus):
    """
    Evaluates an expression in the current LLDB debugging frame
    and returns its string representation (.GetValue()).

    :param expression: The expression to evaluate.
    :param language: The language context (default: ObjC++).
    :return: The string value of the expression result.
    """
    if expression.startswith("(id)"):
        return evaluate_expression_value(expression, language).GetValue()

    frame = (
        lldb.debugger.GetSelectedTarget()
        .GetProcess()
        .GetSelectedThread()
        .GetSelectedFrame()
    )

    options = lldb.SBExpressionOptions()
    options.SetTrapExceptions(False)
    options.SetLanguage(language)

    value = frame.EvaluateExpression(expression, options)

    error = value.GetError()
    if error.Fail():
        print(f"Error evaluating '{expression}': {error}")

    return value.GetValue()


def evaluate_effect(expression):
    """
    Evaluates an expression purely for its side effects (e.g., calling a method).
    Wraps the expression in a (void) cast.

    :param expression: The expression to execute.
    :return: The result of the evaluation (usually None/void).
    """
    return evaluate_expression("(void)(" + expression + ")")


def evaluate_integer_expression(expression):
    """
    Evaluates an expression and ensures the result is converted into a Python integer.
    Handles hex strings and other LLDB formatting quirks.

    :param expression: The expression resulting in an integer.
    :return: An integer value.
    """
    output = evaluate_expression("(int)(" + expression + ")").replace("'", "")
    if output.startswith("\\x"):
        output = output[2:]
    elif output.startswith("\\"):
        output = output[1:]

    try:
        return int(output, 0)
    except ValueError:
        return 0


def evaluate_bool_expression(expression):
    """
    Evaluates an expression as a BOOL (Objective-C style boolean).
    Returns True if the result is non-zero, False otherwise.

    :param expression: The expression resulting in a BOOL.
    :return: True or False.
    """
    return int(evaluate_integer_expression("(BOOL)(" + expression + ")")) != 0
