#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2019 Juliette Monsel <j_4321 at protonmail dot com>

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


Help dialog
"""

from tkinter import Toplevel, TclError

from pytkeditorlib.utils.constants import PATH_DOC, CSS_PATH, CONFIG
from pytkeditorlib.gui_utils.tkhtml import HtmlFrame
from pytkeditorlib.utils import doc2html
from .messagebox import showerror


class HelpDialog(Toplevel):
    def __init__(self, master=None, **kw):
        Toplevel.__init__(self, master, **kw)
        self.transient(master)
        self.title("Help")
        self.minsize(600, 600)
        try:
            with open(PATH_DOC) as fdoc:
                doc = fdoc.read()
        except FileNotFoundError:
            showerror("Error", f"Documentation not found: {PATH_DOC} does not exists.")
            self.destroy()

        content = HtmlFrame(self)
        with open(CSS_PATH.format(theme=CONFIG.get('General', 'theme'))) as f:
            stylesheet = f.read()
        try:
            content.set_content(doc2html(doc))
            content.set_style(stylesheet)
        except TclError:
            pass
        content.pack(fill='both', expand=True)
        self.geometry('600x700')

