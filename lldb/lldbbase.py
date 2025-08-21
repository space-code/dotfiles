#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

from abc import ABC, abstractmethod
import lldb
import shlex


class BaseCommand(ABC):
    """
    Abstract base class for defining custom LLDB commands.
    """

    result = None
    context = None

    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the command as typed in LLDB.
        """
        pass

    @abstractmethod
    def description(self) -> str:
        """
        Returns a multiline string describing the command.
        """
        pass

    def args(self) -> list:
        """
        Returns a list of positional argument definitions (optional).
        """
        return []

    def options(self) -> list:
        """
        Returns a list of supported command-line flags (optional).
        """
        return []

    def lex(self, input_str: str) -> list:
        """
        Parses the raw input string into tokens.
        """
        return shlex.split(input_str)

    @abstractmethod
    def run(self, args: list, options: object):
        """
        Executes the command logic.
        """
        pass


class CommandArgument:
    def __init__(
        self, short="", long="", arg="", type="", help="", default="", boolean=False
    ):
        self.shortName = short
        self.longName = long
        self.argName = arg
        self.argType = type
        self.help = help
        self.default = default
        self.boolean = boolean


def evaluate_expression_value(expression, language=lldb.eLanguageTypeObjC_plus_plus):
    """
    Evaluates an expression in the current LLDB debugging frame
    and returns the raw SBValue object instead of just its value string.
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
        print(error)

    return value


def evaluate_expression(expression, language=lldb.eLanguageTypeObjC_plus_plus):
    """
    Evaluates an expression in the current LLDB debugging frame
    and returns its string representation (.GetValue()).
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
        print(error)

    return value.GetValue()


def evaluate_effect(expression):
    """
    Evaluates an expression purely for its side effects.
    Wraps the expression in a (void) cast so no value is returned.
    """
    return evaluate_expression("(void)(" + expression + ")")


def evaluate_integer_expression(expression):
    """
    Evaluates an expression and ensures the result is converted into an integer.
    Handles LLDB string formatting quirks like quotes and escape sequences.
    """
    output = evaluate_expression("(int)(" + expression + ")").replace("'", "")
    if output.startswith("\\x"):
        output = output[2:]
    elif output.startswith("\\"):
        output = output[1:]
    return int(output, 0)


def evaluate_bool_expression(expression):
    """
    Evaluates an expression as a BOOL (Objective-C style boolean).
    Returns True if nonzero, False otherwise.
    """
    return int(evaluate_integer_expression("(BOOL)(" + expression + ")")) != 0
