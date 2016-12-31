#!/usr/bin/python

import os, sys, copy, math

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

import fracttypes, fractal, fractconfig

#interpolation type constants
INT_LINEAR=    0
INT_LOG=    1
INT_INVLOG=    2
INT_COS=    3

def getAttrOrDefault(attrs, name, default):
    x = attrs.get(name)
    if x == None:
        x = default
    return x
    
def getAttrOrElse(attrs, name):
    x = attrs.get(name)
    if x == None:
        raise ValueError(
            "Invalid file: Cannot find required attribute '%s'" % name)
    return x

class KeyFrame:
    def __init__(self,filename,duration,stop,int_type,flags=(0,0,0,0,0,0)):
        self.filename = filename.encode()
        self.duration = duration
        self.stop = stop
        self.int_type = int_type
        self.flags = flags

    def save(self,fh):
        fh.write(
            '\t\t<keyframe filename="%s" duration="%d" stop="%d" inttype="%d" ' % (self.filename, self.duration, self.stop, self.int_type))
        fh.write(
            'xy="%d" xz="%d" xw="%d" yz="%d" yw="%d" zw="%d"' % self.flags)
        fh.write('/>\n')

    def load_from_xml(attrs):
        kf = KeyFrame(
            getAttrOrElse(attrs,"filename"),
            int(getAttrOrElse(attrs,"duration")),
            int(getAttrOrElse(attrs,"stop")),
            int(getAttrOrElse(attrs,"inttype")),
            (int(getAttrOrDefault(attrs,"xy",0)),
             int(getAttrOrDefault(attrs,"xz",0)),
             int(getAttrOrDefault(attrs,"xw",0)),
             int(getAttrOrDefault(attrs,"yz",0)),
             int(getAttrOrDefault(attrs,"yw",0)),
             int(getAttrOrDefault(attrs,"zw",0))))
        return kf
    
    load_from_xml=staticmethod(load_from_xml)
        
