#!/usr/bin/env python

# a minimal script to fetch a web page. We execute this in a separate process
# so we can cancel flickr requests if they take too long or go wrong

# usage: get.py (dummy arg) method url [content-type ] 
# if -P, this is a POST, read postdata from stdin
# url should already be encoded

# try to keep the import set minimal so it starts quickly
import sys
import urllib2

dummy = sys.argv[1]
is_post = sys.argv[2] == "POST"
url = sys.argv[3]
if is_post:
    content_type = sys.argv[4]

txheaders = {}
data = None

if is_post:
    data = sys.stdin.read()
    txheaders['Content-type'] = content_type
    txheaders['Content-length'] = str(len(data))

try:
    req = urllib2.Request(url,data,txheaders)
    resp = urllib2.urlopen(req).read()
    print resp
except urllib2.HTTPError, err:
    print >>sys.stderr, str(err)
    sys.exit(1)
except urllib2.URLError, err:
    print >>sys.stderr, str(err)
    sys.exit(1)
