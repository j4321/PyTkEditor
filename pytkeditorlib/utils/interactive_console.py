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
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import socket
import ssl
import sys
import signal
import tkinter
import time
import timeit
from datetime import datetime
from os import chdir, getcwd, kill
from os.path import dirname, expanduser, join
from tempfile import mkstemp
from subprocess import run
from textwrap import dedent
import logging
from logging import handlers
import argparse

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


# --- console logging (for logstart, ...)
class TimestampFilter(logging.Filter):

    def filter(self, record):
        if record.levelname == "DEBUG":
            record.timestamp = ""
        else:
            record.timestamp = f"# {datetime.now()}\n"
        return True


class OutputFilter(logging.Filter):
    log_output = False

    def filter(self, record):
        output = record.getMessage().startswith('#[Out] ')
        if output:
            record.timestamp = ""
        return self.log_output or not output

# --- custom stdout / stdin
class Stdin:
    def __init__(self, query_cmd, *args):
        self.query_cmd = query_cmd

    def readline(self):
        return self.query_cmd()


class Stdout:
    def __init__(self, send_cmd, *args):
        self.send_cmd = send_cmd

    def write(self, line):
        self.send_cmd(line)


# --- special console methods
class ConsoleMethods:
    def __init__(self, locals_):
        self.current_gui = ''
        self.locals = locals_
        sys.path.insert(0, '.')
        # log
        self.logger = logging.getLogger("pytkeditor_log")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self._hist = StringIO()
        hist_handler = logging.StreamHandler(self._hist)
        hist_handler.setLevel(logging.INFO)
        hist_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(hist_handler)
        self.handler = None
        self.output_filter = OutputFilter('output_filter')
        self.timestamp_filter = TimestampFilter("timestamp_filter")
        self._log_state = 'Logging is not active'
        self._logstart_parser = argparse.ArgumentParser(prog="%logstart")
        self._logstart_parser.add_argument('filename', nargs='?', default=None, action="store")
        self._logstart_parser.add_argument('-o', dest='output', action='store_true')
        self._logstart_parser.add_argument('-t', dest='timestamps', action='store_true')
        self._logstart_parser.add_argument('log_mode', nargs='?', default='append',
                                           action="store",
                                           choices=['append', 'overwrite', 'rotate'])

    @staticmethod
    def print_doc(obj=None):
        if obj is None:
            print(CONSOLE_HELP)
        else:
            print(dedent(obj.__doc__))

    @staticmethod
    def external(cmd):
        cmd = cmd.split()
        res = run(cmd, capture_output=True)
        err = res.stderr.decode()
        if err:
            sys.stderr.write(err)
        else:
            print(res.stdout.decode())

    @staticmethod
    def cd(path):
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

        * %magic

            Show this message.

        * %gui [gui]

            Enable or disable the console GUI event loop integration.
            Available GUIs are tk (Tkinter), gtk (GTK+) and qt (PyQt5).

        * %logstate

            Print logging status.

        * %logstart [-o|-t] [filename [log_mode]]

            Start logging session (including history) in file 'filename'.
            If 'filename' is not given, uses 'pytkeditor_log.py' in console
            working directory.

        * %logstop

            Stop logging.

        * %pylab [gui]

            Load numpy and matplotlib interactively. Use gui, if provided,
            as matplotlib backend.

        * %run filename

            Set working directory to filename's directory and run filename.

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

    def timeit(self, code):
        """Benchmark a single line statement."""
        locs = self.locals.copy()
        timer = timeit.Timer(lambda: exec(code, locs, locs))
        nb, t_tot = timer.autorange()
        print(f"average time {t_tot/nb} s over {nb} executions")

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

    def logstart(self, arg):
        """
        %logstart [-o|-t] [filename [log_mode]]

        Start logging session (including history).

        Arguments:

            filename: file in which the log is written, if not given, the file
                      'pytkeditor_log.py' in console working directory is used.

            log_mode: logging mode

                append     - append log to existing file (default).
                overwrite  - overwrite existing file.
                rotate     - create a rotating log.

        Options:
            -o   - log also command outputs as comments
            -t   - put timestamps as comments before each output

        """
        try:
            args = self._logstart_parser.parse_args(arg.split())
        except SystemExit:
            return

        if self.handler is not None:
            print("Log is already active")
            return
        if not args.filename:
            args.filename = join(self.locals['_cwd'], 'pytkeditor_log.py')
        if args.log_mode == 'rotate':
            self.handler = handlers.RotatingFileHandler(args.filename, backupCount=100)
            self.handler.doRollover()
        elif args.log_mode == 'append':
            self.handler = logging.FileHandler(args.filename, mode='a')
        elif args.log_mode == 'overwrite':
            self.handler = logging.FileHandler(args.filename, mode='w+')
        else:
            raise ValueError(f"wrong log_mode {args.log_mode!r}: should be 'append', 'overwrite' or 'rotate'")
        self.output_filter.log_output = args.output
        self.handler.setLevel(logging.DEBUG)
        if args.timestamps:
            formatter = logging.Formatter('%(timestamp)s%(message)s')
            self.handler.addFilter(self.timestamp_filter)
        else:
            formatter = logging.Formatter('%(message)s')
        self.handler.addFilter(self.output_filter)
        self._log_state = f"""Filename   : {args.filename}
Mode       : {args.log_mode}
Log output : {args.output}
Timestamp  : {args.timestamps}"""
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)
        self.logger.debug('## PyTkEditor log - %s ##\n', datetime.now())
        hist = self._hist.getvalue()
        if hist:
            self.logger.debug("%s\n", hist)

    def logstop(self, arg):
        """Stop logging."""
        self.logger.removeHandler(self.handler)
        self.handler.close()
        self.handler = None
        self._log_state = 'Logging is not active'

    def logstate(self, arg):
        """Print logging status."""
        print(self._log_state)


