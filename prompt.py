import sys
import shlex
import traceback
import _thread
from xml.dom.minidom import parse

import server

selectedServer = None
MODS = list()

def parsecmd(msg):
  """Parse the command line"""
  try:
    cmds = shlex.split(msg)
    if len(cmds) > 0:
      cmds[0] = cmds[0].lower()
      return cmds
  except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    sys.stdout.write (traceback.format_exception_only(exc_type, exc_value)[0])
  return None

def run(cmds, servers):
  """Launch the command"""
  if cmds[0] in CAPS:
    return CAPS[cmds[0]](cmds, servers)
  else:
    print ("Unknown command: `%s'" % cmds[0])
    return ""

def getPS1():
  """Get the PS1 associated to the selected server"""
  if selectedServer is None:
    return "nemubot"
  else:
    return selectedServer.id

def launch(servers):
  """Launch the prompt"""
  ret = ""
  cmds = list()
  while ret != "quit" and ret != "reset":
    sys.stdout.write("\033[0;33m%s§\033[0m " % getPS1())
    sys.stdout.flush()
    try:
      cmds = parsecmd(sys.stdin.readline().strip())
    except KeyboardInterrupt:
      cmds = parsecmd("quit")
    if cmds is not None and len(cmds) > 0:
      try:
        ret = run(cmds, servers)
      except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sys.stdout.write (traceback.format_exception_only(exc_type, exc_value)[0])
  return ret == "reset"


##########################
#                        #
#  Permorming functions  #
#                        #
##########################

def load(cmds, servers):
  if len(cmds) > 1:
    for f in cmds[1:]:
      dom = parse(f)
      config = dom.getElementsByTagName('config')[0]
      for serveur in config.getElementsByTagName('server'):
        srv = server.Server(serveur, config.getAttribute('nick'), config.getAttribute('owner'), config.getAttribute('realname'))
        if srv.id not in servers:
          servers[srv.id] = srv
          print ("  Server `%s' successfully added." % srv.id)
        else:
          print ("  Server `%s' already added, skiped." % srv.id)
  else:
    print ("Not enough arguments. `load' takes an filename.")
  return

def select(cmds, servers):
  global selectedServer
  if len(cmds) == 2 and cmds[1] != "None" and cmds[1] != "nemubot" and cmds[1] != "none":
    if cmds[1] in servers:
      selectedServer = servers[cmds[1]]
    else:
      print ("select: server `%s' not found." % cmds[1])
  else:
    selectedServer = None
  return

def liste(cmds, servers):
  if len(cmds) > 1:
    for l in cmds[1:]:
      l = l.lower()
      if l == "server" or l == "servers":
        for srv in servers.keys():
          print ("  - %s ;" % srv)
      else:
        print ("  Unknown list `%s'" % l)
  else:
    print ("  Please give a list to show: servers, ...")

def connect(cmds, servers):
  if len(cmds) > 1:
    for s in cmds[1:]:
      if s in servers:
        servers[s].launch(MODS)
      else:
        print ("connect: server `%s' not found." % s)
      
  elif selectedServer is not None:
    selectedServer.launch(MODS)
  else:
    print ("  Please SELECT a server or give its name in argument.")

def disconnect(cmds, servers):
  if len(cmds) > 1:
    for s in cmds[1:]:
      if s in servers:
        if not servers[s].disconnect():
          print ("disconnect: server `%s' already disconnected." % s)
      else:
        print ("disconnect: server `%s' not found." % s)
  elif selectedServer is not None:
    if not selectedServer.disconnect():
      print ("disconnect: server `%s' already disconnected." % selectedServer.id)
  else:
    print ("  Please SELECT a server or give its name in argument.")

def end(cmds, servers):
  if cmds[0] == "reset":
    return "reset"
  else:
    for srv in servers.keys():
      servers[srv].disconnect()
    return "quit"

#Register build-ins
CAPS = {
  'quit': end,
  'exit': end,
  'reset': end,
  'load': load,
  'select': select,
  'list': liste,
  'connect': connect,
  'disconnect': disconnect,
}
