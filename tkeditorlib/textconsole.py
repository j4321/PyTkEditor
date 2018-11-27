#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 12:28:48 2018

@author: juliette
"""

import tkinter as tk
import sys
import re
from os import kill, remove
from os.path import join, dirname
from tkeditorlib.complistbox import CompListbox
from tkeditorlib.tooltip import Tooltip
from tkeditorlib.constants import get_screen, load_style, CONFIG, SERVER_CERT, \
    CLIENT_CERT
from tkeditorlib.messagebox import askyesno
from pygments import lex
from pygments.lexers import Python3Lexer
import jedi
import socket
import ssl
from subprocess import Popen
import signal


class TextConsole(tk.Text):
    def __init__(self, master, history, **kw):
        kw.setdefault('width', 50)
        kw.setdefault('wrap', 'word')
        kw.setdefault('prompt1', '>>> ')
        kw.setdefault('prompt2', '... ')
        kw.setdefault('error_foreground', 'tomato')
        banner = kw.pop('banner', 'Python %s\n' % sys.version)

        self.history = history
        self._hist_item = self.history.get_length()
        self._hist_match = ''

        self._syntax_highlighting_tags = []

        self._prompt1 = kw.pop('prompt1')
        self._prompt2 = kw.pop('prompt2')
        error_foreground = kw.pop('error_foreground')

        tk.Text.__init__(self, master, **kw)

        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)

        self._tooltip = Tooltip(self, title='Arguments',
                                titlestyle='args.title.tooltip.TLabel')
        self._tooltip.withdraw()

        self.menu = tk.Menu(self)
        self.menu.add_command(label='Clear console', command=self._shell_clear)
        self.menu.add_command(label='Restart console', command=self.restart_shell)

        # --- shell socket
        self._init_shell()

        # --- initialization
        self.update_style()

        self.tag_configure('error', foreground=error_foreground)

        self.insert('end', banner, 'banner')
        self.prompt()
        self.mark_set('input', 'insert')
        self.mark_gravity('input', 'left')

        # --- bindings
        self.bind('<parenleft>', self._args_hint)
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
        self.bind('<Destroy>', self.quit)
        self.bind('<FocusOut>', self._on_focusout)
        self.bind("<ButtonPress>", self._on_press)

    def quit(self, event=None):
        self.history.save()
        self.shell_client.shutdown(socket.SHUT_RDWR)
        self.shell_client.close()
        self.shell_socket.close()

    def _init_shell(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(certfile=SERVER_CERT)
        context.load_verify_locations(CLIENT_CERT)

        self.shell_socket = socket.socket()
        self.shell_socket.bind(('127.0.0.1', 0))
        host, port = self.shell_socket.getsockname()
        self.shell_socket.listen(5)

        p = Popen(['python',
                   join(dirname(__file__), 'interactive_console.py'),
                   host, str(port)])
        self.shell_pid = p.pid
        client, addr = self.shell_socket.accept()
        self.shell_client = context.wrap_socket(client, server_side=True)
        self.shell_client.setblocking(False)

    def restart_shell(self):
        rep = askyesno('Confirmation', 'Do you really want to restart the console?')
        if rep:
            kill(self.shell_pid, signal.SIGTERM)
            self.shell_client.shutdown(socket.SHUT_RDWR)
            self.shell_client.close()
            self.shell_socket.close()
            self._shell_clear()
            self._init_shell()

    def _shell_clear(self):
        self.delete('banner.last', 'end')
        self.insert('insert', '\n')
        self.prompt()

    def _on_focusout(self, event):
        self._comp.withdraw()
        self._tooltip.withdraw()

    def _on_press(self, event):
        self._comp.withdraw()
        self._tooltip.withdraw()

    def _comp_sel(self):
        txt = self._comp.get()
        self._comp.withdraw()
        self.insert('insert', txt)
        self.parse()

    def update_style(self):
        FONT = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        CONSOLE_BG, CONSOLE_HIGHLIGHT_BG, CONSOLE_SYNTAX_HIGHLIGHTING = load_style(CONFIG.get('Console', 'style'))
        CONSOLE_FG = CONSOLE_SYNTAX_HIGHLIGHTING.get('Token.Name', {}).get('foreground', 'black')

        self._syntax_highlighting_tags = list(CONSOLE_SYNTAX_HIGHLIGHTING.keys())
        self.configure(fg=CONSOLE_FG, bg=CONSOLE_BG, font=FONT,
                       selectbackground=CONSOLE_HIGHLIGHT_BG,
                       inactiveselectbackground=CONSOLE_HIGHLIGHT_BG,
                       insertbackground=CONSOLE_FG)
        self.tag_configure('prompt', **CONSOLE_SYNTAX_HIGHLIGHTING['Token.Generic.Prompt'])
        self.tag_configure('output', foreground=CONSOLE_FG)
        # --- syntax highlighting
        tags = list(self.tag_names())
        tags.remove('sel')
        tag_props = {key: '' for key in self.tag_configure('sel')}
        for tag, opts in CONSOLE_SYNTAX_HIGHLIGHTING.items():
            props = tag_props.copy()
            props.update(opts)
            self.tag_configure(tag, **props)

    def index_to_tuple(self, index):
        return tuple(map(int, self.index(index).split(".")))

    def parse(self):
        data = self.get('input', 'end')
        start = 'input'
        while data and '\n' == data[0]:
            start = self.index('%s+1c' % start)
            data = data[1:]
        self.mark_set('range_start', start)
        for t in self._syntax_highlighting_tags:
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
        self.insert("insert", txt)
        self.insert_cmd(self.get("input", "end"))
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
            self.insert('end', self._prompt2, 'prompt')
        else:
            self.insert('end', self._prompt1, 'prompt')
        self.mark_set('input', 'end-1c')

    def on_key_press(self, event):
        self._tooltip.withdraw()
        if self.compare('insert', '<', 'input') and event.keysym not in ['Left', 'Right']:
            self._hist_item = self.history.get_length()
            self.mark_set('insert', 'input lineend')
            if not event.char.isalnum():
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
            self.mark_set('insert', 'input lineend')
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

    def get_docstring(self, obj):
        session_code = '\n\n'.join(self.history.get_session_hist()) + '\n\n'
        script = jedi.Script(session_code + obj,
                             len(session_code.splitlines()) + 1,
                             len(obj),
                             'help.py')
        res = script.goto_definitions()
        if res:
            return res[-1]
        else:
            return None

    def _jedi_script(self):

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

        script = jedi.Script(session_code + lines, offset + 1, c - len(self._prompt1),
                             'completion.py')
        return script

    def _args_hint(self, event=None):
        script = self._jedi_script()
        res = script.goto_definitions()
        if res:
            try:
                args = res[-1].docstring().splitlines()[0]
            except IndexError:
                return
            self._tooltip.configure(text=args)
            xb, yb, w, h = self.bbox('insert')
            xr = self.winfo_rootx()
            yr = self.winfo_rooty()
            ht = self._tooltip.winfo_reqheight()
            screen = get_screen(xr, yr)
            y = yr + yb + h
            x = xr + xb
            if y + ht > screen[3]:
                y = yr + yb - ht

            self._tooltip.geometry('+%i+%i' % (x, y))
            self._tooltip.deiconify()

    def _comp_display(self):
        self._comp.withdraw()
        script = self._jedi_script()

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
            for i, l in enumerate(lines):
                if l.endswith('?'):
                    lines[i] = 'help(%s)' % l[:-1]
            line = '\n'.join(lines)

            self.insert('insert', '\n')
            try:
                self.shell_client.send(line.encode())
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
            cmd = self.shell_client.recv(65536).decode()
        except socket.error:
            self.after(10, self._check_result, auto_indent, lines, index)
        else:
            if not cmd:
                return
            res, output, err, wait = eval(cmd)

            if err == "Too long":
                filename = output
                with open(filename) as tmpfile:
                    res, output, err, wait = eval(tmpfile.read())
                remove(filename)

            if wait:
                if output.strip():
                    self.configure(state='normal')
                    self.insert('end', output, 'output')
                    self.mark_set('input', 'end')
                    self.see('end')
                self.configure(state='disabled')
                self.after(1, self._check_result, auto_indent, lines, index)
                return

            self.configure(state='normal')

            if err.strip():
                if err == 'SystemExit\n':
                    self._shell_clear()
                    return
                else:
                    self.insert('end', err, 'error')

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
            self.mark_set('insert', 'input lineend')
            return 'break'
        else:
            self.mark_set('insert', 'end')
            self.parse()
            self.insert('insert', '\n')
            self.insert('insert', self._prompt2, 'prompt')
            self.eval_current(True)

    def on_return(self, event=None):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'input lineend')
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
            self.mark_set('insert', 'input lineend')
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
