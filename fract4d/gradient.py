#!/usr/bin/env python

import math
import re
import StringIO
import copy
import random
import types
import struct
import colorsys


#Class definition for Gradients
#These use the format defined by the GIMP

#The file format is:
# GIMP Gradient ; literal identifier
# Name: <utf8-name> ; optional, else get from filename
# 3 ; number of points N
# ; N  lines like this
# 0.000000 0.166667 0.333333 0.000000 0.000000 1.000000 1.000000 0.000000 0.000000 1.000000 1.000000 0 0
# The format is
# start middle end [range 0...1]
# R G B A left endpoint
# R G B A right endpoint
# segment_type coloring_type

# segment-type is 
#   GIMP_GRADIENT_SEGMENT_LINEAR,
#   GIMP_GRADIENT_SEGMENT_CURVED,
#   GIMP_GRADIENT_SEGMENT_SINE,
#   GIMP_GRADIENT_SEGMENT_SPHERE_INCREASING,
#   GIMP_GRADIENT_SEGMENT_SPHERE_DECREASING

# color type is
#   GIMP_GRADIENT_SEGMENT_RGB,      /* normal RGB           */
#   GIMP_GRADIENT_SEGMENT_HSV_CCW,  /* counterclockwise hue */
#   GIMP_GRADIENT_SEGMENT_HSV_CW    /* clockwise hue        */


#gradientfile_re = re.compile(r'\s*(RGB|HSV)\s+(Linear|Sinusoidal|CurvedI|CurvedD)\s+(\d+\.?\d+)\s+(\d+)\s+(\d+)\s+(\d+\.?\d+)\s+(\d+)\s+(\d+)')

rgb_re = re.compile(r'\s*(\d+)\s+(\d+)\s+(\d+)')

class FileType:
    MAP, GGR, CS, UGR = range(4)
    def guess(s):
        s = s.lower()
        if s.endswith(".map"):
            return FileType.MAP
        elif s.endswith(".cs"):
            return FileType.CS
        elif s.endswith(".ugr"):
            return FileType.UGR
        else:
            # assume a GIMP gradient, those sometimes don't have extensions
            return FileType.GGR
        
    guess = staticmethod(guess)
    
class Blend:
    LINEAR, CURVED, SINE, SPHERE_INCREASING, SPHERE_DECREASING = range(5)

class ColorMode:
    RGB, HSV_CCW, HSV_CW = range(3)

