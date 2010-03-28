import fract4dc
import struct

def parse(type,buffer):
    if type == fract4dc.MESSAGE_TYPE_ITERS:
        return Iters(buffer)
    if type == fract4dc.MESSAGE_TYPE_IMAGE:
        return Image(buffer)
    if type == fract4dc.MESSAGE_TYPE_PROGRESS:
        return Progress(buffer)
    if type == fract4dc.MESSAGE_TYPE_STATUS:
        return Status(buffer)
    if type == fract4dc.MESSAGE_TYPE_TOLERANCE:
        return Tolerance(buffer)
    if type == fract4dc.MESSAGE_TYPE_STATS:
        return Stats(buffer)

class T:
    pass

class Iters(T):
    def __init__(self,buffer):
        (self.iterations,) = struct.unpack("i",buffer)

    def get_name(self):
        return "Iters"
    name = property(get_name)

    def show(self):
        return "Iters: %d" % self.iterations
        
class Image(T):
    def __init__(self,buffer):
        (self.x, self.y, self.w, self.h) = struct.unpack("4i",buffer)

    def get_name(self):
        return "Image"
    name = property(get_name)

    def show(self):
        return "Image: (%d,%d) (%d,%d)" % (self.x, self.y, self.w, self.h)
 
class Progress(T):
    def __init__(self,buffer):
        (p,) = struct.unpack("i",buffer)
        self.progress = float(p)

    def show(self):
        return "Progress: %s" % self.progress

    def get_name(self):
        return "Progress"
    name = property(get_name)


class Status(T):
    def __init__(self,buffer):
        (self.status,) = struct.unpack("i",buffer)

    def show(self):
        return "Status: %d" % self.status

    def get_name(self):
        return "Status"
    name = property(get_name)

class Tolerance(T):
    def __init__(self,buffer):
        (self.tolerance,) = struct.unpack("d",buffer)

    def get_name(self):
        return "Tolerance"
    name = property(get_name)

class Stats(T):
    def fromList(list):        
        instance = Stats()
        instance.iterations = list[0]
        instance.pixels = list[1]
        instance.pixels_calculated = list[2]
        instance.pixels_skipped = list[3]
        instance.pixels_skipped_wrong = list[4]
        instance.pixels_skipped_right = list[5]
        instance.pixels_inside = list[6]
        instance.pixels_outside = list[7]
        instance.pixels_periodic = list[8]
        return instance
    fromList = staticmethod(fromList)

    def __init__(self,buffer=None):
        if buffer:
            (self.iterations, 
             self.pixels, 
             self.pixels_calculated, 
             self.pixels_skipped,
             self.pixels_skipped_wrong,
             self.pixels_skipped_right,
             self.pixels_inside,
             self.pixels_outside,
             self.pixels_periodic,
             dummy,
             dummy,
             dummy,
             dummy) = struct.unpack("13L",buffer)        

    def _get_name(self):
        return "Stats"
    name = property(_get_name)

    def _get_percent_skipped(self):
        if self.pixels == 0:
            return 0.0
        return 100.0 * float(self.pixels_skipped)/self.pixels
    percent_skipped = property(_get_percent_skipped)

    def _get_percent_calculated(self):
        return 100.0 - self.percent_skipped
    percent_calculated = property(_get_percent_calculated)

    def _get_percent_skipped_wrong(self):
        if self.pixels_skipped == 0:
            return 0.0
        return 100.0 * float(self.pixels_skipped_wrong)/self.pixels_skipped
    percent_skipped_wrong = property(_get_percent_skipped_wrong)

    def _get_percent_inside(self):
        if self.pixels_calculated == 0:
            return 0.0
        return 100.0 * float(self.pixels_inside)/self.pixels_calculated
    percent_inside = property(_get_percent_inside)

    def _get_percent_periodic(self):
        if self.pixels_inside == 0:
            return 0.0
        return 100.0 * float(self.pixels_periodic)/self.pixels_inside
    percent_periodic = property(_get_percent_periodic)

    def _get_percent_outside(self):
        return 100.0 - self.percent_inside
    percent_outside = property(_get_percent_outside)

    def show(self):
        return (
            "Calculation Statistics:\n" +
            "Total pixels:%d\n" % self.pixels +
            "Calculated pixels:%d(%2g%%)\n" % \
                (self.pixels_calculated, self.percent_calculated) +
            "  Inside pixels:%d(%2g%%)\n" % (self.pixels_inside, self.percent_inside) +
            "    Perodic pixels:%d(%2g%%)\n" % (self.pixels_periodic, self.percent_periodic) +
            "  Outside pixels:%d(%2g%%)\n" % (self.pixels_outside, self.percent_outside) +
            "Guessed pixels:%d(%2g%%)\n" % (self.pixels_skipped, self.percent_skipped)
            )

            #/out/per:\t%d\t%d\t%d\n" % \
            #    (self.pixels_inside, self.pixels_outside, self.pixels_periodic) +
            #"calc/skip:\t%d\t%d(%2g%%)\n" % \
            #    (self.pixels_calculated, self.pixels_skipped, self.percent_skipped) +
            #"skip right/wrong:\t%d\t%d(%2g%%)\n" % \
            #    (self.pixels_skipped_right, self.pixels_skipped_wrong, self.percent_skipped_wrong)
            #)
