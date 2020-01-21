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

A Qt API selector that can be used to switch between PyQt4/5 and PySide.

This uses the ETS 4.0 selection pattern of:
PySide first, PyQt4 (API v2.) second, then PyQt5.

Do not use this if you need PyQt4 with the old QString/QVariant API.
"""

import os

from .qt_loaders import (load_qt, QT_API_PYSIDE, QT_API_PYSIDE2,
                                         QT_API_PYQT, QT_API_PYQT5)

QT_API = os.environ.get('QT_API', None)
if QT_API not in [QT_API_PYSIDE, QT_API_PYSIDE2, QT_API_PYQT, QT_API_PYQT5, None]:
    raise RuntimeError("Invalid Qt API %r, valid values are: %r, %r, %r, %r" %
                       (QT_API, QT_API_PYSIDE, QT_API_PYSIDE2, QT_API_PYQT, QT_API_PYQT5))
if QT_API is None:
    api_opts = [QT_API_PYQT5, QT_API_PYSIDE2, QT_API_PYSIDE, QT_API_PYQT]
else:
    api_opts = [QT_API]

QtCore, QtGui, QtSvg, QT_API = load_qt(api_opts)
