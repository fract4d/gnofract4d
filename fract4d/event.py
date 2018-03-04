# code to dispatch an event to a number of interested parties

class T:
    def __init__(self):
        self.targets = []

    def __iadd__(self,other):
        self.targets.append(other)
        return self

    def __call__(self,*args,**kwds):
        for t in self.targets:
            t(*args,**kwds)
