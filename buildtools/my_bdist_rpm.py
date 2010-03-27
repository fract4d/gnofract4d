#!/usr/bin/env python

# Override the default bdist_rpm distutils command to do what I want

import re
import glob
import os
import sys

from distutils.command.bdist_rpm import bdist_rpm
from distutils.core import Command

topdir_re = re.compile(r'.*topdir (.*)')

class my_bdist_rpm (bdist_rpm):
    user_options = bdist_rpm.user_options
    def __init__(self, dict):
        bdist_rpm.__init__(self,dict)

    def insert_after(self,spec, find,add):
        for i in xrange(len(spec)):
            if spec[i].startswith(find):
                spec.insert(i,add)
                return

    def replace(self,spec,find, new):
        for i in xrange(len(spec)):
            if spec[i].startswith(find):
                print "replacing %s with %s" % (spec[i], new)
                spec[i] = new
                return
            
    def add_to_section(self,spec,sect,add):
        found = False
        for i in xrange(len(spec)):
            if spec[i].startswith(sect):
                found = True
            elif spec[i].startswith('%'):
                if found:
                    spec.insert(i,add)
                    return
        if found:
            # this is the last section
            spec.insert(i,add)
        else:
            raise IndexError("sect %s not found" % sect)

    def spawn(self,cmd):
        '''HACK: On FC4 rpmbuild creates 2 RPMS, the normal one and a
        debuginfo one. This horrifies the bdist_rpm which comes with pythons
        older than 2.4 - these only expect 1 RPM. This works around
        that by deleting the extraneous debuginfo RPM. Overriding this
        method rather than run() because there's less code. '''
        bdist_rpm.spawn(self,cmd)
        v = sys.version_info[0] * 10 + sys.version_info[1]
        if v < 24 and cmd[0] == "rpmbuild":
            for arg in cmd:
                m = topdir_re.match(arg)
                if m:
                    print "doing 2.3-cleanup"
                    dir = m.group(1)                    
                    debuginfo_glob = os.path.join(
                        dir,"RPMS", "*", "*debuginfo*")
                    rpms = glob.glob(debuginfo_glob)
                    print "found extraneous rpms", rpms
                    for rpm in rpms:
                        os.remove(rpm)

        
    def _make_spec_file(self):
        '''HACK: override the default PRIVATE function to specify:
           AutoReqProv: no
           add some commands to update mime types
           '''
        
        spec = bdist_rpm._make_spec_file(self)

        # reduce the number of explicit pre-requisites
        self.insert_after(spec, 'Url','AutoReqProv: no')

        # remove an old tag that newer rpmbuilds dislike        
        self.replace(spec, 'Copyright', 'License: BSD')
        
        # install a .desktop file and register .fct files with ourselves
        self.insert_after(spec, '%define', '%define desktop_vendor ey')
        self.add_to_section(spec, '%install', '''
%post
update-mime-database %{_datadir}/mime &> /dev/null || :
update-desktop-database &> /dev/null || :

%postun
update-mime-database %{_datadir}/mime &> /dev/null || :
update-desktop-database &> /dev/null || :

''')

        print "SPEC>"
        print "\n".join(spec)
        print "EOF>"
        
        return spec
