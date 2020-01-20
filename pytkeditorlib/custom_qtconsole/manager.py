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

Defines a KernelClient that provides signals and slots.
"""

from .qt import QtCore

# Local imports
from traitlets import Bool, DottedObjectName

from jupyter_client import KernelManager
from jupyter_client.restarter import KernelRestarter

from .kernel_mixins import QtKernelManagerMixin, QtKernelRestarterMixin


class QtKernelRestarter(KernelRestarter, QtKernelRestarterMixin):

    def start(self):
        if self._timer is None:
            self._timer = QtCore.QTimer()
            self._timer.timeout.connect(self.poll)
        self._timer.start(round(self.time_to_dead * 1000))

    def stop(self):
        self._timer.stop()

    def poll(self):
        super(QtKernelRestarter, self).poll()


class QtKernelManager(KernelManager, QtKernelManagerMixin):
    """A KernelManager with Qt signals for restart"""

    client_class = DottedObjectName('qtconsole.client.QtKernelClient')
    autorestart = Bool(True, config=True)

    def start_restarter(self):
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = QtKernelRestarter(
                    kernel_manager=self,
                    parent=self,
                    log=self.log,
                )
                self._restarter.add_callback(self._handle_kernel_restarted)
            self._restarter.start()

    def stop_restarter(self):
        if self.autorestart:
            if self._restarter is not None:
                self._restarter.stop()

    def _handle_kernel_restarted(self):
        self.kernel_restarted.emit()
