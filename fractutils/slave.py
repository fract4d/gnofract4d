# slave.py - run a subordinate process asynchronously

import sys
import os

if "win" not in sys.platform:
    import fcntl
else:
    import win32api
import signal
import select
import errno
import time

import subprocess

def makeNonBlocking(fd):
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    try:
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NDELAY)
    except AttributeError:
        import FCNTL
        fcntl.fcntl(fd, FCNTL.F_SETFL, fl | FCNTL.FNDELAY)

class Slave(object):
    def __init__(self, cmd, *args):
        self.cmd = cmd        
        self.args = list(args)
        self.process = None
        self.input = ""
        self.in_pos = 0
        self.stdin = None
        self.stdout = None
        self.output = ""
        self.err_output = ""
        self.dead = False
        
    def run(self, input):
        self.input = input
        args = [self.cmd, str(len(input))] + self.args
        #print args
        self.process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True)

        makeNonBlocking(self.process.stdin.fileno())
        makeNonBlocking(self.process.stdout.fileno())
        makeNonBlocking(self.process.stderr.fileno())
        self.stdin = self.process.stdin
        self.stdout = self.process.stdout
        self.stderr = self.process.stderr

    def write(self):
        if self.dead:
            self.on_finish_writing()
            return False
        
        bytes_to_write = min(len(self.input) - self.in_pos,1000)
        if bytes_to_write < 1:
            self.stdin.close()
            self.on_finish_writing()
            return False

        try:            
            self.stdin.write(
                self.input[self.in_pos:self.in_pos+bytes_to_write])
            #print "wrote %d" % bytes_to_write
        except IOError, err:
            if err.errno == errno.EAGAIN:
                #print "again!"
                return True
            raise
        
        self.in_pos += bytes_to_write
        return True

    def read(self):
        if self.dead:
            self.on_complete()
            return False
        try:
            data = self.stdout.read(-1)
            #print "read", len(data)
            if data == "":
                # checking all these ways to see if child has died
                # since they don't seem to be reliable
                if self.process.poll() == None or self.process.returncode != None:
                    return False
        except IOError, err:
            if err.errno == errno.EAGAIN:
                #print "again!"
                return True
            raise
        self.output += data
        return True

    def read_stderr(self):
        if self.dead:
            self.on_complete()
            return False
        try:
            data = self.stderr.read(-1)
            #print "read", len(data)
            if data == "":
                # checking all these ways to see if child has died
                # since they don't seem to be reliable
                if self.process.poll() == None or self.process.returncode != None:
                    self.on_complete()
                    return False
        except IOError, err:
            if err.errno == errno.EAGAIN:
                #print "again!"
                return True
            raise
        self.err_output += data
        return True
        
    def on_complete(self):
        pass

    def on_finish_writing(self):
        pass

    def terminate(self):
        try:
            self.dead = True
            os.kill(self.process.pid,signal.SIGKILL)
        except OSError, err:
            if err.errno == errno.ESRCH:
                # already dead
                return
            raise

import gtk
import gobject

class GTKSlave(gobject.GObject,Slave):
    __gsignals__ = {
        'operation-complete' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, ()),
        'progress-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_FLOAT))
        }

    def __init__(self, cmd, *args):
        gobject.GObject.__init__(self)
        Slave.__init__(self,cmd,*args)
        self.write_id = None
        self.read_id = None

    def on_finish_writing(self):
        pass
    

    def on_error_readable(self, source, condition):
        self.read_stderr()
        return True
    
    def on_readable(self, source, condition):        
        #print "readable:", source, condition
        self.emit('progress-changed', "Reading", -1.0)
        self.read()
        return True

    def on_writable(self, source, condition):
        #print "writable:",source,condition
        self.write()
        self.emit('progress-changed', "Writing",
                  (self.in_pos+1.0)/(len(self.input)+1))
        return True

    def remove(self,fd):
        try:
            gobject.source_remove(fd)
        except AttributeError, err:
            gtk.input_remove(fd)
        
    def unregister(self):
        if self.write_id:
            self.remove(self.write_id)
            self.write_id = None

        if self.read_id:
            self.remove(self.read_id)
            self.read_id = None

        if self.err_id:
            self.remove(self.err_id)
            self.err_id = None

    def add_read(self,fd,cb):
        "Hide differences between PyGTK versions"
        try:
            return gobject.io_add_watch(
                fd, gobject.IO_IN | gobject.IO_HUP, cb)
        except AttributeError, err:
            return gtk.input_add(fd, gtk.gdk.INPUT_READ, cb)

    def add_write(self,fd,cb):
        try:
            return gobject.io_add_watch(
                fd, gobject.IO_OUT | gobject.IO_HUP, cb)
        except AttributeError, err:
            return gtk.input_add(fd, gtk.gdk.INPUT_WRITE, cb)
        
    def register(self):
        self.write_id = self.add_write(self.stdin, self.on_writable)
        self.read_id = self.add_read(self.stdout, self.on_readable)
        self.err_id = self.add_read(self.stderr, self.on_error_readable)
        
    def on_complete(self):
        self.unregister()
        
        self.emit('progress-changed', "Done",0.0)
        self.emit('operation-complete')
            
    def run(self,input):
        Slave.run(self,input)

        self.register()

    def terminate(self):
        self.unregister()
        Slave.terminate(self)
        self.on_complete()
        
gobject.type_register(GTKSlave)
