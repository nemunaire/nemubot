# coding=utf-8

import urllib.request
import json

nemubotversion = 3.3

def help_tiny ():
  return "Find info about a movie"

def help_full ():
  return "!imdb <film>"

def load(context):
    from hooks import Hook
    add_hook("cmd_hook", Hook(cmd_imdb, "imdb"))
    add_hook("cmd_hook", Hook(cmd_search, "imdbs"))


def cmd_imdb(msg):
    if (len(msg.cmds) < 2):
        return Response(msg.sender,
                        "Demande incorrecte.\n %s" % help_full(),
                        msg.channel)

    movie_name = msg.cmds[1]

    for x in range(2, len(msg.cmds)):
      movie_name += urllib.parse.quote(' ') + urllib.parse.quote(msg.cmds[x])    

    url = "http://www.omdbapi.com/?t=" + movie_name
    print_debug(url)
    response = urllib.request.urlopen(url)

    data = json.loads(response.read().decode())
    string = "\x02IMDB Rating\x0F: " + data['imdbRating'] + "\n\x02Plot\x0F: " + data['Plot']

    res =  Response(msg.sender,
                    string,
                    msg.channel)
    res.append_message("\x02Released\x0F: " + data['Released']
                       + " \x02Type\x0F: " + data['Type']
                       + " \x02Genre\x0F: " + data['Genre']
                       + " \x02Director\x0F: " + data['Director']
                       + " \x02Writer\x0F: " + data['Writer']
                       + " \x02Actors\x0F: " + data['Actors']
                       + " \x02Country\x0F: " + data['Country'])

    return res
                   
def cmd_search(msg):

  movie_name = msg.cmds[1]

  for x in range(2, len(msg.cmds)):
    movie_name += urllib.parse.quote(' ') + urllib.parse.quote(msg.cmds[x])    

  url = "http://www.omdbapi.com/?s=" + movie_name
  print_debug(url)

  raw = urllib.request.urlopen(url)
  data = json.loads(raw.read().decode())

  search = data['Search']

  movie_list = ""

  for i in range(0, len(search)):
    movie_list += "\x02Title\x0F: " + search[i]['Title']
    movie_list += " \x02Year\x0F: " + search[i]['Year']
    movie_list += " \x02Type\x0F:" + search[i]['Type']
    movie_list += " |--| "
                     
  res = Response(msg.sender, movie_list, msg.channel)
  return res

