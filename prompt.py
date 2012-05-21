import sys
import shlex
import traceback
import imp
from xml.dom.minidom import parse

server = __import__("server")
imp.reload(server)

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
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      sys.stdout.write (traceback.format_exception_only(exc_type, exc_value)[0])
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

def close(cmds, servers):
  global selectedServer
  if len(cmds) > 1:
    for s in cmds[1:]:
      if s in servers:
        servers[s].disconnect()
        del servers[s]
      else:
        print ("close: server `%s' not found." % s)
  elif selectedServer is not None:
    selectedServer.disconnect()
    del servers[selectedServer.id]
    selectedServer = None
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
      elif l == "chan" or l == "channel" or l == "channels":
        if selectedServer is not None:
          for chn in selectedServer.channels:
            print ("  - %s ;" % chn)
        else:
          print ("  Please SELECT a server before ask for channels list.")
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

def join(cmds, servers):
  rd = 1
  if len(cmds) <= rd:
    print ("%s: not enough arguments." % cmds[0])
    return

  if cmds[rd] in servers:
    srv = servers[cmds[rd]]
    rd += 1
  elif selectedServer is not None:
    srv = selectedServer
  else:
    print ("  Please SELECT a server or give its name in argument.")
    return

  if len(cmds) <= rd:
    print ("%s: not enough arguments."  % cmds[0])
    return

  if cmds[0] == "join":
    srv.join(cmds[rd])
  elif cmds[0] == "leave" or cmds[0] == "part":
    srv.leave(cmds[rd])

def send(cmds, servers):
  rd = 1
  if len(cmds) <= rd:
    print ("send: not enough arguments.")
    return

  if cmds[rd] in servers:
    srv = servers[cmds[rd]]
    rd += 1
  elif selectedServer is not None:
    srv = selectedServer
  else:
    print ("  Please SELECT a server or give its name in argument.")
    return

  if len(cmds) <= rd:
    print ("send: not enough arguments.")
    return

  #Check the server is connected
  if not srv.connected:
    print ("send: server `%s' not connected." % srv.id)
    return

  if cmds[rd] in srv.channels:
    chan = cmds[rd]
    rd += 1
  else:
    print ("send: channel `%s' not authorized in server `%s'." % (cmds[rd], srv.id))
    return

  if len(cmds) <= rd:
    print ("send: not enough arguments.")
    return

  srv.send_msg_final(chan, cmds[rd])
  return "done"

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

def zap(cmds, servers):
  if len(cmds) > 1:
    for s in cmds[1:]:
      if s in servers:
        servers[s].connected = not servers[s].connected
      else:
        print ("disconnect: server `%s' not found." % s)
  elif selectedServer is not None:
    selectedServer.connected = not selectedServer.connected
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
  'quit': end, #Disconnect all server and quit
  'exit': end, #Alias for quit
  'reset': end, #Reload the prompt
  'load': load, #Load a servers configuration file
  'close': close, #Disconnect and remove a server from the list
  'select': select, #Select a server
  'list': liste, #Show lists
  'connect': connect, #Connect to a server
  'join': join, #Join a new channel
  'leave': join, #Leave a channel
  'send': send, #Send a message on a channel
  'disconnect': disconnect, #Disconnect from a server
  'zap': zap, #Reverse internal connection state without check
}
