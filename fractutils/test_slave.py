#!/usr/bin/env python

# check that running a slow out-of-proc piece of code in a cancellable way works

import unittest
import select
import sys

import gtk

from . import slave

class GTKTestSlave(object):
    def __init__(self, cmd, *args):
        self.s = slave.GTKSlave(cmd,*args)
        self.complete = False

        window = gtk.Window()
        self.bar = gtk.ProgressBar()
        window.add(self.bar)
        window.show_all()

        self.s.connect('progress-changed',self.on_progress)
        self.s.connect('operation-complete', self.on_complete)

    def on_complete(self,slave):
        self.complete = True
        gtk.main_quit()

    def on_progress(self,slave,type,position):
        if position == -1.0:
            self.bar.pulse()
        else:
            self.bar.set_fraction(position)
        self.bar.set_text(type)
        return True

    def run(self,input):
        self.s.run(input)

        gtk.main()

    
class Test(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def runProcess(self,input,wait_time):
        s = slave.Slave("./stub_subprocess.py", str(wait_time))

        s.run(input)
        return s
    
    def sendInput(self,s,n=sys.maxsize):
        while n > 0:
            (r,w,e) = select.select([],[s.stdin],[],0.01)
            if len(w) == 0:
                continue
            
            if not s.write():
                break

            n -= 1
        #print "done with input"

    def readOutput(self,s):
        bytes_read = 0
        while 1:
            (r,w,e) = select.select([s.stdout],[],[],0.01)
            if len(r) == 0:
                continue
            
            if not s.read():
                break

    def testTerminate(self):
        s = self.runProcess("y" * 200, 2.0)
        self.sendInput(s,1)
        s.terminate()
        self.assertEqual(False, s.write())
        self.assertEqual(False, s.read())
        
    def testRun(self):
        input = "x" * (100 * 1000)
        s = self.runProcess(input, 0.001)
        self.sendInput(s)
        self.readOutput(s)
        self.assertEqual(input, s.output)

    def testNoSuchProcess(self):
        s = GTKTestSlave("./xxx.py", str(0.01))
        input = "x" * 100
        self.assertRaises(OSError, s.run, input)
        
    def testRegister(self):
        s = GTKTestSlave("./stub_subprocess.py", str(0.01))

        input = "x" * (100 * 1000)
        s.run(input)
        self.assertEqual(input, s.s.output)
        self.assertTrue(s.complete, "operation didn't complete")
        
    def testGet(self):
        s = GTKTestSlave("./get.py", "GET", "http://www.google.com/index.html" )
        s.run("")
        if "Name or service not known" in s.s.err_output:
            # we don't have a network connection so can't try this
            return
        self.assertTrue(s.s.output.count("oogle") > 0)

    def testGetBadSite(self):
        s = GTKTestSlave(
            "./get.py", "GET", "http://www.sdgsdvsdvsdvsdbbbs.com/index.html" )
        s.run("")
        self.assertNotEqual(s.s.process.returncode,0)
        self.assertTrue(s.s.err_output.count('Name or service not known') > 0)

    def testGetBadPage(self):
        s = GTKTestSlave(
            "./get.py", "GET", "http://www.google.com/blahblahblah.html" )
        s.run("")
        self.assertEqual(s.s.process.returncode,1)
        if "Name or service not known" in s.s.err_output:
            # we don't have a network connection so can't try this
            return

        self.assertTrue(s.s.err_output.count('404: Not Found') > 0)

        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')



