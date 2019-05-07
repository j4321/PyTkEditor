#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 18 13:33:14 2018

@author: juliette
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


def copen(filename=None):
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
    shell.interact(banner='')


if __name__ == '__main__':
    copen(argv[1])
