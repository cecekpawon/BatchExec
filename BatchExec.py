import os, platform, sublime_plugin

class StartBatchExec(sublime_plugin.TextCommand):
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
      xCmd.append("call \"" + os.path.basename(xFile) + "\"")
    xCmd.append("cmd")
    os.system(" & ".join(xCmd))