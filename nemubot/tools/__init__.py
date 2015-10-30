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

def reload():
    import imp

    import nemubot.tools.config
    imp.reload(nemubot.tools.config)

    import nemubot.tools.countdown
    imp.reload(nemubot.tools.countdown)

    import nemubot.tools.date
    imp.reload(nemubot.tools.date)

    import nemubot.tools.human
    imp.reload(nemubot.tools.human)

    import nemubot.tools.web
    imp.reload(nemubot.tools.web)

    import nemubot.tools.xmlparser
    imp.reload(nemubot.tools.xmlparser)
    import nemubot.tools.xmlparser.node
    imp.reload(nemubot.tools.xmlparser.node)
