#!/usr/bin/env python

# functions to tidy up ir trees in various ways

import copy

import ir
#import fsymbol
import fracttypes

class T:
    def __init__(self,symbols,dump=None):
        self.symbols = symbols
        # used to reverse cjumps
        self.flipTable = {
            '==' : '!=',
            '!=' : '==',
            '>'  : '<=',
            '>=' : '<',
            '<'  : '>=',
            '<=' : '>'
            }
        self.dumpLinear = 0
        self.dumpBlocks = 0
        self.dumpTrace = 0

        if dump != None:
            for k in dump.keys():
                self.__dict__[k]=1
            
    def stms(self, eseq):
        return eseq.children[:-1]

    def canonicalize(self, tree, startLabel, endLabel):
        # top-level driver function
        ltree = self.linearize(tree)
        if self.dumpLinear != 0:
            print "Linearized Tree"
            print ltree.pretty()

        blocks = self.basic_blocks(ltree,startLabel,endLabel)

        if self.dumpBlocks != 0:
            print "Basic Blocks"
            for b in blocks:
                for stm in b:
                    print stm.pretty(),
                print
                
        trace = self.schedule_trace(blocks,endLabel)

        if self.dumpTrace != 0:
            print "Scheduled Trace"
            for stm in trace: print stm.pretty(),
            
        return trace

    def linearize_binop(self, tree, children):
        if isinstance(children[0], ir.ESeq):
            # binop(eseq[stms,e1],e2) => eseq([stms,binop(e1,e2)])
            eseq = children[0]
            stms = self.stms(eseq)
            e1 = eseq.children[-1]
            assert(not isinstance(e1, ir.ESeq))
            e2 = children[1]
            newtree = ir.ESeq(
                stms,
                ir.Binop(tree.op,[e1,e2],tree.node, tree.datatype),
                eseq.node, eseq.datatype)
            newtree = self.linearize(newtree)
        elif isinstance(children[1],ir.ESeq):
            #binop(e1,eseq(stms,e2))
            # => eseq([stms,binop(e1,e2)]) IF commutes(e1,stms)
            # => eseq(move(temp(t),e1), eseq(stms,binop(t, e2)) otherwise
            eseq = children[1]
            e1 = children[0]
            e2 = eseq.children[-1]
            stms = self.stms(eseq)
            if commutes(e1,stms):
                newtree = ir.ESeq(
                    stms,
                    ir.Binop(tree.op,[e1,e2],tree.node, tree.datatype),
                    eseq.node, eseq.datatype)
                newtree = self.linearize(newtree)
            else:
                t = ir.Var(self.symbols.newTemp(e1.datatype), e1.node, e1.datatype)
                move = ir.Move(t ,e1, e1.node,e1.datatype)
                binop = ir.Binop(tree.op, [t,e2], tree.node, tree.datatype)
                eseq = ir.ESeq(stms, binop, eseq.node, eseq.datatype)
                newtree = ir.ESeq([move],eseq, tree.node, tree.datatype)
                newtree = self.linearize(newtree)
        else:
            newtree = ir.Binop(tree.op,children,tree.node,tree.datatype)
        return newtree

    def linearize_cjump(self, tree, children):
        if isinstance(children[0], ir.ESeq):
            # cjump(eseq[stms,e1],e2) => seq([stms,cjump(e1,e2)])
            eseq = children[0]
            stms = self.stms(eseq)
            e1 = eseq.children[-1]
            assert(not isinstance(e1, ir.ESeq))
            e2 = children[1]
            newtree = ir.Seq(
                stms + [ir.CJump(tree.op,e1,e2,
                                 tree.trueDest, tree.falseDest,
                                 tree.node)], 
                eseq.node)
            newtree = self.linearize(newtree)
        elif isinstance(children[1],ir.ESeq):
            #cjump(e1,eseq(stms,e2))
            # => seq([stms,cjump(e1,e2)]) IF commutes(e1,stms)
            # => seq(move(temp(t),e1), seq(stms,cjump(t, e2)) otherwise
            eseq = children[1]
            e1 = children[0]
            e2 = eseq.children[-1]
            stms = self.stms(eseq)
            if commutes(e1,stms):
                newtree = ir.Seq(
                    stms + \
                    [ir.CJump(tree.op,e1,e2,
                              tree.trueDest, tree.falseDest,
                              tree.node)],
                    eseq.node)
                newtree = self.linearize(newtree)
            else:
                t = ir.Var(
                    self.symbols.newTemp(e1.datatype), e1.node, e1.datatype)
                move = ir.Move(t ,e1, e1.node,e1.datatype)
                cjump = ir.CJump(tree.op, t,e2,
                                 tree.trueDest, tree.falseDest, tree.node)
                newtree = ir.Seq([move]+ stms + [cjump], tree.node)
                newtree = self.linearize(newtree)
        else:
            newtree = copy.copy(tree)
            newtree.children = children
        return newtree

    def linearize_seq(self, tree, children):
        # flatten eseq trees, eg:
        #eseq(stms,eseq(stms2,e1),stms3,e2) => eseq(stms,stms2,e1,stms3,e2)
        stms = []
        for stm in children:
            if isinstance(stm,ir.ESeq) or isinstance(stm,ir.Seq):
                stms = stms + stm.children
            else:
                stms.append(stm)
        newtree = copy.copy(tree)
        newtree.children = stms
        return newtree

    def linearize_cast(self, tree, children):
        if isinstance(children[0],ir.ESeq):                
            # cast(eseq(stms,e)) => eseq(stms,cast(e))
            eseq = children[0]
            stms = self.stms(eseq)
            e = eseq.children[-1]
            newtree = ir.ESeq(stms,ir.Cast(e,tree.node, tree.datatype),
                              eseq.node, tree.datatype)
        else:
            newtree = copy.copy(tree)
            newtree.children = children
        return newtree

    def linearize_move(self, tree, children):
        if isinstance(children[1],ir.ESeq):
            # move(x,eseq(stms,e)) => eseq(stms,move(x,e))
            eseq = children[1]
            stms = self.stms(eseq)
            e = eseq.children[-1]
            newtree = ir.ESeq(
                stms,
                ir.Move(children[0],e,tree.node,tree.datatype),
                eseq.node, tree.datatype)
        else:
            newtree = copy.copy(tree)
            newtree.children = children
        return newtree

    def linearize_call(self, tree, children):
        eseq_in_children=False
            
        for child in children:
            if(isinstance(child,ir.ESeq)):
                eseq_in_children = True

        if eseq_in_children:
            # FIXME: assumes arguments & eseq contents commute
            stms = []; i = 0
            for i in range(0,len(children)):
                child = children[i]
                if(isinstance(child,ir.ESeq)):
                    stms = stms + self.stms(child)
                    children[i] = child.children[-1]

            calltree = copy.copy(tree)
            calltree.children = children

            newtree = ir.ESeq(stms,
                              calltree,
                              calltree.node,calltree.datatype)
        else:
            newtree = copy.copy(tree)
            newtree.children = children
        return newtree
    
    def linearize(self,tree):
        ''' remove all ESeq nodes and move Calls to top-level'''
        if tree == None:
            return None
        
        if tree.children == None:
            children = None
        else:
            children = self.linearize_list(tree.children)
            
        if isinstance(tree, ir.Binop):
            newtree = self.linearize_binop(tree, children)            
        elif isinstance(tree, ir.CJump):
            newtree = self.linearize_cjump(tree, children)                
        elif isinstance(tree, ir.ESeq) or isinstance(tree, ir.Seq):
            newtree = self.linearize_seq(tree, children)
        elif isinstance(tree, ir.Cast):
            newtree = self.linearize_cast(tree, children)            
        elif isinstance(tree, ir.Move):
            newtree = self.linearize_move(tree, children)
        elif isinstance(tree, ir.Call) or isinstance(tree,ir.Unop):
            newtree = self.linearize_call(tree, children)                    
        else:
            newtree = copy.copy(tree)
            newtree.children = children
            
        return newtree

    def copy_with_new_children(self,irNode,children):
        newNode = copy.copy(irNode)
        newNode.children = children
        return children
    
    def linearize_list(self,l):
        return map(self.linearize,l)

    def is_block_boundary(self, irNode):
        return self.is_jump(irNode) or isinstance(irNode, ir.Label)

    def is_jump(self, irNode):
        return isinstance(irNode, ir.Jump) or \
               isinstance(irNode, ir.CJump)
        
    def basic_blocks(self, tree, startLabel, endLabel):
        # divides tree into a list of basic blocks
        # we assume it has a Seq() at the top, and no other seqs or eseqs
        assert(isinstance(tree, ir.Seq))
        tree.children.append(ir.Label(endLabel,tree.node))
        
        blocks = []
        label = startLabel
        inBlock = 0
        block = []
        for stm in tree.children:
            if isinstance(stm, ir.Label):
                if block == []:                    
                    block.append(stm)
                else:
                    # close existing block, create a new one
                    if not self.is_jump(block[-1]):
                        # append a jump to current label
                        block.append(ir.Jump(stm.name, stm.node))
                    blocks.append(block)
                    block = [ stm ]
            else:
                if block == []:
                    # manufacture a label if first stm is not a label
                    block.append(ir.Label(label,tree.node))
                    label = self.symbols.newLabel()
                block.append(stm)
                if self.is_jump(stm):
                    blocks.append(block)
                    block = []
        return blocks

    def successors(self, block):
        jump = block[-1]
        if isinstance(jump,ir.Jump):
            return [jump.dest]
        else:
            return [jump.falseDest, jump.trueDest]

    def flip_cjump(self, cjump):
        # reverse the sense of the jump
        new_cjump = copy.copy(cjump)
        new_cjump.op = self.flipTable[cjump.op]
        new_cjump.falseDest = cjump.trueDest
        new_cjump.trueDest = cjump.falseDest
        return new_cjump
    
    def add_block_to_trace(self, trace, in_block):
        # add block to trace. As a side-effect, tidy up last jump to
        # enforce condition that each cjump must be followed by its
        # false label
        block = copy.copy(in_block) # avoid modifying block used by caller
        target = block[0].name
        if trace != []:
            lastjump = trace[-1]
            if isinstance(lastjump,ir.Jump):
                if lastjump.dest == target:
                    # remove jumps to the next stm
                    del trace[-1]
            else:
                assert(isinstance(lastjump, ir.CJump))
                if lastjump.falseDest == target:
                    # no change required
                    pass
                elif lastjump.trueDest == target:
                    trace[-1] = self.flip_cjump(lastjump)
                else:
                    # insert extra label and jump to make it work
                    jump = ir.Jump(lastjump.falseDest, lastjump.node)
                    newFalse = self.symbols.newLabel()
                    label = ir.Label(newFalse, lastjump.node)
                    lastjump.falseDest = newFalse
                    trace += [label,jump]
        trace += block

    def marked(self,hash,name):
        try:
            return hash[name][0]
        except KeyError:
            raise fracttypes.TranslationError(
                "Internal Compiler Error: jump to unknown target %s" % name)
    def mark(self,hash,block):
        hash[block[0].name][0] = 1

    def hash_of_blocks(self,blocks, endLabel):
        hash = {}
        hash[endLabel] = [1,None] # so we don't complain about jumps there
        for b in blocks:
            hash[b[0].name] = [0,b]
        return hash
    
    def schedule_trace(self,blocks, endLabel):
        # converts a list of basic blocks into a linear trace,
        # where every cjump is followed by its false case
        
        # we don't try to make an optimal trace - any one will do
        marks = self.hash_of_blocks(blocks, endLabel)
        queue = copy.copy(blocks)
        trace = []
        while queue != []:
            b = queue[0]
            del queue[0]
            while not self.marked(marks, b[0].name):
                self.mark(marks,b)
                self.add_block_to_trace(trace,b)
                for succ in self.successors(b):
                    if not self.marked(marks,succ):
                        b = marks[succ][1]
                        break
        return trace
                
def commutes(t1,t2):
    '''true iff it doesn\'t matter which of t1 and t2 is done first'''
    # t1, t2 may be lists
    if isinstance(t1,ir.Const) or isinstance(t2,ir.Const):
        # constants always commute
        return 1
    return 0

