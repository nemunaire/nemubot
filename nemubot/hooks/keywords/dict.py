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

from nemubot.exception.keyword import KeywordException
from nemubot.hooks.keywords.abstract import Abstract
from nemubot.tools.human import guess


class Dict(Abstract):


    def __init__(self, d):
        super().__init__()
        self.d = d


    @property
    def chk_noarg(self):
        if not hasattr(self, "_cache_chk_noarg"):
            self._cache_chk_noarg = [k for k in self.d if "=" not in k]
        return self._cache_chk_noarg


    @property
    def chk_args(self):
        if not hasattr(self, "_cache_chk_args"):
            self._cache_chk_args = [k.split("=", 1)[0] for k in self.d if "=" in k]
        return self._cache_chk_args


    def check(self, mkw):
        for k in mkw:
            if (mkw[k] and k not in self.chk_args) or (not mkw[k] and k not in self.chk_noarg):
                if mkw[k] and k in self.chk_noarg:
                    raise KeywordException("Keyword %s doesn't take value." % k)
                elif not mkw[k] and k in self.chk_args:
                    raise KeywordException("Keyword %s requires a value." % k)
                else:
                    ch = [c for c in guess(k, self.d)]
                    raise KeywordException("Unknown keyword %s." % k + (" Did you mean: " + ", ".join(ch) + "?" if len(ch) else ""))

        return super().check(mkw)


    def help(self):
        return ["\x03\x02@%s\x03\x02: %s" % (k, self.d[k]) for k in self.d]