# --- interactive console
class SocketConsole(InteractiveConsole):
    def __init__(self, hostname, port, main_pid, locals_=None, filename='<console>'):
        InteractiveConsole.__init__(self, locals_, filename)
        self.stdout = Stdout(self.send_cmd)
        handler = logging.StreamHandler(self.stdout)
        logging.basicConfig(handlers=[handler])
        self.stderr = StringIO()
        sys.stdin = Stdin(self.get_input)

        self.cm = ConsoleMethods(self.locals)
        self._log_output = ""
        self.locals['exit'] = self._exit
        self.locals['quit'] = self._exit
        self.locals['_console'] = self.cm
        self.locals['_getcwd'] = getcwd
        self.locals['_cwd'] = getcwd()
        self._initial_locals = self.locals.copy()
        signal.signal(signal.SIGINT, self.interrupt)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=SERVER_CERT)
        context.load_cert_chain(certfile=CLIENT_CERT)
        context.load_verify_locations(SERVER_CERT)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pytkeditor_pid = main_pid
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
        lines = data.splitlines()
        if lines:
            self._log_output += f"\n#[Out] {lines[0]}"
            if len(lines) > 1:
                self._log_output += "\n#      " + '\n#      '.join(lines[1:])
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
        self.runcode(code)  # issue: does not give the right output for "print('a')\nprint(2)"
        return False

    def get_input(self):
        """Get input from TextConsole."""
        kill(self.pytkeditor_pid, signal.SIGIO)
        self.socket.setblocking(True)
        user_input = self.socket.recv(65536).decode()
        self.socket.setblocking(False)
        return user_input

    def send_cmd(self, line):
        lines = line.strip().splitlines()
        if lines:
            if len(lines) > 1:
                self._log_output += f"\n#[Out] {lines[0]}\n#      " + '\n#      '.join(lines[1:])
            elif lines[0].strip():
                self._log_output += f"\n#[Out] {lines[0]}"
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
                    code = self.socket.recv(65536).decode()
                    if self.buffer:
                        self.resetbuffer()
                    try:
                        with redirect_stderr(self.stderr):
                            res = self.push(code)
                    except SystemExit:
                        self.write('SystemExit\n')
                        res = False
                    except KeyboardInterrupt:
                        self.write('KeyboardInterrupt\n')
                        res = False
                    err = self.stderr.getvalue()
                    if not res:
                        if code.strip():
                            self.cm.logger.info(code.strip())
                        if self._log_output[1:]:
                            self.cm.logger.info(self._log_output[1:])
                        self._log_output = ""
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


# --- main
if __name__ == '__main__':
    c = SocketConsole(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    c.interact()
