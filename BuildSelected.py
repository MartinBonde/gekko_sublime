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
        extenstion = os.path.splitext(file_path)[1]

        if extenstion == ".gcm":
            # If Gekko is open, get the working folder
            # Else open Gekko with the current dir as working folder and interface remote enabled
            cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
            proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE, universal_newlines=True)
            for line in proc.stdout:
                if "Gekko.exe" in line:
                    if "folder" in line:
                        p = re.compile("Gekko.exe.+[-]folder[:](\S+)")
                        working_folder = p.search(line).group(1)
                    else:
                        working_folder = os.path.dirname(file_path)
                    print("Running Gekko instance found. Remote control commands are written to %s" % working_folder)
                    break
            else:
                if shutil.which("gekko"):
                    working_folder = os.path.dirname(file_path)
                    start_code = "option interface remote = yes;"
                    cmd = ["gekko", "-folder:"+working_folder, start_code]
                    print("New Gekko instance opened. Remote control commands are written to %s" % working_folder)
                    sp.Popen(cmd, stdin=sp.PIPE, universal_newlines=True)
                    time.sleep(5)
                else:
                    sublime.error_message("No open Gekko instance was found. Please open Gekko (or set a path to Gekko so it can be opened automatically).")
                    exit()

            # Remove quotes from working folder path
            if working_folder.startswith('"') and working_folder.endswith('"'):
                working_folder = working_folder[1:-1]

            # Get selected text
            selected = ""
            for region in self.view.sel():
                selected += self.view.substr(region)
            # If none is selected, get the current line and move cursor to next line
            if not selected:
                line = self.view.line(region)
                selected = self.view.substr(line)
                if selected.strip()[-1:] != ";":
                    selected += ";"
                    self.view.insert(edit, line.b, ";\n")
                    line = self.view.line(region)
                self.view.sel().clear()
                self.view.sel().add(line.b+1)


            # The code is run by writing to the remote.gcm file in the working folder
            remote = os.path.join(working_folder, "remote.gcm")
            print("Sending '{}' to gekko".format(selected))
            with open(remote, 'w+') as f:
                f.write(selected)
            # gekko checks remote.gcm file for updates 5 times pr. second
            # After allowing enough time for gekko to update, delete the remote file
            # time.sleep(0.3)
            # os.remove(remote)

            # Center view on selection if out of view
            self.view.show(self.view.line(region))

        else:
            sublime.error_message("Selected build currently only works with .gcm files")


