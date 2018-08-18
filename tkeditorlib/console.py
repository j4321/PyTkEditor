#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 18 13:33:14 2018

@author: juliette
"""

import code
import readline
import rlcompleter
from sys import argv

def copen(filename):
    """Opens interactive console and execute the content of filename"""
    context = globals().copy()
    readline.set_completer(rlcompleter.Completer(context).complete)
    readline.parse_and_bind("tab: complete")
    shell = code.InteractiveConsole(context)
    with open(filename) as f:
        cmds = f.read()
    shell.runcode(cmds)
    shell.interact(banner='')

if __name__ == '__main__':
    copen(argv[1])
