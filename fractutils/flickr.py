# a module for handling interaction with the Flickr photo-sharing service

import os
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, urllib.parse, mimetools, mimetypes
import xml.dom.minidom
import hashlib
import random

from fetch import GET_CMD, Request

API_KEY="f29c6d8fa5d950131c4ae13adc55700d"
SECRET="037ec6eec0e91cab"

BASE_URL="http://www.flickr.com/services/rest/"
AUTH_URL="http://www.flickr.com/services/auth/"
UPLOAD_URL="http://www.flickr.com/services/upload/"

GF4D_GROUP="46555832@N00"

class FlickrError(Exception):
    def __init__(self, msg,code=0):
        Exception.__init__(self, msg)
        self.code = int(code)

def makeRequest(base_url,is_post,
                is_signed=False, input="",
                content_type="application/x-binary",
                **kwds):
    if is_signed:
        kwds["api_sig"]=createSig(**kwds)
    query = urllib.parse.urlencode(kwds)
    url = "%s?%s" % (base_url,query)
    cmd = GET_CMD
    method = is_post and "POST" or "GET"
    args = [ method , url]
    if is_post:
        args.append(content_type) 

    return Request(cmd,args,input)
    
def parseResponse(resp):
    try:
        dom = xml.dom.minidom.parseString(resp)
    except xml.parsers.expat.ExpatError:
        raise FlickrError("Unexpected response:not an xml file")
    
    if dom.documentElement.nodeName != "rsp":
        raise FlickrError("Unexpected response: %s" % resp)

    if dom.documentElement.getAttribute("stat") != "ok":
        # error encountered
        err = dom.getElementsByTagName("err")[0]
        code = err.getAttribute("code")
        msg = err.getAttribute("msg")
        raise FlickrError("Error returned: %s [%s]" % (msg,code),code)
    return dom

def createSig(**kwds):
    keys = list(kwds.keys())
    keys.sort()
    siglist = [ SECRET ]
    for k in keys:
        item = kwds[k]
        siglist.append(k)
        siglist.append(item)
    sig = "".join(siglist)
    hash =  hashlib.md5(sig)
    digest = hash.hexdigest()
    return digest

def getSignedUrl(url,**kwds):
    sig = createSig(**kwds)
    kwds["api_sig"] = sig
    query = urllib.parse.urlencode(kwds)
    url = "%s?%s" % (url, query)
    return url

def getAuthUrl(frob_):
    return getSignedUrl(AUTH_URL,api_key=API_KEY,perms="write",frob=frob_)

def requestFrob():
    return makeRequest(
        BASE_URL,
        False,
        True,
        api_key=API_KEY,
        method="flickr.auth.getFrob")

def parseFrob(resp):
    return resp.getElementsByTagName("frob")[0].firstChild.nodeValue

def requestToken(frob_):
    return makeRequest(
        BASE_URL,
        False,
        True,
        api_key=API_KEY,
        method="flickr.auth.getToken",
        frob=frob_)

def parseToken(resp):
    return Token(resp)

def requestCheckToken(token):
    return makeRequest(
        BASE_URL,
        False,
        True,
        method="flickr.auth.checkToken",
        api_key=API_KEY,auth_token=token)

def parseCheckToken(resp):
    # we'll throw an exception if token is invalid
    return Token(resp)

def requestUpload(photo,token,**kwds):
    kwds["api_key"]=API_KEY
    kwds["auth_token"]=token
    sig = createSig(**kwds)
    kwds["api_sig"] = sig
    files = [("photo",os.path.basename(photo),open(photo).read())]

    content_type, body = encode_multipart_formdata(kwds, files)

    return makeRequest(
        UPLOAD_URL,
        True,
        True,
        body,
        content_type)

def parseUpload(resp):
    photoid = resp.getElementsByTagName("photoid")[0].firstChild.nodeValue
    return photoid

def requestGroupsSearch(query):
    return makeRequest(
        BASE_URL,
        False,
        api_key=API_KEY,
        method="flickr.groups.search",
        text=query)

def parseGroupsSearch(resp):
    groups = [ Group(x) for x in resp.getElementsByTagName("group")]
    return groups

