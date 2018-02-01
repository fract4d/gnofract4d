#!/usr/bin/env python3

# A compiler from UltraFractal or Fractint formula files to C code

# The UltraFractal manual is the best current description of the file
# format. You can download it from http://www.ultrafractal.com/uf3-manual.zip

# The implementation is based on the outline in "Modern Compiler
# Implementation in ML: basic techniques" (Appel 1997, Cambridge)

# Overall structure:
# fractlexer.py and fractparser.py are the lexer and parser, respectively.
# They use the PLY package to do lexing and SLR parsing, and produce as
# output an abstract syntax tree (defined in the Absyn module).

# The Translate module type-checks the code, maintains the symbol
# table (symbol.py) and converts it into an intermediate form (ir.py)

# Canon performs several simplifying passes on the IR to make it easier
# to deal with, then codegen converts it into a linear sequence of
# simple C instructions

# Finally we invoke the C compiler to convert to a native code shared library

import getopt
import sys
import subprocess
import os.path
import stat
import random
import hashlib
import re
import copy

from . import fractconfig
from . import fractparser
from . import fractlexer
from . import translate
from . import codegen
from . import fracttypes
from . import absyn
from . import preprocessor
from . import cache
from . import gradient

class FormulaTypes:
    FRACTAL = 0
    COLORFUNC = 1
    TRANSFORM = 2
    GRADIENT = 3
    NTYPES = 4

    GRAD_UGR=0
    GRAD_MAP=1
    GRAD_GGR=2
    GRAD_CS=3
    matches = [
        re.compile(r'(\.frm\Z)|(\.ufm\Z)', re.IGNORECASE),
        re.compile(r'(\.cfrm\Z)|(\.ucl\Z)', re.IGNORECASE),
        re.compile(r'\.uxf\Z', re.IGNORECASE),
        re.compile(r'(\.ugr\Z)|(\.map\Z)|(\.ggr\Z)|(\.cs\Z)|(\.pal\Z)', re.IGNORECASE)
        ]
    
    # indexed by FormulaTypes above
    extensions = [ "frm", "cfrm", "uxf", "ggr", "pal"]

    @staticmethod
    def extension_from_type(t):
        return FormulaTypes.extensions[t]

    @staticmethod
    def guess_type_from_filename(filename):
        if FormulaTypes.matches[FormulaTypes.FRACTAL].search(filename):
            return translate.T
        elif FormulaTypes.matches[FormulaTypes.COLORFUNC].search(filename):
            return translate.ColorFunc        
        elif FormulaTypes.matches[FormulaTypes.TRANSFORM].search(filename):
            return translate.Transform
        elif FormulaTypes.matches[FormulaTypes.GRADIENT].search(filename):
            return translate.GradientFunc

    @staticmethod
    def guess_formula_type_from_filename(filename):
        for i in range(FormulaTypes.NTYPES):
            if FormulaTypes.matches[i].search(filename):
                return i
        raise ValueError("Unknown file type for '%s'" % filename)

    @staticmethod
    def guess_gradient_subtype_from_filename(filename):
        filename = filename.lower()
        if filename.endswith(".ugr"):
            return FormulaTypes.GRAD_UGR
        if filename.endswith(".map") or filename.endswith(".pal"):
            return FormulaTypes.GRAD_MAP
        if filename.endswith(".ggr"):
            return FormulaTypes.GRAD_GGR
        if filename.endswith(".cs"):
            return FormulaTypes.GRAD_CS
        raise ValueError("Unknown gradient type for '%s'" % filename)

    @staticmethod
    def is_binary_filetype(filename):
        if FormulaTypes.guess_formula_type_from_filename(filename) == FormulaTypes.GRADIENT and \
           FormulaTypes.guess_gradient_subtype_from_filename(filename) == FormulaTypes.GRAD_CS:
            return True
        return False

    @staticmethod
    def isFormula(filename):
        for matcher in FormulaTypes.matches:
            if matcher.search(filename):
                return True
        return False
    
    
