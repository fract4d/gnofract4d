#!/usr/bin/env python3


FORMULA_FILE = "gf4d.frm"
FORMULA_NAME = "Mandelbrot"
COLORING_FORMULA_0_FILE = "gf4d.cfrm"
COLORING_FORMULA_0_NAME = "default"
COLORING_FORMULA_1_FILE = "gf4d.cfrm"
COLORING_FORMULA_1_NAME = "zero"

class MandelbrotCompiledFormula:

    def __init__(self, compiler):
        formula = compiler.get_formula(FORMULA_FILE, FORMULA_NAME)
        coloring_formula_0 = compiler.get_formula(COLORING_FORMULA_0_FILE, COLORING_FORMULA_0_NAME, "cf0")
        coloring_formula_1 = compiler.get_formula(COLORING_FORMULA_1_FILE, COLORING_FORMULA_1_NAME, "cf1")

        self.__formula_params = formula.symbols.default_params() + \
            coloring_formula_0.symbols.default_params() + \
            coloring_formula_1.symbols.default_params()

        self.__library_path = compiler.compile_all(formula,
            coloring_formula_0,
            coloring_formula_1,
            [])

    def get_formula_params(self):
        return self.__formula_params

    def get_library_path(self):
        return self.__library_path