def requestGroupsPoolsAdd(photo,token,group=GF4D_GROUP):
    return makeRequest(
        BASE_URL,
        True,
        True,
        api_key=API_KEY,
        method="flickr.groups.pools.add",
        auth_token=token,
        data="",
        photo_id=photo,
        group_id=group)

# no return value so no parse method
    
def requestPeopleGetPublicGroups(nsid):
    return makeRequest(
        BASE_URL,
        False,
        api_key=API_KEY,
        method="flickr.people.getPublicGroups",
        user_id=nsid)

def parsePeopleGetPublicGroups(resp):
    groups = [ Group(x) for x in resp.getElementsByTagName("group")]
    return groups

def requestUrlsGetUserPhotos(nsid):
    req = makeRequest(
        BASE_URL,
        False,
        True,
        api_key=API_KEY,
        method="flickr.urls.getUserPhotos",
        user_id=nsid)

def parseUrlsGetUserPhotos(resp):
    url = resp.getElementsByTagName("user")[0].getAttribute("url")
    return url

def requestBlogsGetList(token):
    return makeRequest(
        BASE_URL,
        False,
        True,
        api_key=API_KEY,
        auth_token=token,
        method="flickr.blogs.getList")
    
def parseBlogsGetList(resp):
    blogs = [ Blog(x) for x in resp.getElementsByTagName("blog")]
    return blogs

def requestBlogsPostPhoto(blog,photo,title_,description_,token):
    return makeRequest(
        BASE_URL,
        True,
        True,
        api_key=API_KEY,
        method="flickr.blogs.postPhoto",
        auth_token=token,
        blog_id=blog.id,
        photo_id=photo,
        title=title_,
        description=description_)

# no parse method, there's no response

class Blog:
    def __init__(self,element):
        self.id = element.getAttribute("id")
        self.name = element.getAttribute("name")
        self.needspassword = element.getAttribute("needspassword")
        self.url = element.getAttribute("url")
        
class Token:
    def __init__(self,resp):
        self.token = resp.getElementsByTagName("token")[0].firstChild.nodeValue.encode("ascii")
        self.user = User(resp.getElementsByTagName("user")[0])
        
class User:
    def __init__(self,element):
        self.nsid = element.getAttribute("nsid")
        self.username = element.getAttribute("username")
        self.fullname = element.getAttribute("fullname")
        
class Group:
    def __init__(self,element):
        self.nsid = element.getAttribute("nsid")
        self.name = element.getAttribute("name")
    
# This code is from www.voidspace.org.uk/atlantibots/pythonutils.html
def encode_multipart_formdata(fields, files):
    """ Encodes fields and files for uploading.
    fields is a sequence of (name, value) elements for regular form fields - or a dictionary.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files.
    Return (content_type, body) ready for urllib2.Request instance
    You can optionally pass in a boundary string to use or we'll let mimetools provide one.
    """
    try:
        BOUNDARY = '-----'+mimetools.choose_boundary()+'-----'
    except socket.gaierror:
        # occurs on some peoples' computers, appears to be due to subtle
        # misconfiguration. But since we don't really need it...
        BOUNDARY = '-----'+int(random.uniform(1000000000))+'-----'
        
    CRLF = '\r\n'
    L = []
    if isinstance(fields, dict):
        fields = list(fields.items())
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
        
    for (key, filename, value) in files:
        filetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % filetype)
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    try:
        body = CRLF.join(L)
    except UnicodeDecodeError as err:
        print("unicode error", str(err))
        for x in L:
            print(x.__class__)
            if len(x) > 0:
                print("%x" % ord(x[0]))
            print(x[:100])
        raise 
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def build_request(theurl, fields, files, txheaders=None):
    """Given the fields to set and the files to encode it returns a fully formed urllib2.Request object.
    You can optionally pass in additional headers to encode into the object.
    (Content-type and Content-length will be overridden if they are set).
    fields is a sequence of (name, value) elements for regular form fields - or a dictionary.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files.    
    """
    content_type, body = encode_multipart_formdata(fields, files)
    if not txheaders: txheaders = {}
    txheaders['Content-type'] = content_type
    txheaders['Content-length'] = str(len(body))
    return urllib.request.Request(theurl, body, txheaders)
