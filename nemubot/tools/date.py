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

# Extraction/Format text

import re

month_binding = {
    "janvier": 1, "january": 1, "januar": 1,
    "fevrier": 2, "février": 2, "february": 2,
    "march": 3, "mars": 3,
    "avril": 4, "april": 4,
    "mai": 5, "may": 5, "maï": 5,
    "juin": 6, "juni": 6, "junni": 6,
    "juillet": 7, "jully": 7, "july": 7,
    "aout": 8, "août": 8, "august": 8,
    "septembre": 9, "september": 9,
    "october": 10, "oktober": 10, "octobre": 10,
    "november": 11, "novembre": 11,
    "decembre": 12, "décembre": 12, "december": 12,
}

xtrdt = re.compile(r'''^.*? (?P<day>[0-9]{1,4}) .+?
                            (?P<month>[0-9]{1,2}|"''' + "|".join(month_binding) + '''")
                            (?:.+?(?P<year>[0-9]{1,4}))? (?:[^0-9]+
                            (?:(?P<hour>[0-9]{1,2})[^0-9]*[h':]
                            (?:[^0-9]*(?P<minute>[0-9]{1,2})
                            (?:[^0-9]*[m\":][^0-9]*(?P<second>[0-9]{1,2}))?)?)?.*?)?
                    $''', re.X)


def extractDate(msg):
    """Parse a message to extract a time and date"""
    result = xtrdt.match(msg.lower())
    if result is not None:
        day = result.group("day")
        month = result.group("month")

        if month in month_binding:
            month = month_binding[month]

        year = result.group("year")

        if len(day) == 4:
            day, year = year, day

        hour = result.group("hour")
        minute = result.group("minute")
        second = result.group("second")

        if year is None:
            from datetime import date
            year = date.today().year
        if hour is None:
            hour = 0
        if minute is None:
            minute = 0
        if second is None:
            second = 1
        else:
            second = int(second) + 1
            if second > 59:
                minute = int(minute) + 1
                second = 0

        from datetime import datetime
        return datetime(int(year), int(month), int(day),
                        int(hour), int(minute), int(second))
    else:
        return None
