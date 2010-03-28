import os

import fc, event, gradient

FRACTAL = 0
OUTER = 1
INNER = 2
TRANSFORM = 3
GRADIENT = 4

def stricmp(a,b):
    return cmp(a.lower(),b.lower())

class TypeInfo:
    def __init__(self, parent, compiler, t, exclude=None):
        self.parent = parent
        self.formula_type = t
        self.exclude= exclude
        self.fname = None
        self.formula = None
        self.formulas = []
        self.compiler = compiler
        self.update_files()

    def update_files(self):
        self.files = self.compiler.find_files_of_type(self.formula_type)
        self.files.sort(stricmp)
        
    def set_file(self,fname):
        if self.fname == fname:
            return
        if None == fname:
            self.formulas = []
        else:
            ff = self.compiler.get_file(fname)
            self.formulas = ff.get_formula_names(self.exclude)
            self.formulas.sort(stricmp)
        self.fname = fname
        self.set_formula(None)
        self.file_changed()
        
    def set_formula(self,formula):
        if self.formula == formula:
            return
        self.formula = formula
        self.formula_changed()
        
    def file_changed(self):
        self.parent.file_changed()

    def formula_changed(self):
        self.parent.formula_changed()

    def _get_apply_status(self):
        "Indicate whether current settings can be applied"
        if None == self.fname:
            return False
        if None == self.formula:
            if self.formula_type == fc.FormulaTypes.GRADIENT:
                if gradient.FileType.guess(self.fname) != gradient.FileType.UGR:
                    # no formula is only acceptable if this is a map, cs or GGR file
                    return True
            return False
        
        # some other type of file
        ir = self.compiler.get_formula(self.fname, self.formula)
        if ir.errors != []:
            # errors compiling
            return False

        # everything OK
        return True

    can_apply = property(_get_apply_status)
    
    def apply(self,f,t):
        f.freeze()
        try:
            if t == FRACTAL:
                f.set_formula(self.fname,self.formula)
                f.reset()
            elif t == INNER:
                f.set_inner(self.fname,self.formula)
            elif t == OUTER:
                f.set_outer(self.fname,self.formula)
            elif t == TRANSFORM:
                f.append_transform(self.fname,self.formula)
            elif t == GRADIENT:
                f.set_gradient_from_file(self.fname, self.formula)
        finally:
            if f.thaw():
                f.changed()
        

class T:
    def __init__(self,compiler):
        self.compiler = compiler
        self.typeinfo = [
            TypeInfo(self, compiler, fc.FormulaTypes.FRACTAL),
            TypeInfo(self, compiler, fc.FormulaTypes.COLORFUNC, "INSIDE"),
            TypeInfo(self, compiler, fc.FormulaTypes.COLORFUNC, "OUTSIDE"),
            TypeInfo(self, compiler, fc.FormulaTypes.TRANSFORM),
            TypeInfo(self, compiler, fc.FormulaTypes.GRADIENT)
            ]
        self.current_type = -1
        self.type_changed = event.T()
        self.file_changed = event.T()
        self.formula_changed = event.T()
        self.set_type(FRACTAL)
        
    def formula_type_to_browser_type(self,t):
        if t == fc.FormulaTypes.FRACTAL:
            return FRACTAL
        if t == fc.FormulaTypes.COLORFUNC:
            return OUTER
        if t == fc.FormulaTypes.TRANSFORM:
            return TRANSFORM
        if t == fc.FormulaTypes.GRADIENT:
            return GRADIENT
        raise ValueError("unknown formula type %s" % t)

    def guess_type(self,file):
        t = fc.FormulaTypes.guess_formula_type_from_filename(file)
        return self.formula_type_to_browser_type(t)

    def set_type(self,t):
        if self.current_type == t:
            return
        self.current_type = t
        self.current = self.typeinfo[t]
        self.type_changed()

    def set_file(self,fname):
        if fname:
            fname = os.path.basename(fname)
        self.current.set_file(fname)

    def set_formula(self,formula):
        self.current.set_formula(formula)
        
    def get_type_info(self,t):
        return self.typeinfo[t]

    def update(self,fname,formula):
        self.current.update_files()
        self.set_file(fname)
        self.set_formula(formula)

    def apply(self,f):
        self.current.apply(f,self.current_type)

    def get_contents(self):
        fname = self.current.fname
        if not fname:
            return ""

        if self.current_type == GRADIENT:
            # don't bother displaying contents of gradients
            return ""

        r = self.compiler.get_text(fname)
        return r
        
instance = T(fc.instance)
