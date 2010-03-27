# I need to be able to install an executable script to a data directory
# so scripts= is no use. Pretend it's data then fix up the permissions
# with chmod afterwards

import os
import stat

from distutils.command.install_lib import install_lib

class my_install_lib(install_lib):
    def install(self):
        #need to change self.install_dir to the library dir
        outfiles = install_lib.install(self)
        for f in outfiles:
            if f.endswith("get.py"):
                if os.name == 'posix':
                    # Set the executable bits (owner, group, and world) on
                    # the script we just installed.
                    mode = ((os.stat(f)[stat.ST_MODE]) | 0555) & 07777
                    print "changing mode of %s to %o" % (f, mode)
                    os.chmod(f, mode)

        return outfiles

