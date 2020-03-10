#!/usr/bin/env python3

# a utility class used by several test scripts

from fract4d import messages


class FractalSite:
    def __init__(self):
        self.status_list = []
        self.progress_list = []
        self.iters_list = []
        self.image_list = []
        self.stats_list = []

    def status_changed(self, val):
        # print "status: %d" % val
        self.status_list.append(val)

    def progress_changed(self, d):
        # print "progress:", d
        self.progress_list.append(d)

    def is_interrupted(self):
        return False

    def iters_changed(self, iters):
        # print "iters changed to %d" % iters
        self.iters_list.append(iters)

    def image_changed(self, x1, y1, x2, y2):
        # print "image: %d %d %d %d" %  (x1, x2, y1, y2)
        self.image_list.append((x1, y1, x2, y2))

    def stats_changed(self, s):
        s = messages.Stats.fromList(s)
        # print s.show()
        self.stats_list.append(s)
