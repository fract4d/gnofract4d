# UI and logic for generating PNG images
# It receives information from the director class, gets all frame values,
# finds in-between values and calls gtkfractal.HighResolution to create images

import os

from gi.repository import Gtk

from . import gtkfractal, hig
from fract4d import fractal

running = False


class PNGGeneration(Gtk.Dialog, hig.MessagePopper):
    def __init__(self, animation, compiler, parent):
        Gtk.Dialog.__init__(
            self,
            transient_for=parent,
            title="Generating images...",
            modal=True, destroy_with_parent=True)

        self.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL)
        hig.MessagePopper.__init__(self)
        self.get_content_area().append(Gtk.Label(label="Current image progress"))
        self.pbar_image = Gtk.ProgressBar()
        self.get_content_area().append(self.pbar_image)
        self.get_content_area().append(Gtk.Label(label="Overall progress"))
        self.pbar_overall = Gtk.ProgressBar()
        self.get_content_area().append(self.pbar_overall)
        self.anim = animation

        # -------------loads compiler----------------------------
        self.compiler = compiler

    def generate_png(self):
        existing_image = None
        filelist = self.anim.create_list()
        for f in filelist:
            if os.path.exists(f):
                existing_image = f
                break
        if existing_image is None:
            self.run_generate(True)
            return False

        def check_recreate_images(response_id):
            self.run_generate(response_id != Gtk.ResponseType.ACCEPT)
        try:
            folder_png = self.anim.get_png_dir()
            self.ask_question(
                _("The temporary directory: %s already contains"
                  " at least one image" % folder_png),
                _("Use them to speed up generation?"),
                check_recreate_images,
            )
        except Exception as err:
            print(err)
            raise

        return False

    def run_generate(self, create_all_images):
        durations = []
        # --------find values and duration from all keyframes------------
        try:
            # discard duration of final keyframe
            durations = self.anim.get_keyframe_durations()[:-1]
        except Exception as err:
            self.show_error(_("Error processing keyframes"), str(err))
            return
        # ---------------------------------------------------------------
        gt = GenerationManager(
            durations, self.anim, self.compiler, create_all_images, self)
        gt.run()

    def show_error(self, message, secondary):
        self.error = True
        error_dlg = hig.ErrorAlert(
            transient_for=self,
            primary=message,
            secondary=secondary)

        def response(dialog, response_id):
            dialog.destroy()
            self.response(Gtk.ResponseType.DELETE_EVENT)
        error_dlg.connect("response", response)
        error_dlg.present()

    def show_dialog(self, callback, user_data):
        def response(dialog, response_id):
            global running
            dialog.destroy()
            if response_id != Gtk.ResponseType.CANCEL:
                if running is True:  # destroy by user
                    running = False
                    callback(1, user_data)
                else:
                    if self.error is True:  # error
                        callback(-1, user_data)
                    else:  # everything ok
                        callback(0, user_data)
            else:  # cancel pressed
                running = False
                callback(1, user_data)
        self.connect("response", response)
        self.error = False
        self.present()
        self.generate_png()

# interpolate values and call generation of .png files


class GenerationManager:
    def __init__(
            self, durations, animation, compiler,
            create_all_images, dialog):
        self.durations = durations
        self.anim = animation
        self.create_all_images = create_all_images
        self.dialog = dialog
        self.pbar_image = dialog.pbar_image
        self.pbar_overall = dialog.pbar_overall
        # initializing progress bars
        self.pbar_image.set_fraction(0)
        self.pbar_overall.set_fraction(0)

        self.transition_counter = None
        self.image_counter = None
        # sum of all frames
        self.sumN = len(self.anim.keyframes) + sum(self.durations)

        self.compiler = compiler

        self.current = gtkfractal.HighResolution(
            compiler,
            int(self.anim.get_width()), int(self.anim.get_height()))

        self.current.connect('status-changed', self.onStatusChanged)
        self.current.connect('progress-changed', self.onProgressChanged)

    def onProgressChanged(self, f, progress):
        self.pbar_image.set_fraction(progress / 100)

    # one image generation complete - start the next one
    def onStatusChanged(self, f, status_val):
        if status_val != 0:
            # image not yet finished
            return
        self.image_ready()

    def image_ready(self):
        global running
        self.image_counter += 1
        if self.image_counter == self.sumN:
            running = False
            self.dialog.response(Gtk.ResponseType.OK)
        else:
            # update progress bar
            self.pbar_overall.set_fraction(self.image_counter / self.sumN)
            if self.transition_counter > self.transition_length:
                self.load_keyframes(self.keyframe + 1)
            self.next_image()

    def run(self):
        global running
        running = True
        self.image_counter = 0
        # start first transition
        self.load_keyframes(0)
        self.next_image()
        # generate list file
        lfilename = os.path.join(self.anim.get_png_dir(), "list")
        with open(lfilename, "w") as lfile:
            for imagefile in self.anim.create_list():
                print("file '%s'" % imagefile, file=lfile)

    def load_keyframes(self, transition):
        self.keyframe = transition
        # current image
        if self.image_counter == 0:
            self.transition_counter = 0
        else:
            # keyframe already output by end of previous transition
            self.transition_counter = 1
        # current transition
        self.transition_length = self.durations[transition] + 1

        self.f_prev = fractal.T(self.compiler)
        with open(self.anim.get_keyframe_filename(transition)) as fh:
            self.f_prev.loadFctFile(fh)

        self.f_next = fractal.T(self.compiler)
        with open(self.anim.get_keyframe_filename(transition + 1)) as fh:
            self.f_next.loadFctFile(fh)

    # generate next image between transition-th and transition-th + 1 keyframe
    # first, it gets border values (keyframe values)
    # (values - x,y,z,w,size,angles,formula parameters)
    # then generates inter values, fill fractal class with it and
    # calls gtkfractal.HighResolution to generate image
    def next_image(self):
        if self.image_counter == 0:
            # first keyframe
            f_frame = self.f_prev
        elif self.transition_counter == self.transition_length:
            # next keyframe
            f_frame = self.f_next
        else:
            # create a blended fractal partway between prev and next keyframe
            mu = self.anim.get_mu(self.anim.get_keyframe_int(self.keyframe),
                                  self.transition_counter / self.transition_length)
            f_frame = self.f_prev.blend(self.f_next, mu)

        self.transition_counter += 1

        # write .fct file if user wants that
        if self.anim.get_fct_enabled():
            with open(self.anim.get_fractal_filename(self.image_counter), "w") as f:
                f_frame.save(f)

        # check if image already exists and user wants to recreate it or not
        image_name = self.anim.get_image_filename(self.image_counter)
        if os.path.exists(image_name) and self.create_all_images is False:
            self.image_ready()
        else:
            self.current.set_fractal(f_frame)
            self.current.reset_render()
            self.current.draw_image(image_name)
