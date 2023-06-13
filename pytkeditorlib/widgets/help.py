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


GUI widget to display the help about objects in the console or the editor
"""
import tkinter as tk
from tkinter import ttk
from textwrap import dedent

from pytkeditorlib.utils.constants import CSS_PATH, CONFIG
from pytkeditorlib.gui_utils import EntryHistory, HtmlFrame
from pytkeditorlib.utils import doc2html
from .base_widget import BaseWidget


def get_docstring(jedi_def):
    doc = jedi_def.docstring()
    doc2 = ""
    args = ""
    if jedi_def.type == 'module':
        doc = dedent(doc)
    elif jedi_def.type == 'class':
        args = ".. code:: python\n\n    %s\n\n" % doc.splitlines()[0]
        doc = dedent('\n'.join(doc.splitlines()[1:]))
        l = [i for i in jedi_def.defined_names() if i.name == '__init__']
        if l:
            res = l[0]
            doc2 = dedent('\n'.join(res.docstring().splitlines()[1:]))

    else:
        if doc:
            args = ".. code:: python\n\n    %s\n\n" % doc.splitlines()[0]
            doc = dedent('\n'.join(doc.splitlines()[1:]))

    name = jedi_def.name.replace('_', '\_')
    sep = '#' * len(name)
    txt = "{0}\n{1}\n{0}\n\n{2}{3}\n\n{4}".format(sep, name, args, doc, doc2)
    return txt


class Help(BaseWidget):
    """Widget to display help."""
    def __init__(self, master, help_cmds, **kw):
        BaseWidget.__init__(self, master, 'Help', **kw)

        self.help_cmds = help_cmds  # {source: help_cmd}
        self._source = tk.StringVar(self, 'Console')

        top_bar = ttk.Frame(self)

        # --- code source
        self.source = ttk.Combobox(top_bar, width=7, textvariable=self._source,
                                   values=['Console', 'Editor'],
                                   state='readonly')
        self.entry = EntryHistory(top_bar, width=15)
        self.entry.bind('<Return>', self.show_help)
        self.entry.bind('<<ComboboxSelected>>', self.show_help)
        ttk.Label(top_bar, text='Source').pack(side='left', padx=4, pady=4)
        self.source.pack(side='left', padx=4, pady=4)
        ttk.Label(top_bar, text='Object').pack(side='left', padx=4, pady=4)
        self.entry.pack(side='left', padx=4, pady=4, fill='x', expand=True)

        self.html = HtmlFrame(self)
        self.update_style()
        self._source.set('Console')

        # --- placement
        top_bar.pack(fill='x')
        self.html.pack(fill='both', expand=True)

    def focus_set(self):
        """Set focus on entry."""
        self.entry.focus_set()

    def update_style(self):
        with open(CSS_PATH.format(theme=CONFIG.get('General', 'theme'))) as f:
            self.stylesheet = f.read()
        try:
            self.html.set_style(self.stylesheet)
        except tk.TclError:
            pass

    def inspect(self, obj, source=None):
        """Display docstring for obj."""
        if source is not None:
            self._source.set(source)
        self.entry.delete(0, 'end')
        self.entry.insert(0, obj)
        self.show_help()

    def show_help(self, event=None):
        """Display docstring."""
        obj = self.entry.get()
        try:
            jedi_def = self.help_cmds[self._source.get()](obj)
        except Exception as e:
            print(type(e), e)
            jedi_def = None
        if jedi_def:
            self.entry.add_to_history(obj)
            txt = get_docstring(jedi_def)
        else:
            txt = ''
        try:
            self.html.set_content(doc2html(txt))
            self.html.set_style(self.stylesheet)
        except tk.TclError:
            pass