class T:
    def __init__(self, compiler):
        self.compiler = compiler
        self.reset()

    def reset(self):
        self.avi_file=""
        self.width=640
        self.height=480
        self.framerate=25
        self.redblue=True
        #keyframes is a list of KeyFrame objects
        self.keyframes=[]

    def get_fct_enabled(self):
        return fractconfig.instance.getboolean("director","fct_enabled")
    
    def set_fct_enabled(self,fct_enabled):
        if fct_enabled:
            fractconfig.instance.set("director","fct_enabled","1")
        else:
            fractconfig.instance.set("director","fct_enabled","0")
    
    def get_fct_dir(self):
        return fractconfig.instance.get("director","fct_dir")
    
    def set_fct_dir(self,dir):
        fractconfig.instance.set("director","fct_dir",dir)
    
    def get_png_dir(self):
        return fractconfig.instance.get("director","png_dir")
    
    def set_png_dir(self,dir):
        fractconfig.instance.set("director","png_dir",dir)

    def get_avi_file(self):
        return self.avi_file

    def set_avi_file(self,file):
        if file!=None:
            self.avi_file=file
        else:
            self.avi_file=""

    def get_width(self):
        return self.width

    def set_width(self,width):
        if width!=None:
            self.width=int(width)
        else:
            self.width=640

    def get_height(self):
        return self.height

    def set_height(self,height):
        if height!=None:
            self.height=int(height)
        else:
            self.height=480

    def get_framerate(self):
        return self.framerate

    def set_framerate(self,fr):
        if fr!=None:
            self.framerate=int(fr)
        else:
            self.framerate=25

    def get_redblue(self):
        return self.redblue

    def set_redblue(self,rb):
        if rb!=None:
            if rb==1:
                self.redblue=True
            elif rb==0:
                self.redblue=False
                self.redblue=rb
        else:
            self.redblue=True

    def add_keyframe(self,filename,duration,stop,int_type,index=None):
        kf = KeyFrame(filename,duration,stop,int_type)
        if index==None:
            self.keyframes.append(kf)
        else:
            self.keyframes.insert(index, kf)

    def remove_keyframe(self,index):
        self.keyframes[index:index+1]=[]

    def change_keyframe(self,index,duration,stop,int_type):
        if index<len(self.keyframes):
            kf = self.keyframes[index]
            kf.duration = duration
            kf.stop = stop
            kf.int_type = int_type

    def get_keyframe(self,index):
        return self.keyframes[index]

    def get_keyframe_filename(self,index):
        return self.keyframes[index].filename

    def get_keyframe_duration(self,index):
        return self.keyframes[index].duration

    def set_keyframe_duration(self,index,duration):
        if index<len(self.keyframes):
            self.keyframes[index].duration = duration

    def get_keyframe_stop(self,index):
        return self.keyframes[index].stop

    def set_keyframe_stop(self,index,stop):
        if index<len(self.keyframes):
            self.keyframes[index].stop= stop

    def get_keyframe_int(self,index):
        return self.keyframes[index].int_type

    def set_keyframe_int(self,index,int_type):
        if index<len(self.keyframes):
            self.keyframes[index].int_type=int_type

    def get_directions(self,index):
        return self.keyframes[index].flags

    def set_directions(self,index,drct):
        if index<len(self.keyframes):
            self.keyframes[index].flags = drct

    def keyframes_count(self):
        return len(self.keyframes)

    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict since we change it
        #del odict['fh']              # remove filehandle entry
        return odict

    def __setstate__(self,dict):
        self.keyframes=[]
        self.__dict__.update(dict)   # update attributes

    def load_animation(self,file):
        #save __dict__ if there was error
        odict = self.__dict__.copy()
        import traceback
        try:
            self.keyframes=[]
            parser = make_parser()
            ah = AnimationHandler(self)
            parser.setContentHandler(ah)
            parser.parse(open(file))
        except Exception as err:
            #retrieve previous__dict__
            self.__dict__=odict
            raise

    def save_animation(self,file):
        fh=open(file,"w")
        fh.write('<?xml version="1.0"?>\n')
        fh.write("<animation>\n")
        fh.write('\t<keyframes>\n')
        for kf in self.keyframes:
            kf.save(fh)
        fh.write('\t</keyframes>\n')
        fh.write('\t<output filename="%s" framerate="%d" width="%d" height="%d" swap="%d"/>\n'%
             (self.avi_file,self.framerate,self.width,self.height,self.redblue))
        fh.write("</animation>\n")
        fh.close()

    #leftover from debugging purposes
    def pr(self):
        print(self.__dict__)

    def get_image_filename(self,n):
        "The filename of the image containing the Nth frame"
        return os.path.join(self.get_png_dir(),"image_%07d.png" %n)

    def get_fractal_filename(self,n):
        "The filename of the .fct file which generates the Nth frame"
        return os.path.join(self.get_fct_dir(),"file_%07d.fct" % n)

    def get_mu(self, int_type, x):
        if int_type==INT_LINEAR:
            mu=x
        elif int_type==INT_LOG:
            mu=math.log(x+1,2)
        elif int_type==INT_INVLOG:
            mu=(math.exp(x)-1)/(math.e-1)
        elif int_type==INT_COS:
            mu=(1-math.cos(x*math.pi))/2
        else:
            raise ValueError("Unknown interpolation type %d" % int_type)
        return mu
    
    # create a list containing all the filenames of the frames
    def create_list(self):
        framelist = []
        folder_png=self.get_png_dir()

        current=1
        for i in range(self.keyframes_count()):
            for j in range(self.get_keyframe_stop(i)): #output keyframe 'stop' times
                framelist.append(self.get_image_filename(current-1))

            if i < self.keyframes_count()-1:
                # final frame has no transitions following it
                for j in range(self.get_keyframe_duration(i)): #output all transition files
                    framelist.append(self.get_image_filename(current))
                    current=current+1
        
        return framelist

    def get_keyframe_durations(self):
        durations = []
        for i in range(self.keyframes_count()):
            durations.append(self.get_keyframe_duration(i))

        return durations

    def get_total_frames(self):
        count = 0
        nframes = self.keyframes_count()
        for i in range(nframes):
            count += self.get_keyframe_stop(i)
            if i < nframes - 1:
                # don't count the last frame's duration
                count += self.get_keyframe_duration(i)
        return count
    
class AnimationHandler(ContentHandler):
    def __init__(self,animation):
        self.animation=animation

    def startElement(self, name, attrs):
        if name=="output":
            self.animation.set_avi_file(attrs.get("filename"))
            self.animation.set_framerate(attrs.get("framerate"))
            self.animation.set_width(attrs.get("width"))
            self.animation.set_height(attrs.get("height"))
            self.animation.set_redblue(int(attrs.get("swap")))
        elif name=="keyframe":
            kf= KeyFrame.load_from_xml(attrs)
            self.animation.keyframes.append(kf)
        return

