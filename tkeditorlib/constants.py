#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 11:34:11 2018

@author: juliette
"""
import os
from screeninfo import get_monitors
from pygments import token
from pygments.styles.monokai import MonokaiStyle

IMG_PATH = os.path.join(os.path.dirname(__file__), 'images')

IM_CLASS = os.path.join(IMG_PATH, 'c.png')
IM_FCT = os.path.join(IMG_PATH, 'f.png')
IM_HFCT = os.path.join(IMG_PATH, 'hf.png')
IM_SEP = os.path.join(IMG_PATH, 'sep.png')
IM_WARN = os.path.join(IMG_PATH, 'warning.png')
IM_ERR = os.path.join(IMG_PATH, 'error.png')
IM_CLOSE = os.path.join(IMG_PATH, 'close.png')
ICON = os.path.join(IMG_PATH, 'icon.png')


SYNTAX_HIGHLIGHTING = {
    'Token.Text': dict(foreground='black', font="DejaVu\ Sans\ Mono 10"),
    'Token.Punctuation': dict(foreground='#9A0800', font="DejaVu\ Sans\ Mono 10"),
    'Token.Name': dict(foreground='black', font="DejaVu\ Sans\ Mono 10"),
    'Token.Name.Decorator': dict(foreground='#2675C3', font="DejaVu\ Sans\ Mono 10 italic"),
    'Token.Name.Exception': dict(foreground='#3089E3', font="DejaVu\ Sans\ Mono 10"),
    'Token.Name.Class': dict(foreground='#00804B', font="DejaVu\ Sans\ Mono 10 bold"),
    'Token.Name.Function': dict(foreground='dark orange', font="DejaVu\ Sans\ Mono 10 bold"),
    'Token.Name.Builtin': dict(foreground='#3089E3', font="DejaVu\ Sans\ Mono 10 "),
    'Token.Name.Builtin.Pseudo': dict(foreground='#3089E3', font="DejaVu\ Sans\ Mono 10 italic"),
    'Token.Keyword': dict(foreground='#000257', font="DejaVu\ Sans\ Mono 10 bold"),
    'Token.Literal.String': dict(foreground='#E32000', font="DejaVu\ Sans\ Mono 10"),
    'Token.Literal.Number': dict(foreground='#007502', font="DejaVu\ Sans\ Mono 10"),
    'Token.Comment': dict(foreground='blue', font="DejaVu\ Sans\ Mono 10 italic"),
    'Token.Comment.Hashbang': dict(foreground='blue', font="DejaVu\ Sans\ Mono 10 bold italic"),
    'Token.Operator': dict(foreground='#9A0800', font="DejaVu\ Sans\ Mono 10"),
    'Token.Operator.Word': dict(foreground='#000257', font="DejaVu\ Sans\ Mono 10 bold"),
}


def get_screen(x, y):
    monitors = [(m.x, m.y, m.x + m.width, m.y + m.height) for m in get_monitors()]
    i = 0
    while (i < len(monitors) and
           not (monitors[i][0] <= x <= monitors[i][2]
                and monitors[i][1] <= y <= monitors[i][3])):
        i += 1
    if i == len(monitors):
        raise ValueError("(%i, %i) is out of screen" % (x, y))
    else:
        return monitors[i]
