#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
TkEditor - Python IDE
Copyright 2018-2019 Juliette Monsel <j_4321 at protonmail dot com>

TkEditor is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

TkEditor is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


GUI widget to display the help
"""
import tkinter as tk
from tkinter import ttk
from tkeditorlib.tkhtml import HtmlFrame
from tkeditorlib.constants import TEMPLATE_PATH, CSS_PATH, CONFIG
from textwrap import dedent
from docutils.core import publish_string
from docutils.parsers.rst import roles
from docutils.nodes import TextElement, Inline
from docutils.parsers.rst import Directive, directives
from docutils.writers.html4css1 import Writer, HTMLTranslator


sproles = ['data', 'exc', 'func', 'class', 'const', 'attr', 'meth', 'mod', 'obj',
           'py:data', 'py:exc', 'py:func', 'py:class', 'py:const', 'py:attr',
           'py:meth', 'py:mod', 'py:obj', 'any', 'ref', 'doc', 'download', 'numref',
           'envvar', 'token', 'keyword', 'option', 'term', 'eq', 'abbr', 'command',
           'dfn', 'file', 'guilabel', 'kbd', 'mailheader', 'makevar', 'manpage',
           'menuselection', 'mimetype', 'newsgroup', 'program', 'regexp', 'samp',
           'pep', 'rfc']


def run(self):
    thenode = type(self._role, (Inline, TextElement), {})(text=self.arguments[0])
    return [thenode]


for role in sproles:
    roles.register_generic_role(role, type(role, (Inline, TextElement), {}))
    directives.register_directive(role,
                                  type(role.capitalize(),
                                       (Directive,),
                                       {'required_arguments': 1,
                                        'optional_arguments': 0,
                                        'has_content': None,
                                        '_role': role,
                                        'run': run}))


def _visit(self, node, name):
    # don't start tags; use
    #     self.starttag(node, tagname, suffix, empty, **attributes)
    # keyword arguments (attributes) are turned into html tag key/value
    # pairs, e.g. `{'style':'background:red'} => 'style="background:red"'`
    self.body.append(self.starttag(node, 'span', '', CLASS=name.replace(':', '_')))


def _depart(self, node):
    self.body.append('</span>')


attributes = {'visit_' + role: lambda self, node, name=role: _visit(self, node, name) for role in sproles}
attributes.update({'depart_' + role: _depart for role in sproles})

MyHTMLTranslator = type('MyHTMLTranslator', (HTMLTranslator,), attributes)

html_writer = Writer()
html_writer.translator_class = MyHTMLTranslator


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
    out = publish_string(source=doc, writer=html_writer, settings_overrides=rst_opts)

    return out.decode()


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


class Help(ttk.Frame):
    def __init__(self, master=None, help_cmds={}, **kw):
        ttk.Frame.__init__(self, master=None, **kw)

        self.help_cmds = help_cmds  # {source: help_cmd}
        self._source = tk.StringVar(self)

        top_bar = ttk.Frame(self)

        # --- code source
        menu_source = tk.Menu(self, tearoff=False)
        menu_source.add_radiobutton(label='Console', value='Console', variable=self._source)
        menu_source.add_radiobutton(label='Editor', value='Editor', variable=self._source)
        self.source = ttk.Menubutton(top_bar, textvariable=self._source,
                                     menu=menu_source, padding=1, width=7)
        self.entry = ttk.Combobox(top_bar, width=15)
        self.entry.bind('<Return>', self.show_help)
        self.entry.bind('<<ComboboxSelected>>', self.show_help)
        ttk.Label(top_bar, text='Source').pack(side='left', padx=4, pady=4)
        self.source.pack(side='left', padx=4, pady=4)
        ttk.Label(top_bar, text='Object').pack(side='left', padx=4, pady=4)
        self.entry.pack(side='left', padx=4, pady=4, fill='x', expand=True)

        self.html = HtmlFrame(self)
        self.load_stylesheet()
        self._source.set('Console')

        # --- placement
        top_bar.pack(fill='x')
        self.html.pack(fill='both', expand=True)

    def load_stylesheet(self):
        with open(CSS_PATH.format(theme=CONFIG.get('General', 'theme'))) as f:
            self.stylesheet = f.read()
        try:
            self.html.set_style(self.stylesheet)
        except tk.TclError:
            pass

    def show_help(self, event=None):
        obj = self.entry.get()
        try:
            jedi_def = self.help_cmds[self._source.get()](obj)
        except Exception as e:
            print(type(e), e)
            jedi_def = None
        if jedi_def:
            self.entry['values'] = [obj] + list(self.entry['values'])
            txt = get_docstring(jedi_def)
        else:
            txt = ''
        try:
            self.html.set_content(doc2html(txt))
            self.html.set_style(self.stylesheet)
        except tk.TclError:
            pass
