#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 12:28:48 2018

@author: juliette
"""

import tkinter as tk
import code
import rlcompleter
import sys
from threading import Lock
import re
import readline
from os.path import expanduser, join
from tkeditorlib.complistbox import CompListbox
from tkeditorlib.constants import get_screen, FONT, CONSOLE_BG, \
    CONSOLE_HIGHLIGHT_BG, CONSOLE_SYNTAX_HIGHLIGHTING, CONSOLE_FG
from contextlib import redirect_stderr, redirect_stdout
from pygments import lex
from pygments.lexers import Python3Lexer


def save_hist(prev_h_len, histfile):
    new_h_len = readline.get_current_history_length()
    readline.set_history_length(1000)
    readline.append_history_file(new_h_len - prev_h_len, histfile)


def index_to_tuple(text, index):
    return tuple(map(int, text.index(index).split(".")))


def display_list(L):
    txt = ""
    line = ""
    n = max([len(w) for w in L])
    n = max(n, 18) + 2
    fmt = "%-" + str(n) + "s"
    for e in sorted(L):
        e = str(e)
        if len(line) > 60:
            txt += line + '\n'
            line = ""
        else:
            line += fmt % e
    if len(line):
        txt += line
        # txt += '\n'
    return txt


class Completion:
    def __init__(self, complete, name):
        self.name = name
        self.complete = complete


class StdoutRedirector(object):
    def __init__(self, text_widget):
        self.text = text_widget

    def write(self, string):
        self.text.write('end', string, 'output')
        self.text.see('end')

    def writelines(self, lines):
        for line in lines:
            self.text.write(line)

    def flush(self):
        self.text.update_idletasks()


class StderrRedirector(object):
    def __init__(self, text_widget):
        self.text = text_widget

    def write(self, string):
        self.text.write('end', string, 'error')
        self.text.see('end')

    def writelines(self, lines):
        for line in lines:
            self.text.write(line)

    def flush(self):
        self.text.update_idletasks()


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
        kw.setdefault('error_foreground', 'red')
        kw.setdefault('error_background', kw['background'])
        kw.setdefault('font', FONT)
        banner = kw.pop('banner', 'Python %s\n' % sys.version)

        histfile = join(expanduser('~'), '.python_history')
        try:
            readline.read_history_file(histfile)
            prev_h_len = readline.get_current_history_length()
        except FileNotFoundError:
            prev_h_len = 0
        self._hist_item = prev_h_len + 1

        self._prompt1 = kw.pop('prompt1')
        self._prompt2 = kw.pop('prompt2')
        output_foreground = kw.pop('output_foreground')
        output_background = kw.pop('output_background')
        error_foreground = kw.pop('error_foreground')
        error_background = kw.pop('error_background')
        promptcolor = kw.pop('promptcolor')

        tk.Text.__init__(self, master, **kw)

        self.write_lock = Lock()

        self.stdout = StdoutRedirector(self)
        self.stderr = StderrRedirector(self)
        context = globals().copy()
        self.complete = rlcompleter.Completer(context).complete
        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)
        readline.set_auto_history(True)

        self.shell = code.InteractiveConsole(context)

        self.tag_configure('error', foreground=error_foreground,
                           background=error_background)
        self.tag_configure('prompt', foreground=promptcolor)
        self.tag_configure('output', foreground=output_foreground,
                           background=output_background)
        #  --- syntax highlighting
        for tag, opts in CONSOLE_SYNTAX_HIGHLIGHTING.items():
            self.tag_configure(tag, selectforeground=kw['selectforeground'], **opts)

        self.insert('end', banner)
        self.insert('end', self._prompt1, 'prompt')
        self.mark_set('input', 'insert')
        self.mark_gravity('input', 'left')

        self.bind('<Control-Return>', self.on_ctrl_return)
        self.bind('<KeyPress>', self.on_key_press)
        self.bind('<KeyRelease>', self.on_key_release)
        self.bind('<Tab>', self.on_tab)
        self.bind('<Down>', self.on_down)
        self.bind('<Up>', self.on_up)
        self.bind('<Return>', self.on_return)
        self.bind('<BackSpace>', self.on_backspace)
        self.bind('<<Copy>>', self.on_copy)
        self.bind('<<Paste>>', self.on_paste)
        self.bind('<Destroy>', lambda e: save_hist(prev_h_len, histfile))
        self.bind('<FocusOut>', lambda e: self._comp.withdraw())
        self.bind("<ButtonPress>", self._on_press)

    def _on_press(self, event):
        if self._comp.winfo_ismapped():
            self._comp.withdraw()

    def _comp_sel(self):
        txt = self._comp.get()
        self._comp.withdraw()
        self.insert('insert', txt)
        self.parse(self.get('input', 'end'), 'input')

    def parse(self, text, start):
        data = text
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

    def write(self, index, chars, *args):
        self.write_lock.acquire()
        self.insert(index, chars, *args)
        self.write_lock.release()

    def on_copy(self, event):
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
        return 'break'

    def on_paste(self, event):
        if self.compare('insert', '<', 'input'):
            return "break"
        sel = self.tag_ranges('sel')
        if sel:
            self.delete('sel.first', 'sel.last')
        txt = self.clipboard_get()
        self.insert_cmd(txt)
        self.parse(self.get('input', 'end'), 'input')
        return 'break'

    def insert_cmd(self, cmd):
        lines = cmd.splitlines()
        if lines:
            indent = len(re.search(r'^( )*', lines[0]).group())
            self.insert('insert', lines[0][indent:])
            self.parse(self.get('input', 'end'), 'input')
            self.eval_current()
            for line in lines[1:]:
                self.insert('insert', line[indent:])
                self.parse(self.get('input', 'end'), 'input')
                self.eval_current()
        self.see('end')

    def prompt(self, result=False):
        if result:
            self.write('end', self._prompt2, 'prompt')
        else:
            self.write('end', self._prompt1, 'prompt')
        self.mark_set('input', 'insert')

    def on_key_press(self, event):
        if self.compare('insert', '<', 'input') and event.keysym not in ['Left', 'Right']:
            self._hist_item = readline.get_current_history_length() + 1
            return 'break'

    def on_key_release(self, event):
        if self.compare('insert', '<', 'input') and event.keysym not in ['Left', 'Right']:
            self._hist_item = readline.get_current_history_length() + 1
            return 'break'
        elif self._comp.winfo_ismapped():
            if event.char.isalnum():
                self._comp_display()
            elif event.keysym not in ['Tab', 'Down', 'Up']:
                self._comp.withdraw()
        else:
            self.parse(self.get('input', 'end'), 'input')

    def on_up(self, event):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'end')
        elif self._comp.winfo_ismapped():
            self._comp.sel_prev()
        else:
            line = self.get('input', 'insert')
            index = self.index('insert')
            hist_item = self._hist_item
            self._hist_item -= 1
            item = readline.get_history_item(self._hist_item)
            while self._hist_item > 0 and not item.startswith(line):
                self._hist_item -= 1
                item = readline.get_history_item(self._hist_item)
            if self._hist_item > 0:
                self.delete('input', 'insert lineend')
                self.insert('insert', item)
                self.mark_set('insert', index)
            else:
                self._hist_item = hist_item
            self.parse(self.get('input', 'end'), 'input')
        return 'break'

    def on_down(self, event):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'end')
        elif self._comp.winfo_ismapped():
            self._comp.sel_next()
        else:
            line = self.get('input', 'insert')
            index = self.index('insert')
            self._hist_item += 1
            item = readline.get_history_item(self._hist_item)
            while item is not None and not item.startswith(line):
                self._hist_item += 1
                item = readline.get_history_item(self._hist_item)
            if item is not None:
                self.delete('input', 'insert lineend')
                self.insert('insert', item)
                self.mark_set('insert', index)
            else:
                self._hist_item = readline.get_current_history_length() + 1
                self.delete('input', 'insert lineend')
                self.insert('insert', line)
            self.parse(self.get('input', 'end'), 'input')
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
        line = self.get('input', 'end').rstrip('\n')
        cmd = line.strip()
        completions = []
        i = 0
        c = self.complete(cmd, i)
        while c is not None:
            completions.append(c)
            i += 1
            c = self.complete(cmd, i)

        if completions:
            if len(completions) == 1:
                self.delete('input', 'end')
                self.insert('input', line.replace(cmd, completions[0]))
                self.parse(self.get('input', 'end'), 'input')
            else:
                comp = [Completion(c[len(cmd):], c) for c in completions]
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
        self.eval_current()

    def eval_current(self, auto_indent=False):
        lines = self.get('input', 'insert lineend').splitlines()
        self.mark_set('insert', 'insert lineend')
        if lines:
            lines = [lines[0].rstrip()] + [line[len(self._prompt2):].rstrip() for line in lines[1:]]
        line = '\n'.join(lines)
        if lines:
            readline.add_history(line)
        self.insert('insert', '\n')
        self._hist_item = readline.get_current_history_length() + 1
        with redirect_stderr(self.stderr):
            with redirect_stdout(self.stdout):
                res = self.shell.push(line)
        if not res and self.compare('insert linestart', '>', 'insert'):
            self.insert('insert', '\n')
        self.prompt(res)
        if auto_indent:
            indent = re.search(r'^( )*', line).group()
            line = line.strip()
            if line and line[-1] == ':':
                indent = indent + '    '
            self.insert('insert', indent)
        self.see('end')
        self.mark_set('insert', 'end')

    def on_return(self, event=None):
        if self.compare('insert', '<', 'input'):
            return 'break'
        if self._comp.winfo_ismapped():
            self._comp_sel()
        else:
            self.parse(self.get('input', 'end'), 'input')
            self.eval_current(True)
            self.see('end')
        return 'break'

    def on_ctrl_return(self, event=None):
        self.parse(self.get('input', 'end'), 'input')
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
        self.parse(self.get('input', 'end'), 'input')
        return 'break'


if __name__ == '__main__':
    root = tk.Tk()
    t = TextConsole(root)
    t.pack()