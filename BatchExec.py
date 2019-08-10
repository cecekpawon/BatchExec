import os, platform, subprocess, re, webbrowser, sublime, sublime_plugin


#
# Global
#


def glob_init():
  global gSetting, gPath, gProg, gName, gArgs, gInline
  global gPath, gDir, gMode, gCmd
  global gFileName

  gSetting  = sublime.load_settings('BatchExec.sublime-settings')
  gPath     = gSetting.get("path")

  if (platform.system() == "Windows"):
    gProg   = gPath.get(gSetting.get("prog"))
  else:
    gProg   = gPath.get("tm")

  gName     = gProg.get("name")
  gArgs     = gProg.get("args")
  gInline   = gProg.get("inline")

  gPath     = ""
  gDir      = ""
  gMode     = ""
  gCmd      = ""

  gFileName = ""

def glob_args(**Args):
  global gPath, gDir, gMode, gCmd

  glob_init()

  gPath  = Args.get("paths", [])
  gDir   = Args.get("dirs", [])
  gMode  = Args.get("mode", "")
  gCmd   = Args.get("cmd", "")

def glob_enabled(**Args):
  Result = ((platform.system() == "Windows") or (platform.system() == "Darwin"))
  if Result:
    glob_args(**Args)

  return Result

def glob_repo_is_valid():
  return bool(
      gCmd
      and gDir
      and (
        ((gMode == "svn") and os.path.exists(os.path.join(gDir[0], ".svn")))
        or ((gMode == "git") and os.path.exists(os.path.join(gDir[0], ".git")))
      )
    )

def glob_get_command():
  global gCmd

  if gCmd and gDir:
    if (gMode == "svn"):
      gCmd = " ".join([gMode, gCmd, gDir[0]])
    elif (gMode == "git"):
      gCmd = " ".join([gMode, "-C", gDir[0], gCmd])


#
# BatchExecUrlCommand - browser
#


class BatchExecUrlCommand(sublime_plugin.WindowCommand):

  def is_enabled(self, **Args):
    return (glob_enabled(**Args) and glob_repo_is_valid())

  def fix_url(self, Url):
    if Url:
      if (gMode == "svn"):
        Url = re.sub(r"(github.com/.*?)(/branches/+)", r"\1/tree/", Url, re.IGNORECASE)  # svn co
        Url = Url.replace("svn.code.", "") # sourceforge

      elif (gMode == "git"):
        Url = re.sub(".git$", "", Url, flags=re.IGNORECASE)

      if re.search("^http", Url, re.IGNORECASE):
        Url = re.sub("^http:", "https:", Url, flags=re.IGNORECASE)
        Url = re.sub("/$", "", Url)
      else:
        Url = ""

    return Url

  def run(self, **Args):
    glob_get_command()

    Url = self.fix_url(subprocess
                        .check_output(gCmd, shell=True)
                        .strip()
                        .decode('ascii')
                        )

    if Url:
      webbrowser.open(Url, new=0, autoraise=True)


#
# BatchExecCommand - cmd-prompt
#


class BatchExecCommand(sublime_plugin.WindowCommand):

  def is_valid(self, **Args):
    global gFileName

    gFileName = ""

    VarMap  = self.window.extract_variables()

    if (gMode == "directory"):
      if gDir:
        gFileName = gDir[0]
      elif gPath:
        gFileName = os.path.dirname(gPath[0])
      elif 'file' in VarMap:
        gFileName = os.path.dirname(VarMap['file'])

    elif (gMode == "file"):
      if not gDir:
        if gPath:
          gFileName = gPath[0]
        elif 'file' in VarMap and os.path.isfile(VarMap['file']):
          gFileName = VarMap['file']
        if gFileName:
          Ext = os.path.splitext(gFileName)[1][1:].strip().lower()
          if (platform.system() == "Windows"):
            if not Ext in ["bat", "cmd"]:
              gFileName = ""
          else:
            if not Ext in ["sh", "command"]:
              gFileName = ""

    elif (gDir and glob_repo_is_valid()):
      glob_get_command()
      gFileName = gDir[0]

    return (gFileName != "")

  def is_enabled(self, **Args):
    return glob_enabled(**Args) and self.is_valid(**Args)

  def run(self, **Args):
    if gFileName and os.path.exists(gFileName):
      Drive = ""
      Dir   = gFileName
      Cmd   = []
      Shell = False

      if (platform.system() == "Windows"):
        #Cmd.append("cls")
        Drive = os.path.splitdrive(gFileName)[0]
        Cmd.append(Drive)

      if (gMode == "file"):
        Dir = os.path.dirname(gFileName)

      Cmd.append("cd " + "\"" + Dir + "\"")

      if (gMode == "file"):
        if (platform.system() == "Windows"):
          Cmd.append(".\\\\\"" + os.path.basename(gFileName) + "\"")
        else:
          Cmd.append("\"./" + os.path.basename(gFileName) + "\"")
      elif gCmd:
        Cmd.append(gCmd)

      Cmd = (" " + gInline + " ").join(Cmd)

      if (gName.strip().lower() != "cmd"):
        Cmd = Cmd.replace("\"", "\\\"")

      if (platform.system() == "Windows"):
        Cmd = " ".join([gName, gArgs, Cmd])
      else:
        Shell = True
        Osa = """
          tell application "Terminal"
            reopen
            activate
            delay 3
            tell application "System Events"
              keystroke "t" using command down
            end tell
            do script "clear && %s" in window 1
          end tell
        """

        OsaArgs = [Item for Tmp in [("-e", "'" + Line.strip() + "'") for Line in Osa.split('\n') if Line.strip() != ''] for Item in Tmp]

        Cmd = (" ".join(["osascript"] + OsaArgs) % (Cmd))

      subprocess.Popen(Cmd, shell=Shell)
