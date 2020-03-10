#!/usr/bin/env python3

# Translate an abstract syntax tree into tree-structured intermediate
# code, performing type checking as a side effect
import sys

from .absyn import *
from . import fsymbol, fractparser, ir, canon, function
from .fracttypes import *

allowed_param_names = [
    "default",
    "caption",
    "min",
    "max",
    "enum",
    "hint"
]


class TBase:
    def __init__(self, prefix, dump=None):
        # print "translating"
        self.symbols = fsymbol.T(prefix)
        self.canonicalizer = canon.T(self.symbols, dump)
        self.errors = []
        self.warnings = []
        self.sections = {}
        self.canon_sections = {}
        self.output_sections = {}
        self.defaults = {}
        self.fakeNode = Empty(-1)  # node used for code not written by user

        self.dumpCanon = 0
        self.dumpDecorated = 0
        self.dumpProbs = 0
        self.dumpTranslation = 0
        self.dumpVars = 0
        self.dumpPreCanon = 0

        if dump is not None:
            for k in list(dump.keys()):
                print(k)
                self.__dict__[k] = 1

    def post_init(self):
        if self.dumpProbs:
            print(self.errors)
            print(self.warnings)

        if self.dumpDecorated:
            print(f.pretty())

        if self.dumpVars:
            for (name, sym) in list(self.symbols.items()):
                if self.symbols.is_user(name):
                    try:
                        print(name, ": ", sym)
                    except Exception as err:
                        print("Error \"%s\" dumping %s" % (err, name))

        if self.dumpTranslation:
            print(self.dumpSections(f, self.canon_sections))

    def is_direct(self):
        return self.symbols.is_direct()

    def merge(self, other, name):
        for (k, s) in list(other.output_sections.items()):
            existing_section = self.output_sections.get(name + k)
            if existing_section:
                existing_section.extend(s)
            else:
                self.output_sections[name + k] = s
        self.symbols.merge(other.symbols)

    def dumpSections(self, f, dict):
        print(f.leaf + "{")
        for (name, tree) in list(dict.items()):
            if isinstance(tree, ir.T):
                print(" " + name + "(")
                print(tree.pretty(2) + " )")
            elif isinstance(tree, list):
                print(" " + name + "(")
                for t in tree:
                    print(t.pretty(2))
                print(" )")
            elif tree is None:
                pass
            else:
                print("Unknown tree %s in section %s" % (tree, name))
        print("}\n")

    def pretty(self):
        if self.errors:
            return "\n".join(self.errors)
        out = []
        for (name, tree) in list(self.sections.items()):
            if isinstance(tree, ir.T):
                out.append(" " + name + "(")
                out.append(tree.pretty(2) + " )")
            elif isinstance(tree, list):
                out.append(" " + name + "(")
                for t in tree:
                    out.append(t.pretty(2))
                out.append(" )")
            elif tree is None:
                pass
            else:
                out.append("Unknown tree %s in section %s" % (tree, name))
        return "\n".join(out)

    def error(self, msg):
        self.errors.append(msg)

    def warning(self, msg):
        self.warnings.append(msg)

    def canonicalize(self):
        for (k, tree) in list(self.sections.items()):
            startLabel = "t__start_" + self.symbols.prefix + k
            endLabel = "t__end_" + self.symbols.prefix + k
            self.canon_sections[k] = self.canonicalizer.canonicalize(
                tree, startLabel, endLabel)

    def dupSectionWarning(self, sect):
        self.warning(
                    ("Formula contains a fractint-style implicit %s section "
                     "and an explicit UltraFractal %s section. "
                     "Using explicit section.") % (sect, sect))

    def sectionOrNone(self, sectname):
        if sectname in self.sections:
            return self.sections[sectname]
        return None

    def update_settings(self, sectname, node):
        l = self.setlist(node)
        self.add_to_section(sectname, l)

    def default(self, node):
        self.update_settings("default", node)

    def add_to_section(self, sectname, stmlist):
        current = self.sections.get(sectname)
        if current is None:
            self.sections[sectname] = stmlist
        else:
            self.sections[sectname].children += stmlist.children

    def global_(self, node):
        self.add_to_section("global", self.stmlist(node))

    def final(self, node):
        self.add_to_section("final", self.stmlist(node))

    def setlist(self, node):
        children = [c for c in node.children if c.type != "empty"]
        settings = [self.setting(c) for c in children]
        seq = ir.Seq([c for c in settings if c is not None], node)
        return seq

    def paramsetting(self, node, var):
        name = node.children[0].leaf

        if name not in allowed_param_names:
            self.warning(
                "%d: Unrecognized parameter setting '%s' ignored" %
                (node.pos, name))
            return

        if name == "visible" or name == "enabled":
            # FIXME ignore visibility for now, parser can't deal with it
            return

        if name == "default":
            e = self.exp(node.children[1])
            var.full_default = e

        if name == "enum":
            self.enum(node.children[1])

        val = self.const_exp(node.children[1])
        setattr(var, name, val)

    def expand_enum(self, node, v, name):
        if hasattr(v, "enum"):
            if isinstance(v.default, ir.Const) \
                    and v.default.datatype == String:
                try:
                    val = self.find_index_nocase(v.enum.value, v.default.value)
                    v.default = ir.Const(val, node, Int)
                except ValueError:
                    msg = "%d: enum value '%s' invalid for param %s" % \
                          (node.pos, v.default.value, name)
                    raise TranslationError(msg)
        return v.default

    def normalize_name(self, name):
        if name[0] == "@":
            return name
        return "@" + name

    def param(self, node):
        # translate a param block

        # find if this is an enum, override type if so
        for child in node.children:
            if child.type == "set" and child.children[0].leaf == "enum":
                node.datatype = fracttypes.Int
                break

        if node.datatype is None:
            # datatype not specified. Must try to infer from default value
            # in the meantime, will assume it's complex
            datatype = fracttypes.Complex
        else:
            datatype = node.datatype

        name = self.normalize_name(node.leaf)

        # create param if not already present
        # print "call get with", name
        v = self.symbols.get(name)
        set_v = False
        # print "name:%s val:%s" % (name, v)
        if not v:
            # print "not found:",name
            v = Var(datatype, None, node.pos)
            set_v = True

        # check only declared once
        if v.declared:
            self.raise_declare_error(v, node)

        v.declared = True

        # process settings
        for child in node.children:
            if child.type == "set":
                self.paramsetting(child, v)
            else:
                self.error(
                    "%d: invalid statement in parameter block" %
                    node.pos)

        if hasattr(v, "default") and v.default is not None:
            if node.datatype is None:
                # oddly, this was bypassing the property when I used v.type
                v._set_type(v.default.datatype)
                v.value = default_value(v.type)

            v.default = self.expand_enum(node, v, name)
            v.default = self.const_convert(v.default, v.type)

        # if we created new var, write it back
        if set_v:
            self.symbols[name] = v

        if node.datatype:
            if(hasattr(v, "full_default")):
                e = self.coerce(v.full_default, node.datatype)
                defexp = e
            else:
                defexp = ir.Const(None, node, node.datatype)

            return ir.Move(
                ir.Var(name, node, node.datatype),
                defexp,
                node, node.datatype)

    def funcsetting(self, node, func):
        name = node.children[0].leaf
        if name == "default":
            fname = node.children[1].leaf
            fol = self.symbols.get(fname)
            if fol is None:
                msg = "%d: unknown default function '%s'" % (node.pos, fname)
                raise TranslationError(msg)

            # is there an overload which matches our args?
            typelist = func.args
            found = False
            for ol in fol:
                if ol.matchesArgs(typelist) and ol.ret == func.ret:
                    found = True
                    break

            if not found:
                # no suitable overload discovered, modify our type
                f = fol[0]
                func.ret = f.ret
                func.args = f.args

            func.set_func(fname)
        elif name == "visible":
            # fixme can't deal with visibility calculations yet
            return
        elif name == "argtype":
            func.args = [node.datatype]
        else:
            val = self.const_exp(node.children[1])
            setattr(func, name, val)

    def func(self, node):
        # translate a func block
        name = self.normalize_name(node.leaf)

        fol = self.symbols.get(name)
        set_f = False
        if not fol:
            # FIXME make more general
            if node.datatype == Hyper:
                argtype = [Hyper]
                fname = "ident"
            elif node.datatype == Color:
                argtype = [Color, Color]
                fname = "mergenormal"
            else:
                argtype = [Complex]
                fname = "ident"

            f = function.Func(argtype, node.datatype, fname)
            set_f = True
        else:
            # check only declared once
            if fol.declared:
                self.raise_declare_error(fol, node)
            f = fol[0]

        # create func
        for child in node.children:
            if child.type == "set":
                self.funcsetting(child, f)
            else:
                self.error("%d: invalid statement in func block" % node.pos)

        if set_f:
            fol = fsymbol.OverloadList([f])
            fol.declared = True
            self.symbols[name] = fol

    def raise_declare_error(self, obj, node):
        type = isinstance(obj, fracttypes.Var) and "parameter" or "function"
        msg = "%d: %s '%s' has already been declared" % (
            node.pos, type, node.leaf)
        raise TranslationError(msg)

    def setting(self, node):
        if node.type == "param":
            return self.param(node)
        elif node.type == "func":
            return self.func(node)
        elif node.type == "heading":
            # print "heading"
            pass
        elif node.type == "set":
            return self.set(node)
        else:
            self.error("%d: invalid statement in default section" % node.pos)

    def make_const(self, node, type):
        parts = []
        for i in range(len(node.children)):
            parts.append(self.const_convert(
                self.const_exp(node.children[i]), fracttypes.Float))
        return ir.Const(parts, node, type)

    def add_enum_value(self, name, val, pos):
        self.symbols.newEnum(name, val, pos)

    def enum(self, node):
        # declaring an enum
        vals = self.string(node)

        strings = [node.leaf]
        strings += [n.leaf for n in node.children]

        i = 0
        for s in strings:
            self.add_enum_value(s, i, node.pos)
            i += 1

    def const_exp(self, node):
        # FIXME should compute full constant expressions
        if node.type == "const":
            return self.const(node)
        elif node.type == "binop" and node.leaf == "complex":
            re = self.const_convert(self.const_exp(node.children[0]),
                                    fracttypes.Float)
            im = self.const_convert(self.const_exp(node.children[1]),
                                    fracttypes.Float)

            return ir.Const([re, im], node, fracttypes.Complex)

        elif node.type == "unop" and node.leaf == "t__neg":
            val = self.const_exp(node.children[0])
            val.value = -val.value
            return val
        elif node.type == "string":
            return self.string(node)
        elif node.type == "funcall" and node.leaf == "hyper":
            return self.make_const(node, fracttypes.Hyper)
        elif node.type == "funcall" and node.leaf == "rgb":
            const = self.make_const(node, fracttypes.Color)
            const.children.append(
                ir.Const(1.0, node, fracttypes.Float))
            return const
        elif node.type == "funcall" and node.leaf == "rgba":
            return self.make_const(node, fracttypes.Color)
        elif node.type == "id":
            if self.symbols.is_builtin(node.leaf):
                # FIXME: not using the real default value of the var
                t = self.symbols[node.leaf].type

                if t == fracttypes.Complex:
                    val = [ir.Const(0.0, node, fracttypes.Float),
                           ir.Const(0.0, node, fracttypes.Float)]

                elif t == fracttypes.Hyper or t == fracttypes.Color:
                    val = [ir.Const(0.0, node, fracttypes.Float),
                           ir.Const(0.0, node, fracttypes.Float),
                           ir.Const(0.0, node, fracttypes.Float),
                           ir.Const(0.0, node, fracttypes.Float)]
                else:
                    val = ir.Const(0.0, node, fracttypes.Float)

                var = ir.Const(val, node, t)

                # return ir.Var(
                #    node.leaf, node, self.symbols[node.leaf].type)
            else:
                self.error(
                    "%d: only built-in variables (starting with '#') can be used in default sections" %
                    node.pos)
        else:
            # print node.pretty()
            self.error("%d: only constants can be used in default sections" %
                       node.pos)

    def const_convert(self, val, type_out):
        if not fracttypes.canBeCast(val.datatype, type_out):
            self.error("%d: Cannot convert %s (%s) to %s" %
                       (val.node.pos, fracttypes.strOfType(val.datatype),
                        val.value, fracttypes.strOfType(type_out)))
            return val

        if val.datatype == type_out:
            return val

        retval = ir.Const(None, val.node, type_out)

        if val.datatype == fracttypes.Complex:
            if type_out == fracttypes.Bool or \
               type_out == fracttypes.Int or \
               type_out == fracttypes.Float:
                retval.value = float(val.value[0])
            else:
                raise Exception("ICE: Weird types in const_convert")
        elif type_out == fracttypes.Complex:
            retval.value = [ir.Const(float(val.value), val.node, fracttypes.Float),
                            ir.Const(0.0, val.node, fracttypes.Float)]
        else:
            retval.value = float(val.value)

        return retval

    def is4D(self):
        return self.symbols.has_user_key("#zwpixel")

    def set(self, node):
        name = node.children[0].leaf
        if name == "method":
            # skip this, we don't use it
            return
        val = node.children[1]
        self.defaults[name] = self.const_exp(val)

    def stmlist(self, node):
        children = [c for c in node.children if c.type != "empty"]
        seq = ir.Seq([self.stm(c) for c in children], node)
        return seq

    def stmlist_with_label(self, node, label):
        seq = self.stmlist(node)
        seq.children.insert(0, label)
        return seq

    def stm(self, node):
        if node.type == "decl":
            r = self.decl(node)
        elif node.type == "assign":
            r = self.assign(node)
        elif node.type == "if":
            r = self.if_(node)
        elif node.type == "while":
            r = self.while_(node)
        elif node.type == "declarray":
            r = self.declarray(node)
        else:
            r = self.exp(node)
        return r

    def isCompare(self, node):
        op = node.leaf
        return node.type == "binop" and \
            (op == ">" or op == ">=" or op == "<" or op == "<=" or
             op == "==" or op == "!=")

    def isShortcut(self, node):
        op = node.leaf
        return node.type == "binop" and (op == '&&' or op == '||')

    def newLabel(self, node):
        return ir.Label(self.symbols.newLabel(), node)

    def newTemp(self, node):
        return ir.Var(self.symbols.newTemp(node.datatype), node, node.datatype)

    def makeCompare(self, node):
        'convert a node into a comparison op'
        if not self.isCompare(node):
            # insert a "fake" comparison to zero
            node = Binop('!=', node, Const(0, node.pos), node.pos)
        return node

    def while_(self, node):
        '''the result of a while loop is:
        seq(
        label(start)
        cjump(test, end, body)
        seq(label(body), bodyCode, jump start)
        label(end)
        )'''
        start = self.newLabel(node)
        body = self.newLabel(node)
        end = self.newLabel(node)

        node.children[0] = self.makeCompare(node.children[0])

        # convert boolean operation
        children = [self.exp(n) for n in node.children[0].children]
        op = self.findOp(node.children[0].leaf, node.children[0].pos, children)
        convertedChildren = self.coerceList(op.args, children)

        # convert main block of code inside while loop
        bodyCode = self.stmlist_with_label(node.children[1], body)
        bodyCode.children.append(ir.Jump(start.name, node))

        # construct actual if operation
        test = ir.CJump(node.children[0].leaf,
                        convertedChildren[0],
                        convertedChildren[1],
                        body.name, end.name, node)

        # overall code
        whilestm = ir.Seq([start, test, bodyCode, end], node)
        return whilestm

    def if_(self, node):
        '''the result of an if is:
        seq(
            cjump(test,falseDest,trueDest)
            seq(label(trueDest), trueCode, jump end)
            seq(label(falseDest), falseCode)
            label(end)
        )'''

        trueDest = self.newLabel(node)
        falseDest = self.newLabel(node)
        doneDest = self.newLabel(node)

        node.children[0] = self.makeCompare(node.children[0])

        # convert boolean operation
        children = [self.exp(n) for n in node.children[0].children]
        op = self.findOp(node.children[0].leaf, node.children[0].pos, children)
        convertedChildren = self.coerceList(op.args, children)

        # convert blocks of code we jump to
        trueBlock = self.stmlist_with_label(node.children[1], trueDest)
        trueBlock.children.append(ir.Jump(doneDest.name, node))

        falseBlock = self.stmlist_with_label(node.children[2], falseDest)

        # construct actual if operation
        test = ir.CJump(node.children[0].leaf,
                        convertedChildren[0],
                        convertedChildren[1],
                        trueDest.name, falseDest.name, node)

        # overall code
        ifstm = ir.Seq([test, trueBlock, falseBlock, doneDest], node)
        return ifstm

    def checkArrayArity(self, name, indexes, pos):
        try:
            arity = self.symbols[name].arity

            if len(indexes) != arity:
                raise TranslationError(
                    "%d: wrong number of indexes for %s" %
                    (pos, name))

        except KeyError as err:
            raise TranslationError(
                "%d: %s not declared as an array" %
                (pos, name))
        except AttributeError as err:
            # not an array
            raise TranslationError("%d: %s is not an array" % (pos, name))

    def arraylookup(self, node):
        name = node.leaf
        indexes = self.indexes(node)
        self.checkArrayArity(name, indexes, node.pos)

        array = self.symbols[name]
        atype = array.type
        elementType = fracttypes.elementTypeOf(atype)

        r = ir.Call(
            "_read_lookup", [
                ir.Var(
                    name, node, atype)] + indexes, node, elementType)
        return r

    def assign(self, node):
        '''assign a new value to a variable, creating it if required'''
        lvalue = node.children[0]
        lhs = expectedType = None
        rhs = self.exp(node.children[1])

        if lvalue.type == "id" or lvalue.type == "arraylookup":
            name = lvalue.leaf
            if name not in self.symbols:
                # implicitly create a new var - a warning?
                self.symbols[name] = \
                    Var(Complex, None, lvalue.pos)

            if isinstance(self.symbols[name], fracttypes.Var):
                expectedType = self.symbols[name].type
            else:
                msg = "%d: %s is not a variable, assignment to it is not allowed" % (
                    node.pos, name)
                raise TranslationError(msg)

            if lvalue.type == "id":
                lhs = ir.Var(name, node, expectedType)
            else:
                # array lookup
                var = ir.Var(name, node, expectedType)

                indexes = self.indexes(node.children[0])

                self.checkArrayArity(name, indexes, node.pos)
                elementType = fracttypes.elementTypeOf(expectedType)
                rhs = self.coerce(rhs, elementType)
                return ir.Call("_write_lookup", [
                               var] + indexes + [rhs], node, elementType)

        elif lvalue.type == "funcall":
            lhs = self.funcall(lvalue)
            expectedType = lhs.datatype
        else:
            self.error("Internal Compiler Error: bad lvalue %s for assign on %d:"
                       % (lvalue.type, node.pos))

        return ir.Move(lhs, self.coerce(rhs, expectedType), node, expectedType)

    def findPseudoOp(self, var, name, pos):
        # return a 'pseudo-functions' associated with an image or
        # gradient param
        if var.type == fracttypes.Image:
            f = function.Func([Image, Complex], Color, "image")
            f.set_implicit_arg(name)
            f.set_override_name("_image")
            return f
        else:
            raise TranslationError(
                "%s: '%s' is not a function and cannot be called" % (pos, name))

    def findOp(self, func, pos, alist):
        ' find the most appropriate overload for this op'
        try:
            overloadList = self.symbols[func]
        except KeyError:
            if func[0] == "@":
                # an attempt to call an undeclared parameter function,
                # create it now. Point to ident by default
                overloadList = self.symbols[func] = fsymbol.OverloadList([
                    function.Func([Complex], Complex, "ident")])
            else:
                raise

        if isinstance(overloadList, fracttypes.Var):
            return self.findPseudoOp(overloadList, func, pos)

        typelist = [ir.datatype for ir in alist]

        for ol in overloadList:
            if ol.matchesArgs(typelist):
                return ol

        raise TranslationError(
            "Invalid argument types %s for %s on line %s" %
            (list(map(fracttypes.strOfType, typelist)), func, pos))

    def decl(self, node):
        if node.children:
            exp = self.stm(node.children[0])
        else:
            # default initializer
            exp = ir.Const(None, node, node.datatype)

        try:
            self.symbols[node.leaf] = Var(node.datatype, None, node.pos)
            return ir.Move(
                ir.Var(node.leaf, node, node.datatype),
                self.coerce(exp, node.datatype),
                node, node.datatype)

        except KeyError as e:
            self.error("Invalid declaration on line %d: %s" % (node.pos, e))

    def indexes(self, node):
        # for each index, coerce it to an int
        indexes = [
            self.coerce(self.exp(x), fracttypes.Int) for x in node.children]

        if len(indexes) > 2:
            self.error("%d: Arrays can only have up to 2 indexes" % node.pos)

        return indexes

    def declarray(self, node):
        indexes = self.indexes(node)

        atype = fracttypes.arrayTypeOf(node.datatype, node)

        try:
            var = Var(atype, None, node.pos)
            var.arity = len(indexes)
            self.symbols[node.leaf] = var

        except KeyError as e:
            self.error("Invalid declaration on line %d: %s" % (node.pos, e))

        arena = ir.Var("t__p_stub->arena", node, fracttypes.VoidArray)

        # initialize array by calling _alloc() and casting to correct type
        size = ir.Const(fracttypes.elementSizeOf(atype), node, fracttypes.Int)

        # a bit of a hack. Complex arrays are just float arrays twice as big
        if atype == fracttypes.ComplexArray:
            indexes[-1] = ir.Binop(
                '*',
                [ir.Const(2, node, fracttypes.Int), indexes[-1]],
                node, fracttypes.Int)

        init_exp = self.coerce(
            ir.Call("_alloc", [arena, size] +
                    indexes, node, fracttypes.VoidArray),
            atype)

        # return a move(var, alloc(thatnum))
        return ir.Move(
            ir.Var(node.leaf, node, atype),
            init_exp,
            node,
            atype)

    def exp(self, node):
        if node.type == "const":
            r = self.const(node)
        elif node.type == "id":
            r = self.id(node)
        elif node.type == "binop":
            r = self.binop(node)
        elif node.type == "unop":
            r = self.unop(node)
        elif node.type == "funcall":
            r = self.funcall(node)
        elif node.type == "assign":
            r = self.assign(node)
        elif node.type == "string":
            r = self.enum_lookup(node)
        elif node.type == "arraylookup":
            r = self.arraylookup(node)
        else:
            self.badNode(node, "exp")

        return r

    def seq_with_label(self, stm, label, node):
        return ir.Seq([label, stm], node)

    def unop(self, node):
        children = [self.exp(n) for n in node.children]
        op = self.findOp(node.leaf, node.pos, children)
        children = self.coerceList(op.args, children)
        return ir.Unop(node.leaf, children, node, op.ret)

    def funcall(self, node):
        children = [self.exp(n) for n in node.children]
        try:
            op = self.findOp(node.leaf, node.pos, children)
        except TranslationError as err:
            # hack to support old Fractint formulas which use exp(1,0)
            # instead of exp((1,0))
            # convert the args into a single complex and see if call works
            try:
                cop = self.findOp('complex', node.pos, children)
                children = self.coerceList(cop.args, children)
                children = [ir.Binop("complex", children, node, cop.ret)]
                op = self.findOp(node.leaf, node.pos, children)
            except Exception as err2:
                raise err

        except KeyError as err:
            raise TranslationError(
                "Unknown function %s on line %d" % (node.leaf, node.pos))

        if op.implicit_args != []:
            type = op.args[0]
            implicit_children = [
                ir.Var(name, None, type) for name in op.implicit_args]
            children = implicit_children + children

        children = self.coerceList(op.args, children)

        # use the leaf's name unless the function specifies otherwise
        name = getattr(op, "override_name", node.leaf)

        return ir.Call(name, children, node, op.ret)

    def shortcut(self, node):
        # convert into an if-expression
        trueDest = self.newLabel(node)
        falseDest = self.newLabel(node)
        doneDest = self.newLabel(node)

        node.children[0] = self.makeCompare(node.children[0])

        children = [self.exp(n) for n in node.children]
        op = self.findOp(node.leaf, node.pos, children)
        children = self.coerceList(op.args, children)

        temp = ir.Var(self.symbols.newTemp(Bool), node, Bool)

        # a && b = eseq(if(a) then t = (bool)b else t = false; t)
        #        = eseq(cjump(==,a,0,td,fd),
        #               lab(td),move(t,b),jmp(end),
        #               lab(fd),move(t,0),jmp(end),
        #               lab(end), t)
        if node.leaf == "&&":
            # code to calc B and store in temp
            trueBlock = ir.Seq(
                [trueDest, ir.Move(temp, children[1], node, children[1].datatype),
                 ir.Jump(doneDest.name, node)], node)

            # code to set temp to false
            falseBlock = ir.Seq(
                [falseDest,
                 ir.Move(temp, ir.Const(0, node, Bool), node, Bool),
                 ir.Jump(doneDest.name, node)], node)

        else:
            # a || b = eseq(if(a) then t = true else t = (bool)b; t)

            # code to set temp to true
            trueBlock = ir.Seq(
                [trueDest,
                 ir.Move(temp, ir.Const(1, node, Bool), node, Bool),
                 ir.Jump(doneDest.name, node)], node)

            # set temp to (bool)b
            falseBlock = ir.Seq(
                [falseDest,
                 ir.Move(temp, children[1], node, children[1].datatype),
                 ir.Jump(doneDest.name, node)], node)

        # construct actual if operation
        test = ir.CJump(children[0].op,
                        children[0].children[0],
                        children[0].children[1],
                        trueDest.name, falseDest.name, node)

        r = ir.ESeq([test, trueBlock, falseBlock, doneDest],
                    temp, node, op.ret)
        return r

    def find_index_nocase(self, list, value):
        i = 0
        v = value.lower()
        for item in list:
            if item.lower() == v:
                return i
            i += 1
        raise ValueError("not found")

    def binop(self, node):
        if self.isShortcut(node):
            return self.shortcut(node)
        else:
            children = [self.exp(n) for n in node.children]
            op = self.findOp(node.leaf, node.pos, children)
            children = self.coerceList(op.args, children)

            return ir.Binop(node.leaf,
                            children,
                            node, op.ret)

    def id(self, node):
        try:
            node.datatype = self.symbols[node.leaf].type
        except KeyError as e:
            self.warning(
                "Uninitialized variable %s referenced on line %d" %
                (node.leaf, node.pos))
            try:
                self.symbols[node.leaf] = Var(
                    fracttypes.Complex, None, node.pos)
            except KeyError as e:
                raise TranslationError("%d: %s" % (node.pos, e.args[0]))

            node.datatype = fracttypes.Complex
        except AttributeError:
            # if this is a function, it's an error unless it has an overload
            # which takes no arguments
            try:
                op = self.findOp(node.leaf, node.pos, [])
                return ir.Call(node.leaf, [], node, op.ret)
            except TranslationError:
                # couldn't find one, treat this as an accidental function use
                pass

            msg = "%d: '%s' is a function name and cannot be used here. Perhaps you meant to call the function instead?" % \
                (node.pos, node.leaf)
            raise TranslationError(msg)

        return ir.Var(node.leaf, node, node.datatype)

    def const(self, node):
        return ir.Const(node.leaf, node, node.datatype)

    def string(self, node):
        if node.children is None or node.children == []:
            return ir.Const(node.leaf, node, node.datatype)
        else:
            strings = [node.leaf]
            strings += [n.leaf for n in node.children]
            return ir.Enum(strings, node, node.datatype)

    def enum_lookup(self, node):
        try:
            val = self.symbols["__enum_" + node.leaf].value
            return ir.Const(val, node, fracttypes.Int)
        except KeyError as err:
            msg = "%d: Unknown enumeration value '%s'" % (node.pos, node.leaf)
            raise TranslationError(msg)

    def coerceList(self, expList, typeList):
        return [self.coerce(exp_ty[0], exp_ty[1])
                for exp_ty in zip(typeList, expList)]

    def coerce(self, exp, expectedType):
        '''insert code to cast exp to expectedType
           or produce an error if conversion is not permitted'''

        # if exp.datatype == None or expectedType == None:
        #    raise TranslationError("Internal Compiler Error: coercing an untyped node")
        if exp.datatype == expectedType:
            return exp

        if fracttypes.canBeCast(exp.datatype, expectedType):
            self.warnCast(exp, expectedType)
            return ir.Cast(exp, exp.node, expectedType)
        else:
            self.badCast(exp, expectedType)

    def init(self, node):
        self.add_to_section("init", self.stmlist(node))

    def loop(self, node):
        self.add_to_section("loop", self.stmlist(node))

    def bailout(self, node):
        # ensure that last stm is a bool
        if self.sections.get("bailout"):
            raise TranslationError(
                "Internal Compiler Error: conflicting bailouts")
        bailList = self.stmlist(node)
        try:
            bail_stm = self.coerce(bailList.children[-1], Bool)
            # manufacture a Move so not discarded by codegen
            bail_stm = ir.Move(
                ir.Var("__bailout", node, Bool),
                bail_stm, node, Bool)
            bailList.children[-1] = bail_stm
            self.sections["bailout"] = bailList
        except IndexError:
            self.warnings.append(
                "No bailout expression found. Calculation will never bail out.")

    def badNode(self, node, rule):
        msg = "Internal Compiler Error: Unexpected node '%s' in %s" % \
            (node.type, rule)
        raise TranslationError(msg)

    def badCast(self, exp, expectedType):
        raise TranslationError(
            ("%s: invalid type %s for %s, expecting %s" %
             (exp.node.pos, strOfType(exp.datatype),
              exp.node.leaf, strOfType(expectedType))))

    def warnCast(self, exp, expectedType):
        msg = "%s: Warning: conversion from %s to %s" % \
            (exp.node.pos, strOfType(exp.datatype), strOfType(expectedType))
        self.warnings.append(msg)


