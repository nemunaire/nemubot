# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2015  Mercier Pierre-Olivier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
        sentence += " %i an" % an

        if an > 1:
            sentence += "s"
        if resolution > 2:
            sentence += ","
        elif resolution > 1:
            sentence += " et"

    if resolution > 1 and (force or days > 0):
        force = True
        sentence += " %i jour" % days

        if days > 1:
            sentence += "s"
        if resolution > 3:
            sentence += ","
        elif resolution > 2:
            sentence += " et"

    if resolution > 2 and (force or hours > 0):
        force = True
        sentence += " %i heure" % hours
        if hours > 1:
            sentence += "s"
        if resolution > 4:
            sentence += ","
        elif resolution > 3:
            sentence += " et"

    if resolution > 3 and (force or minutes > 0):
        force = True
        sentence += " %i minute" % minutes
        if minutes > 1:
            sentence += "s"
        if resolution > 4:
            sentence += " et"

    if resolution > 4 and (force or seconds > 0):
        force = True
        sentence += " %i seconde" % seconds
        if seconds > 1:
            sentence += "s"
        return sentence[1:]


def countdown_format(date, msg_before, msg_after, tz=None):
    """Replace in a text %s by a sentence incidated the remaining time
    before/after an event"""
    if tz is not None:
        import os
        oldtz = os.environ['TZ']
        os.environ['TZ'] = tz

        import time
        time.tzset()

    from datetime import datetime, timezone

    # Calculate time before the date
    try:
        if datetime.now(timezone.utc) > date:
            sentence_c = msg_after
            delta = datetime.now(timezone.utc) - date
        else:
            sentence_c = msg_before
            delta = date - datetime.now(timezone.utc)
    except TypeError:
        if datetime.now() > date:
            sentence_c = msg_after
            delta = datetime.now() - date
        else:
            sentence_c = msg_before
            delta = date - datetime.now()

    if tz is not None:
        import os
        os.environ['TZ'] = oldtz

    return sentence_c % countdown(delta)
