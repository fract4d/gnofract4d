import re

from . import fctutils 
from . import gradient
from . import fc

class T(fctutils.T):
    '''Parses the various different kinds of color data we have'''
    def __init__(self,parent=None):
        fctutils.T.__init__(self,parent)
        self.name = "default"
        self.gradient = gradient.Gradient()
        self.solids = [(0,0,0,255)]
        self.direct = False
        self.rgb = [0,0,0]
        self.read_gradient = False
        
    def load(self,f):
        line = f.readline()
        while line != "":
            (name,val) = self.nameval(line)
            if name != None:
                if name == self.endsect: break
                self.parseVal(name,val,f)
            line = f.readline()

    def parse_colorizer(self,val,f):
        # old 1.x files: 0 == rgb, 1 == gradient
        t = int(val)
        if t == 0:
            # convert to a direct coloring algorithm
            self.direct = True
        elif t == 1:
            pass
        else:
            raise ValueError("Unknown colorizer type %d" % t)

    def parse_red(self,val,f):
        self.rgb[0] = float(val)

    def parse_green(self,val,f):
        self.rgb[1] = float(val)

    def parse_blue(self,val,f):
        self.rgb[2] = float(val)

    def extract_color(self,val,pos,alpha=False):
        cols = [int(val[pos:pos+2],16),
                int(val[pos+2:pos+4],16),
                int(val[pos+4:pos+6],16),
                255]
        if alpha:
            cols[3] = int(val[pos+6:pos+8],16)
        return cols
        
    def parse_colordata(self,val,f):
        'long list of hex digits: gf4d < 2.0'
        nc =len(val)//6
        i = 0
        colorlist = []
        while i < nc:
            pos = i*6
            cols = self.extract_color(val,pos)
            if i == 0:
                # first color is inside solid color
                self.solids[0] = tuple(cols)
            else:
                c = tuple([float(i-1)/(nc-2)] + cols)
                colorlist.append(c)
            i+= 1
        self.gradient.load_list(colorlist)
        self.read_gradient = True
        
    def parse_solids(self,val,f):
        line = f.readline()
        self.solids = []
        while not line.startswith("]"):
            cols = self.extract_color(line,0,True)            
            self.solids.append(tuple(cols))
            line = f.readline()
        
    def parse_colorlist(self,val,f):
        '0.7234 = 0xffaa3765: gf4d < 2.7'
        line = f.readline()
        colorlist = []
        while not line.startswith("]"):
            entry = line.split("=")
            
            if len(entry) != 2:
                raise ValueError("invalid color %s in file" % line)

            cols = self.extract_color(entry[1],0,True)            
            index = float(entry[0])
            
            colorlist.append(tuple([index] + cols))
            line = f.readline()
        self.gradient.load_list(colorlist)
        self.read_gradient = True
        
    def parse_gradient(self,val,f):
        'Gimp gradient format: gf4d >= 2.7'
        self.gradient.load(f)
        self.read_gradient = True
        
    def parse_file(self,val,f):
        try:
            mapfile = open(val)
        except IOError:            
            # maybe it's not in the right place
            fname = self.parent.compiler.find_file(
                val, fc.FormulaTypes.GRADIENT)
            mapfile = open(fname)

        self.parse_map_file(mapfile)
        mapfile.close()
        
    def parse_map_file(self,mapfile, maxdiff=0):
        x = mapfile.tell()
        try:
            result = self.gradient.load(mapfile)
            if result:
                self.solids[0] = result
            self.read_gradient = True
        except gradient.HsvError as err:
            if self.parent:
                self.parent.warn("Error reading colormap: %s" % str(err))            
        except Exception as err:
            if self.parent:
                self.parent.warn("Error reading colormap: %s" % str(err))

        
