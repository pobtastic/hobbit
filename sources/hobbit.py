# Copyright 2021 Paul Maddern
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from skoolkit.skoolhtml import HtmlWriter
from skoolkit.skoolmacro import parse_ints, MacroParsingError

class HobbitHtmlWriter(HtmlWriter):
    def expand_textmessage(self, text, index, cwd):
        # #TEXTMESSAGEaddress
        end, address = parse_ints(text, index, 1)
        for i in range(address, address+10):
            print(hex(self.snapshot[i]))
        return end, 'test'
