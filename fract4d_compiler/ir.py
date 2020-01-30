# Intermediate representation. The Translate module converts an Absyn tree
# into an IR tree.

from . import absyn, fracttypes

def d(depth,s=""):
    return " " * depth + s

class T:
    def __init__(self, node, datatype, children=None):
        self.datatype = datatype
        self.node = node  # the absyn node we were constructed from
        self.children = []
        
    def pretty_children(self,depth):
        r = []
        for child in self.children:
            if child is None:
                r.append(d(depth+1,"<<None>>"))
            else:
                try:
                    r.append(child.pretty(depth+1))
                except Exception as exn:
                    print("self",self)
                    print(len(child))
                    for c in child:
                        print(c)
                    print("<Error printing child '%s'>" % child)
                    raise
                
        return "".join(r)

    def __iter__(self):
        return absyn.NodeIter(self)

    def pretty(self,depth=0):
        child_str = self.pretty_children(depth)
        if child_str != "":
            end = d(depth,")\n")
        else:
            end = ")\n"
            
        return d(depth,self.__str__()) + child_str + end

    def __str__(self):
        return self.__class__.__name__ + "(\n"
    
# exp and subtypes
# an exp computes a value

class Exp(T):
    def __init__(self, node, datatype):
        assert(datatype in fracttypes.typeList)
        T.__init__(self, node, datatype)

class Const(Exp):
    def __init__(self, value, node, datatype):
        Exp.__init__(self, node, datatype)
        if value is None:
            self.value = fracttypes.default_value(datatype)
        else:
            self.value = value
    def __str__(self):
        return "Const(%s" % self.value

class Enum(Exp):
    def __init__(self, value, node, datatype):
        Exp.__init__(self, node, datatype)
        self.value = value
    def __str__(self):
        return "Enum(%s" % self.value
    
class Temp(Exp):
    def __init__(self, temp, node, datatype):
        Exp.__init__(self, node, datatype)
        self.temp = temp
    def __str__(self):
        return "Temp(%s" % self.temp

class Binop(Exp):
    def __init__(self, op, children, node, datatype):
        Exp.__init__(self, node, datatype)
        (self.op, self.children) = (op,children)
    def __str__(self):
        return "Binop(" + self.op + "\n"

class Unop(Exp):
    def __init__(self, op, children, node, datatype):
        Exp.__init__(self, node, datatype)
        (self.op, self.children) = (op,children)
    def __str__(self):
        return "Unop(" + self.op + "\n"
    
class Var(Exp):
    def __init__(self, name, node, datatype):
        Exp.__init__(self, node, datatype)
        self.name = name
    def __str__(self):
        return "Var<%s>(%s" % (fracttypes.strOfType(self.datatype), self.name)

class Cast(Exp):
    def __init__(self, exp, node, datatype):
        Exp.__init__(self,node, datatype)
        self.children = [exp]
    def __str__(self):
        return "Cast<%s,%s>(\n" % \
                   (fracttypes.strOfType(self.children[0].datatype),
                    fracttypes.strOfType(self.datatype))
    
class Call(Exp):
    def __init__(self, func, args, node, datatype):
        Exp.__init__(self, node, datatype)
        self.op = func
        self.children = args
    def __str__(self):
        return "Call(" + self.op + "\n"
        
class ESeq(Exp):
    def __init__(self, stms, exp, node, datatype):
        Exp.__init__(self, node, datatype)
        self.children = stms + [exp]

class Move(Exp):
    def __init__(self, dest, exp, node, datatype):
        Exp.__init__(self, node, datatype)
        self.children = [dest,exp]

# stm and subtypes
# side effects + flow control

class Stm(T):
    def __init__(self, node, datatype):
        T.__init__(self, node, datatype)
    
class Jump(Stm):
    def __init__(self,dest, node):
        Stm.__init__(self, node, None)
        self.dest = dest
    def pretty(self, depth=0):
        return d(depth) + "Jump(" + self.dest + ")\n"
    
class CJump(Stm):
    def __init__(self,op,exp1,exp2,trueDest, falseDest, node):
        Stm.__init__(self, node, None)
        self.op = op
        self.children = [exp1, exp2]
        self.trueDest = trueDest
        self.falseDest = falseDest
        
    def pretty(self, depth=0):
        return d(depth) + "CJump(op='" + self.op + "'\n" + \
               self.pretty_children(depth) + \
               d(depth+1,"true=" + self.trueDest) + "," + \
               "false=" + self.falseDest + ")\n"
        
class Seq(Stm):
    def __init__(self,stms, node):
        Stm.__init__(self, node, None)
        self.children = stms

class Label(Stm):
    def __init__(self,name, node):
        Stm.__init__(self, node, None)
        self.name = name
    def pretty(self, depth=0):
        return d(depth) + "Label(" + self.name + ")\n"
