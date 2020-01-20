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

Defines a KernelManager that provides signals and slots."""


from .qt import QtCore

from traitlets import HasTraits, Type
from .util import MetaQObjectHasTraits, SuperQObject
from .comms import CommManager


class QtKernelRestarterMixin(MetaQObjectHasTraits('NewBase', (HasTraits, SuperQObject), {})):

    _timer = None


class QtKernelManagerMixin(MetaQObjectHasTraits('NewBase', (HasTraits, SuperQObject), {})):
    """ A KernelClient that provides signals and slots.
    """

    kernel_restarted = QtCore.Signal()


class QtKernelClientMixin(MetaQObjectHasTraits('NewBase', (HasTraits, SuperQObject), {})):
    """ A KernelClient that provides signals and slots.
    """

    # Emitted when the kernel client has started listening.
    started_channels = QtCore.Signal()

    # Emitted when the kernel client has stopped listening.
    stopped_channels = QtCore.Signal()

    #---------------------------------------------------------------------------
    # 'KernelClient' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        super(QtKernelClientMixin, self).__init__(*args, **kwargs)
        self.comm_manager = None
    #------ Channel management -------------------------------------------------

    def start_channels(self, *args, **kw):
        """ Reimplemented to emit signal.
        """
        super(QtKernelClientMixin, self).start_channels(*args, **kw)
        self.started_channels.emit()
        self.comm_manager = CommManager(parent=self, kernel_client=self)

    def stop_channels(self):
        """ Reimplemented to emit signal.
        """
        super(QtKernelClientMixin, self).stop_channels()
        self.stopped_channels.emit()
        self.comm_manager = None
