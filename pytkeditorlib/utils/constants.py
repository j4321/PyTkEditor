# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2020 Juliette Monsel <j_4321 at protonmail dot com>

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


Constants
"""
from os import getcwd, chdir
from os.path import sep, isdir, basename
import os
import configparser
from glob import glob
import re
import logging
from logging.handlers import TimedRotatingFileHandler

import warnings
from jedi import settings
from pygments.lexers import Python3Lexer
from pygments.token import Comment
from pygments.styles import get_style_by_name
from Xlib import display
from Xlib.ext.xinerama import query_screens

settings.case_insensitive_completion = False
os.environ['PYFLAKES_BUILTINS'] = '_'

APP_NAME = 'PyTkEditor'
REPORT_URL = f"https://gitlab.com/j_4321/{APP_NAME}/issues"


class MyLexer(Python3Lexer):
    tokens = Python3Lexer.tokens.copy()
    tokens['root'].insert(5, (r'^#( In\[.*\]| ?%%).*$', Comment.Cell))


PYTHON_LEX = MyLexer()


# --- paths
PATH = os.path.dirname(os.path.dirname(__file__))

if os.access(PATH, os.W_OK) and os.path.exists(os.path.join(PATH, "images")):
    # the app is not installed
    # local directory containing config files
    LOCAL_PATH = os.path.join(PATH, 'config')
    # PATH_LOCALE = os.path.join(PATH, "locale")
    PATH_DOC = os.path.join(PATH, 'doc', "DOC.rst")
    PATH_HTML = os.path.join(PATH, 'html')
    PATH_SSL = os.path.join(PATH, 'ssl')
    PATH_IMG = os.path.join(PATH, 'images')
else:
    # local directory containing config files
    LOCAL_PATH = os.path.join(os.path.expanduser("~"), ".pytkeditor")
    # PATH_LOCALE = "/usr/share/locale"
    PATH_DOC = "/usr/share/doc/pytkeditor/DOC.rst"
    PATH_HTML = "/usr/share/pytkeditor/html"
    PATH_SSL = "/usr/share/pytkeditor/ssl"
    PATH_IMG = "/usr/share/pytkeditor/images"

if not os.path.exists(LOCAL_PATH):
    os.mkdir(LOCAL_PATH)

CSS_PATH = os.path.join(PATH_HTML, '{theme}.css')
TEMPLATE_PATH = os.path.join(PATH_HTML, 'template.txt')
HISTFILE = os.path.join(LOCAL_PATH, 'pytkeditor.history')
PATH_CONFIG = os.path.join(LOCAL_PATH, 'pytkeditor.ini')
PATH_LOG = os.path.join(LOCAL_PATH, 'pytkeditor.log')
PIDFILE = os.path.join(LOCAL_PATH, "pytkeditor.pid")
OPENFILE_PATH = os.path.join(LOCAL_PATH, ".file")
PATH_TEMPLATE = os.path.join(LOCAL_PATH, 'new_file_template.py')

if not os.path.exists(PATH_TEMPLATE):
    with open(PATH_TEMPLATE, 'w') as file:
        file.write('# -*- coding: utf-8 -*-\n"""\nCreated on {date} by {author}\n"""\n')

# --- jupyter qtconsole
JUPYTER_KERNEL_PATH = os.path.join(LOCAL_PATH, "kernel.json")

try:
    import qtconsole  # to test whether the qtconsole is installed
except ImportError:
    JUPYTER = False
else:
    from jupyter_client.connect import ConnectionFileMixin
    from jupyter_client import BlockingKernelClient, find_connection_file
    from jupyter_core.paths import jupyter_runtime_dir
    JUPYTER = True
JUPYTER_ICON = os.path.join(PATH_IMG, 'JupyterConsole.svg')

# --- images
IMAGES = {}
for img in os.listdir(PATH_IMG):
    name, ext = os.path.splitext(img)
    if ext == '.png':
        IMAGES[name] = os.path.join(PATH_IMG, img)

IM_CLOSE = os.path.join(PATH_IMG, 'close_{theme}.png')
IM_SELECTED = os.path.join(PATH_IMG, 'selected_{theme}.png')
ANIM_LOADING = [os.path.join(PATH_IMG, 'animation', file)
                for file in os.listdir(os.path.join(PATH_IMG, 'animation'))]
ANIM_LOADING.sort()

# --- log
handler = TimedRotatingFileHandler(PATH_LOG, when='midnight',
                                   interval=1, backupCount=7)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)s: %(message)s',
                    handlers=[handler])
logging.getLogger().addHandler(logging.StreamHandler())


def customwarn(message, category, filename, lineno, file=None, line=None):
    """Redirect warnings to log"""
    logging.warn(warnings.formatwarning(message, category, filename, lineno))


warnings.showwarning = customwarn


# --- ssl
SERVER_CERT = os.path.join(PATH_SSL, 'server.crt')
CLIENT_CERT = os.path.join(PATH_SSL, 'client.crt')

# --- config
CONFIG = configparser.ConfigParser()

external_consoles = ['guake', 'tilda', 'terminator', 'yakuake', 'konsole',
                     'xfce4-terminal', 'lxterminal', 'gnome-terminal', 'xterm']

i = 0
while i < len(external_consoles) and not os.path.exists(os.path.join('/usr', 'bin', external_consoles[i])):
    print(os.path.join('/usr', 'bin', external_consoles[i]))
    i += 1

if i < len(external_consoles):
    external_console = f"{external_consoles[i]} -e"
else:
    external_console = ''

if not CONFIG.read(PATH_CONFIG):
    CONFIG.add_section('General')
    CONFIG.set('General', 'theme', "light")
    CONFIG.set('General', 'fontfamily', "DejaVu Sans Mono")
    CONFIG.set('General', 'fontsize', "10")
    CONFIG.set('General', 'opened_files', "")
    CONFIG.set('General', 'recent_files', "")
    CONFIG.set('General', 'layout', "horizontal")
    CONFIG.set('General', 'fullscreen', "False")
    CONFIG.add_section('Layout')
    CONFIG.set('Layout', 'horizontal', "0.16 0.65")
    CONFIG.set('Layout', 'horizontal2', "0.65")
    CONFIG.set('Layout', 'vertical', "0.65")
    CONFIG.set('Layout', 'pvertical', "0.16 0.6")
    CONFIG.add_section('Editor')
    CONFIG.set('Editor', 'style', "colorful")
    CONFIG.set('Editor', 'code_check', "True")
    CONFIG.set('Editor', 'style_check', "True")
    CONFIG.set('Editor', 'matching_brackets', '#00B100;;bold')  # fg;bg;font formatting
    CONFIG.set('Editor', 'unmatched_bracket', '#FF0000;;bold')  # fg;bg;font formatting
    CONFIG.set('Editor', 'comment_marker', '~')
    CONFIG.add_section('Code structure')
    CONFIG.set('Code structure', 'visible', "True")
    CONFIG.add_section('Console')
    CONFIG.set('Console', 'style', "monokai")
    CONFIG.set('Console', 'visible', "True")
    CONFIG.set('Console', 'order', "0")
    CONFIG.set('Console', 'matching_brackets', '#00B100;;bold')  # fg;bg;font formatting
    CONFIG.set('Console', 'unmatched_bracket', '#FF0000;;bold')  # fg;bg;font formatting
    CONFIG.add_section('History')
    CONFIG.set('History', 'max_size', "10000")
    CONFIG.set('History', 'visible', "True")
    CONFIG.set('History', 'order', "1")
    CONFIG.add_section('Help')
    CONFIG.set('Help', 'visible', "True")
    CONFIG.set('Help', 'order', "2")
    CONFIG.add_section('File browser')
    CONFIG.set('File browser', 'filename_filter', "README, INSTALL, LICENSE, CHANGELOG, *.npy, *.npz, *.csv, *.txt, *.jpg, *.png, *.gif, *.tif, *.pkl, *.pickle, *.json, *.py, *.ipynb, *.txt, *.rst, *.md, *.dat, *.pdf, *.png, *.svg, *.eps")
    CONFIG.set('File browser', 'visible', "True")
    CONFIG.set('File browser', 'order', "3")
    CONFIG.add_section('Run')
    CONFIG.set('Run', 'console', "external")
    CONFIG.set('Run', 'external_interactive', "True")
    CONFIG.set('Run', 'external_console', external_console)
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
    CONFIG.set('Dark Theme', 'textselectbg', '#4a6984')
    CONFIG.set('Dark Theme', 'textselectfg', 'white')
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
    CONFIG.set('Light Theme', 'textselectbg', '#4a6984')
    CONFIG.set('Light Theme', 'textselectfg', 'white')
    CONFIG.set('Light Theme', 'unselectedfg', '#666666')
    CONFIG.set('Light Theme', 'disabledfg', '#999999')
    CONFIG.set('Light Theme', 'disabledbg', '#dddddd')
    CONFIG.set('Light Theme', 'tooltip_bg', 'light yellow')


def save_config():
    with open(PATH_CONFIG, 'w') as f:
        CONFIG.write(f)


CONFIG.save = save_config


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


# --- console
MAGIC_COMMANDS = ['run', 'gui', 'pylab', 'magic', 'logstart', 'logstop',
                  'logstate', 'timeit']
EXTERNAL_COMMANDS = ['ls', 'cat', 'mv', 'rm', 'rmdir', 'cp', 'mkdir', 'pwd']
CONSOLE_HELP = f"""
Interactive Python Console
==========================

