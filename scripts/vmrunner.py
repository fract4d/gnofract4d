#!/usr/bin/python

import os, shutil

from pyvix import vix

def guest_file(fname):
    return "/home/catenary/" + os.path.basename(fname)

class vminfo:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

vms = [
    vminfo(
        name="ubuntu_704_i386",
        arch="i386",
        file= '/home/edwin/vmware/ubuntu-7.04-x86/Ubuntu 7.04 x86.vmx',
        type = "DEB",
        outfile='gnofract4d_3.12-1ubuntu1_i386.deb',
        distfile='gnofract4d-python25_3.12-1ubuntu1_i386.deb'),
    vminfo(
        name="ubuntu_704_amd64",
        arch="amd64",
        file="/home/edwin/vmware/ubuntu 7.04 amd64/ubuntu 7.04 amd64.vmx",
        type= "DEB",
        outfile='gnofract4d_3.12-1ubuntu1_amd64.deb',
        distfile='gnofract4d-python25_3.12-1ubuntu1_amd64.deb'),
    vminfo(
        name="ubuntu_904_amd64",
        arch="amd64",
        file= '/home/edwin/vmware/ubuntu904/Ubuntu 9/Ubuntu 9.04 64-bit.vmx',
        type = "DEB",
        outfile='gnofract4d_3.12-1ubuntu1_amd64.deb',
        distfile='gnofract4d-python26_3.12-1ubuntu1_amd64.deb'),
    vminfo(
        name="ubuntu_904_i386",
        arch="i386",
        file= '/home/edwin/vmware/ubuntu-9.04-x86/Ubuntu 9.04 x86.vmx',
        type = "DEB",
        outfile='gnofract4d_3.12-1ubuntu1_i386.deb',
        distfile='gnofract4d-python26_3.12-1ubuntu1_i386.deb'),

]

fedora_6_i386 = '/home/edwin/vmware/fedora6/fedora6.vmx'

host_tarfile = '/home/edwin/gnofract4d/dist/gnofract4d-3.12.tar.gz'
assert os.path.exists(host_tarfile)
host_script = 'scripts/guest_cmd.py'
guest_script = guest_file(host_script)
guest_tarfile = guest_file(host_tarfile)


def build_binary_on_vm(vminfo):
    host_outfile = vminfo.outfile
    guest_outfile = guest_file(host_outfile)
    outfile_type = vminfo.type

    revert = True
    powerOff = False
    powerOn = False

    print "processing", vminfo.name
    host = vix.Host() # open the local host
    try:    
        vm = host.openVM(vminfo.file)

        if revert:
            print "get ready snapshot"
            snap = vm.getNamedSnapshot("ready")
            print "revert to it"
            vm.revertToSnapshot(snap)

        if powerOn:
            print "power on"
            vm.powerOn()

        try:
            print "wait for tools"
            vm.waitForToolsInGuest()
            print "logging in"
            #fixme constant should be exposed from vix module
            vm.loginInGuest(
                username="catenary",
                password="..smurf", 
                options=8) # VIX_LOGIN_IN_GUEST_REQUIRE_INTERACTIVE_ENVIRONMENT

            print "copying files to guest"
            vm.copyFileFromHostToGuest(host_tarfile,guest_tarfile)
            vm.copyFileFromHostToGuest(host_script, guest_script)
            print "prepping script"
            vm.runProgramInGuest("/bin/chmod", "+x %s" % guest_script)

            print "running script"
            vm.runProgramInGuest(
                guest_script, 
                "/home/catenary %s %s %s" % \
                    (guest_tarfile, outfile_type, guest_outfile))

            print "retrieving logs"
            vm.copyFileFromGuestToHost('/home/catenary/log.txt', 'log.txt')

            print "retrieving output", host_outfile
            vm.copyFileFromGuestToHost(guest_outfile, host_outfile)

            distfile = "dist/" + vminfo.distfile
            print "copying to dist dir", distfile
            shutil.copy(host_outfile, distfile)

        finally:
            if powerOff:
                vm.powerOff()
    finally:
        host.close()


#build_binary_on_vm(vms[0])
#build_binary_on_vm(vms[1])
#build_binary_on_vm(vms[2])
build_binary_on_vm(vms[3])
