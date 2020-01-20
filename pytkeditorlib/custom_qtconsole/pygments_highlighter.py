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
"""

from .qt import QtGui
from .qstringhelpers import qstring_length

from ipython_genutils.py3compat import PY3, string_types
from pygments.formatters.html import HtmlFormatter
from pygments.lexer import RegexLexer, _TokenType, Text, Error
from pygments.lexers import PythonLexer, Python3Lexer
from pygments.styles import get_style_by_name


def get_tokens_unprocessed(self, text, stack=('root',)):
    """ Split ``text`` into (tokentype, text) pairs.

        Monkeypatched to store the final stack on the object itself.

        The `text` parameter this gets passed is only the current line, so to
        highlight things like multiline strings correctly, we need to retrieve
        the state from the previous line (this is done in PygmentsHighlighter,
        below), and use it to continue processing the current line.
    """
    pos = 0
    tokendefs = self._tokens
    if hasattr(self, '_saved_state_stack'):
        statestack = list(self._saved_state_stack)
    else:
        statestack = list(stack)
    statetokens = tokendefs[statestack[-1]]
    while 1:
        for rexmatch, action, new_state in statetokens:
            m = rexmatch(text, pos)
            if m:
                if action is not None:
                    if type(action) is _TokenType:
                        yield pos, action, m.group()
                    else:
                        for item in action(self, m):
                            yield item
                pos = m.end()
                if new_state is not None:
                    # state transition
                    if isinstance(new_state, tuple):
                        for state in new_state:
                            if state == '#pop':
                                statestack.pop()
                            elif state == '#push':
                                statestack.append(statestack[-1])
                            else:
                                statestack.append(state)
                    elif isinstance(new_state, int):
                        # pop
                        del statestack[new_state:]
                    elif new_state == '#push':
                        statestack.append(statestack[-1])
                    else:
                        assert False, "wrong state def: %r" % new_state
                    statetokens = tokendefs[statestack[-1]]
                break
        else:
            try:
                if text[pos] == '\n':
                    # at EOL, reset state to "root"
                    pos += 1
                    statestack = ['root']
                    statetokens = tokendefs['root']
                    yield pos, Text, u'\n'
                    continue
                yield pos, Error, text[pos]
                pos += 1
            except IndexError:
                break
    self._saved_state_stack = list(statestack)


# Monkeypatch!
RegexLexer.get_tokens_unprocessed = get_tokens_unprocessed


class PygmentsBlockUserData(QtGui.QTextBlockUserData):
    """ Storage for the user data associated with each line.
    """

    syntax_stack = ('root',)

    def __init__(self, **kwds):
        for key, value in kwds.items():
            setattr(self, key, value)
        QtGui.QTextBlockUserData.__init__(self)

    def __repr__(self):
        attrs = ['syntax_stack']
        kwds = ', '.join([ '%s=%r' % (attr, getattr(self, attr))
                           for attr in attrs ])
        return 'PygmentsBlockUserData(%s)' % kwds


class PygmentsHighlighter(QtGui.QSyntaxHighlighter):
    """ Syntax highlighter that uses Pygments for parsing. """

    #---------------------------------------------------------------------------
    # 'QSyntaxHighlighter' interface
    #---------------------------------------------------------------------------

    def __init__(self, parent, lexer=None):
        super(PygmentsHighlighter, self).__init__(parent)

        self._document = self.document()
        self._formatter = HtmlFormatter(nowrap=True)
        self.set_style('default')
        if lexer is not None:
            self._lexer = lexer
        else:
            if PY3:
                self._lexer = Python3Lexer()
            else:
                self._lexer = PythonLexer()

    def highlightBlock(self, string):
        """ Highlight a block of text.
        """
        prev_data = self.currentBlock().previous().userData()
        if prev_data is not None:
            self._lexer._saved_state_stack = prev_data.syntax_stack
        elif hasattr(self._lexer, '_saved_state_stack'):
            del self._lexer._saved_state_stack

        # Lex the text using Pygments
        index = 0
        for token, text in self._lexer.get_tokens(string):
            length = qstring_length(text)
            self.setFormat(index, length, self._get_format(token))
            index += length

        if hasattr(self._lexer, '_saved_state_stack'):
            data = PygmentsBlockUserData(
                syntax_stack=self._lexer._saved_state_stack)
            self.currentBlock().setUserData(data)
            # Clean up for the next go-round.
            del self._lexer._saved_state_stack

    #---------------------------------------------------------------------------
    # 'PygmentsHighlighter' interface
    #---------------------------------------------------------------------------

    def set_style(self, style):
        """ Sets the style to the specified Pygments style.
        """
        if isinstance(style, string_types):
            style = get_style_by_name(style)
        self._style = style
        self._clear_caches()

    def set_style_sheet(self, stylesheet):
        """ Sets a CSS stylesheet. The classes in the stylesheet should
        correspond to those generated by:

            pygmentize -S <style> -f html

        Note that 'set_style' and 'set_style_sheet' completely override each
        other, i.e. they cannot be used in conjunction.
        """
        self._document.setDefaultStyleSheet(stylesheet)
        self._style = None
        self._clear_caches()

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _clear_caches(self):
        """ Clear caches for brushes and formats.
        """
        self._brushes = {}
        self._formats = {}

    def _get_format(self, token):
        """ Returns a QTextCharFormat for token or None.
        """
        if token in self._formats:
            return self._formats[token]

        if self._style is None:
            result = self._get_format_from_document(token, self._document)
        else:
            result = self._get_format_from_style(token, self._style)

        self._formats[token] = result
        return result

    def _get_format_from_document(self, token, document):
        """ Returns a QTextCharFormat for token by
        """
        code, html = next(self._formatter._format_lines([(token, u'dummy')]))
        self._document.setHtml(html)
        return QtGui.QTextCursor(self._document).charFormat()

    def _get_format_from_style(self, token, style):
        """ Returns a QTextCharFormat for token by reading a Pygments style.
        """
        result = QtGui.QTextCharFormat()
        for key, value in style.style_for_token(token).items():
            if value:
                if key == 'color':
                    result.setForeground(self._get_brush(value))
                elif key == 'bgcolor':
                    result.setBackground(self._get_brush(value))
                elif key == 'bold':
                    result.setFontWeight(QtGui.QFont.Bold)
                elif key == 'italic':
                    result.setFontItalic(True)
                elif key == 'underline':
                    result.setUnderlineStyle(
                        QtGui.QTextCharFormat.SingleUnderline)
                elif key == 'sans':
                    result.setFontStyleHint(QtGui.QFont.SansSerif)
                elif key == 'roman':
                    result.setFontStyleHint(QtGui.QFont.Times)
                elif key == 'mono':
                    result.setFontStyleHint(QtGui.QFont.TypeWriter)
        return result

    def _get_brush(self, color):
        """ Returns a brush for the color.
        """
        result = self._brushes.get(color)
        if result is None:
            qcolor = self._get_color(color)
            result = QtGui.QBrush(qcolor)
            self._brushes[color] = result
        return result

    def _get_color(self, color):
        """ Returns a QColor built from a Pygments color string.
        """
        qcolor = QtGui.QColor()
        qcolor.setRgb(int(color[:2], base=16),
                      int(color[2:4], base=16),
                      int(color[4:6], base=16))
        return qcolor

