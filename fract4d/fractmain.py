# This is called by the main gnofract4d script

import shutil, os
import fractal,fc,fract4dc,image, fracttypes, fractconfig

class T:
    def __init__(self):
        self.compiler = fc.Compiler()
        self.update_compiler_prefs(fractconfig.instance)
        self.f = fractal.T(self.compiler)
        
    def update_compiler_prefs(self, prefs):
        self.compiler.update_from_prefs(prefs)
        
    def run(self,options):
        for path in options.extra_paths:            
            self.compiler.add_func_path(path)
        
        if options.flags != None:
            self.compiler.set_flags(options.flags)

        width = options.width or fractconfig.instance.getint("display","width")
        height = options.height or fractconfig.instance.getint("display","height")        
        threads = options.threads or fractconfig.instance.getint(
            "general","threads")

        if len(options.args) > 0:
            self.load(options.args[0])

        self.f.apply_options(options)
        self.f.antialias = options.antialias or \
            fractconfig.instance.getint("display","antialias")

        outfile = self.compile(options)

        if options.buildonly != None:
            self.buildonly(options, outfile)
            return            

        if options.singlepoint:
            self.f.drawpoint()
        else:
            im = image.T(width,height)
            self.f.draw(im,threads)

        if options.save_filename:
            im.save(options.save_filename)

    def compile(self,options):
        if options.usebuilt == None:
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

    def load(self,filename):
        self.f.loadFctFile(open(filename))
