#!/usr/bin/env python

# Override the default build distutils command to do what I want

from distutils.command.build_ext import build_ext
from distutils.core import Command
import os
import re

remove_mtune = re.compile(r'-mtune=\w*')

class my_build_ext (build_ext):
    user_options = build_ext.user_options
    def __init__(self, dict):
        build_ext.__init__(self,dict)
        self._build_temp = None
        
    def build_extensions(self):
        # python2.2 doesn't honor these, so we have to sneak them in
        cxx = os.environ.get("CXX")
        cc = os.environ.get("CC")

        print "compiling with", cc
        if cc:
            self.compiler.preprocessor[0] = cc
            self.compiler.compiler_so[0] = cc
            self.compiler.compiler[0] = cc
        
            if cc.find("33") > -1:
                print "cc is old"
                # rpm thinks we should have -mtune, but older gcc doesn't like it
                cflags = os.environ.get("CFLAGS")
                if cflags != None:
                    cflags = remove_mtune.sub("",cflags)
                    print "cflags", cflags
                    os.environ["CFLAGS"] = cflags

                self.compiler.compiler = [
                    opt for opt in self.compiler.compiler \
                        if opt.find("-mtune") == -1 ]

                self.compiler.compiler_so = [
                    opt for opt in self.compiler.compiler_so \
                        if opt.find("-mtune") == -1 ]

        if cxx:
            if hasattr(self.compiler, "compiler_cxx"):
                self.compiler.compiler_cxx[0] = cxx
            self.compiler.linker_so[0] = cxx

        build_ext.build_extensions(self)

