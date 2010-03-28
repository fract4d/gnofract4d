#!/usr/bin/env python

# create a color map based on an image.
# vaguely octree-inspired

import sys

sys.path.append("..")
from fract4d import gradient

from PIL import ImageFile

import gtk

class Node:
    def __init__(self,r,g,b,count):
        self.branches = [None] * 8
        self.r = r
        self.g = g
        self.b = b
        self.count = count
        self._isleaf = True
        
    def isleaf(self):
        return self._isleaf

    def matches(self,r,g,b):
        return self.r == r and self.g == g and self.b == b

    def difference_from(self,node):
        dr = self.r - node.r
        dg = self.g - node.g
        db = self.b - node.b
        return (dr*dr + dg*dg + db*db) * self.count 

class T:
    R = 0
    G = 1
    B = 2
    def __init__(self):
        'Load an image from open stream "file"'
        self.root = None

    def addLeafNode(self,r,g,b,count):
        return Node(r,g,b,count)

    def addInternalNode(self,r,g,b):
        n = Node(r,g,b,0)
        n._isleaf = False
        return n
    
    def load(self,file):
        p = ImageFile.Parser()
        while 1:
            s = file.read(1024)
            if not s:
                break
            p.feed(s)

        self.im = p.close()
        
    def getdata(self):
        return self.im.getdata()
    
    def build(self,divby=1):
        i = 0
        for (r,g,b) in self.getdata():
            if i % divby == 0:
                self.insertPixel(r,g,b)
            i += 1

    def dump(self,node,indent=""):
        if not node:
            return ""

        if node.isleaf():
            leafness = "L"
        else:
            leafness = "I"
        val = [ indent + "[(%s,%d,%d,%d,%d)" % \
                (leafness, node.r, node.g, node.b, node.count)]
        val += [self.dump(b,indent+"  ") for b in node.branches]
        val += [ indent + "]"]
        return "\n".join(val)
    
    def get_collapse_info(self,node):
        maxchild = None
        maxcount = 0
        totalchildren = 0
        for child in node.branches:
            if child:
                totalchildren += child.count
                if child.count > maxcount:
                    maxchild = child
                    maxcount = child.count
        return (maxchild, totalchildren)

    def get_collapse_error(self,node):
        "How much the image's error will increase if this node is collapsed"
        # only works on internal nodes which only have leaves as children
        if not node or node.isleaf():
            return 0
        (maxchild, totalchildren) = self.get_collapse_info(node)

        error = 0
        for child in node.branches:
            if child:
                error += child.difference_from(maxchild)
        return error

    def find_collapse_candidates(self,node,candidates):
        if not node or node.isleaf():
            return candidates

        has_children = False
        for b in node.branches:
            if b and not b.isleaf():
                self.find_collapse_candidates(b,candidates)
                has_children = True

        if not has_children:
            cost = self.get_collapse_error(node)
            candidates.append((cost,node))
        return candidates
    
    def collapse(self,node):
        '''Collapse all children into this node, getting the most
        popular child color'''
        if not node or node.isleaf():
            raise ArgumentError("Can't collapse")
        
        (maxchild,totalchildren) = self.get_collapse_info(node)
        node._isleaf = True
        node.branches = [None] * 8
        node.count = totalchildren
        node.r = maxchild.r
        node.g = maxchild.g
        node.b = maxchild.b
        
    def getBranch(self,r,g,b,nr,ng,nb):
        branch = 0
        if r > nr:
            branch += 4
        if g > ng:
            branch += 2
        if b > nb:
            branch += 1
        return branch

    def getInteriorRGB(self,r,g,b,nr,ng,nb,size):
        if r > nr:
            nr += size
        else:
            nr -= size
        if g > ng:
            ng += size
        else:
            ng -= size
        if b > nb:
            nb += size
        else:
            nb -= size
        return (nr,ng,nb)
    
    def insertNode(self,parent,r,g,b,count,nr,ng,nb,size):
        if parent == None:
            parent = self.addLeafNode(r,g,b,count)
        elif parent.matches(r,g,b) and parent.isleaf():
            parent.count += 1
        elif parent.isleaf():
            # replace it with a new interior node, reinsert this leaf and the new one
            currentleaf = parent
            parent = self.addInternalNode(nr,ng,nb)
            currentbranch = self.getBranch(
                currentleaf.r,currentleaf.g,currentleaf.b,nr,ng,nb)
            newbranch = self.getBranch(
                r,g,b,nr,ng,nb)
            if currentbranch == newbranch:
                # need to subdivide further
                (nr,ng,nb) = self.getInteriorRGB(r,g,b,nr,ng,nb,size/2)
                parent.branches[newbranch] = self.addInternalNode(nr,ng,nb)
                parent.branches[newbranch] = self.insertNode(
                    parent.branches[newbranch],r,g,b,1,nr,ng,nb,size/2)
                parent.branches[newbranch] = self.insertNode(
                    parent.branches[newbranch],
                    currentleaf.r, currentleaf.g, currentleaf.b,
                    currentleaf.count,
                    nr,ng,nb,size/2)
            else:
                parent.branches[currentbranch] = currentleaf
                parent.branches[newbranch] = self.addLeafNode(r,g,b,1)
        else:
            # parent is an interior node, recurse to appropriate branch
            newbranch = self.getBranch(r,g,b,nr,ng,nb)
            (nr,ng,nb) = self.getInteriorRGB(r,g,b,nr,ng,nb,size/2)
            parent.branches[newbranch] = self.insertNode(
                parent.branches[newbranch],r,g,b,1,nr,ng,nb,size/2)
        return parent
    
    def insertPixel(self,r,g,b):
        self.root = self.insertNode(self.root,r,g,b,1,127,127,127,128)

    def numColors(self):
        return self._numColors(self.root)
    
    def _numColors(self,node):
        if not node:
            return 0
        if node.isleaf():
            return 1

        colors = 0
        return sum(map(self._numColors,node.branches))

    def _colors(self,node,list):
        if not node:
            return
        if node.isleaf():
            list.append((node.r,node.g,node.b))
        for b in node.branches:
            self._colors(b,list)
        return list
    
    def colors(self):
        return self._colors(self.root,[])
    
    def reduceColors(self,n):
        while self.numColors() > n:
            candidates = self.find_collapse_candidates(self.root,[])
            self.collapse(candidates[0][1])

    
class MapMaker(gtk.Window):
    def __init__(self,type=gtk.WINDOW_TOPLEVEL):
        gtk.Window.__init__(self,type)
        self.image = gtk.Image()
        self.add(self.image)
        self.resize(640,480)
        self.connect('delete-event', self.quit)
        
    def load(self,name):
        self.image.set_from_file(name)

    def quit(self,*args):
        gtk.main_quit()

def main(args):
    w = MapMaker()
    w.load(args[0])
    w.show_all()
    

    gtk.main()

def old_main(args):
    mm = T()
    mm.load(open(args[0]))
    mm.build(1)
    
    mm.reduceColors(int(args[1]))
    
    grad = gradient.Gradient()
    
    colors = []
    i = 0
    for (r,g,b) in mm.colors():
        colors.append((i/10.0,r,g,b,255))
        i += 1

    grad.load_list(colors)
    grad.save(sys.stdout)

if __name__ == '__main__':
    main(sys.argv[1:])
