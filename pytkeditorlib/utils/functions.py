# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2020 Juliette Monsel <j_4321 at protonmail dot com>

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


Functions
"""
import os
from os.path import sep, isdir, basename
from glob import glob

from pygments.styles import get_style_by_name
from Xlib import display
from Xlib.ext.xinerama import query_screens

from .constants import CONFIG


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
    d = display.Display()
    screens = query_screens(d).screens
    monitors = [(m.x, m.y, m.x + m.width, m.y + m.height) for m in screens]
    i = 0
    while (i < len(monitors)
           and not (monitors[i][0] <= x <= monitors[i][2]
                    and monitors[i][1] <= y <= monitors[i][3])):
        i += 1
    if i == len(monitors):
        raise ValueError("(%i, %i) is out of screen" % (x, y))
    else:
        return monitors[i]


def valide_entree_nb(d, S):
    """ commande de validation des champs devant contenir
        seulement des chiffres """
    if d == '1':
        return S.isdigit()
    else:
        return True

# --- path autocompletion
class PathCompletion:
    def __init__(self, before_completion, after_completion):
        """
        Completion object for paths.

        Arguments:
            * before_completion: path before completion
            * after_completion: path after completion
        """
        self.complete = after_completion[len(before_completion):] + sep * isdir(after_completion)
        if after_completion[-1] == sep:
            after_completion = after_completion[:-1]
        self.name = basename(after_completion)


def glob_rel(pattern, locdir=None):
    if locdir is None:
        return glob(pattern)
    else:
        cwd = os.getcwd()
        os.chdir(locdir)
        res = glob(pattern)
        os.chdir(cwd)
        return res
