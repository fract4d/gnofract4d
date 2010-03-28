
# The idea of this class is to keep just those settings which have
# been set explicitly, and fallback to default values whenever those
# are missing

class T:
    def __init__(self,fallback,parent=None):
        self.__dict__["fallback"] = fallback
        self.set_dirty(False)
        self.__dict__["parent"] = parent

    def set_dirty(self,val):
        self.__dict__["dirty"] = val

    def __setattr__(self,name,val):
        currentval = self.__getattr__(name)
        if currentval == val:
            return
        self.__dict__[name]=val
        self.changed()
        
    def __getattr__(self,name):
        val = self.__dict__.get(name)
        if val == None:
            return self.fallback.__getattr__(name)
        return val

    def changed(self):
        self.set_dirty(True)
        if self.parent:
            self.parent.changed()