class FormulaFile:
    def __init__(self, formulas, contents,mtime,filename):
        self.formulas = formulas
        self.contents = contents
        self.mtime = mtime
        self.filename = filename
        self.file_backed = True
        
    def out_of_date(self):
        return self.file_backed and \
               os.stat(self.filename)[stat.ST_MTIME] > self.mtime
    
    def get_formula(self,formula):
        return self.formulas.get(formula)
    
    def get_formula_names(self, skip_type=None):
        '''return all the coloring funcs except those marked as only suitable
        for the OTHER kind (inside vs outside)'''
        names = []
        for name in list(self.formulas.keys()):
            sym = self.formulas[name].symmetry
            if sym == None  or sym == "BOTH" or sym != skip_type:
                names.append(name)

        return names
    
class Compiler:
    def __init__(self):
        self.parser = fractparser.parser
        self.lexer = fractlexer.lexer
        self.c_code = ""
        self.path_lists = [ [], [], [], [] ]
        self.cache = cache.T()
        self.cache_dir = os.path.expanduser("~/.gnofract4d-cache/")
        self.init_cache()
        if 'win' != sys.platform[:3]:
            self.compiler_name = "gcc"
            self.flags = "-fPIC -DPIC -g -O3 -shared"
            self.output_flag = "-o "
            self.libs = "-lm"
        else:
            self.compiler_name = "cl"
            self.flags = "/EHsc /Gd /nologo /W3 /LD /MT /TP /DWIN32 /DWINDOWS /D_USE_MATH_DEFINES"
            self.output_flag = "/Fe"
            self.libs = "/link /LIBPATH:\"%s/fract4d\" fract4d_stdlib.lib" % sys.path[0] # /DELAYLOAD:fract4d_stdlib.pyd DelayImp.lib
        self.tree_cache = {}
        self.leave_dirty = False
        self.next_inline_number = 0

    def _get_files(self):
        return self.cache.files

    files = property(_get_files)

    def update_from_prefs(self,prefs):
        self.compiler_name = prefs.get("compiler","name")
        self.flags = prefs.get("compiler","options")

        self.set_func_path_list(prefs.get_list("formula_path"))
        self.path_lists[FormulaTypes.GRADIENT] = copy.copy(
            prefs.get_list("map_path"))
        
    def set_flags(self,flags):
        self.flags = flags

    def add_path(self,path,type):
        self.path_lists[type].append(path)

    def add_func_path(self,path):
        self.path_lists[FormulaTypes.FRACTAL].append(path)
        self.path_lists[FormulaTypes.COLORFUNC].append(path)
        self.path_lists[FormulaTypes.TRANSFORM].append(path)

    def set_func_path_list(self,list):
        self.path_lists[FormulaTypes.FRACTAL] = copy.copy(list)
        self.path_lists[FormulaTypes.COLORFUNC] = copy.copy(list)
        self.path_lists[FormulaTypes.TRANSFORM] = copy.copy(list)
        
    def init_cache(self):
        self.cache.init()

    def find_files(self,type):
        files = {}
        for dir in self.path_lists[type]:
            if not os.path.isdir(dir):
                continue
            for file in os.listdir(dir):
                if os.path.isfile(os.path.join(dir,file)):
                    files[file] = 1
        return list(files.keys())

    def find_files_of_type(self,type):
        matcher = FormulaTypes.matches[type]
        return [file for file in self.find_files(type)
                if matcher.search(file)]

    def find_formula_files(self):
        return self.find_files_of_type(FormulaTypes.FRACTAL)
                
    def find_colorfunc_files(self):
        return self.find_files_of_type(FormulaTypes.COLORFUNC)

    def find_transform_files(self):
        return self.find_files_of_type(FormulaTypes.TRANSFORM)

    def get_text(self,fname):
        file = self.files.get(fname)
        if not file:
            self.load_formula_file(fname)
        
        return self.files[fname].contents

    def nextInlineFile(self,type):
        self.next_inline_number += 1
        ext = FormulaTypes.extension_from_type(type)
        return "__inline__%d.%s" % (self.next_inline_number, ext)

    def add_inline_formula(self,formbody, formtype):
        # formbody contains a string containing the contents of a formula
        formulas = self.parse_file(formbody)

        fname = self.nextInlineFile(formtype)
        ff = FormulaFile(formulas,formbody,0,fname)
        ff.file_backed = False
        self.files[fname] = ff
        names = ff.get_formula_names()
        if len(names) == 0:
            formName = "error"
        else:
            formName = names[0]
        return (fname, formName)

    def last_chance(self,filename):
        '''does nothing here, but can be overridden by GUI to prompt user.'''
        raise IOError("Can't find formula file %s in formula search path" % \
                      filename)

    def compile_one(self,formula):
        self.compile(formula)

        t = translate.T(absyn.Formula("",[],-1))
        cg = self.compile(t)
        t.merge(formula,"")
        outputfile = os.path.abspath(self.generate_code(t, cg))        
        return outputfile
        
    def compile_all(self,formula,cf0,cf1,transforms,options={}):        
        self.compile(formula,options)
        self.compile(cf0,options)
        self.compile(cf1,options)

        for transform in transforms:
            self.compile(transform,options)
            
        # create temp empty formula and merge everything into that
        t = translate.T(absyn.Formula("",[],-1))
        cg = self.compile(t,options)
        t.merge(formula,"")
        t.merge(cf0,"cf0_")        
        t.merge(cf1,"cf1_")

        for transform in transforms:
            t.merge(transform,"t_")
        
        outputfile = os.path.abspath(self.generate_code(t, cg))
        
        return outputfile
    
    def find_file(self,filename,type):
        if os.path.exists(filename):
            dir = os.path.dirname(filename)
            if self.path_lists[type].count(dir) == 0:
                # add directory to search path
                self.path_lists[type].append(dir)            
            return filename

        filename = os.path.basename(filename)
        for path in self.path_lists[type]:
            f = os.path.join(path,filename)
            if os.path.exists(f):
                return f

        return self.last_chance(filename)        

    def add_endlines(self,result,final_line):
        "Add info on which is the final source line of each formula"
        if None == result:
            return

        l = len(result.children)
        for i in range(l):
            if i == l - 1:
                result.children[i].last_line = final_line
            else:
                result.children[i].last_line = result.children[i+1].pos-1
            
    def parse_file(self,s):
        self.lexer.lineno = 1
        result = None
        try:
            pp = preprocessor.T(s)
            result = self.parser.parse(pp.out())
        except preprocessor.Error as err:
            # create an Error formula listing the problem
            result = self.parser.parse('error {\n}\n')

            result.children[0].children[0] = \
                absyn.PreprocessorError(str(err), -1)
            #print result.pretty()

        self.add_endlines(result,self.lexer.lineno)

        formulas = {}
        for formula in result.children:
            formulas[formula.leaf] = formula
        return formulas
    
    def load_formula_file(self, filename):
        try:
            type = FormulaTypes.guess_formula_type_from_filename(filename)            
            filename = self.find_file(filename,type)
            mode= "r"
            if FormulaTypes.is_binary_filetype(filename): mode = "rb"                
            f = open(filename, mode)
            s = f.read() # read in a whole file
            f.close()
            basefile = os.path.basename(filename)
            mtime = os.stat(filename)[stat.ST_MTIME]

            if type == FormulaTypes.GRADIENT:
                # don't try and parse gradient files apart from UGRs
                subtype = FormulaTypes.guess_gradient_subtype_from_filename(filename)
                if subtype == FormulaTypes.GRAD_UGR:
                    formulas = self.parse_file(s)
                else:
                    formulas = {}
            else:
                formulas = self.parse_file(s)

            ff = FormulaFile(formulas,s,mtime,filename)
            self.files[basefile] = ff 

            return ff
        except Exception as err:
            #print "Error parsing '%s' : %s" % (filename, err)
            raise

    def out_of_date(self,filename):
        basefile = os.path.basename(filename)
        ff = self.files.get(basefile)
        if not ff:            
            self.load_formula_file(filename)
            ff = self.files.get(basefile)
        return ff.out_of_date()
    
    def get_file(self,filename):
        basefile = os.path.basename(filename)
        ff = self.files.get(basefile)
        if not ff:
            self.load_formula_file(filename)
            ff = self.files.get(basefile)
        elif ff.out_of_date():
            self.load_formula_file(filename)
            ff = self.files.get(basefile)            
        return ff

    def get_formula_text(self,filename,formname):
        ff = self.get_file(filename)
        form = ff.get_formula(formname)
        start_line = form.pos-1
        last_line = form.last_line
        lines = ff.contents.splitlines()
        return "\n".join(lines[start_line:last_line])

    def is_inline(self,filename, formname):
        return not self.files[filename].file_backed

    def compile(self,ir,options={}):
        cg = codegen.T(ir.symbols,options)
        cg.output_all(ir)
        return cg

    def hashcode(self,c_code):
        hash = hashlib.md5()
        hash.update(c_code.encode('utf-8'))
        hash.update(self.compiler_name.encode('utf-8'))
        hash.update(self.flags.encode('utf-8'))
        hash.update(self.libs.encode('utf-8'))
        return hash.hexdigest()
        
    def generate_code(self,ir, cg, outputfile=None,cfile=None):
        cg.output_decls(ir)
        self.c_code = cg.output_c(ir)

        hash = self.hashcode(self.c_code)
        
        if outputfile == None:
            outputfile = self.cache.makefilename(hash,".so")
            if os.path.exists(outputfile):
                # skip compilation - we already have this code
                return outputfile
        
        if cfile == None:
            cfile = self.cache.makefilename(hash,".c")
            if 'win' in sys.platform:
                objfile = self.cache.makefilename(hash, ".obj")

        f = open(cfile,"w")
        f.write(self.c_code)
        f.close()
        
        # -march=i686 for 10% speed gain
        cmd = "%s \"%s\" %s %s\"%s\"" % \
              (self.compiler_name, cfile, self.flags, self.output_flag, outputfile)
        if 'win' == sys.platform[:3]:
            cmd += " /Fo\"%s\"" % objfile
        cmd += " %s" % self.libs
        #print "cmd: %s" % cmd

        (status,output) = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise fracttypes.TranslationError(
                "Error reported by C compiler:%s" % output)

        return outputfile

    def get_parsetree(self,filename,formname):
        ff = self.get_file(filename)
        if ff == None : return None
        return ff.get_formula(formname)

    def guess_type_from_filename(self,filename):
        return FormulaTypes.guess_type_from_filename(filename)
    
    def get_formula(self, filename, formname,prefix=""):
        type = self.guess_type_from_filename(filename)

        f = self.get_parsetree(filename,formname)

        if f != None:
            f = type(f,prefix)
        return f

    def get_gradient(self, filename, formname):
        g = gradient.Gradient()
        if formname == None:
            file = open(self.find_file(filename, 3))
            g.load(file)
            file.close()
        else:
            compiled_gradient = self.get_formula(filename,formname)
            g.load_ugr(compiled_gradient)
            
        return g

    def get_random_gradient(self):
        return self.get_random_formula(3) # FIXME

    def get_random_formula(self,type):
        files = self.find_files_of_type(type)
        file = random.choice(files)
        
        if gradient.FileType.guess(file) == gradient.FileType.UGR:
            ff = self.get_file(file)
            formulas = list(ff.formulas.keys())
            formula = random.choice(formulas)
        else:
            formula = None
        return (file,formula)
    
    def clear_cache(self):
        if self.cache:
            self.cache.clear()

    def __del__(self):
        if not self.leave_dirty:
            self.clear_cache()

instance = Compiler()
instance.update_from_prefs(fractconfig.instance)

def usage():
    print("FC : a compiler from Fractint .frm files to C code")
    print("fc.py -o [outfile] -f [formula] infile")
    sys.exit(1)

def generate(fc,formulafile, formula, outputfile, cfile):
    # find the function we want
    ir = fc.get_formula(formulafile,formula)
    if ir == None:
        raise Exception("Can't find formula %s in %s" % \
              (formula, formulafile))

    if ir.errors != []:
        print("Errors during translation")
        for e in ir.errors:
            print(e)
        raise Exception("Errors during translation")

    cg = fc.compile(ir)
    fc.generate_code(ir, cg, outputfile,cfile)

def main(args):
    fc = Compiler()
    fc.leave_dirty = True
    for arg in args:
        ff = fc.load_formula_file(arg)
        for name in ff.get_formula_names():
            print(name)
            form = fc.get_formula(arg,name)
            cg = fc.compile(form)
            
if __name__ == '__main__':
    main(sys.argv[1:])

