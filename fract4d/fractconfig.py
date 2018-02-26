import configparser
import os
import sys

class T(configparser.ConfigParser):    
    "Holds preference data"
    def __init__(self, file):
        _shared_formula_dir = self.get_data_path("formulas")
        _shared_map_dir = self.get_data_path("maps")
        comp = 'gcc'

        _defaults = {
            "compiler" : {
              "name" : comp,
              "options" : self.get_default_compiler_options()
            },
            "optimize" : {
              "peephole" : "1"
            },
            "display" : {
              "width" : "640",
              "height" : "480",
              "antialias" : "1",
              "autodeepen" : "1",
              "autotolerance" : "1"
            },
            "helpers" : {
              "editor" : self.get_default_editor(),
              "mailer" : self.get_default_mailer(),
              "browser" : self.get_default_browser()
            },
            "general" : {
              "threads" : "1",
              "compress_fct" : "1",
              "data_dir" : os.path.expandvars("${HOME}/gnofract4d")
            },
            "user_info" : {
              "name" : "",
              "nsid" : ""
            },
            "blogs" : {
            },
            "formula_path" : {
              "0" : "formulas",
              "1" : _shared_formula_dir,
              "2" : os.path.expandvars("${HOME}/gnofract4d/formulas")
            },
            "map_path" : {
              "0" : "maps",
              "1" : _shared_map_dir,
              "2" : os.path.expandvars("${HOME}/gnofract4d/maps"),
              "3" : "/usr/share/gimp/2.0/gradients"
            },
            "recent_files" : {
            },
            "ignored" : {
            },
            "director" : {
              "fct_enabled": "0",
              "fct_dir" : "/tmp",
              "png_dir" : "/tmp"
            }
        }

        self.image_changed_sections = {
            "display" : True,
            "compiler" : True
            }

        configparser.ConfigParser.__init__(self,interpolation=None)

        self.file = os.path.expanduser(file)
        self.read(self.file)

        # we don't use the normal ConfigParser default stuff because
        # we want sectionized defaults

        for (section,entries) in list(_defaults.items()):
            if not self.has_section(section):
                self.add_section(section)
            for (key,val) in list(entries.items()):
                if not self.has_option(section,key):
                    self.set(section,key,val)

        self.ensure_contains("formula_path", _shared_formula_dir)
        self.ensure_contains("map_path", _shared_map_dir)

    def ensure_contains(self,section,required_item):
        l = self.get_list(section)
        if not l.count(required_item):
            l.append(required_item)
            self.set_list(section,l)
    
    def get_data_path(self,subpath=""):
        # find where data files are present. 
        # use share path one level up from gnofract4d script location
        # e.g., if invoked as /usr/bin/gnofract4d, use /usr/share/gnofract4d
        path = os.path.normpath(os.path.join(
            sys.path[0], "../share/gnofract4d", subpath))
        return path

    def find_on_path(self, executable):
        for path in os.environ["PATH"].split(":"):
            fullname = os.path.join(path,executable)
            if os.path.exists(fullname):
                return fullname
        return None

    def find_resource(self, name, local_dir, installed_dir):
        'try and find a file either locally or installed'
        if os.path.exists(name):
            return name

        local_name = os.path.join(local_dir,name)
        if os.path.exists(local_name):
            return local_name

        full_name = os.path.join(self.get_data_path(installed_dir), name)
        if os.path.exists(full_name):
            return full_name

        #print "missing resource %s" % full_name
        return full_name

    def get_default_editor(self):
        return "emacs"

    def get_default_mailer(self):
        return "evolution %s"

    def get_default_browser(self):
        return "firefox %s"

    def get_default_compiler_options(self):
        # appears to work for most unixes
        return "-fPIC -DPIC -D_REENTRANT -O2 -shared -ffast-math"

    def set(self,section,key,val):
        if self.has_section(section) and \
           self.has_option(section,key) and \
           self.get(section,key) == val:
            return

        configparser.ConfigParser.set(self,section,key,val)
        self.changed(section)

    def set_size(self,width,height):
        if self.getint("display","height") == height and \
           self.getint("display","width") == width:
            return
        
        configparser.ConfigParser.set(self,"display","height",str(height))
        configparser.ConfigParser.set(self,"display","width",str(width))
        self.changed("display")

    def get_list(self, name):
        i = 0
        list = []
        while(True):
            try:
                key = "%d" % i
                val = self.get(name,key)
                list.append(val)
                i += 1
            except configparser.NoOptionError:
                return list

    def remove_all_in_list_section(self,name):
        i = 0
        items_left = True
        while items_left:            
            items_left = self.remove_option(name,"%d" % i)
            i += 1
        
    def set_list(self, name, list):
        self.remove_all_in_list_section(name)

        i = 0        
        for item in list:
            configparser.ConfigParser.set(self, name,"%d" % i, item)
            i += 1

        self.changed(name)

    def update_list(self,name,new_entry,maxsize):
        list = self.get_list(name)
        if list.count(new_entry) == 0:
            list.insert(0,new_entry)
            list = list[:maxsize]
            self.set_list(name,list)

        return list
    
    def changed(self, section):
        pass
            
    def save(self):
        f = open(self.file,"w")
        try:
            self.write(f)
        finally:
            f.close()

class DarwinConfig(T):
    def __init__(self,file):
        T.__init__(self,file)

    def get_default_editor(self):
        # edit file in TextPad
        return "open -e"

    def get_default_mailer(self):
        # create message in default mail app
        return "open %s"

    def get_default_browser(self):
        return "open %s"

    def get_default_compiler_options(self):
        return "-fPIC -DPIC -D_REENTRANT -O2 -dynamiclib -flat_namespace -undefined suppress -ffast-math"
        
config_file = "~/.gnofract4d"
if sys.platform[:6] == "darwin":
    instance = DarwinConfig(config_file)
else:
    instance = T(config_file)
