# -*- coding: utf-8 -*-

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

import math

def size(size, unit=True):
    """Convert a given byte size to an more human readable way

    Argument:
    size -- the size to convert
    unit -- append the unit at the end of the string
    """

    if size <= 0:
        return "0 B" if unit else "0"

    units = ['B','KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB']
    p = math.floor(math.log(size, 2) / 10)

    if unit:
        return "%.3f %s" % (size / math.pow(1024,p), units[int(p)])
    else:
        return "%.3f" % (size / math.pow(1024,p))


def word_distance(str1, str2):
    """Perform a Damerau-Levenshtein distance on the two given strings"""

    d = [[i + j for j in range(len(str2) + 1)] for i in range(len(str1) + 1)]

    for i in range(0, len(str1)):
        for j in range(0, len(str2)):
            cost = 0 if str1[i-1] == str2[j-1] else 1
            d[i+1][j+1] = min(
                d[i][j+1] + 1, # deletion
                d[i+1][j] + 1, # insertion
                d[i][j] + cost, # substitution
            )
            if i >= 1 and j >= 1 and str1[i] == str2[j-1] and str1[i-1] == str2[j]:
                d[i+1][j+1] = min(
                    d[i+1][j+1],
                    d[i-1][j-1] + cost, # transposition
                )

    return d[len(str1)][len(str2)]
