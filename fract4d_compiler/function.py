import copy

from . import stdlib
from .fracttypes import canBeCast, suffixOfType


class Func:
    def __init__(self, args, ret, fname, pos=-1):
        self.args = args
        self.implicit_args = []
        self.ret = ret
        self.pos = pos
        self.set_func(fname)

    def __copy__(self):
        c = Func(self.args, self.ret, self.fname, self.pos)
        c.implicit_args = copy.copy(self.implicit_args)
        if hasattr(self, "override_name"):
            c.set_override_name(self.override_name)
        if hasattr(self, "caption"):
            c.caption = self.caption
        return c

    def first(self):
        return self

    def set_implicit_arg(self, arg):
        self.implicit_args.append(arg)

    def set_override_name(self, name):
        self.override_name = name

    def set_func(self, fname):
        # compute the name of the stdlib function to call
        # this is similar in purpose to C++ name mangling
        if fname is None:
            self.genFunc = None
        else:
            typed_fname = fname + "_"
            for arg in self.args:
                typed_fname = typed_fname + suffixOfType[arg]
            typed_fname = typed_fname + "_" + suffixOfType[self.ret]

            self.genFunc = stdlib.__dict__.get(typed_fname, typed_fname)

        self.cname = fname
        self.fname = fname

    def matchesArgs(self, potentialArgs):
        if len(potentialArgs) != len(self.args):
            return False
        i = 0
        for arg in self.args:
            if not canBeCast(potentialArgs[i], arg):
                return False
            i = i + 1
        return True
