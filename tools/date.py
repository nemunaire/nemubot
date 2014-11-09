# -*- coding: utf-8 -*-

# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2014  nemunaire
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

from datetime import datetime
import re

xtrdt = re.compile(r'''^.*? (?P<day>[0-9]{1,4}) .+?
                            (?P<month>[0-9]{1,2}|janvier|january|fevrier|février|february|mars|march|avril|april|mai|maï|may|juin|juni|juillet|july|jully|august|aout|août|septembre|september|october|octobre|oktober|novembre|november|decembre|décembre|december)
                            (?:.+?(?P<year>[0-9]{1,4}))? [^0-9]+
                            (?:(?P<hour>[0-9]{1,2})[^0-9]*[h':]
                            (?:[^0-9]*(?P<minute>[0-9]{1,2})
                            (?:[^0-9]*[m\":][^0-9]*(?P<second>[0-9]{1,2}))?)?)?.*?
                    $''', re.X)


def extractDate(msg):
    """Parse a message to extract a time and date"""
    result = xtrdt.match(msg.lower())
    if result is not None:
        day = result.group("day")
        month = result.group("month")
        if month == "janvier" or month == "january" or month == "januar":
            month = 1
        elif month == "fevrier" or month == "février" or month == "february":
            month = 2
        elif month == "mars" or month == "march":
            month = 3
        elif month == "avril" or month == "april":
            month = 4
        elif month == "mai" or month == "may" or month == "maï":
            month = 5
        elif month == "juin" or month == "juni" or month == "junni":
            month = 6
        elif month == "juillet" or month == "jully" or month == "july":
            month = 7
        elif month == "aout" or month == "août" or month == "august":
            month = 8
        elif month == "september" or month == "septembre":
            month = 9
        elif month == "october" or month == "october" or month == "oktober":
            month = 10
        elif month == "november" or month == "novembre":
            month = 11
        elif month == "december" or month == "decembre" or month == "décembre":
            month = 12

        year = result.group("year")

        if len(day) == 4:
            day, year = year, day

        hour = result.group("hour")
        minute = result.group("minute")
        second = result.group("second")

        if year is None:
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

        return datetime(int(year), int(month), int(day),
                        int(hour), int(minute), int(second))
    else:
        return None
