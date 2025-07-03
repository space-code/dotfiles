#
#  dotfiles
#  Copyright © 2025 Space Code. All rights reserved.
#

import lldbbase as bc


def commands():
    return [HelloCommand()]


class HelloCommand(bc.BaseCommand):
    def name(self):
        return "hello"

    def description(self):
        return "Prints a hello message"

    def run(self, args, options):
        print("hello")
