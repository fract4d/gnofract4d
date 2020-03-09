# a grab-bag of simple optimization techniques

# while we rely on the C compiler to do the heavy lifting,
# it's reluctant to do anything to floating point arithmetic
# in case it changes the behavior of the program. We have
# a freer hand because
# a) this is for drawing pretty pictures, not calculating missile
#    trajectories or anything
# b) we always ignore overflow, NaN, etc

from . import instructions, graph

Nothing = 0
Peephole = 1
ConstantPropagation = 2


class FlowGraph:
    "Builds a control flow graph from a sequence of instructions"

    def __init__(self):
        pass

    def build(self, insns):
        self.control = graph.T()
        self.define = {}
        self.use = {}
        for insn in insns:
            if isinstance(insn, instructions.Insn):
                n = self.control.newNode()
                for d in insn.dest():
                    self.define.setdefault(n, []).append(d)
                for s in insn.source():
                    self.use.setdefault(n, []).append(s)


class T:
    "Holds overall optimization logic"

    def __init__(self):
        pass

    def peephole_binop(self, insn):
        left = insn.src[0]
        right = insn.src[1]
        if isinstance(left, instructions.ConstArg):
            if isinstance(right, instructions.ConstArg):
                # both args constant, replace with new const
                return insn.const_eval()
            else:
                const_index = 0
                other_index = 1
        else:
            if isinstance(right, instructions.ConstArg):
                const_index = 1
                other_index = 0
            else:
                # neither are constant, we can't do anything
                return insn

        if insn.op == "*":
            # 1 * n => n
            if insn.src[const_index].is_one():
                return instructions.Move(
                    [insn.src[other_index]],
                    insn.dst)

            # 0 * n -> 0
            if insn.src[const_index].is_zero():
                return instructions.Move(
                    [insn.src[const_index]],
                    insn.dst)

        return insn

    def peephole_insn(self, insn):
        """Return an optimized version of this instruction, if possible,
        or the same instruction if no change is practical."""
        if isinstance(insn, instructions.Binop):
            return self.peephole_binop(insn)
        else:
            return insn

    def peephole(self, insns):
        """Perform some straightforward algebraic simplifications
        which don't require any global knowledge."""

        out_insns = []

        for insn in insns:
            result = self.peephole_insn(insn)
            if result:
                out_insns.append(result)

        return out_insns

    def constant_propagation(self, insns):
        """if we have:

        t = const
        a = t op b

        Then we can replace that with

        a = const op b

        This is done using dataflow analysis."""

    def optimize(self, flags, insns):
        if (flags & Peephole):
            insns = self.peephole(insns)

        return insns
