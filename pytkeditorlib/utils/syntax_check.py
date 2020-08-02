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


Syntax / PEP8 compliance checks
"""
from subprocess import Popen, PIPE
from multiprocessing import Process, Queue

from pyflakes.api import checkPath
from pyflakes.reporter import Reporter as flakeReporter
from pyflakes.checker import builtin_vars

from .constants import CONFIG, PYLINT

if PYLINT:
    from pylint.reporters.text import TextReporter
    from pylint import lint

    class MyReporter(TextReporter):
        name = "parseable"
        line_format = "{msg_id} (line {line}): {msg}"

        def __init__(self, queue, output=None):
            TextReporter.__init__(self, output)
            self.queue = queue

        def handle_message(self, msg):
            """manage message of different type and in the context of path"""
            self.queue.put((msg.category, msg.format(self._template), msg.line))

        def on_close(self, *args):
            self.queue.put(args)

        def display_messages(self, layout):
            """Launch layouts display"""

        def display_reports(self, layout):
            """Don't do anything in this reporter."""

        def _display(self, layout):
            """Do nothing."""


    def worker_pylint_check(filename, queue):
        """Return the list of messages and the stats from pylint's analysis."""
        lint.Run([filename], reporter=MyReporter(queue=queue), do_exit=True)

    def pylint_check(filename):
        """Launch pylint check in separate thread and return the queue and process."""
        queue = Queue()
        p = Process(target=worker_pylint_check, daemon=True, args=(filename, queue))
        p.start()
        return queue, p

else:

    def pylint_check():
        """Do nothing (pylint not installed)."""

builtin_vars.append('_')


class Logger:
    """Logger to collect checks output."""
    def __init__(self):
        self.log = []

    def write(self, string):
        self.log.append(string)


class Reporter(flakeReporter):
    """
    Formats the results of pyflakes checks to users.
    """
    def unexpectedError(self, filename, msg):
        self._stderr.write("%s:1: %s\n" % (filename, msg))

    def syntaxError(self, filename, msg, lineno, offset, text):
        line = text.splitlines()[-1]
        if offset is not None:
            offset = offset - (len(text) - len(line))
            self._stderr.write('%s:%d:%d: %s\n' %
                               (filename, lineno, offset + 1, msg))
        else:
            self._stderr.write('%s:%d: %s\n' % (filename, lineno, msg))

    def flake(self, message):
        self._stdout.write(str(message))


def parse_message_style(message, results):
    """Parse pycodestyle output."""
    txt = message.split(':')
    line = int(txt[1])
    msg = ':'.join(txt[3:]).strip()
    if line in results:
        results[line][1].append(msg)
        results[line][2] = '%s\n%s: %s' % (results[line][2], txt[2], msg)
    else:
        results[line] = ['warning', [msg], '%s: %s' % (txt[2], msg)]


def parse_message_flake(message, category, results):
    """Parse pyflakes output."""
    txt = message.split(':')
    line = int(txt[1])
    msg = ':'.join(txt[2:]).strip()
    if line in results:
        results[line][1].append(msg)
        results[line][2] = '%s\n%s' % (results[line][2], msg)
    else:
        results[line] = [category, [msg], msg]


def pyflakes_check(filename):
    """Run pyflakes on file and return output."""
    warning_log, err_log = Logger(), Logger()
    checkPath(filename, Reporter(warning_log, err_log))
    return err_log.log, warning_log.log


def pycodestyle_check(filename):
    """Run pycodestyle on file and return output."""
    p = Popen(['pycodestyle', filename], stdout=PIPE)
    return p.stdout.read().decode().splitlines()


def check_file(filename):
    """Run syntax and style checks on file."""
    results = {}
    if CONFIG.getboolean('Editor', 'code_check', fallback=True):
        err, warn = pyflakes_check(filename)
    else:
        err, warn = [], []

    if err:
        for line in err:
            parse_message_flake(line, 'error', results)
    else:
        for line in warn:
            parse_message_flake(line, 'warning', results)
        if CONFIG.getboolean('Editor', 'style_check', fallback=True):
            warn2 = pycodestyle_check(filename)
            for line in warn2:
                parse_message_style(line, results)
    return results
