"""Perform requests to openai"""

# PYTHON STUFFS #######################################################

from openai import OpenAI

from nemubot import context
from nemubot.hooks import hook
from nemubot.tools import web

from nemubot.module.more import Response


# LOADING #############################################################

CLIENT = None
MODEL = "gpt-4"
ENDPOINT = None

def load(context):
    global CLIENT, ENDPOINT, MODEL
    if not context.config or ("apikey" not in context.config and "endpoint" not in context.config):
        raise ImportError ("You need a OpenAI API key in order to use "
                           "this module. Add it to the module configuration: "
                           "\n<module name=\"openai\" "
                           "apikey=\"XXXXXX-XXXXXXXXXX\" endpoint=\"https://...\" model=\"gpt-4\" />")
    kwargs = {
        "api_key": context.config["apikey"] or "",
    }

    if "endpoint" in context.config:
        ENDPOINT = context.config["endpoint"]
        kwargs["base_url"] = ENDPOINT

    CLIENT = OpenAI(**kwargs)

    if "model" in context.config:
        MODEL = context.config["model"]


# MODULE INTERFACE ####################################################

@hook.command("list_models",
      help="list available LLM")
def cmd_listllm(msg):
    llms = web.getJSON(ENDPOINT + "/models", timeout=6)
    return Response(message=[m for m in map(lambda i: i["id"], llms["data"])], title="Here is the available models", channel=msg.channel)


@hook.command("set_model",
      help="Set the model to use when talking to nemubot")
def cmd_setllm(msg):
    if len(msg.args) != 1:
        raise IMException("Indicate 1 model to use")

    wanted_model = msg.args[0]

    llms = web.getJSON(ENDPOINT + "/models", timeout=6)
    for model in llms["data"]:
        if wanted_model == model["id"]:
            break
    else:
        raise IMException("Unable to set such model: unknown")

    MODEL = wanted_model
    return Response("New model in use: " + wanted_model, channel=msg.channel)


@hook.ask()
def parseask(msg):
    chat_completion = CLIENT.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a kind multilingual assistant. Respond to the user request in 255 characters maximum. Be conscise, go directly to the point. Never add useless terms.",
            },
            {
                "role": "user",
                "content": msg.message,
            }
        ],
        model=MODEL,
    )

    return Response(chat_completion.choices[0].message.content,
                    msg.channel,
                    msg.frm)
