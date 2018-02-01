#!/usr/bin/env python

# unit tests for flickr api

import unittest
import copy
import sys

import gtk

from . import flickr
from . import slave

sys.path.append("..")

class GTKTestSlave(object):
    def __init__(self, request):
        self.s = slave.GTKSlave(request.cmd,*request.args)
        
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

    def response(self):
        return flickr.parseResponse(self.s.output)
    
    def run(self,input):
        self.s.run(input)
        gtk.main()
        return self.response()

def get_resp(request):
    return GTKTestSlave(request).run(request.input)

# don't want to tell the world this token, so it's kept in this
# non-checked-in file. User needs to create it initially
try:
    TOKEN = open("token.txt").read().strip()
except IOError as err:
    frob_req = flickr.requestFrob()
    resp = get_resp(frob_req)
    frob = flickr.parseFrob(resp)
    
    url = flickr.getAuthUrl(frob)
    print("""
You need to get an authorization token to allow this test program
to access your Flickr account. Click on the URL below and follow
the instructions, then close the browser window and press ENTER.

""")
    print(url)
    sys.stdin.readline()
    token_req = flickr.requestToken(frob)
    resp = get_resp(token_req)
    token = flickr.parseToken(resp)

    print("token",token)
    TOKEN=token.token
    open("token.txt","w").write(token.token)    

class Test(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def testEcho(self):
        request = flickr.makeRequest(
            "http://www.flickr.com/services/rest/",
            False,
            method="flickr.test.echo",
            name="hello",
            api_key=flickr.API_KEY)

        resp = get_resp(request)
        
        self.assertSuccessfulRest(resp)
        self.assertEqual(
            resp.getElementsByTagName("name")[0].firstChild.nodeValue,"hello")

    def testToken(self):
        request = flickr.requestCheckToken(TOKEN)
        resp = get_resp(request)

        t = flickr.parseCheckToken(resp)
        user = t.user
        self.assertNotEqual(user.username,"")
        self.assertNotEqual(user.nsid,"")

    def disabled_testUpload(self):
        req = flickr.requestUpload(
            "../pixmaps/gnofract4d-logo.png",
            TOKEN,
            title="Burning Bush",
            description="test image of exceptional ugliness")

        resp = get_resp(req)
        id = flickr.parseUpload(resp)
        
    def testGetGnofract4DGroup(self):
        groups_req = flickr.requestGroupsSearch("gnofract 4d")

        resp = get_resp(groups_req)
        groups = flickr.parseGroupsSearch(resp)
        
        found = False
        for g in groups:
            if g.name == "Gnofract 4D":
                self.assertEqual(g.nsid,flickr.GF4D_GROUP)
                found = True
        self.assertTrue(found)

    def testAddPhotoToGroup(self):
        photo = '48623980'
        try:
            req = flickr.requestGroupsPoolsAdd(photo,TOKEN,flickr.GF4D_GROUP)
            resp = get_resp(req)

            self.fail("Should have thrown an exception")
        except flickr.FlickrError as err:
            self.assertEqual(err.code,3)
        
    def testGroupMembership(self):
        token_req = flickr.requestCheckToken(TOKEN)

        resp = get_resp(token_req)
        user = flickr.parseCheckToken(resp).user
                
        nsid = user.nsid
        groups_req = flickr.requestPeopleGetPublicGroups(nsid)
        resp = get_resp(groups_req)
        groups = flickr.parsePeopleGetPublicGroups(resp)
    
        gf4d = [g for g in groups if g.nsid == flickr.GF4D_GROUP]
        if len(gf4d) == 0:
            # current user is not a member of gf4d group
            print("\nYou're not a member of the Gnofract 4D group. You should join!")

    def assertWellFormedRest(self, resp):        
        docNode = resp.documentElement
        self.assertEqual(docNode.nodeName,"rsp")

    def assertSuccessfulRest(self,resp):
        self.assertWellFormedRest(resp)
        docNode = resp.documentElement
        self.assertEqual(docNode.getAttribute("stat"),"ok")
    
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')



