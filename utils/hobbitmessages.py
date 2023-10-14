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

from skoolkit.snapshot import get_snapshot


class Hobbit:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self._snapshots = []

    def push_snapshot(self):
        self._snapshots.append(self.snapshot[:])

    def pop_snapshot(self):
        self.snapshot = self._snapshots.pop()

    def get_text_message(self, address):
        addr = int(address)
        while True:
            byte = self.snapshot[addr]
            print(byte)
            if not byte & (1 << 7):
                if byte < 32:
                    word_table = 29333 + byte * 2
                    word = self.snapshot[word_table] + self.snapshot[word_table + 1] * 256
                    print(chr(word))
                if byte > 96:
                    self.get_common_word(byte)
            else:
                byte &= 127
                print(hex(byte))
            if (self.snapshot[addr] & (1 << 7)) > 96:
                break
            addr += 1

    def get_common_word(self, byte):
        byte -= 96
        ptr = 44349 + byte * 2
        common_word = (80 + self.snapshot[ptr + 1]) & 15
        common_word_ptr = 24576 + self.snapshot[ptr] + common_word * 256
        text = []
        while True:
            letter = self.snapshot[common_word_ptr]
            print(chr(letter))
            if letter & 31:
                print("break")
                break
            text.append(letter + 96)
            common_word_ptr += 1
        print(text)


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


def run(address, options):
    snapshot = get_snapshot('{}/HobbitThe.z80'.format(HOBBIT_HOME))
    _do_pokes(options.pokes, snapshot)
    game = Hobbit(snapshot)
    game.get_text_message(address)


###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage='hobbitmessages.py [options] 44991',
    description="Tests the messaging system in The Hobbit v1.2.",
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False
)
parser.add_argument('address', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-p', dest='pokes', metavar='A[-B[-C]],V', action='append', default=[],
                   help="Do POKE N,V for N in {A, A+C, A+2C,...B} (this option may\n"
                        "be used multiple times)")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.address:
    parser.exit(2, parser.format_help())
run(namespace.address, namespace)
