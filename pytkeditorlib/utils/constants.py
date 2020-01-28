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
import os
import configparser
import logging
from logging.handlers import TimedRotatingFileHandler

import warnings
from jedi import settings
from pygments.lexers import Python3Lexer
from pygments.token import Comment

settings.case_insensitive_completion = False
os.environ['PYFLAKES_BUILTINS'] = '_'

APP_NAME = 'PyTkEditor'
REPORT_URL = "https://gitlab.com/j_4321/{}/issues".format(APP_NAME)


class MyLexer(Python3Lexer):
    tokens = Python3Lexer.tokens.copy()
    tokens['root'].insert(5, (r'^# *(In\[.*\]|%%).*$', Comment.Cell))


PYTHON_LEX = MyLexer()


# --- paths
PATH = os.path.dirname(os.path.dirname(__file__))

if os.access(PATH, os.W_OK) and os.path.exists(os.path.join(PATH, "images")):
    # the app is not installed
    # local directory containing config files
    LOCAL_PATH = os.path.join(PATH, 'config')
    # PATH_LOCALE = os.path.join(PATH, "locale")
    PATH_HTML = os.path.join(PATH, 'html')
    PATH_SSL = os.path.join(PATH, 'ssl')
    PATH_IMG = os.path.join(PATH, 'images')
else:
    # local directory containing config files
    LOCAL_PATH = os.path.join(os.path.expanduser("~"), ".pytkeditor")
    # PATH_LOCALE = "/usr/share/locale"
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

if not CONFIG.read(PATH_CONFIG):
    CONFIG.add_section('General')
    CONFIG.set('General', 'theme', "light")
    CONFIG.set('General', 'fontfamily', "DejaVu Sans Mono")
    CONFIG.set('General', 'fontsize', "10")
    CONFIG.set('General', 'opened_files', "")
    CONFIG.set('General', 'recent_files', "")
    CONFIG.set('General', 'layout', "horizontal")
    CONFIG.add_section('Layout')
    CONFIG.set('Layout', 'horizontal', "0.16 0.65")
    CONFIG.set('Layout', 'horizontal2', "0.65")
    CONFIG.set('Layout', 'vertical', "0.65")
    CONFIG.set('Layout', 'pvertical', "0.16 0.6")
    CONFIG.add_section('Editor')
    CONFIG.set('Editor', 'style', "colorful")
    CONFIG.set('Editor', 'code_check', "True")
    CONFIG.set('Editor', 'style_check', "True")
    CONFIG.add_section('Code structure')
    CONFIG.set('Code structure', 'visible', "True")
    CONFIG.add_section('Console')
    CONFIG.set('Console', 'style', "monokai")
    CONFIG.set('Console', 'visible', "True")
    CONFIG.set('Console', 'order', "0")
    CONFIG.add_section('History')
    CONFIG.set('History', 'maxsize', "10000")
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

# --- console
MAGIC_COMMANDS = ['run', 'gui', 'pylab', 'magic']
EXTERNAL_COMMANDS = ['ls', 'cat', 'mv', 'rm', 'cp', 'mkdir']
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