Graphical python interpreter with special commands, command history,
autocompletion and compatible with some shell commands.

Features
--------

* Magic commands: a few magic commands, in the spirit of IPython, are
  available, type %magic for details.

* External shell commands: {', '.join(EXTERNAL_COMMANDS)}

* Help on an object: type object? to print its docstring, or type object?? to
  display the full help (equivalent to help(object)).

* Autocompletion: hitting Tab will complete the text with available python
  commands or variable names and show a list of possibility if there is an
  ambiguity.

* History: navigate in the command history by using the up and down arrow
  keys, only the commands matching the text between the prompt and the
  cursor will be shown. The history is persistent between sessions and its
  length can be changed from PyTkEditor's settings.

* Syntax highlighting of the input code, the style can be changed from
  PyTkEditor's settings.

* Auto-closing of brackets and quotes.
"""

# --- --- long output formatter
INDENT_REGEXP = re.compile(r" *")
TAIL_REGEXP = re.compile(r"[\n ]*$")
SPLITTER_REGEXP = re.compile(r',(?!(?:[^\(]*\)|[^\[]*\]|[^\{]*\})) ?')
OPEN_CHAR = {"}": "{", "]": "[", ")": "("}
CLOSE_CHAR = {"{": "}", "(": ")", "[": "]"}
DICKEY_REGEXP = re.compile(r"^[^:]*:")


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


def format_long_output(output, wrap_length, head='', indent2=''):
    if len(output) <= wrap_length:
        return head + output
    indent1 = INDENT_REGEXP.match(output).group()
    tail = TAIL_REGEXP.search(output).group()

    if tail:
        text = output[len(indent1):-len(tail)]
    else:
        text = output[len(indent1):]
    if not head:
        indent2 = indent1 + indent2
        head = indent1
    if text[0] in CLOSE_CHAR:
        close = find_closing_bracket(text, text[0], 0)
        if close == len(text) - 1:
            content = SPLITTER_REGEXP.split(text[1:-1])
            if text[0] == '{':
                fcontent = []
                for c in content:
                    m = DICKEY_REGEXP.match(c)
                    if m:
                        h = m.group()
                    else:
                        h = ''
                    fcontent.append(format_long_output(c[len(h):], wrap_length - len(indent2) + 1, h, indent2 + ' '))
            else:
                fcontent = [format_long_output(c, wrap_length - len(indent2) + 1, '', indent2 + ' ')
                            for c in content]
            if len(fcontent) > 1:
                return f"{head}{text[0]}{fcontent[0]},\n{indent2} " + f",\n{indent2} ".join(fcontent[1:]) + text[-1] + tail
    return head + output


# --- --- ANSI format parser
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
