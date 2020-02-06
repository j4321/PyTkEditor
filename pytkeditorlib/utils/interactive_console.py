#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2019 Juliette Monsel <j_4321 at protonmail dot com>

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


Python interpreter to execute the commands from the TextConsole
"""

from code import InteractiveConsole
from contextlib import redirect_stdout
from io import StringIO
import socket
import ssl
import sys
import signal
import tkinter
import time
from os import chdir, getcwd
from os.path import dirname, expanduser
from tempfile import mkstemp
from subprocess import run
from textwrap import dedent

from constants import CLIENT_CERT, SERVER_CERT, CONSOLE_HELP

GUI = ['', 'tk']
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    pass
else:
    GUI.append('qt')
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except ImportError:
    pass
else:
    GUI.append('gtk')


class Stdout:
    def __init__(self, send_cmd, *args):
        self.send_cmd = send_cmd

    def write(self, line):
        self.send_cmd(line)


class ConsoleMethods:
    def __init__(self, locals):
        self.current_gui = ''
        self.locals = locals
        sys.path.insert(0, '.')

    @staticmethod
    def print_doc(obj=None):
        if obj is None:
            print(CONSOLE_HELP)
        else:
            print(dedent(obj.__doc__))

    def external(self, cmd):
        cmd = cmd.split()
        res = run(cmd, capture_output=True)
        err = res.stderr.decode()
        if err:
            print(err)
        else:
            print(res.stdout.decode())

    def cd(self, path):
        "Change the current working directory."
        if '~' in path:
            path = expanduser(path)
        chdir(path)
        print(getcwd())

    # --- magic commands
    def magic(self, arg):
        """
        Console magic commands
        ======================

        * %magic: Show this message.

        * %pylab [gui]: Load numpy and matplotlib interactively. Use gui, if
                        provided, as matplotlib backend.

        * %run filename: Set working directory to filename's directory and run filename.

        * %gui [gui]: Enable or disable the console GUI event loop integration.
                      Available GUIs are tk (Tkinter), gtk (GTK+) and qt (PyQt5).
        """
        print(dedent(self.magic.__doc__))

    def pylab(self, gui=''):
        """
        Load numpy and matplotlib interactively.

        Set matplotlib backend to the one corresponding to gui (tk, qt, gtk)
        if provided and start the gui event loop.

        The following imports are made:

            import numpy
            import matplotlib
            from matplotlib import pyplot as plt
            np = numpy
        """
        import numpy
        import matplotlib

        if gui not in GUI:
            raise ValueError(f"should be in {', '.join(GUI)}")
        if gui == 'tk':
            matplotlib_backend = 'TkAgg'
        elif gui == 'qt':
            matplotlib_backend = 'Qt5Agg'
        elif gui == 'gtk':
            matplotlib_backend = 'Gtk3Agg'
        else:
            matplotlib_backend = None
        if gui:
            self.current_gui = gui

        if matplotlib_backend is not None:
            matplotlib.use(matplotlib_backend)

        from matplotlib import pyplot as plt
        plt.interactive(True)

        self.locals['numpy'] = numpy
        self.locals['matplotlib'] = matplotlib
        self.locals['plt'] = plt
        self.locals['np'] = numpy

    def run(self, filename):
        """Set working directory to filename's directory and run filename."""
        wdir = dirname(filename)
        with open(filename) as file:
            code = file.read()
        chdir(wdir)
        exec(code, self.locals, self.locals)

    def gui(self, gui):
        """
        Enable or disable the console GUI event loop integration.

        The following GUI toolkits are supported: Tkinter, GTK 3, PyQt5

            %gui tk   - enable Tkinter event loop integration
            %gui qt   - enable PyQt5 event loop integration
            %gui gtk  - enable GTK 3 event loop integration
            %gui      - disable event loop integration
        """
        if gui not in GUI:
            raise ValueError(f"should be in {', '.join(GUI)}")
        self.current_gui = gui


class SocketConsole(InteractiveConsole):
    def __init__(self, hostname, port, locals=None, filename='<console>'):
        InteractiveConsole.__init__(self, locals, filename)
        self.stdout = Stdout(self.send_cmd)
        self.stderr = StringIO()

        cm = ConsoleMethods(self.locals)
        self.locals['exit'] = self._exit
        self.locals['quit'] = self._exit
        self.locals['_console'] = cm
        self.locals['_getcwd'] = getcwd
        self.locals['_cwd'] = getcwd()
        self._initial_locals = self.locals.copy()
        signal.signal(signal.SIGINT, self.interrupt)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=SERVER_CERT)
        context.load_cert_chain(certfile=CLIENT_CERT)
        context.load_verify_locations(SERVER_CERT)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port
        self.host = hostname
        self.socket = context.wrap_socket(sock, server_side=False,
                                          server_hostname='PyTkEditor_Server')
        self.socket.connect((self.host, self.port))

    def interrupt(self, *args):
        raise KeyboardInterrupt

    def _exit(self):
        self.resetbuffer()
        self.locals = self._initial_locals.copy()
        raise SystemExit

    def write(self, data):
        self.stderr.write(data)

    def runcode(self, code):
        try:
            exec(code, self.locals)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception:
            self.showtraceback()

    def runsource(self, source, filename="<input>", symbol="single"):
        try:
            code = self.compile(source, filename, symbol)
        except SyntaxError:
            self.runcode(source)
            return False
        except (OverflowError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            return False

        if code is None:
            # Case 2
            return True

        # Case 3
        self.runcode(code)
        return False

    def send_cmd(self, line):
        msg = 'False, {!r}, "", True, {!r}'.format(line + '\n', self.locals["_cwd"])
        if len(msg) > 16300:
            fileno, filename = mkstemp(text=True)
            with open(filename, 'w') as tmpfile:
                tmpfile.write(msg)
                msg = f'False, {filename!r}, "Too long", True, {self.locals["_cwd"]!r}'
        self.socket.send(msg.encode())

    def _gui_loop(self):
        gui = self.locals['_console'].current_gui
        if gui == 'tk':
            if tkinter._default_root is not None:
                tkinter._default_root.update()
        elif gui == 'gtk':
            while Gtk.events_pending():
                Gtk.main_iteration()
        elif gui == 'qt':
            app = QApplication.instance()
            if app:
                app.processEvents()

    def interact(self):
        self.socket.setblocking(False)
        with redirect_stdout(self.stdout):
            while True:
                try:
                    line = self.socket.recv(65536).decode()
                    if self.buffer:
                        self.resetbuffer()
                    try:
                        res = self.push(line)
                    except SystemExit:
                        self.write('SystemExit\n')
                        res = False
                    except KeyboardInterrupt:
                        self.write('KeyboardInterrupt\n')
                        res = False
                    err = self.stderr.getvalue()
                    if not res and not err:
                        self.push('_cwd = _getcwd()')
                    msg = f'{res}, "", {err!r}, False, {self.locals["_cwd"]!r}'
                    if len(msg) > 16300:
                        fileno, filename = mkstemp(text=True)
                        with open(filename, 'w') as tmpfile:
                            tmpfile.write(msg)
                        msg = f'{res}, {filename!r}, "Too long", True, {self.locals["_cwd"]!r}'
                    self.socket.send(msg.encode())
                    self.stderr.close()
                    self.stderr = StringIO()
                except BrokenPipeError:
                    self.socket.close()
                    break
                except socket.error as e:
                    if e.errno != 2:
                        print('%r' % e, type(e), e)
                    self._gui_loop()
                    time.sleep(0.05)


if __name__ == '__main__':
    c = SocketConsole(sys.argv[1], int(sys.argv[2]))
    c.interact()
