# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2019 Juliette Monsel <j_4321 at protonmail dot com>
code based on the tkinterhtml module by Aivar Annamaa copyright 2015-2016
https://pypi.python.org/pypi/tkinterhtml


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


Convert rst to html
"""
from docutils.core import publish_string
from docutils.parsers.rst import roles
from docutils.nodes import TextElement, Inline
from docutils.parsers.rst import Directive, directives
from docutils.writers.html4css1 import Writer, HTMLTranslator

from pytkeditorlib.utils.constants import TEMPLATE_PATH


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

