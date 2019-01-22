import sublime_plugin
import sublime
import subprocess as sp
import os
import shutil
import time
import re


class BuildSelectedCommand(sublime_plugin.TextCommand):
    """
    Run selected Gekko commands by sending them to the remote file in the working directory.
    If no Gekko process is found, open Gekko with remote interface enabled and working directory set to current file directory.
    """

    def run(self, edit):
        file_path = self.view.window().active_view().file_name()

        settings = sublime.load_settings("Gekko.sublime-settings")
        gekko_path = os.path.expandvars(settings.get("gekko_path")) + "\\Gekko.exe"
        remote_file_path = os.path.expandvars(settings.get("remote_file_path"))
        directory = os.path.dirname(remote_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # If Gekko is open, get the working folder
        cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
        with sp.Popen(cmd, shell=True, stdout=sp.PIPE, universal_newlines=True) as proc:
            for line in proc.stdout:
                if "Gekko.exe" in line:
                    print("Running Gekko instance found. Remote control commands are written to %s" % remote_file_path)
                    break
        # Else open Gekko with the current dir as working folder and interface remote enabled
            else:
                if os.path.isfile(gekko_path):
                    working_folder = os.path.dirname(file_path)
                    start_code = "option interface remote = yes; OPTION interface remote file = '%s';" % remote_file_path
                    cmd = [gekko_path, "-folder:" + working_folder, start_code]
                    print("New Gekko instance opened. Remote control commands are written to %s" % remote_file_path)
                    sp.Popen(cmd, stdin=sp.PIPE, universal_newlines=True)
                    time.sleep(5)
                else:
                    return sublime.error_message("Open Gekko or add a path to Gekko in Package Settings.")

        # Get selected text
        selected = ""
        for region in self.view.sel():
            selected += self.view.substr(region)
        # If none is selected, get the current line and move cursor to next line
        if not selected:
            line = self.view.line(region)
            selected = self.view.substr(line)
            if selected and selected[:2] != "//" and selected.strip()[-1:] != ";":
                selected += ";"
                self.view.insert(edit, line.b, ";\n")
                line = self.view.line(region)
            self.view.sel().clear()
            self.view.sel().add(line.b + 1)

        # The code is run by writing to the remote.gcm file
        print("Sending '{}' to gekko".format(selected))
        with open(remote_file_path, 'w+') as f:
            f.write(selected)
        # gekko checks remote.gcm file for updates 5 times pr. second
        # time.sleep(0.3)

        # Center view on selection if out of view
        self.view.show(self.view.line(region))


