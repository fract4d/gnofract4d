# UI and logic for generation of AVI file from bunch of images
# it knows from director bean class where images are stored (there is also a list file
# containing list of images that will be frames - needed for transcode) and it create
# thread to call transcode.

# Limitations: user can destroy dialog, but it will not destroy transcode process!?

import os
import re
from threading import *

from gi.repository import Gdk, Gtk, GLib

class AVIGeneration:
    def __init__(self, animation, parent):
        self.dialog=Gtk.Dialog(
            transient_for=parent,
            title="Generating AVI file...",
            modal=True,
            destroy_with_parent=True)

        self.dialog.add_buttons(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL)
        self.pbar = Gtk.ProgressBar()
        self.pbar.set_text("Please wait...")
        self.dialog.vbox.pack_start(self.pbar,True,True,0)
        geometry = Gdk.Geometry()
        geometry.min_aspect = 3.5
        geometry.max_aspect = 3.5
        self.dialog.set_geometry_hints(None, geometry, Gdk.WindowHints.ASPECT)
        self.animation=animation
        self.delete_them=-1

    def generate_avi(self):
        # -------getting all needed information------------------------------
        folder_png=self.animation.get_png_dir()
        list_file = os.path.join(folder_png, "list")

        avi_file=self.animation.get_avi_file()
        framerate=self.animation.get_framerate()
        yield True
        # ------------------------------------------------------------------

        try:
            if self.running is False:
                yield False
                return

            if not os.path.exists(list_file):
                Gdk.threads_enter()
                error_dlg = Gtk.MessageDialog(
                    self.dialog,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                    "In directory: %s there is no listing file. Cannot continue" %(folder_png))
                error_dlg.run()
                error_dlg.destroy()
                Gdk.threads_leave()
                event = Gdk.Event(Gdk.EventType.DELETE)
                self.dialog.emit('delete_event', event)
                yield False
                return
            
            # --------calculating total number of frames------------
            count=self.animation.get_total_frames()
            # ------------------------------------------------------
            # calling ffmpeg
            swap=""
            if self.animation.get_redblue():
                swap='-vf "colorchannelmixer=rr=0:rb=1:br=1:bb=0"'

            call = "ffmpeg -r %d -f concat -safe 0 -i %s %s -r %d %s" % \
                (framerate, list_file, swap, framerate, avi_file)
            dt=DummyThread(call,self.pbar,float(count))
            dt.start()

            working=True
            while(working):
                dt.join(0.5)  # refresh gtk every 0.5 seconds
                working=dt.isAlive()
                yield True

            if self.running is False:
                yield False
                return
            yield True
        except Exception as err:
            self.running=False
            self.error=True
            Gdk.threads_enter()
            error_dlg = Gtk.MessageDialog(self.dialog,Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                    _("Error during generation of avi file: %s" % err))
            error_dlg.run()
            error_dlg.destroy()
            Gdk.threads_leave()
            event = Gdk.Event(Gdk.EventType.DELETE)
            self.dialog.emit('delete_event', event)
            yield False
            return
        if self.running is False:
            yield False
            return
        self.running=False
        self.dialog.destroy()
        yield False

    def show(self):
        # ------------------------------------------------------------
        self.dialog.show_all()
        self.running=True
        self.error=False
        task=self.generate_avi()
        GLib.idle_add(task.__next__)
        response = self.dialog.run()
        if response != Gtk.ResponseType.CANCEL:
            if self.running is True:  # destroy by user
                self.running=False
                self.dialog.destroy()
                return 1
            else:
                if self.error is True:  # error
                    self.dialog.destroy()
                    return -1
                else:  # everything ok
                    self.dialog.destroy()
                    return 0
        else:  # cancel pressed
            self.running=False
            self.dialog.destroy()
            return 1

# thread for calling transcode
class DummyThread(Thread):
    def __init__(self,s,pbar,count):
        Thread.__init__(self)
        self.s=s
        self.pbar=pbar
        self.count=count

    def run(self):
        #os.system(self.s) <----this is little faster, but user can't see any progress
        reg=re.compile("\[.*-.*\]")
        pipe=os.popen(self.s)
        for line in pipe:
            m=reg.search(line)
            if m is not None:
                cur=re.split("-",m.group())[1][0:-1]
                self.pbar.set_fraction(float(cur)/self.count)
        pipe.close()
        return
