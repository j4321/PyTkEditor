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

Provides bracket matching for Q[Plain]TextEdit widgets.
"""

# System library imports
from .qt import QtCore, QtGui


class BracketMatcher(QtCore.QObject):
    """ Matches square brackets, braces, and parentheses based on cursor
        position.
    """

    # Protected class variables.
    _opening_map = { '(':')', '{':'}', '[':']' }
    _closing_map = { ')':'(', '}':'{', ']':'[' }

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    def __init__(self, text_edit):
        """ Create a call tip manager that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(text_edit, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(BracketMatcher, self).__init__()

        # The format to apply to matching brackets.
        self.format = QtGui.QTextCharFormat()
        self.format.setBackground(QtGui.QColor('silver'))

        self._text_edit = text_edit
        text_edit.cursorPositionChanged.connect(self._cursor_position_changed)

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _find_match(self, position):
        """ Given a valid position in the text document, try to find the
            position of the matching bracket. Returns -1 if unsuccessful.
        """
        # Decide what character to search for and what direction to search in.
        document = self._text_edit.document()
        start_char = document.characterAt(position)
        search_char = self._opening_map.get(start_char)
        if search_char:
            increment = 1
        else:
            search_char = self._closing_map.get(start_char)
            if search_char:
                increment = -1
            else:
                return -1

        # Search for the character.
        char = start_char
        depth = 0
        while position >= 0 and position < document.characterCount():
            if char == start_char:
                depth += 1
            elif char == search_char:
                depth -= 1
            if depth == 0:
                break
            position += increment
            char = document.characterAt(position)
        else:
            position = -1
        return position

    def _selection_for_character(self, position):
        """ Convenience method for selecting a character.
        """
        selection = QtGui.QTextEdit.ExtraSelection()
        cursor = self._text_edit.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(QtGui.QTextCursor.NextCharacter,
                            QtGui.QTextCursor.KeepAnchor)
        selection.cursor = cursor
        selection.format = self.format
        return selection

    #------ Signal handlers ----------------------------------------------------

    def _cursor_position_changed(self):
        """ Updates the document formatting based on the new cursor position.
        """
        # Clear out the old formatting.
        self._text_edit.setExtraSelections([])

        # Attempt to match a bracket for the new cursor position.
        cursor = self._text_edit.textCursor()
        if not cursor.hasSelection():
            position = cursor.position() - 1
            match_position = self._find_match(position)
            if match_position != -1:
                extra_selections = [ self._selection_for_character(pos)
                                     for pos in (position, match_position) ]
                self._text_edit.setExtraSelections(extra_selections)
