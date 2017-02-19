# code to maintain a list of dialogs which user has chosen not to display again

from . import preferences
import configparser

class T:
    def __init__(self, name, suggest_ignore, response):
        self.prefs = preferences.userPrefs
        self.name = name
        self.suggest_ignore = suggest_ignore
        self.response = response
        
    def is_ignored(self):
        try:
            x = self.prefs.get("ignored",self.name)
            return x == "yes"
        except configparser.NoOptionError:
            return False

    def ignore(self):
        self.prefs.set("ignored",self.name, "yes")

    def is_ignore_suggested(self):
        return self.suggest_ignore
        
