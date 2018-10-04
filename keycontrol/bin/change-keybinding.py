#!/usr/bin/env python3
import subprocess
import os


path = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:" + \
       "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"


check_binding = "<Super>d"
check_command = "/usr/lib/budgie-desktop/plugins/budgie-hcorners/showdesktop"
check_name = "Hide/Show desktop"
target_command = '/usr/share/budgie-desktop/showdesktop/showdesktop'


keyinfo = subprocess.check_output([
    "dconf", "dump",
    "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/",
]).decode("utf-8").split("\n\n")


for s in keyinfo:
    if all([check_binding in s, check_command in s]):
        custom = s.splitlines()[0].replace("[", "").replace("]", "")
        command = [
            "gsettings", "set", path + custom + "/", "command", target_command
        ]
        try:
            subprocess.Popen(command)
        except Exception:
            pass