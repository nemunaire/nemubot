# coding=utf-8

from datetime import timedelta
from queue import Queue
import re
import subprocess
from threading import Thread

from nemubot.hooks import hook
from nemubot.message import TextMessage
from nemubot.message.visitor import AbstractVisitor

nemubotversion = 3.4

queue = Queue()
spk_th = None
last = None

SMILEY = list()
CORRECTIONS = list()

def load(context):
    for smiley in CONF.getNodes("smiley"):
        if smiley.hasAttribute("txt") and smiley.hasAttribute("mood"):
            SMILEY.append((smiley.getAttribute("txt"), smiley.getAttribute("mood")))
    print ("%d smileys loaded" % len(SMILEY))

    for correct in CONF.getNodes("correction"):
        if correct.hasAttribute("bad") and correct.hasAttribute("good"):
            CORRECTIONS.append((" " + (correct.getAttribute("bad") + " "), (" " + correct.getAttribute("good") + " ")))
    print ("%d corrections loaded" % len(CORRECTIONS))


class Speaker(Thread):

    def run(self):
        global queue, spk_th
        while not queue.empty():
            sentence = queue.get_nowait()
            lang = "fr"
            print_debug(sentence)
            subprocess.call(["espeak", "-v", lang, "--", sentence])
            queue.task_done()

        spk_th = None


class SpeakerVisitor(AbstractVisitor):

    def __init__(self, last):
        self.pp = ""
        self.last = last


    def visit_TextMessage(self, msg):
        force = (self.last is None)

        if force or msg.date - self.last.date > timedelta(0, 500):
            self.pp += "A %d heure %d : " % (msg.date.hour, msg.date.minute)
            force = True

        if force or msg.channel != self.last.channel:
            if msg.to_response == msg.to:
                self.pp += "sur %s. " % (", ".join(msg.to))
            else:
                self.pp += "en message priver. "

        action = False
        if msg.message.find("ACTION ") == 0:
            self.pp += "%s " % msg.frm
            msg.message = msg.message.replace("ACTION ", "")
            action = True
        for (txt, mood) in SMILEY:
            if msg.message.find(txt) >= 0:
                self.pp += "%s %s : " % (msg.frm, mood)
                msg.message = msg.message.replace(txt, "")
                action = True
                break

        if not action and (force or msg.frm != self.last.frm):
            self.pp += "%s dit : " % msg.frm

        if re.match(".*https?://.*", msg.message) is not None:
            msg.message = re.sub(r'https?://([^/]+)[^ ]*', " U.R.L \\1", msg.message)

        self.pp += msg.message


    def visit_DirectAsk(self, msg):
        res = TextMessage("%s: %s" % (msg.designated, msg.message),
                         server=msg.server, date=msg.date,
                          to=msg.to, frm=msg.frm)
        res.accept(self)


    def visit_Command(self, msg):
        res = TextMessage("Bang %s%s%s" % (msg.cmd,
                                           " " if len(msg.args) else "",
                                           " ".join(msg.args)),
                          server=msg.server, date=msg.date,
                          to=msg.to, frm=msg.frm)
        res.accept(self)


    def visit_OwnerCommand(self, msg):
        res = TextMessage("Owner Bang %s%s%s" % (msg.cmd,
                                                 " " if len(msg.args) else "",
                                                 " ".join(msg.args)),
                          server=msg.server, date=msg.date,
                          to=msg.to, frm=msg.frm)
        res.accept(self)


@hook("in")
def treat_for_speak(msg):
    if not msg.frm_owner:
        append_message(msg)

def append_message(msg):
    global last, spk_th

    if hasattr(msg, "message") and msg.message.find("TYPING ") == 0:
        return

    vprnt = SpeakerVisitor(last)
    msg.accept(vprnt)
    queue.put_nowait(vprnt.pp)
    last = msg

    if spk_th is None:
        spk_th = Speaker()
        spk_th.start()
