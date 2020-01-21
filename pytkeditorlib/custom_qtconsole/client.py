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
import atexit
import errno
from threading import Thread
import time

import zmq
# import ZMQError in top-level namespace, to avoid ugly attribute-error messages
# during garbage collection of threads at exit:
from zmq import ZMQError
from zmq.eventloop import ioloop, zmqstream

from .qt import QtCore

# Local imports
from traitlets import Type, Instance
from jupyter_client.channels import HBChannel
from jupyter_client import KernelClient
from jupyter_client.channels import InvalidPortNumber
from jupyter_client.threaded import ThreadedKernelClient, ThreadedZMQSocketChannel

from .kernel_mixins import QtKernelClientMixin
from .util import SuperQObject

class QtHBChannel(SuperQObject, HBChannel):
    # A longer timeout than the base class
    time_to_dead = 3.0

    # Emitted when the kernel has died.
    kernel_died = QtCore.Signal(object)

    def call_handlers(self, since_last_heartbeat):
        """ Reimplemented to emit signals instead of making callbacks.
        """
        # Emit the generic signal.
        self.kernel_died.emit(since_last_heartbeat)

from jupyter_client import protocol_version_info

major_protocol_version = protocol_version_info[0]

class QtZMQSocketChannel(ThreadedZMQSocketChannel,SuperQObject):
    """A ZMQ socket emitting a Qt signal when a message is received."""
    message_received = QtCore.Signal(object)

    def process_events(self):
        """ Process any pending GUI events.
        """
        QtCore.QCoreApplication.instance().processEvents()


    def call_handlers(self, msg):
        """This method is called in the ioloop thread when a message arrives.

        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application level
        handlers are called in the application thread.
        """
        # Emit the generic signal.
        self.message_received.emit(msg)


class QtKernelClient(QtKernelClientMixin, ThreadedKernelClient):
    """ A KernelClient that provides signals and slots.
    """

    iopub_channel_class = Type(QtZMQSocketChannel)
    shell_channel_class = Type(QtZMQSocketChannel)
    stdin_channel_class = Type(QtZMQSocketChannel)
    hb_channel_class = Type(QtHBChannel)
