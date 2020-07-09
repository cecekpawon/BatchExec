import os, platform, subprocess, re, webbrowser, sublime, sublime_plugin


#
# Global
#


class Exec():
  def init(self):
    Setting = sublime.load_settings("BatchExec.sublime-settings")
    Path    = Setting.get("path")

    if (platform.system() == "Windows"):
      Prog  = Path.get(Setting.get("prog"))
    else:
      Prog  = Path.get("tm")

    self.gName      = Prog.get("name")
    self.gArgs      = Prog.get("args")
    self.gInline    = Prog.get("inline")

    self.gPath      = ""
    self.gDir       = ""
    self.gMode      = ""
    self.gCmd       = ""

    self.gFileName  = ""

  def args(self, **Args):
    self.init()

    self.gPath      = Args.get("paths", [])
    self.gDir       = Args.get("dirs", [])
    self.gMode      = Args.get("mode", "")
    self.gCmd       = Args.get("cmd", "")

  def enabled(self, **Args):
    Result = ((platform.system() == "Windows") or (platform.system() == "Darwin"))
    if Result:
      self.args(**Args)

    return Result

  def repo_is_valid(self):
    return bool(
        self.gCmd
        and self.gDir
        and (
          ((self.gMode == "svn") and os.path.exists(os.path.join(self.gDir[0], ".svn")))
          or ((self.gMode == "git") and os.path.exists(os.path.join(self.gDir[0], ".git")))
        )
      )

  def get_command(self):
    if self.gCmd and self.gDir:
      if (self.gMode == "svn"):
        self.gCmd = " ".join([self.gMode, self.gCmd, self.gDir[0]])
      elif (self.gMode == "git"):
        self.gCmd = " ".join([self.gMode, "-C", self.gDir[0], self.gCmd])


#

bExec = Exec()

#

#
# BatchExecUrlCommand - browser
#


class BatchExecUrlCommand(sublime_plugin.WindowCommand):

  def is_enabled(self, **Args):
    return (bExec.enabled(**Args) and bExec.repo_is_valid())

  def rep_url(self, Url, Dict):
    for find, rep in Dict.items():
      Url = re.sub(find, rep, Url, re.IGNORECASE)

    return Url

  def fix_url(self, Url):
    if Url:

      #
      # svn
      #
      if (bExec.gMode == "svn"):
        Dict = {
          r"(github.com/.*?)(/branches/+)"  : r"\1/tree/",
          r"(github.com/.*?)(/trunk/+)"     : r"\1/tree/master/",
          "svn.code."                       : ""
        }

        Url = self.rep_url(Url, Dict)

      #
      # git
      #
      elif (bExec.gMode == "git"):
        Dict = {
          r"(.git$)"    : ""
        }

        Url = self.rep_url(Url, Dict)

      #
      # http check valid protocol
      #
      if re.search("^http", Url, re.IGNORECASE):
        Dict = {
          r"^(http+):"  : r"\1s:",
          r"(/$)"       : "",
        }

        Url = self.rep_url(Url, Dict)

      #
      # Non http, give em soft warn
      #
      else:
        Ret = sublime.ok_cancel_dialog("Open '" + Url + "' anyway?")
        if not Ret:
          Url = ""

    return Url

  def run(self, **Args):
    bExec.get_command()

    Url = self.fix_url(subprocess
                        .check_output(bExec.gCmd, shell=True)
                        .strip()
                        .decode("ascii")
                        )

    if Url:
      webbrowser.open(Url, new=0, autoraise=True)


#
# BatchExecCommand - cmd-prompt
#


class BatchExecCommand(sublime_plugin.WindowCommand):

  def is_valid(self, **Args):
    bExec.gFileName = ""

    VarMap  = self.window.extract_variables()

    #
    # directory
    #
    if (bExec.gMode == "directory"):
      if bExec.gDir:
        bExec.gFileName = bExec.gDir[0]
      elif bExec.gPath:
        bExec.gFileName = os.path.dirname(bExec.gPath[0])
      elif "file" in VarMap:
        bExec.gFileName = os.path.dirname(VarMap["file"])

    #
    # file
    #
    elif (bExec.gMode == "file"):
      if not bExec.gDir:
        if bExec.gPath:
          bExec.gFileName = bExec.gPath[0]
        elif "file" in VarMap and os.path.isfile(VarMap["file"]):
          bExec.gFileName = VarMap["file"]
        if bExec.gFileName:
          Ext = os.path.splitext(bExec.gFileName)[1][1:].strip().lower()
          if (platform.system() == "Windows"):
            if not Ext in ["bat", "cmd"]:
              bExec.gFileName = ""
          else:
            if not Ext in ["sh", "command"]:
              bExec.gFileName = ""

    #
    # repo
    #
    elif (bExec.gDir and bExec.repo_is_valid()):
      bExec.get_command()
      bExec.gFileName = bExec.gDir[0]

    return (bExec.gFileName != "")

  def is_enabled(self, **Args):
    return bExec.enabled(**Args) and self.is_valid(**Args)

  def run(self, **Args):
    if bExec.gFileName and os.path.exists(bExec.gFileName):
      Drive = ""
      Dir   = bExec.gFileName
      Cmd   = []
      Shell = False

      if (platform.system() == "Windows"):
        #Cmd.append("cls")
        Drive = os.path.splitdrive(bExec.gFileName)[0]
        Cmd.append(Drive)

      if (bExec.gMode == "file"):
        Dir = os.path.dirname(bExec.gFileName)

      Cmd.append("cd " + "\"" + Dir + "\"")

      if (bExec.gMode == "file"):
        if (platform.system() == "Windows"):
          Cmd.append(".\\\\\"" + os.path.basename(bExec.gFileName) + "\"")
        else:
          Cmd.append("\"./" + os.path.basename(bExec.gFileName) + "\"")
      elif bExec.gCmd:
        Cmd.append(bExec.gCmd)

      Cmd = (" " + bExec.gInline + " ").join(Cmd)

      if (bExec.gName.strip().lower() != "cmd"):
        Cmd = Cmd.replace("\"", "\\\"")

      #
      # cmd-prompt
      #
      if (platform.system() == "Windows"):
        Cmd = " ".join([bExec.gName, bExec.gArgs, Cmd])

      #
      # terminal
      #
      else:
        Shell = True
        Osa = """
          tell application "Terminal"
            activate
            reopen
            repeat until busy of window 1 is false
              delay .5
            end repeat
            activate
            reopen
            tell application "System Events"
              keystroke "t" using command down
            end tell
            do script "clear && %s" in window 1
          end tell
        """

        OsaArgs = [Item for Tmp in [("-e", "'" + Line.strip() + "'") for Line in Osa.split('\n') if Line.strip() != ''] for Item in Tmp]

        Cmd = (" ".join(["osascript"] + OsaArgs) % (Cmd))

      #
      # exec
      #
      subprocess.Popen(Cmd, shell=Shell)
