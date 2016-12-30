#!/usr/bin/env python3

# this is deliberately not included in test.py since it hits a live website
# and I don't want to screw up their bandwidth allocation

import sys
sys.path.insert(1,"..")

import unittest
import io
import socketserver
import http.server
import posixpath
import urllib.request, urllib.parse, urllib.error
import http.client
import os
import threading, time
import zipfile
import fractutils.slave

import formdb


# Rather than hassle the real UF formula DB when running unit tests,
# we run a temporary fake web server
formdb.target_base = "http://localhost:8090/"

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    # same as a simplehttprequesthandler, but with a different base dir
    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = [_f for _f in words if _f]
        path = posixpath.normpath("../testdata")
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    #def log_message(self, format, *args):
    #    # hide log messages
    #    pass
    
def threadStart():
    handler = MyRequestHandler
    httpd = socketserver.TCPServer(("",8090), handler)
    httpd.serve_forever()

thread = threading.Thread(target=threadStart)
thread.setDaemon(True)
thread.start()
# hack - make sure local server has started before running tests
time.sleep(0.5) 

class Test(unittest.TestCase):
    def testFetch(self):
        conn = http.client.HTTPConnection('localhost',8090)
        conn.request("GET", "/trigcentric.fct")
        response = conn.getresponse()
        self.assertEqual(200, response.status)

    def testFetchWithFormDB(self):
        slave = formdb.beginFetchZip("test.zip")
        self.assertEqual("http://localhost:8090/test.zip", url)
        
    def testFetchAndUnpack(self):        
        conn = http.client.HTTPConnection('localhost',8090)
        conn.request("GET", "/test.zip")
        response = conn.getresponse()
        self.assertEqual(200, response.status)
        zf = zipfile.ZipFile(io.StringIO(response.read()),"r")
        info = zf.infolist()
        self.assertEqual("trigcentric.fct", info[0].filename)
        
    def testCreate(self):
        f = open("../testdata/example_formula_db.txt")
        
        formlinks = formdb.parse(f)

        self.assertEqual(5, len(formlinks))

        self.assertEqual(
            "/cgi-bin/formuladb?view;file=gwfa.ucl;type=.txt", formlinks[0])
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

