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
from tempfile import mkstemp

from constants import CLIENT_CERT, SERVER_CERT


class Stdout(StringIO):
    def __init__(self, send_cmd, *args):
        StringIO.__init__(self, *args)
        self.send_cmd = send_cmd

    def write(self, line):
        StringIO.write(self, line)
        self.send_cmd(line)


class SocketConsole(InteractiveConsole):
    def __init__(self, hostname, port, locals=None, filename='<console>'):
        InteractiveConsole.__init__(self, locals, filename)
        self.stdout = Stdout(self.send_cmd)
        self.stderr = StringIO()
        self.locals['exit'] = self._exit
        self.locals['quit'] = self._exit
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
        msg = 'False, %r, "", True' % (line + '\n')
        if len(msg) > 16300:
            fileno, filename = mkstemp(text=True)
            with open(filename, 'w') as tmpfile:
                tmpfile.write(msg)
                msg = 'False, %r, "Too long", True' % (filename)
        self.socket.send(msg.encode())

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
                # output = self.stdout.getvalue()
                err = self.stderr.getvalue()
                msg = '%s, %r, %r, %s' % (res, '', err, False)
                if len(msg) > 16300:
                    fileno, filename = mkstemp(text=True)
                    with open(filename, 'w') as tmpfile:
                        tmpfile.write(msg)
                    msg = '%s, %r, "Too long"' % (res, filename)
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
                if tkinter._default_root is not None:
                    tkinter._default_root.update()
                time.sleep(0.05)


if __name__ == '__main__':
    c = SocketConsole(sys.argv[1], int(sys.argv[2]))
    c.interact()