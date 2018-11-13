#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 27 08:55:30 2018

@author: juliette
"""

from code import InteractiveConsole
from contextlib import redirect_stdout
from io import StringIO
import socket
import ssl
import sys
import signal
from constants import CLIENT_CERT, SERVER_CERT
import tkinter
import time
from tempfile import mkstemp


class SocketConsole(InteractiveConsole):
    def __init__(self, hostname, port, locals=None, filename='<console>'):
        InteractiveConsole.__init__(self, locals, filename)
        self.stdout = StringIO()
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
                                          server_hostname='TkEditor_Server')
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
                output = self.stdout.getvalue()
                err = self.stderr.getvalue()
                msg = '%s, %r, %r' % (res, output, err)
                if len(msg) > 65536:
                    fileno, filename = mkstemp(text=True)
                    with open(filename, 'w') as tmpfile:
                        tmpfile.write(msg)
                    msg = '%s, %r, "Too long"' % (res, filename)
                self.socket.send(msg.encode())
                self.stdout.close()
                self.stderr.close()
                self.stdout = StringIO()
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
