#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 11:34:11 2018

@author: juliette
"""
import os
from screeninfo import get_monitors
from pygments.styles import get_style_by_name
from jedi import settings
import hashlib
from Crypto.Cipher import AES


settings.case_insensitive_completion = False

PATH = os.path.dirname(__file__)
IMG_PATH = os.path.join(PATH, 'images')

IM_CLASS = os.path.join(IMG_PATH, 'c.png')
IM_FCT = os.path.join(IMG_PATH, 'f.png')
IM_HFCT = os.path.join(IMG_PATH, 'hf.png')
IM_SEP = os.path.join(IMG_PATH, 'sep.png')
IM_WARN = os.path.join(IMG_PATH, 'warning.png')
IM_ERR = os.path.join(IMG_PATH, 'error.png')
IM_CLOSE = os.path.join(IMG_PATH, 'close.png')
ICON = os.path.join(IMG_PATH, 'icon.png')

FONT = ("DejaVu Sans Mono", 10)

EDITOR_STYLE = 'persolight'
CONSOLE_STYLE = 'perso'

if os.access(PATH, os.W_OK):
    LOCAL_PATH = os.path.join(PATH, 'config')
else:
    LOCAL_PATH = os.path.join(os.path.expanduser('~'), '.tkeditor')

if not os.path.exists(LOCAL_PATH):
    os.mkdir(LOCAL_PATH)


def load_style(stylename):
    s = get_style_by_name(stylename)
    style = s.list_styles()
    style_dic = {}
    for token, opts in style:
        name = str(token)
        style_dic[name] = {}
        fg = opts['color']
        bg = opts['bgcolor']
        if fg:
            style_dic[name]['foreground'] = '#' + fg
        if bg:
            style_dic[name]['background'] = '#' + bg
        font = FONT + tuple(key for key in ('bold', 'italic') if opts[key])
        style_dic[name]['font'] = font
        style_dic[name]['underline'] = opts['underline']
    return s.background_color, s.highlight_color, style_dic


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


CONSOLE_BG, CONSOLE_HIGHLIGHT_BG, CONSOLE_SYNTAX_HIGHLIGHTING = load_style(CONSOLE_STYLE)
CONSOLE_FG = CONSOLE_SYNTAX_HIGHLIGHTING.get('Token.Name', {}).get('foreground', 'black')

EDITOR_BG, EDITOR_HIGHLIGHT_BG, EDITOR_SYNTAX_HIGHLIGHTING = load_style(EDITOR_STYLE)
EDITOR_FG = EDITOR_SYNTAX_HIGHLIGHTING.get('Token.Name', {}).get('foreground', 'black')

PWD_FILE = os.path.join(LOCAL_PATH, '.pwd')
IV_FILE = os.path.join(LOCAL_PATH, '.iv')


def decrypt(msg, pwd, iv):
    """Returns the login and password for the mailbox that where encrypted using pwd."""
    key = hashlib.sha256(pwd.encode()).digest()
    cipher = AES.new(key, AES.MODE_CFB, iv)
    return cipher.decrypt(msg).decode()


def encrypt(msg, pwd, iv):
    """Encrypt the mailbox connection information using pwd."""
    key = hashlib.sha256(pwd.encode()).digest()
    cipher = AES.new(key, AES.MODE_CFB, iv)
    return cipher.encrypt(msg)
