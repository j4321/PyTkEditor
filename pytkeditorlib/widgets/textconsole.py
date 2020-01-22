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


Python console text widget
"""

import tkinter as tk
import sys
import re
from os import kill, remove
from os.path import join, dirname
import socket
import ssl
from subprocess import Popen
import signal

from pygments import lex
from pygments.lexers import Python3Lexer
import jedi

from pytkeditorlib.utils.constants import get_screen, SERVER_CERT, CLIENT_CERT
from pytkeditorlib.dialogs import askyesno, CompListbox, Tooltip
from pytkeditorlib.gui_utils import AutoHideScrollbar
from .base_widget import BaseWidget, RichText


class TextConsole(RichText):
    def __init__(self, master, history, **kw):
        kw.setdefault('width', 50)
        kw.setdefault('wrap', 'word')
        kw.setdefault('prompt1', '>>> ')
        kw.setdefault('prompt2', '... ')
        kw.setdefault('undo', True)
        kw.setdefault('autoseparators', False)
        banner = kw.pop('banner', f'Python {sys.version.splitlines()[0]}\n')

        self.history = history
        self._hist_item = self.history.get_length()
        self._hist_match = ''

        self._prompt1 = kw.pop('prompt1')
        self._prompt2 = kw.pop('prompt2')

        RichText.__init__(self, master, **kw)

        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)

        self._tooltip = Tooltip(self, title='Arguments',
                                titlestyle='args.title.tooltip.TLabel')
        self._tooltip.withdraw()

        # --- shell socket
        self._init_shell()

        # --- initialization
        # self.update_style()

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
        self.bind('<ISO_Left_Tab>', self.unindent)
        self.bind('<Down>', self.on_down)
        self.bind('<Up>', self.on_up)
        self.bind('<Return>', self.on_return)
        self.bind('<BackSpace>', self.on_backspace)
        self.bind('<Control-c>', self.on_ctrl_c)
        self.bind('<Control-y>', self.redo)
        self.bind('<Control-z>', self.undo)
        self.bind("<Control-w>", lambda e: "break")
        self.bind("<Control-h>", lambda e: "break")
        self.bind("<Control-i>", lambda e: "break")
        self.bind("<Control-b>", lambda e: "break")
        self.bind("<Control-t>", lambda e: "break")
        self.bind('<<Paste>>', self.on_paste)
        self.bind('<<Cut>>', self.on_cut)
        self.bind('<<LineStart>>', self.on_goto_linestart)
        self.bind('<Destroy>', self.quit)
        self.bind('<FocusOut>', self._on_focusout)
        self.bind("<ButtonPress>", self._on_press)
        self.bind("<apostrophe>", self.auto_close_string)
        self.bind("<quotedbl>", self.auto_close_string)
        self.bind('<parenleft>', self.auto_close, True)
        self.bind("<bracketleft>", self.auto_close)
        self.bind("<braceleft>", self.auto_close)
        self.bind("<parenright>", self.close_brackets)
        self.bind("<bracketright>", self.close_brackets)
        self.bind("<braceright>", self.close_brackets)

    def undo(self, event=None):
        try:
            self.edit_undo()
        except tk.TclError:
            pass
        finally:
            self.parse()
        return "break"

    def redo(self, event=None):
        try:
            self.edit_redo()
        except tk.TclError:
            pass
        finally:
            self.parse()
        return "break"

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
                   join(dirname(dirname(__file__)), 'utils', 'interactive_console.py'),
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
            self.configure(state='normal')
            self.history.new_session()
            self.shell_clear()
            self._init_shell()

    def shell_clear(self):
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

    def on_goto_linestart(self, event):
        self.edit_separator()
        self.mark_set('insert', 'insert linestart+%ic' % (len(self._prompt1)))
        return "break"

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

    def on_cut(self, event):
        try:
            if self.compare('sel.first', '<', 'input'):
                self.tag_remove('sel', 'sel.first', 'input')
            # if self.compare('sel.last', '<', 'input'):
                # return "break"
        except tk.TclError:
            pass

    def on_paste(self, event):
        if self.compare('insert', '<', 'input'):
            return "break"
        try:
            if self.compare('sel.first', '<', 'input'):
                self.tag_remove('sel', 'sel.first', 'input')
            self.delete('sel.first', 'sel.last')
        except tk.TclError:
            pass
        self.edit_separator()
        txt = self.clipboard_get()
        self.insert("insert", txt)
        self.insert_cmd(self.get("input", "end"))
        self.parse()
        return 'break'

    def insert_cmd(self, cmd):
        self.edit_separator()
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
            self.edit_separator()
            self.insert('end', self._prompt2, 'prompt')
        else:
            self.insert('end', self._prompt1, 'prompt')
            self.edit_reset()
        self.mark_set('input', 'end-1c')

    def on_key_press(self, event):
        self._tooltip.withdraw()
        if 'Control' not in event.keysym:
            try:
                self.tag_remove('sel', 'sel.first', 'input')
            except tk.TclError:
                pass
        if self.compare('insert', '<', 'input') and event.keysym not in ['Left', 'Right']:
            self._hist_item = self.history.get_length()
            self.mark_set('insert', 'input lineend')
            if not event.char.isalnum():
                return 'break'

    def on_key_release(self, event):
        if self.compare('insert', '<', 'input') and event.keysym not in ['Left', 'Right']:
            self._hist_item = self.history.get_length()
            self.tag_remove('highlight', '1.0', 'end')
            return 'break'
        elif self._comp.winfo_ismapped():
            if event.char.isalnum():
                self._comp_display()
            elif event.keysym not in ['Tab', 'Down', 'Up']:
                self._comp.withdraw()
        else:
            if (event.char in [' ', ':', ',', ';', '(', '[', '{', ')', ']', '}']
               or event.keysym in ['BackSpace', 'Left', 'Right']):
                self.edit_separator()
            self.tag_remove('highlight', '1.0', 'end')
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
            txt = self.get(f'insert linestart+{len(self._prompt1)}c', 'insert')
            if txt == ' ' * len(txt):
                self.insert('insert', '    ')
            else:
                self._comp_display()
        return "break"

    def unindent(self, event=None):
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            start = str(self.index('sel.first'))
            end = str(self.index('sel.last'))
        else:
            start = str(self.index('insert'))
            end = str(self.index('insert'))
        start_line = int(start.split('.')[0])
        end_line = int(end.split('.')[0]) + 1
        start_char = len(self._prompt1)
        for line in range(start_line, end_line):
            start = f"{line}.{start_char}"
            if self.get(start, start + "+4c") == '    ':
                self.delete(start, start + "+4c")
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
        index = self.index('insert')
        script = self._jedi_script()
        res = script.goto_definitions()
        self.mark_set('insert', index)
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
            screen = self.winfo_screenheight()
            y = yr + yb + h
            x = xr + xb
            if y + hcomp > screen:
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
                self.history.new_session()
                self.shell_clear()
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
                    self.history.new_session()
                    self.shell_clear()
                    return
                else:
                    self.insert('end', err, 'Token.Error')

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
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            self.delete('sel.first', 'sel.last')
        else:
            linestart = self.get('insert linestart', 'insert')
            if re.search(r'    $', linestart):
                self.delete('insert-4c', 'insert')
            elif self.get('insert-2c', 'insert') in [c1 + c2 for c1, c2 in self._autoclose.items()]:
                self.delete('insert-2c', 'insert')
            else:
                self.delete('insert-1c')
        self.parse()
        return 'break'

    # --- brackets
    def auto_close(self, event):
        sel = self.tag_ranges('sel')
        if sel:
            self.insert('sel.first', event.char)
            self.insert('sel.last', self._autoclose[event.char])
            self.mark_set('insert', 'sel.last+1c')
            self.tag_remove('sel', 'sel.first', 'sel.last')
            self.parse()
        else:
            self.tag_remove('highlight', '1.0', 'end')
            self.insert('insert', event.char, ['Token.Punctuation', 'highlight'])
            if not self._find_matching_par():
                self.insert('insert', self._autoclose[event.char], ['Token.Punctuation', 'highlight'])
                self.mark_set('insert', 'insert-1c')
        self.edit_separator()
        return 'break'

    def auto_close_string(self, event):
        self.tag_remove('highlight', '1.0', 'end')
        sel = self.tag_ranges('sel')
        if sel:
            text = self.get('sel.first', 'sel.last')
            if len(text.splitlines()) > 1:
                char = event.char * 3
            else:
                char = event.char
            self.insert('sel.first', char)
            self.insert('sel.last', char)
            self.mark_set('insert', 'sel.last+%ic' % (len(char)))
            self.tag_remove('sel', 'sel.first', 'sel.last')
        elif self.get('insert') == event.char:
            self.mark_set('insert', 'insert+1c')
        else:
            self.insert('insert', event.char * 2)
            self.mark_set('insert', 'insert-1c')
        self.parse()
        self.edit_separator()
        return 'break'

    def close_brackets(self, event):
        self.tag_remove('highlight', '1.0', 'end')
        if self.get('insert') == event.char:
            self.mark_set('insert', 'insert+1c')
        else:
            self.insert('insert', event.char, 'Token.Punctuation')
        self._find_opening_par(event.char)
        return 'break'


class ConsoleFrame(BaseWidget):
    def __init__(self, master, history, **kw):
        BaseWidget.__init__(self, master, 'Console', **kw)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sy = AutoHideScrollbar(self, orient='vertical')
        self.console = TextConsole(self, history,
                                   yscrollcommand=sy.set, relief='flat',
                                   borderwidth=0, highlightthickness=0)
        sy.configure(command=self.console.yview)
        sy.grid(row=0, column=1, sticky='ns')
        self.console.grid(row=0, column=0, sticky='nswe')

        self.menu = tk.Menu(self)
        self.menu.add_command(label='Clear console', command=self.console.shell_clear)
        self.menu.add_command(label='Restart console', command=self.console.restart_shell)

        self.update_style = self.console.update_style
