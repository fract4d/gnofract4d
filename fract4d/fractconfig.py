from collections import OrderedDict
import configparser
import os
import sys

CONFIG_FILE = "~/.gnofract4d"


class T(configparser.ConfigParser):
    "Holds preference data"

    def __init__(self, file):
        _shared_formula_dir = T.get_data_path("formulas")
        _shared_map_dir = T.get_data_path("maps")
        comp = 'gcc'

        _defaults = OrderedDict((
            ("compiler",
             OrderedDict((
                         ("name", comp),
                         ("options", self.get_default_compiler_options()),
                         ))
             ),
            ("optimize",
             OrderedDict((
                         ("peephole", "1"),
                         ))
             ),
            ("main_window",
             OrderedDict((
                         ("width", "933"),
                         ("height", "594"),
                         ))
             ),
            ("display",
             OrderedDict((
                         ("width", "640"),
                         ("height", "480"),
                         ("antialias", "1"),
                         ("autodeepen", "1"),
                         ("autotolerance", "1"),
                         ))
             ),
            ("helpers",
             OrderedDict((
                         ("editor", self.get_default_editor()),
                         ("mailer", self.get_default_mailer()),
                         ("browser", self.get_default_browser()),
                         ))
             ),
            ("general",
             OrderedDict((
                         ("threads", "1"),
                         ("compress_fct", "1"),
                         ("data_dir", os.path.expandvars(
                             "${HOME}/gnofract4d")),
                         ("cache_dir", os.path.expandvars(
                             "${HOME}/.gnofract4d-cache")),
                         ))
             ),
            ("user_info",
             OrderedDict((
                         ("name", ""),
                         ("nsid", ""),
                         ))
             ),
            ("blogs",
             OrderedDict()
             ),
            ("formula_path",
             OrderedDict((
                         ("0", "formulas"),
                         ("1", _shared_formula_dir),
                         ("2", os.path.expandvars(
                             "${HOME}/gnofract4d/formulas")),
                         ))
             ),
            ("map_path",
             OrderedDict((
                         ("0", "maps"),
                         ("1", _shared_map_dir),
                         ("2", os.path.expandvars("${HOME}/gnofract4d/maps")),
                         ("3", "/usr/share/gimp/2.0/gradients"),
                         ))
             ),
            ("recent_files",
             OrderedDict()
             ),
            ("ignored",
             OrderedDict()
             ),
            ("director",
             OrderedDict((
                         ("fct_enabled", "0"),
                         ("fct_dir", "/tmp"),
                         ("png_dir", "/tmp"),
                         ))
             ),
        ))

        self.image_changed_sections = {
            "display": True,
            "compiler": True
        }

        configparser.ConfigParser.__init__(self, interpolation=None)
        self.read_dict(_defaults)
        self.file = os.path.expanduser(file)
        self.read(self.file)

        self.ensure_contains("formula_path", _shared_formula_dir)
        self.ensure_contains("map_path", _shared_map_dir)

    def ensure_contains(self, section, required_item):
        l = self.get_list(section)
        if not l.count(required_item):
            l.append(required_item)
            self.set_list(section, l)

    @staticmethod
    def get_data_path(subpath=""):
        # find where data files are present.
        # use share path one level up from module location
        moduledir = os.path.dirname(sys.modules[__name__].__file__)
        path = os.path.normpath(os.path.join(
            moduledir, "../../../../share/gnofract4d", subpath))
        #print("Looking in %s" % path)
        return path

    @staticmethod
    def find_on_path(executable):
        for path in os.environ["PATH"].split(":"):
            fullname = os.path.join(path, executable)
            if os.path.exists(fullname):
                return fullname
        return None

    @staticmethod
    def find_resource(name, resource_dir):
        'try and find a file either locally or installed'
        local_name = os.path.join(resource_dir, name)
        if os.path.exists(local_name):
            return local_name

        full_name = os.path.join(T.get_data_path(resource_dir), name)
        if os.path.exists(full_name):
            return full_name

        #print("missing resource %s" % full_name)
        return full_name

    def get_default_editor(self):
        return "emacs"

    def get_default_mailer(self):
        return "evolution %s"

    def get_default_browser(self):
        return "firefox %s"

    def get_default_compiler_options(self):
        # appears to work for most unixes
        return "-fPIC -DPIC -O2 -shared -ffast-math"

    def set(self, section, key, val):
        if self.has_section(section) and \
           self.has_option(section, key) and \
           self.get(section, key) == val:
            return

        configparser.ConfigParser.set(self, section, key, val)
        self.changed(section)

    def set_size(self, width, height):
        if self.getint("display", "height") == height and \
           self.getint("display", "width") == width:
            return

        configparser.ConfigParser.set(self, "display", "height", str(height))
        configparser.ConfigParser.set(self, "display", "width", str(width))
        self.changed("display")

    def set_main_window_size(self, width, height):
        if self.getint("main_window", "height") == height and \
           self.getint("main_window", "width") == width:
            return

        configparser.ConfigParser.set(
            self, "main_window", "height", str(height))
        configparser.ConfigParser.set(self, "main_window", "width", str(width))
        self.changed("main_window")

    def get_list(self, name):
        i = 0
        list = []
        while(True):
            try:
                key = "%d" % i
                val = self.get(name, key)
                list.append(val)
                i += 1
            except configparser.NoOptionError:
                return list

    def remove_section_item(self, section, number):
        # section is an OrderedDict therefore reuse removed item and delete
        # last
        self[section][str(number)] = ""
        i = 0
        for key in self[section]:
            if self[section][key]:
                self[section][str(i)] = self[section][key]
                i += 1
        del self[section][key]

    def remove_all_in_list_section(self, name):
        i = 0
        items_left = True
        while items_left:
            items_left = self.remove_option(name, "%d" % i)
            i += 1

    def set_list(self, name, list):
        self.remove_all_in_list_section(name)

        i = 0
        for item in list:
            configparser.ConfigParser.set(self, name, "%d" % i, item)
            i += 1

        self.changed(name)

    def changed(self, section):
        pass

    def save(self):
        with open(self.file, "w") as f:
            self.write(f)


class DarwinConfig(T):
    def __init__(self, file):
        T.__init__(self, file)

    def get_default_editor(self):
        # edit file in TextPad
        return "open -e"

    def get_default_mailer(self):
        # create message in default mail app
        return "open %s"

    def get_default_browser(self):
        return "open %s"

    def get_default_compiler_options(self):
        return "-fPIC -DPIC -O2 -dynamiclib -flat_namespace -undefined suppress -ffast-math"


def userConfig():
    if sys.platform[:6] == "darwin":
        userConfig = DarwinConfig(CONFIG_FILE)
    else:
        userConfig = T(CONFIG_FILE)
    return userConfig
