#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 12:28:48 2018

@author: juliette
"""

import tkinter as tk
import sys
import re
from os import kill, chmod
from os.path import expanduser, join, dirname
from tkeditorlib.complistbox import CompListbox
from tkeditorlib.constants import get_screen, FONT, CONSOLE_BG, CONSOLE_FG,\
    CONSOLE_HIGHLIGHT_BG, CONSOLE_SYNTAX_HIGHLIGHTING, PWD_FILE, IV_FILE, \
    decrypt, encrypt
from pygments import lex
from pygments.lexers import Python3Lexer
import pickle
import jedi
import socket
from subprocess import Popen
import signal
import string
import secrets
from Crypto.Cipher import AES
from Crypto import Random


class History:
    """Python console command history."""

    def __init__(self, histfile, max_size=10000):
        """ Crée un historique vide """
        self.histfile = histfile
        self.maxsize = max_size
        self.history = []
        try:
            with open(histfile, 'rb') as file:
                dp = pickle.Unpickler(file)
                self.history = dp.load()
            self._session_start = len(self.history)
        except (FileNotFoundError, pickle.UnpicklingError, EOFError):
            self._session_start = 0

    def save(self):
        try:
            with open(self.histfile, 'rb') as file:
                dp = pickle.Unpickler(file)
                prev = dp.load()
        except (FileNotFoundError, pickle.UnpicklingError, EOFError):
            prev = []
        with open(self.histfile, 'wb') as file:
            pick = pickle.Pickler(file)
            hist = prev + self.history[self._session_start:]
            l = len(hist)
            if l > self.maxsize:
                hist = hist[l - self.maxsize:]
            pick.dump(hist)

    def add_history(self, line):
        self.history.append(line)

    def replace_history_item(self, pos, line):
        self.history[pos] = line

    def remove_history_item(self, pos):
        del self.history[pos]

    def get_history_item(self, pos):
        try:
            return self.history[pos]
        except IndexError:
            return None

    def get_length(self):
        return len(self.history)

    def set_max_size(self, maxsize):
        self.maxsize = maxsize

    def get_max_size(self):
        return self.maxsize

    def get_session_hist(self):
        return self.history[self._session_start:]


class TextConsole(tk.Text):
    def __init__(self, master=None, **kw):
        kw.setdefault('wrap', 'word')
        kw.setdefault('background', CONSOLE_BG)
        kw.setdefault('foreground', CONSOLE_FG)
        kw.setdefault('selectforeground', CONSOLE_FG)
        kw.setdefault('selectbackground', CONSOLE_HIGHLIGHT_BG)
        kw.setdefault('insertbackground', kw['foreground'])
        kw.setdefault('prompt1', '>>> ')
        kw.setdefault('prompt2', '... ')
        kw.setdefault('promptcolor', kw['foreground'])
        kw.setdefault('output_foreground', kw['foreground'])
        kw.setdefault('output_background', kw['background'])
        kw.setdefault('error_foreground', 'tomato')
        kw.setdefault('error_background', kw['background'])
        kw.setdefault('font', FONT)
        banner = kw.pop('banner', 'Python %s\n' % sys.version)

        histfile = join(expanduser('~'), '.tkeditor_history')
        self.history = History(histfile)
        self._hist_item = self.history.get_length()
        self._hist_match = ''

        self._prompt1 = kw.pop('prompt1')
        self._prompt2 = kw.pop('prompt2')
        output_foreground = kw.pop('output_foreground')
        output_background = kw.pop('output_background')
        error_foreground = kw.pop('error_foreground')
        error_background = kw.pop('error_background')
        promptcolor = kw.pop('promptcolor')

        tk.Text.__init__(self, master, **kw)

        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)

        self._pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(1024))
        with open(PWD_FILE, 'w') as f:
            f.write(self._pwd)
        chmod(PWD_FILE, 0o600)

        self._iv = Random.new().read(AES.block_size)

        with open(IV_FILE, 'wb') as f:
            f.write(self._iv)
        chmod(IV_FILE, 0o600)

        # --- shell socket
        self.shell_socket = socket.socket()
        self.shell_socket.bind((socket.gethostname(), 0))
        host, port = self.shell_socket.getsockname()
        self.shell_socket.listen(5)
        p = Popen(['python',
                   join(dirname(__file__), 'interactive_console.py'),
                   host, str(port)])
        self.shell_pid = p.pid
        self.shell_client, addr = self.shell_socket.accept()
        self.shell_client.setblocking(False)

        #  --- syntax highlighting
        for tag, opts in CONSOLE_SYNTAX_HIGHLIGHTING.items():
            self.tag_configure(tag, selectforeground=kw['selectforeground'], **opts)

        self.tag_configure('error', foreground=error_foreground,
                           background=error_background)
        self.tag_configure('prompt', foreground=promptcolor)
        self.tag_configure('output', foreground=output_foreground,
                           background=output_background)

        self.insert('end', banner, 'banner')
        self.prompt()
        self.mark_set('input', 'insert')
        self.mark_gravity('input', 'left')

        self.bind('<Control-Return>', self.on_ctrl_return)
        self.bind('<Shift-Return>', self.on_shift_return)
        self.bind('<KeyPress>', self.on_key_press)
        self.bind('<KeyRelease>', self.on_key_release)
        self.bind('<Tab>', self.on_tab)
        self.bind('<Down>', self.on_down)
        self.bind('<Up>', self.on_up)
        self.bind('<Return>', self.on_return)
        self.bind('<BackSpace>', self.on_backspace)
        self.bind('<Control-c>', self.on_ctrl_c)
        self.bind('<<Paste>>', self.on_paste)
        self.bind('<Destroy>', lambda e: self.history.save())
        self.bind('<FocusOut>', lambda e: self._comp.withdraw())
        self.bind("<ButtonPress>", self._on_press)

    def _on_destroy(self):
        self.history.save()
        self.shell_client.close()
        self.shell_socket.close()

    def _shell_clear(self):
        self.delete('banner.last', 'end')
        self.insert('insert', '\n')
        self.prompt()

    def _on_press(self, event):
        if self._comp.winfo_ismapped():
            self._comp.withdraw()

    def _comp_sel(self):
        txt = self._comp.get()
        self._comp.withdraw()
        self.insert('insert', txt)
        self.parse()

    def index_to_tuple(self, index):
        return tuple(map(int, self.index(index).split(".")))

    def parse(self):
        data = self.get('input', 'end')
        start = 'input'
        while data and '\n' == data[0]:
            start = self.index('%s+1c' % start)
            data = data[1:]
        self.mark_set('range_start', start)
        for t in CONSOLE_SYNTAX_HIGHLIGHTING:
            self.tag_remove(t, start, "range_start +%ic" % len(data))
        for token, content in lex(data, Python3Lexer()):
            self.mark_set("range_end", "range_start + %ic" % len(content))
            for t in token.split():
                self.tag_add(str(t), "range_start", "range_end")
            self.mark_set("range_start", "range_end")

    def on_ctrl_c(self, event):
        sel = self.tag_ranges('sel')
        if sel:
            txt = self.get('sel.first', 'sel.last').splitlines()
            lines = []
            for i, line in enumerate(txt):
                if line.startswith(self._prompt1):
                    lines.append(line[len(self._prompt1):])
                elif line.startswith(self._prompt2):
                    lines.append(line[len(self._prompt2):])
                else:
                    lines.append(line)
            self.clipboard_clear()
            self.clipboard_append('\n'.join(lines))
        elif self.cget('state') == 'disabled':
            kill(self.shell_pid, signal.SIGINT)
        return 'break'

    def on_paste(self, event):
        if self.compare('insert', '<', 'input'):
            return "break"
        sel = self.tag_ranges('sel')
        if sel:
            self.delete('sel.first', 'sel.last')
        txt = self.clipboard_get()
        self.insert_cmd(txt)
        self.parse()
        return 'break'

    def insert_cmd(self, cmd):
        input_index = self.index('input')
        self.delete('input', 'end')
        lines = cmd.splitlines()
        if lines:
            indent = len(re.search(r'^( )*', lines[0]).group())
            self.insert('insert', lines[0][indent:])
            for line in lines[1:]:
                line = line[indent:]
                self.insert('insert', '\n')
                self.prompt(True)
                self.insert('insert', line)
                self.mark_set('input', input_index)
        self.see('end')

    def prompt(self, result=False):
        if result:
            self.insert('insert', self._prompt2, 'prompt')
        else:
            self.insert('insert', self._prompt1, 'prompt')
        self.mark_set('input', 'insert')

    def on_key_press(self, event):
        if self.compare('insert', '<', 'input') and event.keysym not in ['Left', 'Right']:
            self._hist_item = self.history.get_length()
            return 'break'

    def on_key_release(self, event):
        if self.compare('insert', '<', 'input') and event.keysym not in ['Left', 'Right']:
            self._hist_item = self.history.get_length()
            return 'break'
        elif self._comp.winfo_ismapped():
            if event.char.isalnum():
                self._comp_display()
            elif event.keysym not in ['Tab', 'Down', 'Up']:
                self._comp.withdraw()
        else:
            self.parse()

    def on_up(self, event):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'end')
            return 'break'
        elif self._comp.winfo_ismapped():
            self._comp.sel_prev()
            return 'break'
        elif self.index('input linestart') == self.index('insert linestart'):
            line = self.get('input', 'insert')
            self._hist_match = line
            hist_item = self._hist_item
            self._hist_item -= 1
            item = self.history.get_history_item(self._hist_item)
            while self._hist_item >= 0 and not item.startswith(line):
                self._hist_item -= 1
                item = self.history.get_history_item(self._hist_item)
            if self._hist_item >= 0:
                index = self.index('insert')
                self.insert_cmd(item)
                self.mark_set('insert', index)
            else:
                self._hist_item = hist_item
            self.parse()
            return 'break'

    def on_down(self, event):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'end')
            return 'break'
        elif self._comp.winfo_ismapped():
            self._comp.sel_next()
            return 'break'
        elif self.compare('insert lineend', '==', 'end-1c'):
            line = self._hist_match
            self._hist_item += 1
            item = self.history.get_history_item(self._hist_item)
            while item is not None and not item.startswith(line):
                self._hist_item += 1
                item = self.history.get_history_item(self._hist_item)
            if item is not None:
                self.insert_cmd(item)
                self.mark_set('insert', 'input+%ic' % len(self._hist_match))
            else:
                self._hist_item = self.history.get_length()
                self.delete('input', 'end')
                self.insert('insert', line)
            self.parse()
            return 'break'

    def on_tab(self, event):
        if self.compare('insert', '<', 'input'):
            return "break"
        elif self._comp.winfo_ismapped():
            self._comp_sel()
            return "break"

        sel = self.tag_ranges('sel')
        if sel:
            start = str(self.index('sel.first'))
            end = str(self.index('sel.last'))
            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0]) + 1
            for line in range(start_line, end_line):
                self.insert('%i.0' % line, '    ')
        else:
            txt = self.get('insert-1c')
            if not txt.isalnum() and txt != '.':
                self.insert('insert', '    ')
            else:
                self._comp_display()
        return "break"

    def _comp_display(self):
        self._comp.withdraw()

        index = self.index('insert wordend')
        if index[-2:] != '.0':
            line = self.get('insert wordstart', 'insert wordend')
            i = len(line) - 1
            while i > -1 and line[i] in [')', ']', '}']:
                i -= 1
            self.mark_set('insert', 'insert wordstart +%ic' % (i + 1))

        lines = self.get('insert linestart + %ic' % len(self._prompt1), 'end').rstrip('\n')

        session_code = '\n\n'.join(self.history.get_session_hist()) + '\n\n'

        offset = len(session_code.splitlines())
        r, c = self.index_to_tuple('insert')

        script = jedi.Script(session_code + lines, offset + 1, c - len(self._prompt1), 'completion.py')
        comp = script.completions()

        if len(comp) == 1:
            self.insert('insert', comp[0].complete)
            self.parse()
        elif len(comp) > 1:
            self._comp.update(comp)
            xb, yb, w, h = self.bbox('insert')
            xr = self.winfo_rootx()
            yr = self.winfo_rooty()
            hcomp = self._comp.winfo_reqheight()
            screen = get_screen(xr, yr)
            y = yr + yb + h
            x = xr + xb
            if y + hcomp > screen[3]:
                y = yr + yb - hcomp
            self._comp.geometry('+%i+%i' % (x, y))
            self._comp.deiconify()

    def execute(self, cmd):
        self.delete('input', 'end')
        self.insert_cmd(cmd)
        self.parse()
        self.focus_set()
        self.eval_current()

    def eval_current(self, auto_indent=False):
        index = self.index('input')
        lines = self.get('input', 'insert lineend').splitlines()
        self.mark_set('insert', 'insert lineend')
        if lines:
            lines = [lines[0].rstrip()] + [line[len(self._prompt2):].rstrip() for line in lines[1:]]
            line = '\n'.join(lines)

            self.insert('insert', '\n')
            print('%r' % line)
            try:
                self.shell_client.send(encrypt(line, self._pwd, self._iv))
                self.configure(state='disabled')
            except SystemExit:
                self._shell_clear()
                return
            except Exception as e:
                print(e)
                return

            self.after(1, self._check_result, auto_indent, lines, index)
        else:
            self.insert('insert', '\n')
            self.prompt()

    def _check_result(self, auto_indent, lines, index):
        try:
            cmd = decrypt(self.shell_client.recv(65536), self._pwd, self._iv)
        except socket.error:
            self.after(10, self._check_result, auto_indent, lines, index)
        else:
            if not cmd:
                return
            res, output, err = eval(cmd)
            self.configure(state='normal')

            if err.strip():
                if err == 'SystemExit\n':
                    self._shell_clear()
                    return
                else:
                    self.insert('end', err, 'error')
            elif output.strip():
                self.insert('end', output, 'output')

            if not res and self.compare('insert linestart', '>', 'insert'):
                self.insert('insert', '\n')
            self.prompt(res)
            if auto_indent and lines:
                indent = re.search(r'^( )*', lines[-1]).group()
                line = lines[-1].strip()
                if line and line[-1] == ':':
                    indent = indent + '    '
                self.insert('insert', indent)
            self.see('end')
            if res:
                self.mark_set('input', index)
            elif lines:
                self.history.add_history('\n'.join(lines))
                self._hist_item = self.history.get_length()

    def on_shift_return(self, event):
        if self.compare('insert', '<', 'input'):
            return 'break'
        else:
            self.mark_set('insert', 'end')
            self.parse()
            self.insert('insert', '\n')
            self.insert('insert', self._prompt2, 'prompt')
            self.eval_current(True)

    def on_return(self, event=None):
        if self.compare('insert', '<', 'input'):
            return 'break'
        if self._comp.winfo_ismapped():
            self._comp_sel()
        else:
            self.parse()
            self.eval_current(True)
            self.see('end')
        return 'break'

    def on_ctrl_return(self, event=None):
        self.parse()
        self.insert('insert', '\n' + self._prompt2, 'prompt')
        return 'break'

    def on_backspace(self, event):
        if self.compare('insert', '<=', 'input'):
            return 'break'
        sel = self.tag_ranges('sel')
        if sel:
            self.delete('sel.first', 'sel.last')
        else:
            linestart = self.get('insert linestart', 'insert')
            if re.search(r'    $', linestart):
                self.delete('insert-4c', 'insert')
            else:
                self.delete('insert-1c')
        self.parse()
        return 'break'

