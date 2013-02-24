import getopt # FIXME now we've dropped 2.2 we can use optparse
import os
import string

import fractal

# version of Gnofract 4D
version = '3.14.1'

class OptionError(Exception):
    pass

class T:
    "Gathers command-line args, wraps crappy getOpt interface"
    longparams = [
            "params=",
            "maxiter=",
            "width=",
            "height=",
            "antialias=",
            "save=",
            "help",
            "path=",
            "formula=",            
            "inner=",
            "outer=",
            "transforms=",
            "map=",
            "xcenter=","ycenter=","zcenter=","wcenter=",
            "xyangle=","xzangle=","xwangle=",
            "yzangle=","ywangle=","zwangle=",
            "magnitude=",
            "quit",
            "explorer",
            "trace",
            "tracez",
            "nogui",
            "buildonly=",
            "usebuilt=",
            "cflags=",
            "printstats",
            "version",
            "singlepoint",
            "threads=",
            "nopreview"]

    def __init__(self):
        (self.basename,self.func) = (None,None)
        (self.innername,self.innerfunc) = (None,None)
        (self.outername,self.outerfunc) = (None,None)
        self.transforms = []
        self.maxiter = -1
        self.trace = False
        self.tracez = False
        self.buildonly = None
        self.usebuilt = None
        self.flags = None
        self.printstats = False
        self.singlepoint = False
        self.print_version = False
        self.paramchanges = {}
        self.quit_now = False
        self.quit_when_done = False
        self.output = ""
        self.explore = False
        self.save_filename = None
        self.extra_paths = []
        self.map = None
        self.nogui = False
        self.antialias = None
        self.threads = None
        (self.width, self.height) = (0,0)
        self.preview = True

    def help(self):
        return """Gnofract 4D %s
Usage: gnofract4d [flags] [paramfile]

To generate an image non-interactively, use:
gnofract4d -s myimage.png -q myfractal.fct 

General Flags:
-h --help\t\tShow this message
-v --version\t\tShow version info
-q --quit\t\tExit as soon as the image is finished
-X --explorer\t\tStart in explorer mode

Fractal Settings:
-p --params FILE\tUse FILE as a parameter file
-P --path P\t\tAdd P to the formula search path
-f --formula F#func\tUse formula 'func' from file F
   --inner F#func\tUse coloring algorithm 'func' from file F
   --outer F#func\tUse coloring algorithm 'func' from file F
   --transforms F#func1,F2#func2\tApply transforms 'func1' and 'func2'
-m --maxiter N\t\tUse N as maximum number of iterations
   --map FILE\t\tLoad map file FILE

Output Settings:
-s --save IMAGEFILE\tSave image to IMAGEFILE after calculation
-i --width N\t\tMake image N pixels wide
-j --height N\t\tMake image N pixels tall
-a --antialias MODE\tAntialiasing mode (one of none|fast|best)

Positional Parameters:
   --xcenter N
   --ycenter N
   --zcenter N
   --wcenter N
   --xyangle N
   --xzangle N
   --xwangle N
   --yzangle N
   --ywangle N
   --zwangle N
   --magnitude N

Obscure settings:
   --nogui\t\tRun with no UI (doesn't require X or GTK)
   --threads N\t\tUse N threads for calculations
   --nopreview\t\tUse the UI, but no preview window

Debugging and Profiling settings (most only work with --nogui):
   --trace\t\tProduce voluminous tracing output
   --tracez\t\tPrint values of #z as loop runs
   --printstats\tPrint timing information after each image
   --buildonly FILE\tGenerate code to FILE and quit
   --usebuilt FILE\tInstead of using compiler, load FILE (from buildonly)
   --singlepoint\tGenerate only a single point many times over (for benchmarking)
   --cflags FLAGS\tPass these flags to C compiler (overrides prefs)

""" % version

    def parse(self,args):
        (opts, self.args) = (None,None)
        try:
            (opts, self.args) = getopt.getopt(
                args,
                "p:m:i:j:a:s:f:qhP:Xv", T.longparams)
        except getopt.GetoptError, err:
            raise OptionError(err)
        
        for (name, val) in opts:
            if name=="-p" or name=="--params":
                self.args.insert(0,val)
            elif name=="-m" or name=="--maxiter":
                self.maxiter=int(val)
            elif name=="-q" or name=="--quit":
                self.quit_when_done = True
            elif name=="-s" or name=="--save":
                self.save_filename = val
            elif name=="-i" or name=="--width":
                self.width = int(val)
            elif name=="-j" or name=="--height":
                self.height = int(val)
            elif name=="-a" or name=="--antialias":
                self.antialias = self.parse_aa(val)
            elif name=="-h" or name=="--help":
                self.output += self.help()
                self.quit_now = True
            elif name=="-P" or name=="--path":
                self.extra_paths.append(val)
            elif name=="-X" or name=="--explorer":
                self.explore = True
            elif name=="-f" or name=="--formula":
                (self.basename,self.func) = self.splitarg(val,name)
            elif name=="--inner":
                (self.innername,self.innerfunc) = self.splitarg(val,name)
            elif name=="--outer":
                (self.outername,self.outerfunc) = self.splitarg(val,name)
            elif name=="--transforms":
                tlist = string.split(val,",")
                for t in tlist:
                    self.transforms.append(self.splitarg(t,name))
            elif (name=="--map"):
                self.map = val
            elif name=="--version" or name=="-v":
                self.print_version = True
                self.quit_now = True
            elif name=="--trace":
                self.trace = True
            elif name=="--tracez":
                self.tracez = True
            elif name=="--buildonly":
                self.buildonly = val
            elif name=="--usebuilt":
                self.usebuilt = val
            elif name=="--cflags":
                self.flags = val
            elif name=="--nogui":
                self.nogui = True
            elif name=="--nopreview":
                self.preview = False
            elif name=="--threads":
                self.threads = int(val)
            elif name=="--printstats":
                self.printstats = True
            elif name=="--singlepoint":
                self.singlepoint = True
            else:
                # see if it's a positional param
                pname = name[2:].upper()
                if hasattr(fractal.T,pname):
                    pnum = getattr(fractal.T,pname)
                    self.paramchanges[pnum]= val
                else:
                    self.output += "Unknown argument: '%s' with value '%s'" % (name, val)

    def splitarg(self,val, name):
        n = val.rfind('#')
        if n==-1:            
            raise OptionError(
                "argument '%s' to %s should be file#func" % (val,name))
        
        (file, func) = (val[:n], val[n+1:])
        path = os.path.dirname(file)
        if path:
            self.extra_paths.append(path)

        basename = os.path.basename(file)
        return (basename,func)

    def parse_aa(self,val):
        val = val.lower()
        if val == "none":
            return 0
        if val == "fast":
            return 1
        if val == "best":
            return 2
        raise OptionError(
            "antialias option must be one of: 'none', 'fast', 'best', not '%s'" % val)
            