class T(TBase):
    def __init__(self, f, prefix="f", dump=None):
        TBase.__init__(self, "f", dump)

        # magic vars always included in funcs
        self.symbols["__bailout"] = Var(Bool, 0)

        try:
            self.main(f)
            if self.dumpPreCanon:
                self.dumpSections(f, self.sections)
            self.canonicalize()
        except TranslationError as e:
            self.errors.append(e.msg)

        self.post_init()

    def main(self, f):
        if len(f.children) == 0:
            return

        if f.children[0].type == "error":
            self.error(f.children[0].leaf)
            return

        self.canonicalizeSections(f)

        # reference gradient, even if user doesn't do so explicitly
        gradient_var = Var(Gradient, 0, -1)
        self.symbols.ensure("@_gradient", gradient_var)
        self.symbols["@_gradient"].default = ir.Const(0, f, Gradient)

        # lookup sections in order
        s = f.childByName("default")
        if s:
            self.default(s)
        s = f.childByName("global")
        if s:
            self.global_(s)
        s = f.childByName("init")
        if s:
            self.init(s)
        s = f.childByName("loop")
        if s:
            self.loop(s)
        s = f.childByName("bailout")
        if s:
            self.bailout(s)
        s = f.childByName("final")
        if s:
            self.final(s)

        #  ignore switch and builtin for now

    def canonicalizeSections(self, f):
        '''a nameless section (started by ':') is the same as a loop
           section with the last stm as a bailout section - make this
           change'''

        # a "nameless" section is really an init section
        s = f.childByName("nameless")
        if s and s.children != []:
            oldinit = f.childByName("init")
            if oldinit:
                self.dupSectionWarning("init")
            else:
                s.leaf = "init"

        s = f.childByName("")
        if not s or s.children == []:
            return
        elif len(s.children) == 1:
            self.warning("No bailout condition specified")
            bailout = []
            loop = s.children
        else:
            bailout = [s.children[-1]]
            loop = s.children[:-1]

        oldbailout = f.childByName("bailout")
        if oldbailout:
            self.dupSectionWarning("bailout")
        else:
            f.children.append(Stmlist("bailout", bailout, -1))

        oldloop = f.childByName("loop")
        if oldloop:
            self.dupSectionWarning("loop")
        else:
            f.children.append(Stmlist("loop", loop, loop[0].pos))

        f.children.remove(s)

        if self.dumpCanon:
            print(f.pretty())


