#!/usr/bin/python 

import os
import sys
import commands

dir = sys.argv[1]
file = sys.argv[2]
type = sys.argv[3] # RPM or DEB
binary = sys.argv[4]
def runAndCheck(command):
    print "running '%s'" % command
    (exitcode, output) = commands.getstatusoutput(command)
    print output
    if exitcode != 0:
        print "command '%s' failed. Exit: %d" % (command,exitcode)
        raise Exception("failed")
    return output

os.chdir(dir)
sys.stderr = sys.stdout = open("log.txt","w")
print "guest script"
print "running in %s" % dir
print "untarring %s" % file
runAndCheck("tar xzvf %s" % file)
dirname = file.replace(".tar.gz","")
print "moving to dirname %s" % dirname
os.chdir(dirname)

print "build"
runAndCheck("python ./setup.py build")

try:
    output = runAndCheck("python ./test.py")
    if output.count("FAIL:") > 0:
        print "tests failed"
except Exception, err:
    print "tests failed", err

print "building package"
if type == "DEB":
    runAndCheck('echo "..smurf" | sudo -S make -f debian/rules binary')

print "installing package"
if type == "DEB":
    runAndCheck('echo "..smurf" | sudo -S dpkg -i ../gnofract4d*.deb')


#runAndCheck("echo '..smurf' | sudo -S python ./setup.py
