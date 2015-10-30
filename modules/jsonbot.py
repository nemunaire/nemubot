from nemubot.hooks import hook
from nemubot.exception import IMException
from nemubot.tools import web
from more import Response
import json

nemubotversion = 3.4

def help_full():
    return "Retrieves data from json"

def getRequestedTags(tags, data):
  response = ""
  if isinstance(data, list):
    for element in data:
      repdata = getRequestedTags(tags, element)
      if response:
        response = response + "\n" + repdata
      else:
        response = repdata
  else:
    for tag in tags:
      if tag in data.keys():
        if response:
          response += ", " + tag + ": " + str(data[tag])
        else:
          response = tag + ": " + str(data[tag])
  return response

def getJsonKeys(data):
  if isinstance(data, list):
    pkeys = []
    for element in data:
      keys = getJsonKeys(element)
      for key in keys:
        if not key in pkeys:
          pkeys.append(key)
    return pkeys
  else:
    return data.keys()

@hook("cmd_hook", "json")
def get_json_info(msg):
    if not len(msg.args):
      raise IMException("Please specify a url and a list of JSON keys.")

    request_data = web.getURLContent(msg.args[0].replace(' ', "%20"))
    if not request_data:
      raise IMException("Please specify a valid url.")
    json_data = json.loads(request_data)

    if len(msg.args) == 1:
      raise IMException("Please specify the keys to return (%s)" % ", ".join(getJsonKeys(json_data)))

    tags = ','.join(msg.args[1:]).split(',')
    response = getRequestedTags(tags, json_data)

    return Response(response, channel=msg.channel, nomore="No more content", count=" (%d more lines)")
