#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 10:41:14 2018

@author: juliette
"""
from pyflakes.api import checkPath
from pyflakes.reporter import Reporter as flakeReporter
from pyflakes.checker import builtin_vars
from subprocess import Popen, PIPE

builtin_vars.append('_')


class Logger(object):
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
    txt = message.split(':')
    line = int(txt[1])
    msg = ':'.join(txt[3:]).strip()
    if line in results:
        results[line][1].append(msg)
        results[line][2] = '%s\n%s: %s' % (results[line][2], txt[2], msg)
    else:
        results[line] = ['warning', [msg], '%s: %s' % (txt[2], msg)]


def parse_message_flake(message, category, results):
    txt = message.split(':')
    line = int(txt[1])
    msg = ':'.join(txt[2:]).strip()
    if line in results:
        results[line][1].append(msg)
        results[line][2] = '%s\n%s' % (results[line][2], msg)
    else:
        results[line] = [category, [msg], msg]


def pyflakes_check(filename):
    warning_log, err_log = Logger(), Logger()
    checkPath(filename, Reporter(warning_log, err_log))
    return err_log.log, warning_log.log


def pycodestyle_check(filename):
    p = Popen(['pycodestyle', filename], stdout=PIPE)
    return p.stdout.read().decode().splitlines()


def check_file(filename, style=True):
    err, warn = pyflakes_check(filename)
    results = {}
    if err:
        for line in err:
            parse_message_flake(line, 'error', results)
    else:
        for line in warn:
            parse_message_flake(line, 'warning', results)
        if style:
            warn2 = pycodestyle_check(filename)
            for line in warn2:
                parse_message_style(line, results)
    return results
