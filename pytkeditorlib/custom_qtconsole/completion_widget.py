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

A dropdown completer widget for the qtconsole.
"""

import os
import sys

from .qt import QtCore, QtGui


class CompletionWidget(QtGui.QListWidget):
    """ A widget for GUI tab completion.
    """

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    def __init__(self, console_widget):
        """ Create a completion widget that is attached to the specified Qt
            text edit widget.
        """
        text_edit = console_widget._control
        assert isinstance(text_edit, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(CompletionWidget, self).__init__(parent=console_widget)

        self._text_edit = text_edit
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        # We need Popup style to ensure correct mouse interaction
        # (dialog would dissappear on mouse click with ToolTip style)
        self.setWindowFlags(QtCore.Qt.Popup)

        self.setAttribute(QtCore.Qt.WA_StaticContents)
        original_policy = text_edit.focusPolicy()

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        text_edit.setFocusPolicy(original_policy)

        # Ensure that the text edit keeps focus when widget is displayed.
        self.setFocusProxy(self._text_edit)

        self.setFrameShadow(QtGui.QFrame.Plain)
        self.setFrameShape(QtGui.QFrame.StyledPanel)

        self.itemActivated.connect(self._complete_current)

    def eventFilter(self, obj, event):
        """ Reimplemented to handle mouse input and to auto-hide when the
            text edit loses focus.
        """
        if obj is self:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                pos = self.mapToGlobal(event.pos())
                target = QtGui.QApplication.widgetAt(pos)
                if (target and self.isAncestorOf(target) or target is self):
                    return False
                else:
                    self.cancel_completion()

        return super(CompletionWidget, self).eventFilter(obj, event)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter,
                   QtCore.Qt.Key_Tab):
            self._complete_current()
        elif key == QtCore.Qt.Key_Escape:
            self.hide()
        elif key in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down,
                     QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown,
                     QtCore.Qt.Key_Home, QtCore.Qt.Key_End):
            return super(CompletionWidget, self).keyPressEvent(event)
        else:
            QtGui.QApplication.sendEvent(self._text_edit, event)

    #--------------------------------------------------------------------------
    # 'QWidget' interface
    #--------------------------------------------------------------------------

    def hideEvent(self, event):
        """ Reimplemented to disconnect signal handlers and event filter.
        """
        super(CompletionWidget, self).hideEvent(event)
        try:
            self._text_edit.cursorPositionChanged.disconnect(self._update_current)
        except TypeError:
            pass
        self.removeEventFilter(self)

    def showEvent(self, event):
        """ Reimplemented to connect signal handlers and event filter.
        """
        super(CompletionWidget, self).showEvent(event)
        self._text_edit.cursorPositionChanged.connect(self._update_current)
        self.installEventFilter(self)

    #--------------------------------------------------------------------------
    # 'CompletionWidget' interface
    #--------------------------------------------------------------------------

    def show_items(self, cursor, items, prefix_length=0):
        """ Shows the completion widget with 'items' at the position specified
            by 'cursor'.
        """
        text_edit = self._text_edit
        point = self._get_top_left_position(cursor)
        self.clear()
        for item in items:
            list_item = QtGui.QListWidgetItem()
            list_item.setData(QtCore.Qt.UserRole, item)
            # Check if the item could refer to a file. The replacing of '"'
            # is needed for items on Windows
            if os.path.isfile(os.path.abspath(item.replace("\"", ""))):
                list_item.setText(item)
            else:
                list_item.setText(item.replace("\"", "").split('.')[-1])
            self.addItem(list_item)
        height = self.sizeHint().height()
        screen_rect = QtGui.QApplication.desktop().availableGeometry(self)
        if (screen_rect.size().height() + screen_rect.y() -
                point.y() - height < 0):
            point = text_edit.mapToGlobal(text_edit.cursorRect().topRight())
            point.setY(point.y() - height)
        w = (self.sizeHintForColumn(0) +
             self.verticalScrollBar().sizeHint().width() +
             2 * self.frameWidth())
        self.setGeometry(point.x(), point.y(), w, height)

        # Move cursor to start of the prefix to replace it
        # when a item is selected
        cursor.movePosition(QtGui.QTextCursor.Left, n=prefix_length)
        self._start_position = cursor.position()
        self.setCurrentRow(0)
        self.raise_()
        self.show()

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _get_top_left_position(self, cursor):
        """ Get top left position for this widget.
        """
        point = self._text_edit.cursorRect(cursor).center()
        point_size = self._text_edit.font().pointSize()

        if sys.platform == 'darwin':
            delta = int((point_size * 1.20) ** 0.98)
        elif os.name == 'nt':
            delta = int((point_size * 1.20) ** 1.05)
        else:
            delta = int((point_size * 1.20) ** 0.98)

        y = delta - (point_size / 2)
        point.setY(point.y() + y)
        point = self._text_edit.mapToGlobal(point)
        return point

    def _complete_current(self):
        """ Perform the completion with the currently selected item.
        """
        text = self.currentItem().data(QtCore.Qt.UserRole)
        self._current_text_cursor().insertText(text)
        self.hide()

    def _current_text_cursor(self):
        """ Returns a cursor with text between the start position and the
            current position selected.
        """
        cursor = self._text_edit.textCursor()
        if cursor.position() >= self._start_position:
            cursor.setPosition(self._start_position,
                               QtGui.QTextCursor.KeepAnchor)
        return cursor

    def _update_current(self):
        """ Updates the current item based on the current text and the
            position of the widget.
        """
        # Update widget position
        cursor = self._text_edit.textCursor()
        point = self._get_top_left_position(cursor)
        self.move(point)

        # Update current item
        prefix = self._current_text_cursor().selection().toPlainText()
        if prefix:
            items = self.findItems(prefix, (QtCore.Qt.MatchStartsWith |
                                            QtCore.Qt.MatchCaseSensitive))
            if items:
                self.setCurrentItem(items[0])
            else:
                self.hide()
        else:
            self.hide()

    def cancel_completion(self):
        self.hide()
