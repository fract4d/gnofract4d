#!/usr/bin/env python3

from fract4d import messages


class MockMessageHandler:

    def __init__(self):
        self.__iterations = []
        self.__progresses = []
        self.__stats = []
        self.__statuses = []
        self.__tiles = []

    def iters_changed(self, iteration_number):
        self.__iterations.append(iteration_number)

    def progress_changed(self, progress):
        self.__progresses.append(progress)

    def stats_changed(self, stat):
        stat_from_messages = messages.Stats.fromList(stat)
        self.__stats.append(stat_from_messages)

    def status_changed(self, status):
        self.__statuses.append(status)

    def image_changed(self, tile_x1, tile_y1, tile_x2, tile_y2):
        self.__tiles.append((tile_x1, tile_y1, tile_x2, tile_y2))

    @staticmethod
    def is_interrupted():
        return False

    def get_statuses_history(self):
        return self.__statuses

    def get_last_image_tile_drawn(self):
        return self.__tiles[-1]

    def has_finished(self):
        return self.__statuses[-1] == 0
