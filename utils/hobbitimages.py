#!/usr/bin/env python3

import sys
import os
import argparse

# Use the current development version of SkoolKit
SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
	sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
	sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
	sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
	sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.image import ImageWriter
from skoolkit.snapshot import get_snapshot
from skoolkit.graphics import Udg as BaseUdg, Frame

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOBBIT_Z80 = '{}/HobbitThe.z80'.format(parent_dir)


class Hobbit:
	def __init__(self, snapshot):
		self.snapshot = snapshot
		self._snapshots = []

	def push_snapshot(self):
		self._snapshots.append(self.snapshot[:])

	def pop_snapshot(self):
		self.snapshot = self._snapshots.pop()

	def get_location_address(self, location):
		address = 0xCC00
		while self.snapshot[address] != 0xFF:
			if self.snapshot[address] == int(location):
				return self.snapshot[address + 0x02] * 0x100 + self.snapshot[address + 0x01]
			address += 0x03
		return False

	def get_location(self, location, x, y, w, h):
		address = self.get_location_address(location)
		for row in range(y, y + h):
			for col in range(x, x + w):
				print()


def run(snafile, location, imgfname, options):
	snapshot = get_snapshot(snafile)
	game = Hobbit(snapshot)
	x = y = 0
	width, height = 256, 42

	if options.geometry:
		wh, xy = options.geometry.split('+', 1)
		width, height = [int(n) for n in wh.split('x')]
		x, y = [int(n) for n in xy.split('+')]

	for spec in options.pokes:
		addr, val = spec.split(',', 1)
		step = 1
		if '-' in addr:
			addr1, addr2 = addr.split('-', 1)
			addr1 = int(addr1)
			if '-' in addr2:
				addr2, step = [int(i) for i in addr2.split('-', 1)]
			else:
				addr2 = int(addr2)
		else:
			addr1 = int(addr)
			addr2 = addr1
		addr2 += 1
		value = int(val)
		for a in range(addr1, addr2, step):
			snapshot[a] = value

	udg_array = game.get_location(location, x, y, width, height)
	frame = Frame(udg_array, options.scale)
	image_writer = ImageWriter()
	with open(imgfname, "wb") as f:
		image_writer.write_image([frame], f)


###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
	usage='hobbitimages.py [options] LOCATION_ID FILE.png',
	description="Create an image of the location drawings from The Hobbit (v1.2).",
	formatter_class=argparse.RawTextHelpFormatter,
	add_help=False
)
parser.add_argument('location', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('imgfname', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-g', dest='geometry', metavar='WxH+X+Y', help='Create the image with this geometry')
group.add_argument('-p', dest='pokes', metavar='A[-B[-C]],V', action='append', default=[],
				   help="Do POKE N,V for N in {A, A+C, A+2C,...B} (this option may\n"
						"be used multiple times)")
group.add_argument('-s', dest='scale', type=int, default=2, help='Set the scale of the image (default: 2)')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.location or not namespace.imgfname:
	parser.exit(2, parser.format_help())
run(HOBBIT_Z80, namespace.location, namespace.imgfname, namespace)
