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

A simple completer for the qtconsole
"""


from .qt import QtCore, QtGui
import ipython_genutils.text as text


class CompletionPlain(QtGui.QWidget):
    """ A widget for tab completion,  navigable by arrow keys """

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    def __init__(self, console_widget):
        """ Create a completion widget that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(console_widget._control, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(CompletionPlain, self).__init__()

        self._text_edit = console_widget._control
        self._console_widget = console_widget

        self._text_edit.installEventFilter(self)

    def eventFilter(self, obj, event):
        """ Reimplemented to handle keyboard input and to auto-hide when the
            text edit loses focus.
        """
        if obj == self._text_edit:
            etype = event.type()

            if etype in( QtCore.QEvent.KeyPress, QtCore.QEvent.FocusOut ):
                self.cancel_completion()

        return super(CompletionPlain, self).eventFilter(obj, event)

    #--------------------------------------------------------------------------
    # 'CompletionPlain' interface
    #--------------------------------------------------------------------------
    def cancel_completion(self):
        """Cancel the completion, reseting internal variable, clearing buffer """
        self._console_widget._clear_temporary_buffer()


    def show_items(self, cursor, items, prefix_length=0):
        """ Shows the completion widget with 'items' at the position specified
            by 'cursor'.
        """
        if not items :
            return
        self.cancel_completion()
        strng = text.columnize(items)
        # Move cursor to start of the prefix to replace it
        # when a item is selected
        cursor.movePosition(QtGui.QTextCursor.Left, n=prefix_length)
        self._console_widget._fill_temporary_buffer(cursor, strng, html=False)
