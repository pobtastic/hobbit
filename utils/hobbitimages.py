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

HOBBIT_HOME = os.environ.get('HOBBIT_HOME')
if not HOBBIT_HOME:
    sys.stderr.write('HOBBIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(HOBBIT_HOME):
    sys.stderr.write('HOBBIT_HOME={}; directory not found\n'.format(HOBBIT_HOME))
    sys.exit(1)
sys.path.insert(0, '{}/sources'.format(HOBBIT_HOME))

from skoolkit.image import ImageWriter
from skoolkit.snapshot import get_snapshot
from skoolkit.graphics import Udg, Frame


class Hobbit:
    def __init__(self, snapshot):
        self.address = 0x0000
        self.ink = 0x00
        self.paper = 0x00
        self.snapshot = snapshot
        self._snapshots = []

    def push_snapshot(self):
        self._snapshots.append(self.snapshot[:])

    def pop_snapshot(self):
        self.snapshot = self._snapshots.pop()

    def set_location_address(self, location):
        """Sets the memory address for the
        given location ID.
        """
        self.address = self.get_location_address(location)
        if self.address is False:
            raise ValueError('No location found with ID {}'.format(location))

    def get_location_address(self, location):
        """Returns the memory address from
        a given location ID.
        """
        address = 0xCC00
        while self.snapshot[address] != 0xFF:
            if self.snapshot[address] == int(location):
                return self.snapshot[address + 0x02] * 0x100 + self.snapshot[address + 0x01]
            address += 0x03
        return False

    def set_colours(self):
        """The first byte relates to the
        paper and ink colours.
        """
        self.ink = (self.snapshot[self.address] >> 3) & 7
        self.paper = self.snapshot[self.address] & 7
        self.address += 0x01

    def areaFill(self, x, y, c):
        print([x, y, c])

    def drawLine(self, x, y, c, d, n, m):
        print([x, y, c, d, n, m])

    def drawPixel(self, x, y, c):
        print([x, y, c])

    def paintBackground(self, a, c, d, n):
        print([a, c, d, n])

    def draw(self):
        x = y = c = 0
        play_area_udgs = []
        addr = 0x4000
        for row in range(0x05):
            play_area_udgs.append([])
            for col in range(0x20):
                play_area_udgs[-1].append(Udg(self.paper, self.snapshot[addr+(row*col):addr+(row*col)+0x20]))
        while True:
            action = self.snapshot[self.address]
            # Move to X/ Y co-ordinates.
            if action == 0x08:
                self.address += 0x01
                x = self.snapshot[self.address]
                self.address += 0x01
                y = 0x7F - self.snapshot[self.address]
                self.drawPixel(x, y, c)
            # Draw line segment.
            elif action > 0x7F:
                self.drawLine(
                    x, y, c,
                    (action & 0x07),
                    (self.snapshot[self.address] & 0x3F),
                    (((action & 0x78) >> 0x01) + ((self.snapshot[self.address] & 0xC0) >> 0x06)))
            # Fill area.
            elif action > 0x3F:
                self.areaFill(x, y, c)
                self.address += 0x02
            # Paint background:
            elif action > 0x1F:
                h, l = self.snapshot[self.address + 0x01], self.snapshot[self.address + 0x02]
                a = (h * 0x100 + l) - 0x5800
                self.address += 0x03
                while True:
                    d = self.snapshot[self.address]
                    if d == 0xFF:
                        break
                    a = self.paintBackground(a, action & 0x07, d & 0x03, (d & 0xFC) >> 2)
                    self.address += 0x01
            # Exit.
            elif action == 0x00:
                break

            self.address += 0x01
        return play_area_udgs


def _do_pokes(specs, snapshot):
    for spec in specs:
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


def run(location, imgfname, options):
    snapshot = get_snapshot('{}/HobbitThe.z80'.format(HOBBIT_HOME))
    _do_pokes(options.pokes, snapshot)
    game = Hobbit(snapshot)

    game.set_location_address(location)
    game.set_colours()
    udg_array = game.draw()

    if options.geometry:
        wh, xy = options.geometry.split('+', 1)
        width, height = [int(n) for n in wh.split('x')]
        x, y = [int(n) for n in xy.split('+')]
        udg_array = [row[x:x + width] for row in udg_array[y:y + height]]

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
run(namespace.location, namespace.imgfname, namespace)
