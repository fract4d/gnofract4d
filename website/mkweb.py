#!/usr/bin/env python

# A script used to rebuild the website. We use kid for templating,
# generate all the HTML statically, and upload the new version

import os
import string, re

import kid

module = kid.load_template("outline.kid",cache=1)

class Bag:
    def __init__(self,**kwds):
        self.__dict__["url_prefix"]=""
        self.__dict__.update(kwds)
        
announce = Bag(
    date="May 18th, 2011",
    text="Version 3.14.1 released. This contains bug fixes for Mac vs Windows in the build system.")

manual_pages = [
    Bag(name="Using Gnofract 4D",
        file="manual/using.html",
        url_prefix="../"),

    Bag(name="Command Reference",
        file="manual/cmdref.html",
        url_prefix="../"),

    Bag(name="About the maths",
        file="manual/maths.html",
        url_prefix="../"),

    Bag(name="Writing Functions",
        file="manual/compiler.html",        
        url_prefix="../"),
    
    Bag(name="Language Reference",
        file="manual/formref.html",
        url_prefix="../"),
    
    Bag(name="Internals",
        file="manual/internals.html",
        url_prefix="../"),
    
    Bag(name="Known Issues",
        file="manual/bugs.html",
        url_prefix="../"),

    Bag(name="About Gnofract 4D",
        file="manual/about.html",
        url_prefix="../")
    ]
    
pages = [
    Bag(name="Home",
        file="index.html",
        comments=[
             "It warms my heart to see such a fine open source fractal program. A really great job!",
            "After my opinion it is the best open source fractal editor/browser available on the web...",
             "Thanks for producing the best piece of fractal software for Linux!",],
        image="front.jpg",
        announce=announce),

    Bag(name="Features",
        file="features.html",
        image="cheby.jpg",
        comments=[
        "What a great program...",
        "Holy smokes, Batman!  It's the fractal program we'd always dreamed of, but never thought we'd see!",
        "It all works great, it's a whole new world I'm discovering..."
        ]
        ),

    Bag(name="Screencast",
        file="screencast.html",
        image="screencast.jpg",
        comments=[
            "Thanks for creating Gnofract 4D, I've found it a real pleasure to use so far...",
            "Thanks for the great fractal program...",
            "Well, this pretty much rocks...",
        ]
        ),

    Bag(name="Screenshots",
        image="newton.jpg",
        file="screenshots.html",
        comments=[
    "Thanks for a really cool program...",
    "Gnofract4D, c'est &#224; mon avis, le meilleur logiciel de fractales sous Linux.",
    "...recht schnell und sehr sch&#246;n..." 
    ]
    ),
    
    Bag(name="Galleries",
        image="front_buffalo.jpg",
        file="gallery.html",
        comments=[
        "I'm always surprised how fast it runs...",
        "I'm still dribbling out of my slack-jawed mouth...",
        "I'm an enthusiastic user of your program gnofract4d. It's really great...",
        "mieux que mario kart wii... c'est magnifique..."
        ]
        ),
    
    Bag(name="Help Wanted",
        file="contributing.html",
        image="bg_parts.jpg",
        comments=[
           "I wanted to thank you for gnofract4d, it's a beautiful application, generates some true work of arts.",
           "Gnofract4d is one of my all time favorite programs."]
        ),

    Bag(name="Manual",
        file="manual/index.html",
        image="images/manual.jpg",
        url_prefix="../",
        children = manual_pages),

    Bag(name="Links",
        file="links.html",
        image="jm.jpg",
        comments=[
    "Thanks for a cool site and amazing app/creations!",
    "Really a nice tool."
    ]),

    ]

def create_manual():
    global pages
    if not os.path.isdir("manual/figures"):
        os.makedirs("manual/figures")
    os.system("cp ../doc/gnofract4d-manual/C/*.xml .")
    os.system("cp ../doc/gnofract4d-manual/C/figures/*.png manual/figures")
    os.chdir("in/manual")
    os.system("xsltproc --param use.id.as.filename 1 ../../gnofract4d.xsl ../../gnofract4d-manual.xml")
    os.system("cp * ../../manual")
    os.chdir("../..")


def strip_body(s):
    # remove everything outside <body></body>, if present
    # because docbook XSLT produces <head> and other tags I don't want
    bstart = s.find("<body>")
    if bstart != -1:
        bstart += 6
        bend = s.find("</body>",bstart)
        if bend == -1:
            bend = len(s)
        s = s[bstart:bend]
        s = s.replace('xmlns=""', " ")
    return s

re_empty_link = re.compile(r'<a id="(.*?)" />')
re_navheader = re.compile(r'<div class="navheader"(.*?)</div>')
re_clear_style = re.compile(r'style="clear: both"')

def strip_empty_hrefs(s):
    # Seem to end up with <a id="blah"/> sometimes. Firefox makes the whole next para into a link to nowhere
    s = re_empty_link.sub('',s)
    # navheader doesn't display properly, just remove it
    s = re_navheader.sub('',s)
    # clearing styles causes content to move down to below avmenu. Why? god knows
    s = re_clear_style.sub('',s)
    return s

def process_all(pages,side_pages):
    for page in pages:
        if hasattr(page,"stub"):
            continue
        
        body_text = open(os.path.join("in", page.file)).read()
        body_text = strip_body(body_text)

        print "processing ",page.file
        out = open(page.file, "w")
        template = module.Template(
            body=body_text,
            pages=side_pages,
            page=page)
        
        try:
            processed_page = str(template)
            print >>out, strip_empty_hrefs(processed_page)
        except Exception, exn:
            print "Error processing page %s" % page.file
            raise
            
        out.close()
        if hasattr(page,"children"):
            print "children",page.children
            process_all(page.children,pages)

create_manual()
process_all(pages,pages)
