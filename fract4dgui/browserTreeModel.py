# an object to connect the GTK-independent browser_model class to GTK

import string
import os

from gi.repository import GObject
from gi.repository import Gtk

from fract4d import fc, gradient, browser_model

class T(Gtk.GenericTreeModel):
    column_types = (str, )
    column_names = ['Name']

    def __init__(self, m):
        # m is an instance of browser_model
        self.m = m
        GObject.GObject.__init__(self)

    # treeModel interface

    def on_get_flags(self):
        return 0 # no persistent refs, we are a tree

    def on_get_n_columns(self):
        return len(self.column_types)

    def on_get_column_type(self, n):
        return self.column_types[n]

    def on_get_iter(self, path):
        pass