class Transform(TBase):
    "For transforms (.uxf files)"

    def __init__(self, f, prefix, dump=None):
        TBase.__init__(self, prefix, dump)

        try:
            self.main(f)
            if self.dumpPreCanon:
                self.dumpSections(f, self.sections)
            self.canonicalize()
        except TranslationError as e:
            self.errors.append(e.msg)

        self.post_init()

    def main(self, f):
        if len(f.children) == 0:
            return

        if f.children[0].type == "error":
            self.error(f.children[0].leaf)
            return

        s = f.childByName("default")
        if s:
            self.default(s)
        s = f.childByName("global")
        if s:
            self.global_(s)
        s = f.childByName("transform")
        if s:
            self.transform(s)

    def transform(self, node):
        self.add_to_section("transform", self.stmlist(node))


class ParFile(TBase):
    "For translating Fractint .par files"

    def __init__(self, f, dump=None):
        TBase.__init__(self, "g", dump)

        self.grad = []
        self.main(f)

    def main(self, f):
        if len(f.children) == 0:
            return

        if f.children[0].type == "error":
            self.error(f.children[0].leaf)
            return

        # lookup sections in order
        s = f.childByName("nameless")
        if s:
            self.params(s)

    def params(self, node):
        self.update_settings("gradient", node)

    def set(self, node):
        name = node.children[0].leaf
        val = self.const_exp(node.children[1])
        return ir.Move(
            ir.Var(name, node, val.datatype),
            val, node, val.datatype)


