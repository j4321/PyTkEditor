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
from os import getcwd, chdir
from os.path import sep, isdir, basename
from glob import glob
import re

from pygments.styles import get_style_by_name
from Xlib import display
from Xlib.ext.xinerama import query_screens

from .constants import CONFIG, MAGIC_COMMANDS


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


# --- autocompletion

class CompletionObj:
    """Dummy completion object for compatibility with jedi output."""

    def __init__(self, name, complete):
        self.name = name
        self.complete = complete


def magic_complete(string):
    if not string or not string[0] == '%':
        return []
    comp = []
    string = string[1:]
    l = len(string)
    for cmd in MAGIC_COMMANDS:
        if cmd.startswith(string):
            comp.append(CompletionObj('%' + cmd, cmd[l:]))
    return comp


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


def glob_rel(pattern, locdir):
    cwd = getcwd()
    chdir(locdir)
    paths = glob(pattern)
    chdir(cwd)
    return paths


# --- long output formatter
INDENT_REGEXP = re.compile(r" *")
TAIL_REGEXP = re.compile(r"[\n ]*$")
SPLITTER_REGEXP = re.compile(r',(?!(?:[^\(]*\)|[^\[]*\]|[^\{]*\})) ?')
OPEN_CHAR = {"}": "{", "]": "[", ")": "("}
CLOSE_CHAR = {"{": "}", "(": ")", "[": "]"}


def find_closing_bracket(text, open_char, open_index):
    close_char = CLOSE_CHAR[open_char]
    index = open_index + 1
    close_index = text.find(close_char, index)
    stack = 1
    while stack > 0 and close_index > 0:
        stack += text.count(open_char, index, close_index) - 1
        index = close_index + 1
        close_index = text.find(close_char, index)
    if stack == 0:
        return index - 1
    else:
        return -1


def format_long_output(output, wrap_length):
    if len(output) <= wrap_length:
        return output
    indent = INDENT_REGEXP.match(output).group()
    tail = TAIL_REGEXP.search(output).group()

    if tail:
        text = output[len(indent):-len(tail)]
    else:
        text = output[len(indent):]
    if text[0] in CLOSE_CHAR:
        close = find_closing_bracket(text, text[0], 0)
        if close == len(text) - 1:
            content = SPLITTER_REGEXP.split(text[1:-1])
            if len(content) > 1:
                return f"{indent}{text[0]}{content[0]},\n{indent} " + f",\n{indent} ".join(content[1:]) + text[-1] + tail
    return output


# --- ANSI format parser
ANSI_COLORS_DARK = ['black', 'red', 'green', 'yellow', 'royal blue', 'magenta',
                    'cyan', 'light gray']
ANSI_COLORS_LIGHT = ['dark gray', 'tomato', 'light green', 'light goldenrod', 'light blue',
                     'pink', 'light cyan', 'white']
ANSI_FORMAT = {0: 'reset',
               1: 'bold',
               3: 'italic',
               4: 'underline',
               9: 'overstrike',
               #~21: 'reset bold',
               #~23: 'reset italic',
               #~24: 'reset underline',
               #~29: 'reset overstrike',
               39: 'foreground default',
               49: 'background default'}

for i in range(8):
    ANSI_FORMAT[30 + i] = 'foreground ' + ANSI_COLORS_DARK[i]
    ANSI_FORMAT[90 + i] = 'foreground ' + ANSI_COLORS_LIGHT[i]
    ANSI_FORMAT[40 + i] = 'background ' + ANSI_COLORS_DARK[i]
    ANSI_FORMAT[100 + i] = 'background ' + ANSI_COLORS_LIGHT[i]


ANSI_REGEXP = re.compile(r"\x1b\[((\d+;)*\d+)m")


def parse_ansi(text, line_offset=1):
    """
    Parse ANSI formatting in text.

    Return a dictionary of tag ranges (for a tkinter Text widget)
    and the text stripped from the ANSI escape sequences.
    """
    res = []
    lines = text.splitlines()
    for l, line in enumerate(lines, line_offset):
        delta = 0
        for match in ANSI_REGEXP.finditer(line):
            codes = [int(c) for c in match.groups()[0].split(';')]
            start, end = match.span()
            res.append(((l, start - delta), codes))
            delta += end - start
    stripped_text = ANSI_REGEXP.sub('', text)
    tag_ranges = {}
    opened_tags = []
    for pos, codes in res:
        for code in codes:
            if code == 0:
                for tag in opened_tags:
                    tag_ranges[tag].append('%i.%i' % pos)
                opened_tags.clear()
            else:
                tag = ANSI_FORMAT[code]
                if tag not in tag_ranges:
                    tag_ranges[tag] = []
                tag_ranges[tag].append('%i.%i' % pos)
                opened_tags.append(tag)
    for tag in opened_tags:
        tag_ranges[tag].append('end')

    return tag_ranges, stripped_text
