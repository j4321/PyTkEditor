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

A generic Emacs-style kill ring, as well as a Qt-specific version.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# System library imports
from .qt import QtCore, QtGui

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class KillRing(object):
    """ A generic Emacs-style kill ring.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        """ Clears the kill ring.
        """
        self._index = -1
        self._ring = []

    def kill(self, text):
        """ Adds some killed text to the ring.
        """
        self._ring.append(text)

    def yank(self):
        """ Yank back the most recently killed text.

        Returns
        -------
        A text string or None.
        """
        self._index = len(self._ring)
        return self.rotate()

    def rotate(self):
        """ Rotate the kill ring, then yank back the new top.

        Returns
        -------
        A text string or None.
        """
        self._index -= 1
        if self._index >= 0:
            return self._ring[self._index]
        return None

class QtKillRing(QtCore.QObject):
    """ A kill ring attached to Q[Plain]TextEdit.
    """

    #--------------------------------------------------------------------------
    # QtKillRing interface
    #--------------------------------------------------------------------------

    def __init__(self, text_edit):
        """ Create a kill ring attached to the specified Qt text edit.
        """
        assert isinstance(text_edit, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(QtKillRing, self).__init__()

        self._ring = KillRing()
        self._prev_yank = None
        self._skip_cursor = False
        self._text_edit = text_edit

        text_edit.cursorPositionChanged.connect(self._cursor_position_changed)

    def clear(self):
        """ Clears the kill ring.
        """
        self._ring.clear()
        self._prev_yank = None

    def kill(self, text):
        """ Adds some killed text to the ring.
        """
        self._ring.kill(text)

    def kill_cursor(self, cursor):
        """ Kills the text selected by the give cursor.
        """
        text = cursor.selectedText()
        if text:
            cursor.removeSelectedText()
            self.kill(text)

    def yank(self):
        """ Yank back the most recently killed text.
        """
        text = self._ring.yank()
        if text:
            self._skip_cursor = True
            cursor = self._text_edit.textCursor()
            cursor.insertText(text)
            self._prev_yank = text

    def rotate(self):
        """ Rotate the kill ring, then yank back the new top.
        """
        if self._prev_yank:
            text = self._ring.rotate()
            if text:
                self._skip_cursor = True
                cursor = self._text_edit.textCursor()
                cursor.movePosition(QtGui.QTextCursor.Left,
                                    QtGui.QTextCursor.KeepAnchor,
                                    n = len(self._prev_yank))
                cursor.insertText(text)
                self._prev_yank = text

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    #------ Signal handlers ----------------------------------------------------

    def _cursor_position_changed(self):
        if self._skip_cursor:
            self._skip_cursor = False
        else:
            self._prev_yank = None