class GradientFunc(TBase):
    "For translating UltraFractal .ugr files"

    def __init__(self, f, prefix, dump=None):
        TBase.__init__(self, prefix, dump)

        self.grad = []
        self.main(f)

    def main(self, f):
        if len(f.children) == 0:
            return

        if f.children[0].type == "error":
            self.error(f.children[0].leaf)
            return

        # lookup sections in order
        s = f.childByName("gradient")
        if s:
            self.gradient(s)
        s = f.childByName("opacity")
        if s:
            self.opacity(s)

    def gradient(self, node):
        self.update_settings("gradient", node)

    def opacity(self, node):
        self.update_settings("opacity", node)

    def set(self, node):
        name = node.children[0].leaf
        val = self.const_exp(node.children[1])
        return ir.Move(
            ir.Var(name, node, val.datatype),
            val, node, val.datatype)


class ColorFunc(TBase):
    "For translating .ucl files"

    def __init__(self, f, name, dump=None):
        TBase.__init__(self, name, dump)

        self.create_standard_vars()

        try:
            self.main(f)
            if self.dumpPreCanon:
                self.dumpSections(f, self.sections)
            self.canonicalize()
        except TranslationError as e:
            self.errors.append(e.msg)

        self.post_init()

    def create_standard_vars(self):
        # magic vars always included in colorfuncs
        offset = Var(Float, 0.0, -1)
        offset.min = ir.Const(0.0, -1, fracttypes.Float)
        offset.max = ir.Const(1.0, -1, fracttypes.Float)
        offset.caption = ir.Const("Color Offset", -1, fracttypes.String)
        self.symbols["@_offset"] = offset

        density = Var(Float, 0.0, -1)
        density.default = ir.Const(1.0, -1, fracttypes.Float)
        density.caption = ir.Const("Color Density", -1, fracttypes.String)
        self.symbols["@_density"] = density

    def index_calc(self, var):
        # @transfer(var) * @density + @offset
        return \
            Binop('+',
                  Binop('*',
                        ID("@_density", -1),
                        Funcall("@_transfer", [var], -1), -1),
                  ID("@_offset", -1), -1)

    def funcall(self, node):
        # special handling for gradient function to insert density,
        # offset and transfer
        if node.leaf == "gradient":
            children = [self.exp(self.index_calc(node.children[0]))]
            op = self.findOp(node.leaf, node.pos, children)
            children = self.coerceList(op.args, children)
            return ir.Call(node.leaf, children, node, op.ret)
        else:
            return TBase.funcall(self, node)

    def final(self, f):
        # append [#index = @transfer(#index) * @density + @offset]
        transfer = Stmlist(
            "",
            [Assign(ID("#index", -1), self.index_calc(ID("#index", -1)), -1)],
            -1)

        TBase.final(self, f)
        TBase.final(self, transfer)

    def main(self, f):
        if f.children[0].type == "error":
            self.error(f.children[0].leaf)
            return

        self.canonicalizeSections(f)
        s = f.childByName("default")
        if s:
            self.default(s)
        s = f.childByName("global")
        if s:
            self.global_(s)
        s = f.childByName("init")
        if s:
            self.init(s)
        s = f.childByName("loop")
        if s:
            self.loop(s)
        s = f.childByName("final")
        if s:
            self.final(s)

    def canonicalizeSections(self, f):
        '''if there are no section headers in a colorfunc,
        just a final block is implied'''
        s = f.childByName("nameless")
        if s:
            oldfinal = f.childByName("final")
            if oldfinal:
                self.dupSectionWarning("final")
            else:
                s.leaf = "final"

        if self.dumpCanon:
            print(f.pretty())


parser = fractparser.parser


def main(args):
    for arg in args:
        s = open(arg, "r").read()  # read in a whole file
        result = parser.parse(s)
        for formula in result.children:
            print(formula.leaf)
            t = T(formula)
            if t.errors != []:
                print("Errors translating %s:" % formula.leaf)
                for e in t.errors:
                    print("\t", e)


# debugging
if __name__ == '__main__':
    main(sys.argv[1:])
