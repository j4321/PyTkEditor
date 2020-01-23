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
from os import chdir, getcwd, listdir
from os.path import dirname
from tempfile import mkstemp

from constants import CLIENT_CERT, SERVER_CERT

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


class Stdout(StringIO):
    def __init__(self, send_cmd, *args):
        StringIO.__init__(self, *args)
        self.send_cmd = send_cmd

    def write(self, line):
        StringIO.write(self, line)
        self.send_cmd(line)

class ConsoleMethods:
    def __init__(self):
        self.current_gui = ''

    def cd(self, path):
        chdir(path)
        print(getcwd())

    def ls(self, path):
        print(*listdir(path))

    def cat(self, file):
        with open(file) as f:
            print(f.read())

    def gui(self, gui):
        if gui not in GUI:
            raise ValueError(f"should be in {', '.join(GUI)}")
        self.current_gui = gui


class SocketConsole(InteractiveConsole):
    def __init__(self, hostname, port, locals=None, filename='<console>'):
        InteractiveConsole.__init__(self, locals, filename)
        self.stdout = Stdout(self.send_cmd)
        self.stderr = StringIO()

        self.locals['exit'] = self._exit
        self.locals['quit'] = self._exit
        self.locals['_console'] = ConsoleMethods()
        self.locals['_set_cwd'] = chdir
        self.locals['_get_cwd'] = getcwd
        self.locals['_cwd'] = getcwd()
        self.locals['run'] = self.runfile
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

    def runfile(self, filename):
        """Set working directory to filename's directory and run filename."""
        wdir = dirname(filename)
        with open(filename) as file:
            code = file.read()
        exec(f'chdir({wdir!r})', globals(), self.locals)
        exec(code, globals(), self.locals)

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
        while True:
            try:
                line = self.socket.recv(65536).decode()
                if self.buffer:
                    self.resetbuffer()
                with redirect_stdout(self.stdout):
                    try:
                        res = self.push(line)
                    except SystemExit:
                        self.write('SystemExit\n')
                        res = False
                    except KeyboardInterrupt:
                        self.write('KeyboardInterrupt\n')
                        res = False
                self.push('_cwd = _get_cwd()')
                # output = self.stdout.getvalue()
                err = self.stderr.getvalue()
                msg = f'{res}, "", {err!r}, False, {self.locals["_cwd"]!r}'
                if len(msg) > 16300:
                    fileno, filename = mkstemp(text=True)
                    with open(filename, 'w') as tmpfile:
                        tmpfile.write(msg)
                    msg = f'{res}, {filename!r}, "Too long", True, {self.locals["_cwd"]!r}'
                self.socket.send(msg.encode())
                self.stdout.close()
                self.stderr.close()
                self.stdout = Stdout(self.send_cmd)
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
