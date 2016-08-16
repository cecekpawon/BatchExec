import os, platform, subprocess, sublime, sublime_plugin

class StartBatchExec(sublime_plugin.TextCommand):
  def __init__(self, *xView, **xArgs):
    sublime_plugin.TextCommand.__init__(self, *xView, **xArgs)
    self.settings = sublime.load_settings('BatchExec.sublime-settings')
    self.uName = self.settings.get("path").get(self.settings.get("prog")).get("name")
    self.uArgs = self.settings.get("path").get(self.settings.get("prog")).get("args")
    self.uInline = self.settings.get("path").get(self.settings.get("prog")).get("inline")

  def run(self, *xView, **xArgs):
    xFile = self.view.file_name()

    if (
      not os.path.exists(xFile) or
      not os.path.isfile(xFile) or
      platform.system() != "Windows"
    ):
      return

    xExt = os.path.splitext(xFile)[1][1:].strip().lower()

    if not xExt in ["bat", "cmd"]:
      return

    xMode = xArgs.get("mode", "")
    xDrive = os.path.splitdrive(xFile)[0]
    xDir = os.path.dirname(xFile)
    xCmd = []
    xCmd.append(xDrive)
    xCmd.append("cd \"" + xDir + "\"")
    if (xMode == "file"):
      xCmd.append(".\\\\\"" + os.path.basename(xFile) + "\"")

    xCmd = (" " + self.uInline + " ").join(xCmd)
    subprocess.Popen(" ".join([self.uName, self.uArgs, xCmd]))
