#!/usr/bin/env python3

from fract4d import messages


class MessageHandler:
    def __init__(self):
        self.__iterations = []
        self.__progresses = []
        self.__stats = []
        self.__statuses = []
        self.__tiles = []

    def iters_changed(self, iters):
        self.__iterations.append(iters)

    def progress_changed(self, d):
        self.__progresses.append(d)

    def stats_changed(self, s):
        s = messages.Stats.fromList(s)
        self.__stats.append(s)

    def status_changed(self, val):
        self.__statuses.append(val)

    def image_changed(self, x1, y1, x2, y2):
        self.__tiles.append((x1, y1, x2, y2))

    def is_interrupted(self):
        return False

    def get_statuses_history(self):
        return self.__statuses

    def get_last_image_tile_drawn(self):
        return self.__tiles[-1]

    def has_finished(self):
        return self.__statuses[-1] == 0
