# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright (c) 2017, Project Jupyter Contributors
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


Modified version of the qtconsole module of the Jupyter Project
<https://github.com/jupyter/qtconsole>.
    - Catch exceptions in base_frontend_mixin.BaseFrontendMixin._dispatch() 
      for when the qtconsole is not ready yet when the first line of code is sent
    - Modify icon and title to reflect the connexion with PyTkEditor
    - Take --PyTkEditor.pid command line argument to get the pid of the
      currently running PyTkEditor
    - Signal PyTkEditor when started

Originally distributed under the terms of the Modified BSD License available
in the ORIGINAL_LICENSE file in this module.

Style utilities, templates, and defaults for syntax highlighting widgets.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from colorsys import rgb_to_hls
from pygments.styles import get_style_by_name
from pygments.token import Token

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

default_template = '''\
    QPlainTextEdit, QTextEdit {
        background-color: %(bgcolor)s;
        background-clip: padding;
        color: %(fgcolor)s;
        selection-background-color: %(select)s;
    }
    .inverted {
        background-color: %(fgcolor)s;
        color: %(bgcolor)s;
    }
    .error { color: red; }
    .in-prompt-number { font-weight: bold; }
    .out-prompt-number { font-weight: bold; }
'''

# The default light style sheet: black text on a white background.
default_light_style_template = default_template + '''\
    .in-prompt { color: navy; }
    .out-prompt { color: darkred; }
'''
default_light_style_sheet = default_light_style_template%dict(
                bgcolor='white', fgcolor='black', select="#ccc")
default_light_syntax_style = 'default'

# The default dark style sheet: white text on a black background.
default_dark_style_template = default_template + '''\
    .in-prompt,
    .in-prompt-number { color: lime; }
    .out-prompt,
    .out-prompt-number { color: red; }
'''
default_dark_style_sheet = default_dark_style_template%dict(
                bgcolor='black', fgcolor='white', select="#555")
default_dark_syntax_style = 'monokai'

# The default monochrome
default_bw_style_sheet = default_template%dict(
                bgcolor='white', fgcolor='black', select="#ccc")
default_bw_syntax_style = 'bw'


def hex_to_rgb(color):
    """Convert a hex color to rgb integer tuple."""
    if color.startswith('#'):
        color = color[1:]
    if len(color) == 3:
        color = ''.join([c*2 for c in color])
    if len(color) != 6:
        return False
    try:
        r = int(color[:2],16)
        g = int(color[2:4],16)
        b = int(color[4:],16)
    except ValueError:
        return False
    else:
        return r,g,b

def dark_color(color):
    """Check whether a color is 'dark'.

    Currently, this is simply whether the luminance is <50%"""
    rgb = hex_to_rgb(color)
    if rgb:
        return rgb_to_hls(*rgb)[1] < 128
    else: # default to False
        return False

def dark_style(stylename):
    """Guess whether the background of the style with name 'stylename'
    counts as 'dark'."""
    return dark_color(get_style_by_name(stylename).background_color)

def get_colors(stylename):
    """Construct the keys to be used building the base stylesheet
    from a templatee."""
    style = get_style_by_name(stylename)
    fgcolor = style.style_for_token(Token.Text)['color'] or ''
    if len(fgcolor) in (3,6):
        # could be 'abcdef' or 'ace' hex, which needs '#' prefix
        try:
            int(fgcolor, 16)
        except TypeError:
            pass
        else:
            fgcolor = "#"+fgcolor

    return dict(
        bgcolor = style.background_color,
        select = style.highlight_color,
        fgcolor = fgcolor
    )

def sheet_from_template(name, colors='lightbg'):
    """Use one of the base templates, and set bg/fg/select colors."""
    colors = colors.lower()
    if colors=='lightbg':
        return default_light_style_template%get_colors(name)
    elif colors=='linux':
        return default_dark_style_template%get_colors(name)
    elif colors=='nocolor':
        return default_bw_style_sheet
    else:
        raise KeyError("No such color scheme: %s"%colors)
