# A persistent cache of pre-compiled formulas

import os
import stat
import cPickle
import hashlib

class TimeStampedObject:
    "An object and the last time it was updated"
    def __init__(self,obj,time,file=None):
        self.time = time
        self.obj = obj
        self.cache_file = file
        
class T:
    def __init__(self,dir="~/.gnofract4d-cache"):
        self.dir = os.path.expanduser(dir)
        self.files = {}
        
    def init(self):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        self._loadHash()

    def _indexName(self):
        return os.path.join(self.dir,"index_v00.pkl")
    
    def _loadHash(self):
        if os.path.exists(self._indexName()):
            self.files = self.loadPickledFile(self._indexName())
                                               
    def save(self):
        self.createPickledFile(self._indexName(), self.files)
    
    def clear(self):
        for f in os.listdir(self.dir):
            try:
                os.remove(os.path.join(self.dir,f))
            except:
                pass

    def makefilename(self,name,ext):
        return os.path.join(self.dir, "fract4d_%s%s" % (name, ext))

    def hashcode(self,s,*extras):
        hash = hashlib.md5(s)
        for x in extras:
            hash.update(x)

        return hash.hexdigest()

    def makePickleName(self,s,*extras):
        name = self.hashcode(s,*extras) +".pkl"
        fullname = os.path.join(self.dir, name)
        return fullname
    
    def createPickledFile(self,file,contents):
        f = open(file,"wb")
        try:
            cPickle.dump(contents,f,True)
            #print "created %s" % file
        finally:
            f.close()

    def loadPickledFile(self,file):
        f = open(file, "rb")
        try:
            contents = cPickle.load(f)
        finally:
            f.close()
        return contents
    
    def getcontents(self,file,parser):
        mtime = os.stat(file)[stat.ST_MTIME]

        tso = self.files.get(file,None)
        if tso:            
            if tso.time == mtime:
                return tso.obj
        
        val = parser(open(file))

        hashname = self.makePickleName(file)
        #self.createPickledFile(hashname,val)
        self.files[file] = TimeStampedObject(val,mtime,hashname)
        
        return val
    
