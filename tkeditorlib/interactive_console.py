#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 27 08:55:30 2018

@author: juliette
"""

from code import InteractiveConsole
from contextlib import redirect_stdout
from io import StringIO
from os import remove
import socket
import sys
import signal
from tkeditorlib.constants import PWD_FILE, IV_FILE, decrypt, encrypt
import tkinter
import time


class SocketConsole(InteractiveConsole):
    def __init__(self, hostname, port, locals=None, filename='<console>'):
        InteractiveConsole.__init__(self, locals, filename)
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.locals['exit'] = self._exit
        self.locals['quit'] = self._exit
        self._initial_locals = self.locals.copy()
        signal.signal(signal.SIGINT, self.interrupt)

        with open(PWD_FILE, 'r') as f:
            self._pwd = f.read()
        remove(PWD_FILE)

        with open(IV_FILE, 'rb') as f:
            self._iv = f.read()
        remove(IV_FILE)

        self.socket = socket.socket()
        self.port = port
        self.host = hostname
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
                line = decrypt(self.socket.recv(65536), self._pwd, self._iv)
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
                self.socket.send(encrypt('%s, %r, %r' % (res, output, err), self._pwd, self._iv))
                self.stdout.close()
                self.stderr.close()
                self.stdout = StringIO()
                self.stderr = StringIO()
            except socket.error as e:
                if e.errno == socket.errno.EAGAIN:
                    if tkinter._default_root is not None:
                        tkinter._default_root.update()
                    time.sleep(0.05)
                else:
                    self.socket.close()
                    break


if __name__ == '__main__':
    c = SocketConsole(sys.argv[1], int(sys.argv[2]))
    c.interact()
