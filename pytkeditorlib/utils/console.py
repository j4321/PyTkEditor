#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2019 Juliette Monsel <j_4321 at protonmail dot com>

PyTkEditor is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PyTkEditor is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Python console to run files
"""

import code
import os
import readline
import rlcompleter
from sys import argv


START = """
import os
os.chdir('{path}')
import sys
sys.path.remove(os.path.dirname(__file__))
sys.path.insert(0, '')
"""


def copen(filename=None, interactive='True'):
    """Opens interactive console and execute the content of filename"""
    context = globals().copy()
    readline.set_completer(rlcompleter.Completer(context).complete)
    readline.parse_and_bind("tab: complete")
    shell = code.InteractiveConsole(context)
    if filename:
        with open(filename) as f:
            cmds = f.read()
        shell.runcode(START.format(path=os.path.dirname(filename)))
        shell.runcode(cmds)
    if interactive == 'True':
        shell.interact(banner='')
    else:
        txt = 'Press return to close window'
        print(f'\n{"-" * len(txt)}\n{txt}')
        input('')


if __name__ == '__main__':
    copen(*argv[1:])