class Error(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class HsvError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class Segment:
    EPSILON=1.0E-7
    def __init__(self, left, left_color, right, right_color, mid=None,
                 blend_mode=Blend.LINEAR,
                 color_mode=ColorMode.RGB):
        
        self.cmode = color_mode
        self.bmode = blend_mode
        self.left = left
        self.left_color = left_color
        self.right = right
        self.right_color = right_color
        if mid == None:
            self.center()
        else:
            self.mid = mid

    def __copy__(self):
        return Segment(
            self.left, self.left_color[:],
            self.right, self.right_color[:], self.mid,
            self.blend_mode, self.color_mode)
    
    def __eq__(self,other):
        if other == None: return False
        if not isinstance(other, Segment): return False
        return self.cmode == other.cmode and \
               self.bmode == other.bmode and \
               self.close(self.left, other.left) and \
               self.close(self.right, other.right) and \
               self.close(self.mid, other.mid) and \
               self.close(self.left_color, other.left_color) and \
               self.close(self.right_color, other.right_color)

    def __ne__(self, other):
        return not self.__eq__(other)

    def left_of(self,other):
        # true if other.left == this.right
        return other.left == self.right and \
               other.left_color[0] == self.right_color[0] and \
               other.left_color[1] == self.right_color[1] and \
               other.left_color[2] == self.right_color[2] and \
               other.left_color[3] == self.right_color[3]

    def right_of(self,other):
        # true if other.right == this.left
        return other.right == self.left and \
               other.right_color[0] == self.left_color[0] and \
               other.right_color[1] == self.left_color[1] and \
               other.right_color[2] == self.left_color[2] and \
               other.right_color[3] == self.left_color[3]
    
    def close(self, a, b):
        # True if a is nearly == b
        if isinstance(a, types.ListType):
            for (ax,bx) in zip(a,b):
                if abs(ax-bx) > 1.0E-5:
                    return False
            return True
        else:
            return abs(a-b) < 1.0E-5
    
    def center(self):
        self.mid = (self.left + self.right) / 2.0
        
    def get_linear_factor(self, pos, middle):
        if pos <= middle:
            if middle < Segment.EPSILON:
                return 0.0
            else:
                return 0.5 * pos / middle
        else:
            pos -= middle;
            middle = 1.0 - middle
            if middle < Segment.EPSILON:
                return 1.0
            else:
                return 0.5 + 0.5 * pos / middle

    def get_curved_factor(self, pos, middle):
        if middle < Segment.EPSILON:
            middle = Segment.EPSILON

        try:
            return math.pow(pos, ( math.log(0.5) / math.log(middle) ))
        except ZeroDivisionError:
            # 0^negative number is NaN
            return 0.0
        
    def get_sine_factor(self, pos, middle):
        pos = self.get_linear_factor(pos, middle)
        return (math.sin ((-math.pi / 2.0) + math.pi * pos) + 1.0) / 2.0
    def get_sphere_increasing_factor(self, pos, middle):
        pos = self.get_linear_factor(pos, middle) - 1.0
        return math.sqrt (1.0 - pos * pos)
    def get_sphere_decreasing_factor(self, pos, middle):
        pos = self.get_linear_factor(pos, middle)
        return 1.0 - math.sqrt (1.0 - pos * pos)

    def get_color_at(self, pos):
        'compute the color value for a point in this segment'
        
        lcol = self.left_color
        rcol = self.right_color
        if self.cmode == ColorMode.HSV_CCW or self.cmode == ColorMode.HSV_CW:
            lcol = [v for v in colorsys.rgb_to_hsv(lcol[0],lcol[1],lcol[2])] + [lcol[3]]
            rcol = [v for v in colorsys.rgb_to_hsv(rcol[0],rcol[1],rcol[2])] + [rcol[3]]
        if self.cmode == ColorMode.HSV_CCW:
            if lcol[0] >= rcol[0]: rcol[0] += 1.0
        if self.cmode == ColorMode.HSV_CW:
            if lcol[0] <= rcol[0]: lcol[0] += 1.0
            
            
        len = self.right-self.left
        if len < Segment.EPSILON:
            # avoid division by zero
            mpos = 0.5
            pos = 0.5
        else:
            mpos = (self.mid - self.left) / len
            pos  = (pos- self.left) / len
        
        if self.bmode == Blend.LINEAR:
            factor = self.get_linear_factor(pos, mpos)
        elif self.bmode == Blend.CURVED:
            factor = self.get_curved_factor(pos, mpos)
        elif self.bmode == Blend.SINE:
            factor = self.get_sine_factor(pos, mpos)
        elif self.bmode == Blend.SPHERE_INCREASING:
            factor = self.get_sphere_increasing_factor(pos, mpos)
        elif self.bmode == Blend.SPHERE_DECREASING:
            factor = self.get_sphere_decreasing_factor(pos, mpos)
        
        #Assume RGB mode, for the moment
        RH = lcol[0] + (rcol[0] - lcol[0]) * factor
        GS = lcol[1] + (rcol[1] - lcol[1]) * factor
        BV = lcol[2] + (rcol[2] - lcol[2]) * factor
        A  = lcol[3] + (rcol[3] - lcol[3]) * factor
        
        if self.cmode == ColorMode.RGB:
            return [RH, GS, BV, A]
        if self.cmode == ColorMode.HSV_CCW or self.cmode == ColorMode.HSV_CW:
            if RH > 1: RH -= 1
            return [v for v in colorsys.hsv_to_rgb(RH,GS,BV)] + [A]

    def save(self,f,skip_left=False):
        if skip_left:
            # this segment's left end == previous right, so leave it out
            print >>f, "+%6f %6f" % (self.mid, self.right),
            for x in self.right_color:
                print >>f, "%6f" % x,
        else:
            print >>f, "%6f %6f %6f" % (self.left, self.mid, self.right),
            for x in self.left_color + self.right_color:
                print >>f, "%6f" % x,
        
        print >>f, "%d %d" % (self.bmode, self.cmode)
            
class Gradient:
    def __init__(self):
        self.segments=[
            Segment(0,[0,0,0,1.0], 1.0, [1.0,1.0,1.0,1.0])]

        self.name=None
        self.alternate=0
        self.offset=0
        self.cobject=None

    def __copy__(self):
        c = Gradient()
        c.name = self.name
        c.alternate = self.alternate
        c.offset = self.offset
        c.segments = copy.deepcopy(self.segments)
        return c

    def __eq__(self, other):
        if other == None: return False
        if not isinstance(other, Gradient): return False
        if self.name != other.name: return False
        if self.segments != other.segments: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def serialize(self):
        s = StringIO.StringIO()
        self.save(s,True)
        return s.getvalue()

    def save(self,f,compress=False):
        print >>f, "GIMP Gradient"
        if self.name:
            print >>f, "Name:", self.name
        print >>f, len(self.segments)
        last = None
        for seg in self.segments:
            compress_seg = compress and last != None and seg.right_of(last)
            seg.save(f, compress_seg)
            last = seg

    def load_cs(self, f):
        "Load a ColorSchemer (.cs) palette file"
        # this appears to work but file format was reverse engineered
        # so there may be cases unaccounted for
        (ncolors,) = struct.unpack("2xB5x",f.read(8))
        list = []
        for i in xrange(ncolors):
            (r,g,b,skip) = struct.unpack("<BBBxI", f.read(8))
            entry = (i/float(ncolors), r,g,b,255)
            f.read(skip)
            (r2,g2,b2,skip) = struct.unpack("BBBB", f.read(4))
            f.read(skip+1)
            list.append(entry)
            
        self.load_list(list)
        
    def load_ugr(self, f):
        "Load an ir tree parsed by the translator"
        prev_index = 0.0
        index = 0.0
        segments = []
        prev_color = [0.0,0.0,0.0,0.0]
        for s in f.sections["gradient"].children:
            (name,val) = (s.children[0].name, s.children[1].value)
            if name == "index":
                index = float(val)/400.0
            elif name == "color":
                icolor = val
                color = [
                    float(icolor & 0xFF) / 256.0,
                    float((icolor >> 8) & 0xFF) / 256.0,
                    float((icolor >> 16) & 0xFF) / 256.0,
                    1.0]
                seg = Segment(
                    prev_index, prev_color,
                    index, color,
                    (prev_index + index)/2.0,
                    Blend.LINEAR, ColorMode.RGB)
                segments.append(seg)
                prev_index = index
                prev_color = color
            elif name == "smooth":
                pass #self.smooth = val
            elif name == "title":
                self.name = val

        # append a last chunk from the final value to 1.0
        seg = Segment(
            prev_index, prev_color,
            1.0, prev_color,
            (prev_index + 1.0)/2.0,
            Blend.LINEAR, ColorMode.RGB)
        segments.append(seg)
        
        self.segments = segments

    def load_gimp_gradient(self,f):
        new_segments = []
        name = None

        line = f.readline()
        if line.startswith("Name:"):
            name = line[5:].strip()
            line = f.readline()
        num_vals = int(line)
        for i in xrange(num_vals):
            line = f.readline()
            if line[:1] == "+":
                # a compressed continuation, use last vals
                left = right
                lr,lg,lb,la = rr,rg,rb,ra
                [mid,right,rr,rg,rb,ra,bmode,cmode] = line.split()
            else:
                list_elements = line.split()
                [left, mid, right,
                 lr, lg, lb, la,
                 rr, rg, rb, ra,
                 bmode, cmode] = list_elements[0:13]

            seg = Segment(
                float(left), [float(lr), float(lg), float(lb), float(la)],
                float(right),[float(rr), float(rg), float(rb), float(ra)],
                float(mid),
                int(bmode), int(cmode))
            new_segments.append(seg)
        
        self.segments = new_segments
        self.name = name

    def load(self,f):
        if hasattr(f, "readline"):
            # assume this is a file type
            line = f.readline()
            if line == "GIMP Gradient\n":
                return self.load_gimp_gradient(f)
            elif line[:2] == "\x03\x00":
                # a .cs file, we suspect
                f.seek(0)
                return self.load_cs(f)
            else:
                f.seek(0)
                return self.load_map_file(f)
        else:
            # assume it's a translated UGR file
            return self.load_ugr(f)
            
    def compare_colors(self, c1, c2, maxdiff=0):
        # return true if floating-point colors c1 and c2 are close
        # enough that they would be equal when truncated to 8 bits
        for (a,b) in zip(c1, c2):
            a8 = int(a * 255.0)
            b8 = int(b * 255.0)
            if abs(a8 - b8) > maxdiff:
                return False
        return True

    def load_map_file(self,mapfile,maxdiff=0):
        i = 0
        colorlist = []
        solid = (0,0,0,255)
        for line in mapfile:
            m = rgb_re.match(line)
            if m != None:
                (r,g,b) = (min(255, int(m.group(1))),
                           min(255, int(m.group(2))),
                           min(255, int(m.group(3))))
                
                if i == 0:
                    # first color is inside solid color
                    solid = (r,g,b,255)
                else:
                    colorlist.append(((i-1)/255.0,r,g,b,255))
            i += 1
        self.load_list(colorlist,maxdiff)
        return solid
    
    def load_list(self,l, maxdiff=0):
        # a colorlist is a simplified gradient, of the form
        # (index, r, g, b, a) (colors are 0-255 ints)
        # each index is the left-hand end of the segment
        
        # each colorlist entry is mapped to a segment endpoint

        if len(l) == 0:
            raise Error("No colors found")
        
        new_segments = []
        last_index = 0.0
        last_color = [0.0,0.0,0.0,1.0]
        before_last_color = [-1000.0, -1000.0 , -1000.0, -1000.0] # meaningless color
        before_last_index = -1.0
        
        for (index,r,g,b,a) in l:
            color = [r/255.0, g/255.0, b/255.0, a/255.0]
            if index != last_index:
                test_segment = Segment(
                    before_last_index,
                    before_last_color,
                    index,
                    color)
                if self.compare_colors(
                    test_segment.get_color_at(last_index), last_color, maxdiff):
                    # can compress, update in place
                    new_segments[-1].right_color = color
                    new_segments[-1].right = index
                    new_segments[-1].center()
                else:
                    new_segments.append(
                        Segment(last_index, last_color, index, color))

                    before_last_index = last_index
                    before_last_color = last_color
            last_color = color
            last_index = index
            
        # fix gradient by adding extra flat section if last index not 1.0
        if new_segments[-1].right != 1.0:
            new_segments.append(
                Segment(new_segments[-1].right, last_color, 1.0, last_color))
            
        self.segments = new_segments

    def load_fractint(self,l):
        # l is a list of colors from a Fractint .par file

        # convert format to colorlist
        i = 0
        colors = []
        for (r,g,b) in l:
            colors.append((i/255.0,r*4,g*4,b*4,255))
            i += 1
        # load it
        
        self.load_list(colors,-1.0)

    def set_color(self,seg_id,is_left,r,g,b):
        if seg_id < 0 or seg_id >= len(self.segments):
            return False
        seg = self.segments[seg_id]
        if is_left:
            seg.left_color = [r,g,b, seg.left_color[3]]
        else:
            seg.right_color = [r,g,b, seg.right_color[3]]

        return True

    def complementaries(self, base_color):
        # return some other colors that "go" with this one
        hsv = RGBtoHSV(base_color)

        (h,s,v,a) = hsv
        
        # take 2 colors which are almost triads
        h = hsv[0]
        delta = random.gauss(0.0, 0.8)
        h2 = math.fmod(h + 2.5 + delta, 6.0)
        h3 = math.fmod(h + 3.5 - delta, 6.0)

        # take darker and lighter versions
        v = hsv[2]
        vlight = self.clamp(v * 1.5, 0.0, 1.0)
        vdark = v * 0.5

        colors = [
            [h, s, vdark, a],
            [h, s, v, a],
            [h, s, vlight, a],
            [h2, s, vlight, a],
            [h2, s, v, a],
            [h2, s, vdark, a],
            [h3, s, vdark, a],
            [h3, s, v, a],
            [h3, s, vlight, a]]

        colors = [ HSVtoRGB(x) for x in colors]
        return colors

    def randomize(self, length):
        if random.random() < 0.5:
            self.randomize_complementary(length)
        else:
            self.randomize_spheres((int(random.random() * 4)+3)*2)
            
    def randomize_complementary(self,length):
        base = [random.random(), random.random(), random.random(), 1.0]
        colors = self.complementaries(base)
        self.segments = []
        prev_index = 0.0
        prev_color = colors[0]
        first_color = prev_color
        for i in xrange(9-1):
            index = float(i+1)/length
            color = colors[i]
            self.segments.append(
                Segment(prev_index, prev_color, index, color))
            prev_color = color
            prev_index = index
        
        self.segments.append(
            Segment(prev_index, prev_color, 1.0, first_color)) # make it wrap

    def random_bright_color(self):
        return HSVtoRGB(
            [ random.random() * 360.0,
              random.random(),
              random.random() * 0.6 + 0.4,
              1.0])
    
    def randomize_spheres(self, length):
        self.segments = []
        prev_index = 0.0
        prev_color = self.random_bright_color()
        first_color = prev_color
        for i in xrange(length-1):
            index = float(i+1)/length
            if i % 2 == 1:                
                color = self.random_bright_color()
                blend = Blend.SPHERE_INCREASING
            else:
                color = [0.0, 0.0, 0.0, 1.0]
                blend = Blend.SPHERE_DECREASING
            self.segments.append(
                Segment(prev_index, prev_color, index, color, None, blend))
            prev_color = color
            prev_index = index
        
        self.segments.append(
            Segment(prev_index, prev_color, 1.0, first_color)) # make it wrap

    def get_color_at(self, pos):
        # returns the color at position x (0 <= x <= 1.0) 
        seg = self.get_segment_at(pos)
        return seg.get_color_at(pos)
        
    def get_segment_at(self, pos):
        #Returns the segment in which pos resides.
        if pos < 0.0:
            raise IndexError("Must be between 0 and 1, is %s" % pos)
        for seg in self.segments:
            if pos <= seg.right:
                return seg
        
        # not found - must be > 1.0
        raise IndexError("Must be between 0 and 1, is %s" % pos)

    def get_index_at(self, pos):
        # returns the index of the segment in which pos resides
        if pos < 0.0:
            raise IndexError("Must be between 0 and 1")
        length = len(self.segments)
        for i in xrange(length):
            if pos <= self.segments[i].right:
                return i
        
        # not found - must be > 1.0
        raise IndexError("Must be between 0 and 1")

    def add(self, segindex):
        # split the segment which contains point x in half
        seg = self.segments[segindex]
        
        if segindex+1 < len(self.segments):
            # copy info from next segment to right
            segright = self.segments[segindex+1]
            right_index = segright.left
            right_color = segright.left_color
        else:
            # adding at right-hand end
            right_index = 1.0
            right_color = seg.right_color
        
        s_len = (seg.right-seg.left)
        s_mid = seg.left + s_len*0.5
        newcol= self.get_color_at(s_mid)

        # update existing segment to occupy left half
        seg.right = s_mid
        seg.right_color = newcol
        seg.center()
        
        # add new segment to fill right half
        self.segments.insert(
            segindex+1,
            Segment(s_mid, newcol,
                    right_index, right_color,
                    None, 
                    seg.bmode, seg.cmode))

    def remove(self, segindex, smooth=False):
        # remove the segment which contains point x
        # extend each of our neighbors so they get half our space each
        if len(self.segments) < 2:
            raise Error("Can't remove last segment")
        
        seg = self.segments[segindex]

        if segindex > 0:
            # we have a previous segment
            if segindex+1 < len(self.segments):
                # and we have a next. Move them both to touch in the middle
                self.segments[segindex-1].right=seg.mid                
                self.segments[segindex+1].left=seg.mid
                self.segments[segindex-1].center()
                self.segments[segindex+1].center()
                if smooth:
                    midcolor = seg.get_color_at(seg.mid)
                    self.segments[segindex-1].right_color = copy.copy(midcolor)
                    self.segments[segindex+1].left_color = copy.copy(midcolor)
            else:
                # just a left-hand neighbor, let that take over
                self.segments[segindex-1].right = 1.0
                if smooth:
                    self.segments[segindex-1].right_color = \
                        copy.copy(self.segments[segindex].right_color)
                    
                self.segments[segindex-1].center()
        else:
            # we must have a later segment
            self.segments[segindex+1].left=0.0
            if smooth:
                self.segments[segindex+1].left_color = \
                    copy.copy(self.segments[segindex].left_color)
            self.segments[segindex+1].center()
            
        self.segments.pop(segindex)
        
    def clamp(self,a,min,max):
        if a > max:
            return max
        elif a < min:
            return min
        else:
            return a
        
    def set_left(self,i,pos):
        # set left end of segment i to pos, if possible
        if i < 0 or i >= len(self.segments):
            raise IndexError("No such segment")

        if i == 0:
            # can't move left-hand end of entire gradient
            return 0.0
        else:
            pos = self.clamp(pos,
                             self.segments[i-1].mid + Segment.EPSILON,
                             self.segments[i].mid - Segment.EPSILON)
            self.segments[i-1].right = self.segments[i].left = pos
            return pos

    def set_right(self,i,pos):
        # set left end of segment i to pos, if possible
        if i < 0 or i >= len(self.segments):
            raise IndexError("No such segment")

        max = len(self.segments)-1
        if i == max:
            # can't move right-hand end of entire gradient
            return 1.0
        else:
            pos = self.clamp(pos,
                             self.segments[i].mid + Segment.EPSILON,
                             self.segments[i+1].mid - Segment.EPSILON)
                             
            self.segments[i+1].left = self.segments[i].right = pos
            return pos

    def set_middle(self,i,pos):
        # set middle of segment i to pos, if possible
        if i < 0 or i >= len(self.segments):
            raise IndexError("No such segment")

        pos = self.clamp(pos,
                         self.segments[i].left + Segment.EPSILON,
                         self.segments[i].right - Segment.EPSILON)
                             
        self.segments[i].mid = pos
        return pos
        
    def broken_move(self, handle, move):
        seg, side = self.getSegFromHandle(handle)
        segindex = self.segments.index(seg)
        
        if (segindex > 0 or side == 'right') and (segindex < len(self.segments)-1 or side == 'left'):
            if side == 'left':
                self.segments[segindex-1].right.pos+=move
                if self.segments[segindex-1].right.pos > 1:
                    self.segments[segindex-1].right.pos = 1
                elif self.segments[segindex-1].right.pos < 0:
                    self.segments[segindex-1].right.pos = 0
                        
                seg.left.pos+=move
                if seg.left.pos > 1:
                    seg.left.pos =1
                elif seg.left.pos < 0:
                    seg.left.pos =0
                    
                if seg.left.pos > seg.right.pos:
                    seg.left.pos = seg.right.pos
                    self.segments[segindex-1].right.pos=seg.right.pos
                elif self.segments[segindex-1].right.pos < self.segments[segindex-1].left.pos:
                    self.segments[segindex-1].right.pos=self.segments[segindex-1].left.pos
                    seg.left.pos=self.segments[segindex-1].left.pos
            else:
                self.segments[segindex+1].left.pos+=move
                if self.segments[segindex+1].left.pos > 1:
                    self.segments[segindex+1].left.pos = 1
                elif self.segments[segindex+1].left.pos < 0:
                    self.segments[segindex+1].left.pos = 0
                    
                seg.right.pos+=move
                if seg.right.pos > 1:
                    seg.right.pos =1
                elif seg.right.pos < 0:
                    seg.right.pos =0
                    
                if seg.left.pos > seg.right.pos:
                    seg.right.pos=seg.left.pos
                    self.segments[segindex+1].left.pos=seg.left.pos
                elif self.segments[segindex+1].right.pos < self.segments[segindex+1].left.pos:
                    self.segments[segindex+1].left.pos=self.segments[segindex+1].right.pos
                    seg.right.pos=self.segments[segindex+1].right.pos

# These two are adapted from the algorithms at
# http://www.cs.rit.edu/~ncs/color/t_convert.html
def RGBtoHSV(rgb):
    hsv = [0,0,0,rgb[3]]
    trgb = rgb[0:3]
    trgb.sort()
    
    min = trgb[0]
    max = trgb[2]

    delta = float(max - min)
    hsv[2] = max

    if delta == 0:
        # r = g = b = 0        # s = 0, v is undefined
        hsv[1] = 0
        hsv[0] = -1
    else:
        hsv[1]=delta / max
        
        if rgb[0] == max:
            hsv[0] = (rgb[1] - rgb[2]) / delta        # between yellow & magenta
        elif rgb[1] == max:
            hsv[0] = 2 + (rgb[2] - rgb[0] ) / delta    # between cyan & yellow
        else:
            hsv[0] = 4 + (rgb[0] - rgb[1] ) / delta    # between magenta & cyan

    hsv[0] *= 60                # degrees
    if hsv[0] < 0:
        hsv[0] += 360
        
    return hsv

def HSVtoRGB(hsv):
    rgb=[0,0,0,hsv[3]] # pass through alpha channel
    
    hsv[0]/=60
    
    if hsv[1] == 0:
        return [hsv[2],hsv[2],hsv[2]]
    
    i = int(hsv[0])
    f = hsv[0] - i                            #Decimal bit of hue
    p = hsv[2] * (1 - hsv[1])
    q = hsv[2] * (1 - hsv[1] * f)
    t = hsv[2] * (1 - hsv[1] * (1 - f))
    
    if i == 0:
        rgb[0] = hsv[2]
        rgb[1] = t
        rgb[2] = p
    elif i == 1:
        rgb[0] = q
        rgb[1] = hsv[2]
        rgb[2] = p
    elif i == 2:
        rgb[0] = p
        rgb[1] = hsv[2]
        rgb[2] = t
    elif i == 3:
        rgb[0] = p
        rgb[1] = q
        rgb[2] = hsv[2]
    elif i == 4:
        rgb[0] = t
        rgb[1] = p
        rgb[2] = hsv[2]
    elif i == 5:
        rgb[0] = hsv[2]
        rgb[1] = p
        rgb[2] = q
    
    return rgb        
