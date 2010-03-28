# utilities for fetching web pages in a non-blocking way

import os

GET_CMD=os.path.join(os.path.dirname(__file__),"get.py")

class Request(object):
    def __init__(self, cmd, args, input):
        self.cmd = cmd
        self.args = args
        self.input = input

