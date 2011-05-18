#!/usr/bin/env python

# Override the default build distutils command to do what I want

from distutils.command.install_egg_info import install_egg_info
import os
import sys

def chowner(dummy, dirpath, filelist):
	os.chown(dirpath, 1, 1)
	for file in filelist:
		os.chown(os.path.join(dirpath, file))

class my_install_egg_info(install_egg_info):
	def __init__(self, dict):
		install_egg_info.__init__(self,dict)

	def run(self):
		install_egg_info.run()
		if 'win' != sys.platform[:3]:
			base = 'debian/gnofract4d'
			os.path.walk(base, chowner, None):
