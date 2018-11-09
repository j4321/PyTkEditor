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
import configparser
from pygments.lexers import Python3Lexer
from pygments.token import Comment
settings.case_insensitive_completion = False


class MyLexer(Python3Lexer):
    tokens = Python3Lexer.tokens.copy()
    tokens['root'].insert(5, (r'^# *In\[.*\].*$', Comment.Cell))


PYTHON_LEX = MyLexer()

PATH = os.path.dirname(__file__)
CSS_PATH = os.path.join(PATH, 'html', '{theme}.css')
TEMPLATE_PATH = os.path.join(PATH, 'html', 'template.txt')
IMG_PATH = os.path.join(PATH, 'images')

IM_CLASS = os.path.join(IMG_PATH, 'c.png')
IM_FCT = os.path.join(IMG_PATH, 'f.png')
IM_HFCT = os.path.join(IMG_PATH, 'hf.png')
IM_SEP = os.path.join(IMG_PATH, 'sep.png')
IM_CELL = os.path.join(IMG_PATH, 'cell.png')
IM_WARN = os.path.join(IMG_PATH, 'warning.png')
IM_ERR = os.path.join(IMG_PATH, 'error.png')
IM_RUN = os.path.join(IMG_PATH, 'run.png')
IM_NEW = os.path.join(IMG_PATH, 'new.png')
IM_OPEN = os.path.join(IMG_PATH, 'open.png')
IM_REOPEN = os.path.join(IMG_PATH, 'reopen.png')
IM_SAVE = os.path.join(IMG_PATH, 'save.png')
IM_SAVEAS = os.path.join(IMG_PATH, 'saveas.png')
IM_SAVEALL = os.path.join(IMG_PATH, 'saveall.png')
IM_RECENTS = os.path.join(IMG_PATH, 'recents.png')
IM_UNDO = os.path.join(IMG_PATH, 'undo.png')
IM_REDO = os.path.join(IMG_PATH, 'redo.png')
IM_QUIT = os.path.join(IMG_PATH, 'quit.png')
IM_FIND = os.path.join(IMG_PATH, 'find.png')
IM_REPLACE = os.path.join(IMG_PATH, 'replace.png')
IM_SETTINGS = os.path.join(IMG_PATH, 'settings.png')
IM_CLOSE = os.path.join(IMG_PATH, 'close_{theme}.png')
ICON = os.path.join(IMG_PATH, 'icon.png')

if os.access(PATH, os.W_OK):
    LOCAL_PATH = os.path.join(PATH, 'config')
else:
    LOCAL_PATH = os.path.join(os.path.expanduser('~'), '.tkeditor')

if not os.path.exists(LOCAL_PATH):
    os.mkdir(LOCAL_PATH)

HISTFILE = os.path.join(LOCAL_PATH, 'tkeditor.history')
CONFIG_PATH = os.path.join(LOCAL_PATH, 'tkeditor.ini')

# --- ssl
SERVER_CERT = os.path.join(PATH, 'ssl', 'server.crt')
CLIENT_CERT = os.path.join(PATH, 'ssl', 'client.crt')

# --- config
CONFIG = configparser.ConfigParser()

if not CONFIG.read(CONFIG_PATH):
    CONFIG.add_section('General')
    CONFIG.set('General', 'theme', "light")
    CONFIG.set('General', 'fontfamily', "DejaVu Sans Mono")
    CONFIG.set('General', 'fontsize', "10")
    CONFIG.set('General', 'opened_files', "")
    CONFIG.set('General', 'recent_files', "")
    CONFIG.add_section('Editor')
    CONFIG.set('Editor', 'style', "colorful")
    CONFIG.add_section('Console')
    CONFIG.set('Console', 'style', "monokai")
    CONFIG.add_section('Dark Theme')
    CONFIG.set('Dark Theme', 'bg', '#454545')
    CONFIG.set('Dark Theme', 'activebg', '#525252')
    CONFIG.set('Dark Theme', 'pressedbg', '#262626')
    CONFIG.set('Dark Theme', 'fg', '#E6E6E6')
    CONFIG.set('Dark Theme', 'fieldbg', '#303030')
    CONFIG.set('Dark Theme', 'lightcolor', '#454545')
    CONFIG.set('Dark Theme', 'darkcolor', '#454545')
    CONFIG.set('Dark Theme', 'bordercolor', '#131313')
    CONFIG.set('Dark Theme', 'focusbordercolor', '#353535')
    CONFIG.set('Dark Theme', 'selectbg', '#1f1f1f')
    CONFIG.set('Dark Theme', 'selectfg', '#E6E6E6')
    CONFIG.set('Dark Theme', 'unselectedfg', '#999999')
    CONFIG.set('Dark Theme', 'disabledfg', '#666666')
    CONFIG.set('Dark Theme', 'disabledbg', '#454545')
    CONFIG.set('Dark Theme', 'tooltip_bg', '#131313')
    CONFIG.add_section('Light Theme')
    CONFIG.set('Light Theme', 'bg', '#dddddd')
    CONFIG.set('Light Theme', 'activebg', '#efefef')
    CONFIG.set('Light Theme', 'pressedbg', '#c1c1c1')
    CONFIG.set('Light Theme', 'fg', 'black')
    CONFIG.set('Light Theme', 'fieldbg', 'white')
    CONFIG.set('Light Theme', 'lightcolor', '#ededed')
    CONFIG.set('Light Theme', 'darkcolor', '#cfcdc8')
    CONFIG.set('Light Theme', 'bordercolor', '#888888')
    CONFIG.set('Light Theme', 'focusbordercolor', '#5E5E5E')
    CONFIG.set('Light Theme', 'selectbg', '#c1c1c1')
    CONFIG.set('Light Theme', 'selectfg', 'black')
    CONFIG.set('Light Theme', 'unselectedfg', '#666666')
    CONFIG.set('Light Theme', 'disabledfg', '#999999')
    CONFIG.set('Light Theme', 'disabledbg', '#dddddd')
    CONFIG.set('Light Theme', 'tooltip_bg', 'light yellow')


def save_config():
    with open(CONFIG_PATH, 'w') as f:
        CONFIG.write(f)


# --- style
def load_style(stylename):
    s = get_style_by_name(stylename)
    style = s.list_styles()
    style_dic = {}
    FONT = (CONFIG.get("General", "fontfamily"),
            CONFIG.getint("General", "fontsize"))
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


# --- screen size
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
