# This is called by the main gnofract4d script

import os
import shutil

from fract4d_compiler import fc
from . import fractal, image


class T:
    def __init__(self, userConfig):
        self.userConfig = userConfig
        self.compiler = fc.Compiler(userConfig)
        self.f = fractal.T(self.compiler)

    def run(self, options):
        for path in options.extra_paths:
            self.compiler.add_func_path(path)

        if options.flags is not None:
            self.compiler.set_flags(options.flags)

        width = options.width or self.userConfig.getint("display", "width")
        height = options.height or self.userConfig.getint("display", "height")
        threads = options.threads or self.userConfig.getint(
            "general", "threads")

        if options.paramfile:
            self.load(options.paramfile)

        self.f.apply_options(options)
        self.f.antialias = options.antialias or \
            self.userConfig.getint("display", "antialias")

        outfile = self.compile(options)

        if options.buildonly is not None:
            self.buildonly(options, outfile)
            return

        if options.singlepoint:
            self.f.drawpoint()
        else:
            im = image.T(width, height)
            self.f.draw(im, threads)

        if options.save_filename:
            im.save(options.save_filename)

    def compile(self, options):
        if options.usebuilt is None:
            return self.f.compile()
        else:
            self.f.set_output_file(options.usebuilt)

    def buildonly(self, options, outfile):
        outdirname = os.path.dirname(options.buildonly)
        if len(outdirname) > 0:
            os.makedirs(outdirname)

        shutil.copy(outfile, options.buildonly)
        (base, ext) = os.path.splitext(outfile)
        cfile = base + ".c"
        shutil.copy(cfile, options.buildonly + ".c")

    def load(self, filename):
        self.f.loadFctFile(open(filename))
