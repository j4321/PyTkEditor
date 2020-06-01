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

A minimal application using the Qt console-style Jupyter frontend.

This is not a complete console app, as subprocess will not be able to receive
input, there is no real readline support, among other limitations.
"""
import signal
import os

from qtconsole.qtconsoleapp import JupyterQtConsoleApp
from qtconsole import jupyter_widget
from qtconsole import rich_jupyter_widget
from qtpy import QtGui, QtWidgets
from jupyter_client.consoleapp import JupyterConsoleApp
from traitlets import Any

from pytkeditorlib.utils.constants import JUPYTER_ICON


class JupyterWidget(jupyter_widget.JupyterWidget):

    def _dispatch(self, msg):
        """ Calls the frontend handler associated with the message type of the
            given message.
        """
        msg_type = msg['header']['msg_type']
        handler = getattr(self, '_handle_' + msg_type, None)
        if handler:
            try:
                handler(msg)
            except Exception as e:
                print(f'Jupyter QTConsole: {repr(e)}')


class RichJupyterWidget(rich_jupyter_widget.RichJupyterWidget):

    def _dispatch(self, msg):
        """ Calls the frontend handler associated with the message type of the
            given message.
        """
        msg_type = msg['header']['msg_type']
        handler = getattr(self, '_handle_' + msg_type, None)
        if handler:
            try:
                handler(msg)
            except Exception as e:
                print(f'Jupyter QTConsole: {repr(e)}')


class PyTkQtConsoleApp(JupyterQtConsoleApp):
    classes = [JupyterWidget] + JupyterConsoleApp.classes

    def _focus(self, *args):
        self.window.raise_()
        self.window.update()

    def parse_command_line(self, argv=None):
        i = 0
        while i < len(argv) and not argv[i].startswith('--PyTkEditor.pid'):
            i += 1
        if i < len(argv):
            self.pytkeditor_pid = int(argv[i][len('--PyTkEditor.pid') + 1:])
            del argv[i]
        else:
            self.pytkeditor_pid = None
        super(JupyterQtConsoleApp, self).parse_command_line(argv)
        self.build_kernel_argv(self.extra_args)

    def _plain_changed(self, name, old, new):
        kind = 'plain' if new else 'rich'
        self.config.ConsoleWidget.kind = kind
        if new:
            self.widget_factory = JupyterWidget
        else:
            self.widget_factory = RichJupyterWidget

    # the factory for creating a widget
    widget_factory = Any(RichJupyterWidget)

    def init_qt_elements(self):
        # Create the widget.
        super(PyTkQtConsoleApp, self).init_qt_elements()
        self.app.icon = QtGui.QIcon(JUPYTER_ICON)
        QtWidgets.QApplication.setWindowIcon(self.app.icon)
        self.window.setWindowTitle('Jupyter QtConsole - PyTkEditor')

    def start(self):
        super(JupyterQtConsoleApp, self).start()

        # draw the window
        if self.maximize:
            self.window.showMaximized()
        else:
            self.window.show()
        self.window.raise_()
        os.kill(self.pytkeditor_pid, signal.SIGUSR2)
        signal.signal(signal.SIGUSR1, self._focus)
        # Start the application main loop.
        self.app.exec_()


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def main():
    PyTkQtConsoleApp.launch_instance()


if __name__ == '__main__':
    main()
