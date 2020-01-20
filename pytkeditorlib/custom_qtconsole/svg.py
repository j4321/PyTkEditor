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

Defines utility functions for working with SVG documents in Qt.
"""

# System library imports.
from .qt import QtCore, QtGui, QtSvg

# Our own imports
from ipython_genutils.py3compat import unicode_type

def save_svg(string, parent=None):
    """ Prompts the user to save an SVG document to disk.

    Parameters
    ----------
    string : basestring
        A Python string containing a SVG document.

    parent : QWidget, optional
        The parent to use for the file dialog.

    Returns
    -------
    The name of the file to which the document was saved, or None if the save
    was cancelled.
    """
    if isinstance(string, unicode_type):
        string = string.encode('utf-8')

    dialog = QtGui.QFileDialog(parent, 'Save SVG Document')
    dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
    dialog.setDefaultSuffix('svg')
    dialog.setNameFilter('SVG document (*.svg)')
    if dialog.exec_():
        filename = dialog.selectedFiles()[0]
        f = open(filename, 'wb')
        try:
            f.write(string)
        finally:
            f.close()
        return filename
    return None

def svg_to_clipboard(string):
    """ Copy a SVG document to the clipboard.

    Parameters
    ----------
    string : basestring
        A Python string containing a SVG document.
    """
    if isinstance(string, unicode_type):
        string = string.encode('utf-8')

    mime_data = QtCore.QMimeData()
    mime_data.setData('image/svg+xml', string)
    QtGui.QApplication.clipboard().setMimeData(mime_data)

def svg_to_image(string, size=None):
    """ Convert a SVG document to a QImage.

    Parameters
    ----------
    string : basestring
        A Python string containing a SVG document.

    size : QSize, optional
        The size of the image that is produced. If not specified, the SVG
        document's default size is used.

    Raises
    ------
    ValueError
        If an invalid SVG string is provided.

    Returns
    -------
    A QImage of format QImage.Format_ARGB32.
    """
    if isinstance(string, unicode_type):
        string = string.encode('utf-8')

    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(string))
    if not renderer.isValid():
        raise ValueError('Invalid SVG data.')

    if size is None:
        size = renderer.defaultSize()
    image = QtGui.QImage(size, QtGui.QImage.Format_ARGB32)
    image.fill(0)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    return image
