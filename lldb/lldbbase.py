#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

from abc import ABC, abstractmethod

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
        return []
    
    @abstractmethod
    def run(self, args: list, options: object):
        """
        Executes the command logic.
        """
        pass