#!/usr/bin/env python

# Override the default build distutils command to do what I want

from distutils.command.build import build
from distutils.core import Command

class my_build (build):
    user_options = build.user_options
    def __init__(self, dict):
        build.__init__(self,dict)

        new_commands = []
        for (name,pred) in build.sub_commands:
            if name == "build_ext":
                name = "my_build_ext"
            new_commands.append((name,pred))
            
        build.sub_commands = new_commands

