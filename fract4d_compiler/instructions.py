# simple types for "assembler" instructions

from .fracttypes import (Bool, Int, Float, Complex, Hyper, Color, Image,
                         TranslationError, typeObjectList)


class ComplexArg:
    ' a pair of args'

    def __init__(self, re, im):
        self.re = re
        self.im = im

    def format(self):
        [self.re.format(), self.im.format()]

    def __str__(self):
        return "Complex(%s,%s)" % (self.re, self.im)


class HyperArg:
    'four args'

    def __init__(self, re, im1, im2, im3):
        self.parts = [re, im1, im2, im3]

    def format(self):
        return [x.format() for x in self.parts]

    def __str__(self):
        return "Hyper(%s,%s,%s,%s)" % tuple(self.parts)


class ColorArg:
    'four args'

    def __init__(self, re, im1, im2, im3):
        self.parts = [re, im1, im2, im3]

    def format(self):
        return [x.format() for x in self.parts]

    def __str__(self):
        return "Color(%s,%s,%s,%s)" % tuple(self.parts)


class ConstArg:
    def __init__(self, value):
        self.value = value


class ConstFloatArg(ConstArg):
    def __init__(self, value):
        ConstArg.__init__(self, value)

    def cformat(self):
        return "%.17f"

    def format(self):
        return "%.17f" % self.value

    def __str__(self):
        return "Float(%s)" % self.format()

    def is_one(self):
        return self.value == 1.0

    def is_zero(self):
        return self.value == 0.0


class ConstIntArg(ConstArg):
    def __init__(self, value):
        ConstArg.__init__(self, value)

    def cformat(self):
        return "%d"

    def format(self):
        return "%d" % self.value

    def __str__(self):
        return "Int(%s)" % self.format()

    def is_one(self):
        return self.value == 1

    def is_zero(self):
        return self.value == 0


class TempArg:
    def __init__(self, value, type):
        self.value = value
        self.type = typeObjectList[type]

    def format(self):
        return self.value

    def cformat(self):
        return self.type.printf

    def __str__(self):
        return "Temp(%s)" % self.format()


def create_arg_from_val(type, val):
    if type == Int or type == Bool or type == Image:
        return ConstIntArg(val)
    elif type == Float:
        return ConstFloatArg(val)
    elif type == Complex:
        return ComplexArg(ConstFloatArg(val[0]), ConstFloatArg(val[1]))
    elif type == Hyper:
        return HyperArg(
            ConstFloatArg(val[0]), ConstFloatArg(val[1]),
            ConstFloatArg(val[2]), ConstFloatArg(val[3]))
    elif type == Color:
        return ColorArg(
            ConstFloatArg(val[0]), ConstFloatArg(val[1]),
            ConstFloatArg(val[2]), ConstFloatArg(val[3]))
    else:
        raise TranslationError(
            "Internal Compiler Error: Unknown constant type %s" % type)


def create_arg(t):
    return create_arg_from_val(t.datatype, t.value)


class Insn:
    'An instruction to be written to output stream'

    def __init__(self, assem):
        self.assem = assem  # string format of instruction

    def source(self):
        return []

    def dest(self):
        return []

    def format(self):
        try:
            lookup = {}
            i = 0
            if self.source() is not None:
                for src in self.source():
                    sname = "s%d" % i
                    lookup[sname] = src.format()
                    i = i + 1
                i = 0

            if self.dest() is not None:
                for dst in self.dest():
                    dname = "d%d" % i
                    lookup[dname] = dst.format()
                    i = i + 1
            return self.assem % lookup
        except Exception as exn:
            print(exn)
            msg = "%s with %s" % (self, lookup)
            raise TranslationError(
                "Internal Compiler Error: can't format " + msg)


class Literal(Insn):
    'A loophole in the system to sneak through text directly'

    def __init__(self, text):
        self.text = text

    def cformat(self):
        return self.text

    def format(self):
        return self.text

    def dest(self):
        return []

    def source(self):
        return []


class Oper(Insn):
    'An operation'

    def __init__(self, assem, src, dst, jumps=[]):
        Insn.__init__(self, assem)
        self.src = src
        self.dst = dst
        self.jumps = jumps

    def dest(self):
        return self.dst

    def source(self):
        return self.src

    def __str__(self):
        return "OPER(%s,[%s],[%s],%s)" % \
               (self.assem,
                ",".join([x.__str__() for x in self.src]),
                ",".join([x.__str__() for x in self.dst]),
                self.jumps)


class Binop(Oper):
    'A binary infix operation, like addition'

    def __init__(self, op, src, dst, generate_trace=False):
        Insn.__init__(self, "")
        self.op = op
        self.src = src
        self.dst = dst
        self.trace = generate_trace

    def const_eval(self):
        c1 = self.src[0]
        c2 = self.src[1]
        klass = c1.__class__
        if self.op == "*":
            val = klass(c1.value * c2.value)
        elif self.op == "+":
            val = klass(c1.value + c2.value)
        elif self.op == "-":
            val = klass(c1.value - c2.value)
        elif self.op == "/":
            val = klass(c1.value / c2.value)
        else:
            # don't know how to const_eval
            return self

        return Move([val], self.dst)

    def __str__(self):
        return "BINOP(%s,[%s],[%s])" % \
               (self.op,
                ",".join([x.__str__() for x in self.src]),
                ",".join([x.__str__() for x in self.dst]))

    def format(self):
        result = "%s = %s %s %s;" % (
            self.dst[0].format(),
            self.src[0].format(),
            self.op,
            self.src[1].format())
        if self.trace:
            result += "printf(\"%s = %s (%s %s %s)\\n\",%s);" % (
                self.dst[0].format(),
                self.dst[0].cformat(),
                self.src[0].format(),
                self.op,
                self.src[1].format(),
                self.dst[0].format())
        return result


class Label(Insn):
    'A label which can be jumped to'

    def __init__(self, label):
        Insn.__init__(self, "%s: ;\n" % label)
        self.label = label

    def format(self):
        return "%s ;\n" % self

    def __str__(self):
        return "%s:" % self.label


class Move(Insn):
    ' A move instruction'

    def __init__(self, src, dst, generate_trace=False):
        Insn.__init__(self, "%(d0)s = %(s0)s;")
        self.src = src
        self.dst = dst
        self.trace = generate_trace

    def dest(self):
        return [self.dst]

    def source(self):
        return [self.src]

    def format(self):
        result = "%s = %s;" % (self.dst[0].format(), self.src[0].format())
        if self.trace:
            result += "printf(\"%s = %s\\n\",%s);" % (
                self.dst[0].format(),
                self.dst[0].cformat(),
                self.src[0].format())
        return result

    def __str__(self):
        return "MOVE(%s,%s,%s)" % (self.assem, self.src, self.dst)


class Decl(Insn):
    ' a variable declaration'

    def __init__(self, assem):
        Insn.__init__(self, assem)
        self.src = None
        self.dst = None

    def __str__(self):
        return "DECL(%s,%s)" % (self.src, self.dst)
