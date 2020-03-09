# UI and logic for generation of a video file from a bunch of images.
# Uses a list file containing the images that will be frames
# and creates a subprocess to execute ffmpeg.

import os
import signal

from gi.repository import Gdk, Gtk, GLib


class AVIGeneration:
    def __init__(self, animation, parent):
        self.animation = animation
        self.converterpath = parent.converterpath
        self.error_watch = None
        self.fh_err = None
        self.pid = None

        self.dialog = Gtk.Dialog(
            transient_for=parent,
            title="Generating video file",
            modal=True,
            destroy_with_parent=True
        )
        self.dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.spinner = Gtk.Spinner()
        label = Gtk.Label.new("Please wait...")
        self.dialog.vbox.pack_start(self.spinner, True, True, 10)
        self.dialog.vbox.pack_start(label, True, True, 10)
        geometry = Gdk.Geometry()
        geometry.min_aspect = 3.5
        geometry.max_aspect = 3.5
        self.dialog.set_geometry_hints(None, geometry, Gdk.WindowHints.ASPECT)

    def generate_avi(self):
        folder_png = self.animation.get_png_dir()
        list_file = os.path.join(folder_png, "list")
        video_file = self.animation.get_avi_file()
        framerate = self.animation.get_framerate()

        if not os.path.exists(list_file):
            error_dlg = Gtk.MessageDialog(
                transient_for=self.dialog,
                title="Cannot continue",
                modal=True,
                destroy_with_parent=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="In directory: %s there is no listing file" % (folder_png)
            )
            error_dlg.run()
            error_dlg.destroy()
            return

        if not self.converterpath:
            error_dlg = Gtk.MessageDialog(
                transient_for=self.dialog,
                title="Cannot continue",
                modal=True,
                destroy_with_parent=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Cannot find ffmpeg video conversion utility"
            )
            error_dlg.run()
            error_dlg.destroy()
            return

        self.spinner.start()

        # calling ffmpeg
        # https://trac.ffmpeg.org/wiki/Concatenate
        # https://trac.ffmpeg.org/wiki/Encode/VP9
        call = [
            self.converterpath, "-nostdin", "-y",
            "-loglevel", "error", "-hide_banner",
            "-r", str(framerate), "-f", "concat", "-safe", "0", "-i", list_file]
        if self.animation.get_redblue():
            call.extend(["-vf", "colorchannelmixer=rr=0:rb=1:br=1:bb=0"])
        call.extend([
            "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0",
            "-r", str(framerate), video_file])
        self.pid, fd_in, fd_out, fd_err = GLib.spawn_async(call,
                                                           flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                           standard_output=False, standard_error=True)
        self.fh_err = os.fdopen(fd_err, "r")
        GLib.child_watch_add(
            GLib.PRIORITY_DEFAULT,
            self.pid,
            self.video_complete)
        self.error_watch = GLib.io_add_watch(self.fh_err, GLib.PRIORITY_DEFAULT,
                                             GLib.IOCondition.IN, self.video_error)

    def video_error(self, source, condition):
        error_text = source.read()
        print(error_text)
        error_dlg = Gtk.MessageDialog(
            transient_for=self.dialog,
            title=_("Error generating video file"),
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=error_text)
        error_dlg.run()
        error_dlg.destroy()

    def video_complete(self, pid, status):
        self.spinner.stop()
        self.running = False
        if status == 0:
            self.error = False
        else:
            self.error = True
        self.dialog.emit('delete_event', Gdk.Event())

    def show(self):
        self.dialog.show_all()
        self.running = True
        self.error = False

        try:
            self.generate_avi()
        except GLib.GError as err:
            error_dlg = Gtk.MessageDialog(
                transient_for=self.dialog,
                title=_("Error executing video converter"),
                modal=True,
                destroy_with_parent=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=str(err))
            error_dlg.run()
            error_dlg.destroy()
            self.dialog.destroy()

            return -1

        result = 0
        response = self.dialog.run()
        if response == Gtk.ResponseType.CANCEL:
            # cancel pressed
            result = 1
        else:
            if self.running is True:  # destroy by user
                GLib.spawn_close_pid(self.pid)
                os.kill(self.pid, signal.SIGTERM)
                result = 1
            elif self.error is True:  # error
                result = -1

        if self.error_watch is not None:
            GLib.source_remove(self.error_watch)
        if self.fh_err:
            self.fh_err.close()
        self.dialog.destroy()
        return result
