# Nemubot is a smart and modulable IM bot.
# Copyright (C) 2012-2016  Mercier Pierre-Olivier
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

from nemubot.datastore.abstract import Abstract
from nemubot.datastore.xml import XML


def reload():
    global Abstract, XML
    import imp

    import nemubot.datastore.abstract
    imp.reload(nemubot.datastore.abstract)
    Abstract = nemubot.datastore.abstract.Abstract

    import nemubot.datastore.xml
    imp.reload(nemubot.datastore.xml)
    XML = nemubot.datastore.xml.XML
