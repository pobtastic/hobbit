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
from skoolkit.skoolmacro import parse_strings, parse_ints, MacroParsingError
from skoolkit import (BASE_10, BASE_16, CASE_LOWER, CASE_UPPER)

class HobbitHtmlWriter(HtmlWriter):
	def expand_locationattribute(self, attribute, index, cwd):
		# #LOCATIONATTRIBUTEbyte
		end, attribute = parse_ints(attribute, index, 1)
		attributes = []
		if attribute & (1 << 7):
			attributes.append('Light')
		else:
			attributes.append('Dark')
		if attribute & (1 << 1) and attribute & (1 << 2):
			attributes.append('ON')
		elif attribute & (1 << 1):
			attributes.append('INSIDE')
		elif attribute & (1 << 2):
			attributes.append('IN')
		elif attribute & (1 << 3):
			attributes.append('AT')
		else:
			attributes.append('OUTSIDE')
		return end, '; '.join(attributes)

	def expand_textmessage(self, text, index, cwd):
		# #TEXTMESSAGEaddress
		end, address = parse_ints(text, index, 1)
		words = []
		address = self.snapshot[address] + self.snapshot[address + 1] * 0x100
		while True:
			character = self.snapshot[address]
			if character & (1 << 7) == 0:
				if character < 0x20:
					print(f"fizz {hex(address)} {hex(character)}")
					if character > 0x14:
						break
				elif character >= 0x60:
					words.append(self.get_common_word(character))
				else:
					print(f"pop {hex(address)} {hex(character)}")
				address += 0x01
			else:
				lsb = character & 0x7F
				msb = self.snapshot[address + 1]
				if character & 0xF0 == 0x20 or character & 0xF0 == 0x30 or character & 0xF0 == 0x60:
					words.append(self.get_word(msb * 0x100 + lsb))
				else:
					words.append('')#self.get_token(msb, lsb))
				address += 0x02
				# words.append(self.get_word((msb & 0xF0) * 0x100 + lsb))
		return end, ' '.join(words)

	def expand_location(self, text, index, cwd):
		# #LOCATIONid[,affix,hex][(prefix[,suffix])]
		end, id, affix, tohex = parse_ints(text, index, 3, (0, 0, 0))
		if affix:
			end, (prefix, suffix) = parse_strings(text, end, 2, ('', ''))
		else:
			prefix = suffix = ''
		address = 0xB9E0 + id * 2
		anchor = '#{}'.format(self.snapshot[address] + self.snapshot[address + 1] * 0x100)
		href = self._asm_relpath(cwd, 0xBA8A, '') + anchor
		if self.base == BASE_16:
			if self.case == CASE_LOWER:
				link_text = '{}{:0{}x}{}'.format(prefix, id, 2, suffix)
			else:
				link_text = '{}{:0{}X}{}'.format(prefix, id, 2, suffix)
		else:
			link_text = '{}'.format(id)
		return end, self.format_link(href, link_text)

	def expand_locationname(self, text, index, cwd):
		# #LOCATIONNAMEid
		end, id = parse_ints(text, index, 1)
		address = 0xB9E0 + id * 0x02
		target = self.snapshot[address] + self.snapshot[address + 1] * 0x100
		target += 0x02
		return end, self.get_words(target, True)

	def expand_object(self, text, index, cwd):
		# #OBJECTid[,affix,hex][(prefix[,suffix])]
		end, id, affix, tohex = parse_ints(text, index, 3, (0, 0, 0))
		if affix:
			end, (prefix, suffix) = parse_strings(text, end, 2, ('', ''))
		else:
			prefix = suffix = ''
		if id == 0xFF:
			return end, "none"
		address = 0xC063
		while self.snapshot[address] != 0xFF:
			if self.snapshot[address] == id:
				break
			address += 3
		if self.snapshot[address] == 0xFF:
			return end, "invalid ID"
		address += 1
		target = self.snapshot[address] + self.snapshot[address + 1] * 0x100
		anchor = '#{}'.format(target)
		target += 0x08
		href = self._asm_relpath(cwd, 0xC11B, '') + anchor
		if self.base == BASE_16:
			if self.case == CASE_LOWER:
				link_text = '{}{:0{}x}{}'.format(prefix, id, 2, suffix)
			else:
				link_text = '{}{:0{}X}{}'.format(prefix, id, 2, suffix)
		else:
			link_text = '{}'.format(id)
		return end, '{} - "{}"'.format(self.format_link(href, link_text), self.get_words(target, True))

	def expand_texttoken(self, text, index, cwd):
		# #TEXTTOKENaddress[,order]
		end, address, order = parse_ints(text, index, 2, (0, 0))
		return end, self.get_words(address, order)

	def get_common_word(self, index):
		address = 0xAD3D + (index - 0x60) * 2
		lsb = self.snapshot[address]
		msb = self.snapshot[address + 1] + 0x50
		return self.get_token(msb, lsb)

	def get_token(self, msb, lsb):
		if (msb & 0x0F | lsb) == 0:
			return
		return self.get_word((msb & 0x0F) * 0x100 + lsb + 0x6000)

	def get_word(self, address):
		word = []
		while True:
			letter = self.snapshot[address]
			word.append(chr((letter & 0x1F) + 0x60))
			if letter & (1 << 7):
				break
			address += 1
		return ''.join(word)

	def get_words(self, address, order):
		words = []
		for i in range(0, 6, 2):
			lsb = self.snapshot[address + i]
			msb = self.snapshot[address + i + 1]
			if msb & 0x0F | lsb != 0x00:
				words.append(self.get_word(0x6000 + (msb & 0x0F) * 0x100 + lsb))
		if order and len(words) > 1:
			first = words.pop(0)
			words.append(first)
		return ' '.join(word.capitalize() for word in words)

	def expand_firstletter(self, text, index, cwd):
		# #FIRSTLETTERaddress
		end, address = parse_ints(text, index, 1)
		base_letter = self.snapshot[int(address)]
		extra_params = self.snapshot[int(address) + 1]
		suffix = ''
		#print(hex(base_letter))
		if base_letter & (1 << 7):
			print(7)
			base_letter &= 0x7F
			suffix = 'DUNNO'
		if base_letter & (1 << 6):
			base_letter &= 0x1F
			suffix = '(ARTICLE_MISC)'
			print(6)
		if base_letter & (1 << 5):
			print(5)
		if base_letter & (1 << 4):
			print(4)
		if base_letter & (1 << 3):
			print(3)
		if base_letter & (1 << 2):
			print(2)
		if extra_params & (1 << 6):
			suffix = '(PREPOSITION)'
		elif extra_params & (1 << 5):
			suffix = '(SYSTEM_PRONOUN)'
		return end, "%s %s" % (chr(0x40 + base_letter), suffix)

	def expand_letter(self, text, index, cwd):
		# #LETTERaddress
		end, address = parse_ints(text, index, 1)
		base_letter = self.snapshot[int(address)]
		suffix = ''
		if base_letter & (1 << 8):
			base_letter &= 0x8F
		elif base_letter & (1 << 7):
			base_letter &= 0x7F
			suffix = '+$80 (escape character)'
		elif base_letter & (1 << 6):
			base_letter -= 0x60
			suffix = '(PREPOSITION?)'
		elif base_letter & (1 << 5):
			base_letter -= 0x20
			suffix = '(SYSTEM_PRONOUN?)'
		return end, "%s %s" % (chr(0x40 + base_letter), suffix)
