import argparse
import collections
import os.path
import sys

# version of Gnofract 4D
VERSION = '4.0'

POSITION_ARGUMENTS = ("xcenter", "ycenter", "zcenter", "wcenter",
    "xyangle", "xzangle", "xwangle", "yzangle", "ywangle", "zwangle",
    "magnitude")

Formula = collections.namedtuple('Formula', ['path', 'name', 'func'])

def formula_type_parse(name, string):
        n = string.rfind('#')
        if n == -1:
            raise argparse.ArgumentTypeError(
                "argument '%s' to %s should be file#func" % (string, name))
        
        file, func = string[:n], string[n+1:]
        path = os.path.dirname(file)
        basename = os.path.basename(file)
        
        f = Formula(path, basename, func)
        return f

def formula_arg(string):
    return formula_type_parse("--formula", string)
    
def inner_arg(string):
    return formula_type_parse("--inner", string)

def outer_arg(string):
    return formula_type_parse("--outer", string)

def transforms_arg(string):
    transforms = []
    tlist = string.split(",")
    for t in tlist:
        transforms.append(formula_type_parse("--transforms", t))
    return transforms

class Arguments(argparse.ArgumentParser):
    def __init__(self):
        argparse.ArgumentParser.__init__(self,
            description="Gnofract 4D %s" % VERSION,
            epilog="To generate an image non-interactively, use:\n"
                    "  gnofract4d -s myimage.png -q myfractal.fct",
            formatter_class=argparse.RawDescriptionHelpFormatter
            )

        self.add_argument("paramfile", nargs='?', metavar="PARAMFILE",
            help="Use PARAMFILE as a parameter file")

        self.add_argument("-v", "--version", action="version",
            version="Gnofract 4D %s" % VERSION, help="Show version info")

        self.add_argument("-q", "--quit", action="store_true",
            dest="quit_when_done", help="Exit as soon as the image is finished")

        self.add_argument("-X", "--explorer", action="store_true",
            dest="explore", help="Start in explorer mode")

        fractal = self.add_argument_group("Fractal Settings")
        output = self.add_argument_group("Output Settings")
        position = self.add_argument_group("Position Arguments")
        obscure = self.add_argument_group("Obscure Settings")
        debug = self.add_argument_group(
            "Debugging and Profiling Settings (most only work with --nogui)")
        
        fractal.add_argument("-P", "--path",
            metavar="PATH", nargs="*", dest="extra_paths", default=[],
            help="Add PATH to the formula search path")

        fractal.add_argument("-f", "--formula", type=formula_arg,
            metavar="F#FUNC", default=Formula(None, None, None),
            help="Use formula 'FUNC' from file F")

        fractal.add_argument("--inner", type=inner_arg,
            metavar="F#FUNC", default=Formula(None, None, None),
            help="Use coloring algorithm 'FUNC' from file F")

        fractal.add_argument("--outer", type=outer_arg,
            metavar="F#FUNC", default=Formula(None, None, None),
            help="Use coloring algorithm 'FUNC' from file F")

        fractal.add_argument("--transforms", type=transforms_arg,
            metavar="F#FUNC1,F2#FUNC2", default=[],
            help="Apply transforms 'FUNC1' and 'FUNC2'")

        fractal.add_argument("-m", "--maxiter", type=int,
            metavar="N", default=-1,
            help="Use N as maximum number of iterations")

        fractal.add_argument("--map", metavar="FILE",
            help="Load map file FILE")

        output.add_argument("-s", "--save", metavar="IMAGEFILE", dest="save_filename",
            help="Save image to IMAGEFILE after calculation")

        output.add_argument("-i", "--width", type=int, metavar="N",
            help="Make image N pixels wide")

        output.add_argument("-j", "--height", type=int, metavar="N",
            help="Make image N pixels tall")

        output.add_argument("--antialias", metavar="MODE",
            choices=['none', 'fast', 'best'],
            help="Antialiasing MODE (one of none|fast|best)")

        for p in POSITION_ARGUMENTS:
            position.add_argument("--%s" % p, type=int, metavar="N")

        obscure.add_argument("--nogui", action="store_true",
            help="Run with no UI (doesn't require X or GTK+)")

        obscure.add_argument("--threads", type=int, metavar="N",
            help="Use N threads for calculations")

        obscure.add_argument("--nopreview", action="store_false",
            dest="preview", help="Use the UI, but no preview window")

        debug.add_argument("--trace", action="store_true",
            help="Produce voluminous tracing output")

        debug.add_argument("--tracez", action="store_true",
            help="Print values of #z as loop runs")

        #debug.add_argument("--printstats", action="store_true",
        #    help="Print timing information after each image")

        debug.add_argument("--buildonly", metavar="FILE",
            help="Generate code to FILE and quit")

        debug.add_argument("--usebuilt", metavar="FILE",
            help="Instead of using compiler, load FILE (from buildonly)")

        debug.add_argument("--singlepoint", action="store_true",
            help="Generate only a single point many times over (for benchmarking)")

        debug.add_argument("--cflags", dest="flags",
            help="Pass these FLAGS to C compiler (overrides prefs)")

    def parse_args(self, args=sys.argv):
        opts = argparse.ArgumentParser.parse_args(self, args)

        if opts.formula.path:
            opts.extra_paths.append(opts.formula.path)
        if opts.inner.path:
            opts.extra_paths.append(opts.inner.path)
        if opts.outer.path:
            opts.extra_paths.append(opts.outer.path)
        for t in opts.transforms:
            if t.path:
                opts.extra_paths.append(t.path)

        opts.paramchanges = {}
        for a in POSITION_ARGUMENTS:
            val = getattr(opts, a)
            if val is not None:
                pnum = getattr(fractal.T, a.upper())
                opts.paramchanges[pnum] = val

        return opts
