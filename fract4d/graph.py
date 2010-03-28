# a graph type used for dataflow analysis.
# Not a very general implementation
# based on the description in Appel's book

from bisect import bisect, insort

class T:
    def __init__(self):
        self._nodes = []
        self._succ = {}
        self._pred = {}
        self.nextNode = 0

    def _getNextNode(self):
        n = self.nextNode
        self.nextNode += 1
        return n
    
    def succ(self,node):
        "return a sorted list of successor nodes"
        return self._succ[node]

    def pred(self,node):
        "return a sorted list of predecessor nodes"
        return self._pred[node]

    def adj(self, node):
        "return a list of adjacent nodes"
        pass
    
    def eq(self, a, b):
        "return true if a and b are the same node"
        pass
    
    def newNode(self):
        "return a new unconnected node"
        n = self._getNextNode()
        # consider using array.array or a bitset for these
        self._succ[n] = []
        self._pred[n] = []
        return n
    
    def newEdge(self, a, b):
        "make a new edge from a to b"
        s = self._succ[a]
        i = bisect(s,b)
        if i == 0 or s[i-1] != b:
            s.insert(i,b)

        s = self._pred[b]
        i = bisect(s,a)
        if i == 0 or s[-1] != a:
            s.insert(i,a)        

    def delEdge(self, a, b):
        "remove the edge between a and b"

    
