from datetime import datetime
import time

def countdown(delta, resolution=5):
    sec = delta.seconds
    hours, remainder = divmod(sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    an = int(delta.days / 365.25)
    days = delta.days % 365.25

    sentence = ""
    force = False

    if resolution > 0 and (force or an > 0):
        force = True
        sentence += " %i an"%(an)

        if an > 1:
            sentence += "s"
        if resolution > 2:
            sentence += ","
        elif resolution > 1:
            sentence += " et"

    if resolution > 1 and (force or days > 0):
        force = True
        sentence += " %i jour"%(days)

        if days > 1:
            sentence += "s"
        if resolution > 3:
            sentence += ","
        elif resolution > 2:
            sentence += " et"

    if resolution > 2 and (force or hours > 0):
        force = True
        sentence += " %i heure"%(hours)
        if hours > 1:
            sentence += "s"
        if resolution > 4:
            sentence += ","
        elif resolution > 3:
            sentence += " et"

    if resolution > 3 and (force or minutes > 0):
        force = True
        sentence += " %i minute"%(minutes)
        if minutes > 1:
            sentence += "s"
        if resolution > 4:
            sentence += " et"

    if resolution > 4 and (force or seconds > 0):
        force = True
        sentence += " %i seconde"%(seconds)
        if seconds > 1:
            sentence += "s"
        return sentence[1:]


def countdown_format(date, msg_before, msg_after, timezone=None):
    """Replace in a text %s by a sentence incidated the remaining time before/after an event"""
    if timezone != None:
        os.environ['TZ'] = timezone
        time.tzset()

    #Calculate time before the date
    if datetime.now() > date:
        sentence_c = msg_after
        delta = datetime.now() - date
    else:
        sentence_c = msg_before
        delta = date - datetime.now()

    if timezone != None:
        os.environ['TZ'] = "Europe/Paris"

    return sentence_c % countdown(delta)
