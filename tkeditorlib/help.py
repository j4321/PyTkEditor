#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 14:19:58 2018

@author: juliette
"""
import tkinter as tk
from tkinter import ttk
from tkeditorlib.tkhtml import HtmlFrame
from tkeditorlib.constants import TEMPLATE_PATH, CSS_PATH
from textwrap import dedent
from docutils.core import publish_string


class Help(ttk.Frame):
    def __init__(self, master=None, help_cmds={}, **kw):
        ttk.Frame.__init__(self, master=None, **kw)

        self.help_cmds = help_cmds  # {source: help_cmd}
        self._source = tk.StringVar(self)

        with open(CSS_PATH) as f:
            self.stylesheet = f.read()

        top_bar = ttk.Frame(self)

        # --- code source
        menu_source = tk.Menu(self, tearoff=False)
        menu_source.add_radiobutton(label='Console', value='Console', variable=self._source)
        menu_source.add_radiobutton(label='Editor', value='Editor', variable=self._source)
        self.source = ttk.Menubutton(top_bar, textvariable=self._source,
                                     menu=menu_source, padding=1)
        self.entry = ttk.Combobox(top_bar)
        self.entry.bind('<Return>', self.show_help)
        self.entry.bind('<<ComboboxSelected>>', self.show_help)
        ttk.Label(top_bar, text='Source').pack(side='left', padx=4, pady=4)
        self.source.pack(side='left', padx=4, pady=4)
        ttk.Label(top_bar, text='Object').pack(side='left', padx=4, pady=4)
        self.entry.pack(side='left', padx=4, pady=4, fill='x', expand=True)

        self.html = HtmlFrame(self)
        self._source.set('Console')

        # --- placement
        top_bar.pack(fill='x')
        self.html.pack(fill='both', expand=True)

    @staticmethod
    def doc2html(doc):
        rst_opts = {
            'no_generator': True,
            'no_source_link': True,
            'tab_width': 4,
            'file_insertion_enabled': False,
            'raw_enabled': False,
            'stylesheet_path': None,
            'traceback': True,
            'halt_level': 5,
            'template': TEMPLATE_PATH
        }

        if not doc:
            doc = """
                  .. error::
                        No documentation available
                  """
        out = publish_string(doc, writer_name='html', settings_overrides=rst_opts)

        return out.decode()

    def show_help(self, event=None):
        obj = self.entry.get()
        try:
            name, doc = self.help_cmds[self._source.get()](obj)
        except Exception as e:
            print(type(e), e)
            name, doc = "", ""
        if doc:
            self.entry['values'] = [obj] + list(self.entry['values'])
            args = "::\n\n    %s\n\n" % doc.splitlines()[0]
            doc = dedent('\n'.join(doc.splitlines()[1:]))
            txt = '#' * len(name) + '\n' + name + '\n' + '#' * len(name) + '\n\n' + args + doc
        else:
            txt = ''
        self.html.set_content(self.doc2html(txt))
        self.html.set_style(self.stylesheet)
