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
from tkinter.font import Font
import sys
import re
from os import kill, remove, getcwd
from os.path import join, dirname, sep, expanduser
from glob import glob
import socket
import ssl
from subprocess import Popen
import signal

from pygments import lex
from pygments.lexers import Python3Lexer
import jedi

from pytkeditorlib.utils.constants import SERVER_CERT, CLIENT_CERT, \
    MAGIC_COMMANDS, EXTERNAL_COMMANDS, get_screen, PathCompletion, glob_rel, \
    magic_complete, parse_ansi, format_long_output
from pytkeditorlib.dialogs import askyesno, Tooltip, CompListbox
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
        self._prompt1 = kw.pop('prompt1')
        self._prompt2 = kw.pop('prompt2')

        self._line_height = 17

        self._inspect_obj = '', None

        self.cwd = getcwd()  # console current working directory

        # --- history
        self.history = history
        self._hist_item = self.history.get_length()
        self._hist_match = ''

        RichText.__init__(self, master, **kw)
        self._orig = self._w + "_orig"

        # --- regexp
        ext_cmds = "|".join(EXTERNAL_COMMANDS)
        magic_cmds = "|".join(MAGIC_COMMANDS)
        pre_path = rf"(?:(?:(?:{ext_cmds}|cd|%run|%logstart) )|(?:\"|'))"
        self._re_abspaths = re.compile(rf'{pre_path}((?:~\w*)?(?:\{sep}\w+)+\{sep}?)$')
        self._re_relpaths = re.compile(rf'{pre_path}(\w+(?:\{sep}\w+)*\{sep}?)$')
        self._re_console_cd = re.compile(r'^cd ?(.*)\n*$')
        self._re_console_run = re.compile(r"^_console.run\('(.*)'\)$")
        self._re_console_external = re.compile(rf'^({ext_cmds}) ?(.*)\n*$')
        self._re_console_magic = re.compile(rf'^%({magic_cmds}) ?(.*)\n*$')
        self._re_help = re.compile(r'([.\w]*)(\?{1,2})$')
        self._re_expanduser = re.compile(r'(~\w*)')
        self._re_trailing_spaces = re.compile(r' *$', re.MULTILINE)
        self._re_prompt = re.compile(rf'^{re.escape(self._prompt2)}?', re.MULTILINE)
        self._re_prompts = re.compile(rf'^({re.escape(self._prompt2)}|{re.escape(self._prompt1)})?', re.MULTILINE)

        self._jedi_comp_external = '\n'.join([f'\ndef {cmd}():\n    pass\n'
                                              for cmd in EXTERNAL_COMMANDS])
        self._jedi_comp_extra = ''
        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)

        self._tooltip = Tooltip(self, title='Arguments',
                                titlestyle='args.title.tooltip.TLabel')
        self._tooltip.withdraw()

        # --- shell socket
        self._init_shell()

        # --- initialization
        self.insert('end', banner, 'banner')
        self.mark_set('input_end', 'insert')
        self.prompt()
        self.mark_set('input', 'insert')
        self.mark_gravity('input', 'left')
        self.mark_set('input_end', 'insert')
        self.mark_gravity('input_end', 'right')

        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

        self._poll_id = ""

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
        self.bind("<Control-i>", self.inspect)
        self.bind("<Control-b>", lambda e: "break")
        self.bind("<Control-f>", lambda e: "break")
        self.bind("<Control-t>", lambda e: "break")
        self.bind("<Control-l>", self.shell_clear)
        self.bind('<<Paste>>', self.on_paste)
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
        self.bind("<Configure>", self._on_configure)
        self.bind("<Shift-Escape>", lambda e: self.delete("input", "input_end"))

    def _proxy(self, *args):
        """
        Proxy between tkinter widget and tcl interpreter to catch unwanted actions.

        Prevent edition of text outside of current prompt.
        """
        largs = list(args)
        if args[0] in ("insert", "replace", "delete"):
            self._clear_highlight()
            self._tooltip.withdraw()
        if args[0] == "insert":
            if self.compare('insert', '<', 'input') or self.compare('insert', '>', 'input_end'):
                self.mark_set('insert', 'input_end')
                self._hist_item = self.history.get_length()
        elif args[0] == "delete":
            try:
                if self.compare(args[1], '<', 'input'):
                    largs[1] = 'input'
                if len(args) > 2 and self.compare(args[2], '>', 'input_end'):
                    largs[2] = 'input_end'
            except tk.TclError:
                return
        elif args[0:3] == ("mark", "set", "insert"):
            try:
                if self.compare(args[3], '>', 'input_end'):
                    largs[3] = 'input_end'
            except tk.TclError:
                return
        elif args[0:3] == ('tag', 'add', 'sel'):
            if self.compare(args[4], '>', 'input_end'):
                largs[4] = 'input_end'

        cmd = (self._orig,) + tuple(largs)
        
        try:
            result = self.tk.call(cmd)
            if largs[0] == 'delete':
                self.tag_remove('sel', '1.0', 'end')
        except tk.TclError as e:
            print(e)
        else:
            return result

    def _delete(self, index1, index2):
        """Call delete without going through _proxy."""
        self.tk.call(self._orig, 'delete', index1, index2)

    def update_style(self):
        RichText.update_style(self)
        self._line_height = Font(self, self.cget('font')).metrics('linespace')

    def parse(self):
        data = self.get('input', 'input_end')
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

    def index_to_tuple(self, index):
        return tuple(map(int, self.index(index).split(".")))

    # --- remote python interpreter
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
            try:
                self.shell_client.shutdown(socket.SHUT_RDWR)
                self.shell_client.close()
                self.shell_socket.close()
            except OSError:
                pass
            self.configure(state='normal')
            self._jedi_comp_extra = ''
            self.history.new_session()
            self.shell_clear()
            self._init_shell()

    def shell_clear(self, event=None):
        self._delete('banner.last', 'end')
        self.insert('insert', '\n')
        self.prompt()

    # --- autocompletion / hints
    def _comp_sel(self):
        txt = self._comp.get()
        self._comp.withdraw()
        self.insert('insert', txt)
        self.parse()

    def _jedi_script(self):

        lines = self.get('insert linestart + %ic' % len(self._prompt1), 'input_end').rstrip('\n')

        session_code = '\n\n'.join([self._jedi_comp_external, self._jedi_comp_extra] + self.history.get_session_hist()) + '\n\n'

        offset = len(session_code.splitlines())
        r, c = self.index_to_tuple('insert')

        script = jedi.Script(session_code + lines, offset + 1, c - len(self._prompt1),
                             'completion.py')
        return script

    def _args_hint(self, event=None):
        index = self.index('insert')
        try:
            script = self._jedi_script()
            res = script.goto_definitions()
        except Exception:
            return
        self.mark_set('insert', index)
        if res:
            try:
                args = res[-1].docstring().splitlines()[0]
            except Exception:
                # usually caused by an exception raised in Jedi
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
        index = self.index('insert wordend')
        if index[-2:] != '.0':
            self.mark_set('insert', 'insert-1c wordend')
        jedi_comp = False
        line = self.get('insert linestart', 'insert')
        # --- magic command
        comp = magic_complete(line.split()[-1])
        if not comp:
            # --- path autocompletion
            # absolute paths
            match_path = self._re_abspaths.search(line)
            if match_path:
                before_completion = match_path.groups()[0]
                if '~' in before_completion:
                    before_completion = expanduser(before_completion)
                paths = glob(before_completion + '*')
                comp = [PathCompletion(before_completion, path) for path in paths]
            # relative paths
            if not comp:
                match_path = self._re_relpaths.search(line)
                if match_path:
                    before_completion = match_path.groups()[0]
                    paths = glob_rel(before_completion + '*', self.cwd)
                    comp = [PathCompletion(before_completion, path) for path in paths]
                    jedi_comp = sep not in before_completion
            # --- jedi code autocompletion
            if not comp or jedi_comp:
                try:
                    script = self._jedi_script()
                    comp.extend(script.completions())
                except Exception:
                    # jedi raised an exception
                    pass

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

    # --- bindings
    def _on_configure(self, event):
        nb_lines = event.height // self._line_height - 1
        insert = self.index('insert')
        input_end = self.index('input_end')
        self._delete('input_end', 'end')
        self.insert('end', '\n' * nb_lines)
        self.mark_set('insert', insert)
        self.mark_set('input_end', input_end)

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
        try:
            self.after_cancel(self._poll_id)
        except ValueError:
            pass
        try:
            self.shell_client.shutdown(socket.SHUT_RDWR)
            self.shell_client.close()
            self.shell_socket.close()
        except OSError:
            pass

    def _on_focusout(self, event):
        self._comp.withdraw()
        self._tooltip.withdraw()

    def _on_press(self, event):
        self._clear_highlight()
        self._comp.withdraw()
        self._tooltip.withdraw()

    def on_goto_linestart(self, event):
        self.edit_separator()
        self.mark_set('insert', 'insert linestart+%ic' % (len(self._prompt1)))
        return "break"

    def on_ctrl_c(self, event):
        try:
            self.clipboard_clear()
            self.clipboard_append(self._re_prompts.sub('', self.get('sel.first', 'sel.last')))
        except tk.TclError:
            if self.cget('state') == 'disabled':
                kill(self.shell_pid, signal.SIGINT)
        return 'break'

    def on_paste(self, event):
        try:
            self.delete('sel.first', 'sel.last')
            self.tag_remove('sel', 'sel.first', 'sel.last')
        except tk.TclError:
            pass
        self.edit_separator()
        txt = self.clipboard_get()
        if self.get("input", "input_end").strip():
            self.insert("insert", txt.replace('\n', f"\n{self._prompt2}"))
        else:
            self.insert_cmd(txt)
        self.parse()
        return 'break'

    def on_key_press(self, event):
        if event.char.isalnum() and self.tag_ranges('sel'):
            self.edit_separator()

    def on_key_release(self, event):
        if self.compare('insert', '<', 'input') and event.keysym not in ['Left', 'Right']:
            self._hist_item = self.history.get_length()
            return 'break'
        elif self.compare('insert', '>', 'input_end') and event.keysym not in ['Left', 'Right']:
            self._hist_item = self.history.get_length()
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
            self.parse()

    def on_up(self, event):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'input')
            return 'break'
        elif self.compare('insert', '>', 'input_end'):
            self.mark_set('insert', 'input_end')
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
            self.mark_set('insert', 'input_end')
            return 'break'
        elif self.compare('insert', '>', 'input_end'):
            self.mark_set('insert', 'input_end')
            return 'break'
        elif self._comp.winfo_ismapped():
            self._comp.sel_next()
            return 'break'
        elif self.compare('insert lineend', '==', 'input_end'):
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
                self.delete('input', 'input_end')
                self.insert('insert', line)
            self.parse()
            return 'break'

    def on_tab(self, event):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'input_end')
            return "break"
        if self.compare('insert', '>', 'input_end'):
            self.mark_set('insert', 'input_end')
            return "break"
        if self._comp.winfo_ismapped():
            self._comp_sel()
            return "break"
        self.edit_separator()
        try:
            if self.compare('sel.first', '<', 'input'):
                self.tag_remove('sel', 'sel.first', 'input')
            if self.compare('sel.last', '>', 'input_end'):
                self.tag_remove('sel', 'input_end', 'sel.last')
            start = str(self.index('sel.first'))
            end = str(self.index('sel.last'))
            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0]) + 1
            char = len(self._prompt1)
            for line in range(start_line, end_line):
                self.insert(f'{line}.{char}', '    ')
        except tk.TclError:
            txt = self.get(f'insert linestart+{len(self._prompt1)}c', 'insert')
            if txt == ' ' * len(txt):
                self.insert('insert', '    ')
            else:
                self._comp_display()
        return "break"

    def unindent(self, event=None):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'input_end')
            return "break"
        if self.compare('insert', '>', 'input_end'):
            self.mark_set('insert', 'input_end')
            return "break"
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            if self.compare('sel.first', '<', 'input'):
                self.tag_remove('sel', 'sel.first', 'input')
            if self.compare('sel.last', '>', 'input_end'):
                self.tag_remove('sel', 'input_end', 'sel.last')
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

    def on_shift_return(self, event):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'input_end')
            return 'break'
        elif self.compare('insert', '>', 'input_end'):
            self.mark_set('insert', 'input_end')
            return 'break'
        else:
            self.mark_set('insert', 'input_end')
            self.parse()
            self.insert('insert', '\n')
            self.insert('insert', self._prompt2, 'prompt')
            self.see('input_end')
            self.eval_current(True)

    def on_return(self, event=None):
        if self.compare('insert', '<', 'input'):
            self.mark_set('insert', 'input_end')
            return 'break'
        if self.compare('insert', '>', 'input_end'):
            self.mark_set('insert', 'input_end')
            return 'break'
        if self._comp.winfo_ismapped():
            self._comp_sel()
        else:
            self.parse()
            if self.index('input_end linestart') == self.index('input linestart'):
                self.eval_current(True)
            else:
                text = self._re_prompt.sub('', self.get('insert', 'input_end')).strip()
                if text:
                    self.insert('insert', '\n' + self._prompt2, 'prompt')
                else:
                    self.eval_current(True)
            self.see('input_end')
        return 'break'

    def on_ctrl_return(self, event=None):
        self.parse()
        self.insert('insert', '\n')
        self.insert('insert', self._prompt2, 'prompt')
        self.see('input_end')
        return 'break'

    def on_backspace(self, event):
        self._clear_highlight()
        self.edit_separator()

        if self.tag_ranges('sel'):
            self.delete('sel.first', 'sel.last')
            self.tag_remove('sel', '1.0', 'end')
        else:
            if self.compare('insert', '<=', 'input') or self.compare('insert', '>', 'input_end'):
                self.mark_set('insert', 'input_end')
                return 'break'
            linestart = self.get('insert linestart', 'insert')
            text = self.get('insert-1c', 'insert+1c')
            if re.search(r'    $', linestart):
                self.delete('insert-4c', 'insert')
            elif linestart == self._prompt2:
                self.delete("insert linestart -1c", "insert")
            elif text in ["()", "[]", "{}"]:
                self.delete('insert-1c', 'insert+1c')
            elif text in ["''"]:
                if 'Token.Literal.String.Single' not in self.tag_names('insert-2c'):
                    # avoid situation where deleting the 2nd quote in '<text>'' result in deletion of both the 2nd and 3rd quotes
                    self.delete('insert-1c', 'insert+1c')
                else:
                    self.delete('insert-1c')
            elif text in ['""']:
                if 'Token.Literal.String.Double' not in self.tag_names('insert-2c'):
                    # avoid situation where deleting the 2nd quote in "<text>"" result in deletion of both the 2nd and 3rd quotes
                    self.delete('insert-1c', 'insert+1c')
                else:
                    self.delete('insert-1c')
            else:
                self.delete('insert-1c')
        self.parse()
        self._find_matching_par()
        return 'break'

    # --- insert
    def insert_cmd(self, cmd):
        self.edit_separator()
        input_index = self.index('input')
        self.delete('input', 'input_end')
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
        self.see('input_end')

    def prompt(self, result=False):
        if result:
            self.edit_separator()
            self.insert('input_end', self._prompt2, 'prompt')
        else:
            self.insert('input_end', self._prompt1, 'prompt')
            self.edit_reset()
        self.mark_set('input', 'input_end')

    # --- docstrings
    def inspect(self, event):
        try:
            self._inspect_obj = self.get('sel.first', "sel.last"), "Console"
        except tk.TclError:
            return "break"
        self.event_generate('<<Inspect>>')
        return "break"

    def get_docstring(self, obj):
        session_code = self._jedi_comp_extra + '\n\n'.join(self.history.get_session_hist()) + '\n\n'
        script = jedi.Script(session_code + obj,
                             len(session_code.splitlines()) + 1,
                             len(obj),
                             'help.py')
        res = script.goto_definitions()
        if res:
            return res[-1]
        else:
            return None

    # --- execute
    def execute(self, cmd):
        self.delete('input', 'input_end')
        self.insert_cmd(cmd)
        self.parse()
        self.focus_set()
        self.eval_current()

    def eval_current(self, auto_indent=False):
        index = self.index('input')
        code = self.get('input', 'insert lineend')
        self.mark_set('insert', 'insert lineend')
        if code:
            add_to_hist = True
            # remove trailing spaces
            code = self._re_trailing_spaces.sub('', code)
            # remove leading prompts
            code = self._re_prompt.sub('', code)
            # external cmds
            match = self._re_console_external.search(code)
            if match:
                self.history.add_history(code)
                self._hist_item = self.history.get_length()
                exp_match = tuple(self._re_expanduser.finditer(code))
                for m in reversed(exp_match):
                    p = m.group()
                    start, end = m.span()
                    code = code[:start] + expanduser(p) + code[end:]
                if match.groups()[1] in ['?', '??']:
                    code = f"{code[:-1]} --help"
                code = f"_console.external({code!r})"
                add_to_hist = False
            else:
                # cd
                match = self._re_console_cd.search(code)
                if match:
                    self.history.add_history(code)
                    self._hist_item = self.history.get_length()
                    if code in ['cd?', 'cd??']:
                        code = "print(_console.cd.__doc__)"
                    else:
                        code = f"_console.cd({match.groups()[0]!r})"
                    add_to_hist = False
                else:
                    # magic cmds
                    match = self._re_console_magic.match(code)
                    if match:
                        self.history.add_history(code)
                        self._hist_item = self.history.get_length()
                        cmd, arg = match.groups()
                        arg = arg.strip()
                        if arg in ['?', '??']:
                            code = f"_console.print_doc(_console.{cmd})"
                        else:
                            if cmd == 'pylab':
                                self._jedi_comp_extra += '\nimport numpy\nimport matplotlib\nfrom matplotlib import pyplot as plt\nnp = numpy\n'
                            code = f"_console.{cmd}({arg!r})"
                        add_to_hist = False
                    else:
                        # help
                        match = self._re_help.search(code)
                        if match:
                            self.history.add_history(code)
                            self._hist_item = self.history.get_length()
                            obj, h = match.groups()
                            if obj:
                                if h == '?':
                                    code = f"_console.print_doc({obj})"
                                else:  # h == '??'
                                    code = f"help({obj})"
                            else:
                                code = "_console.print_doc()"
                            add_to_hist = False

            self.insert('insert', '\n')
            try:
                self.shell_client.send(code.encode())
                self.configure(state='disabled')
            except SystemExit:
                self.history.new_session()
                self.shell_clear()
                return
            except Exception as e:
                print(e)
                return
            try:
                self.after_cancel(self._poll_id)
            except ValueError:
                pass
            self.after(1, self._check_result, auto_indent, code, index, add_to_hist)
        else:
            self.insert('insert', '\n')
            self.prompt()

    def _poll_output(self):
        """Get outputs coming in between """
        try:
            cmd = self.shell_client.recv(65536).decode()
        except socket.error:
            self._poll_id = self.after(100, self._poll_output)
        else:
            if cmd:
                res, output, err, wait, cwd = eval(cmd)
                index = self.index('input linestart -1c')
                if output.strip():
                    output = format_long_output(output, self["width"])
                    if '\x1b' in output:  # ansi formatting
                        offset = int(index.split('.')[0]) + 1
                        tag_ranges, text = parse_ansi(output, offset)
                        self.insert(f'{index}+1c', text, 'output')
                        for tag, r in tag_ranges.items():
                            self.tag_add(tag, *r)
                    else:
                        self.insert(f'{index}+1c', output, 'output')
                    self.see('input_end')
            self._poll_id = self.after(10, self._poll_output)

    def _check_result(self, auto_indent, code, index, add_to_hist=True):
        try:
            cmd = self.shell_client.recv(65536).decode()
        except socket.error:
            self.after(10, self._check_result, auto_indent, code, index, add_to_hist)
        else:
            if not cmd:
                return
            res, output, err, wait, cwd = eval(cmd)

            if err == "Too long":
                filename = output
                with open(filename) as tmpfile:
                    res, output, err, wait, cwd = eval(tmpfile.read())
                remove(filename)
            self.cwd = cwd
            if wait:
                if output.strip():
                    output = format_long_output(output, self["width"])
                    if '\x1b' in output:  # ansi formatting
                        offset = int(self.index('input_end').split('.')[0]) - 1
                        tag_ranges, text = parse_ansi(output, offset)
                        self.configure(state='normal')
                        self.insert('input_end', text, 'output')
                        for tag, r in tag_ranges.items():
                            self.tag_add(tag, *r)
                    else:
                        self.configure(state='normal')
                        self.insert('input_end', output, 'output')
                    self.mark_set('input', 'input_end')
                    self.see('input_end')
                self.configure(state='disabled')
                self.after(1, self._check_result, auto_indent, code, index, add_to_hist)
                return

            self.configure(state='normal')

            if err.strip():
                if err == 'SystemExit\n':
                    self.history.new_session()
                    self.shell_clear()
                    return
                else:
                    self.insert('input_end', err, 'Token.Error')

            if not res and self.compare('insert linestart', '>', 'insert'):
                self.insert('insert', '\n')
            self.prompt(res)
            if res and auto_indent and code:
                lines = code.splitlines()
                indent = re.search(r'^( )*', lines[-1]).group()
                line = lines[-1].strip()
                if line and line[-1] == ':':
                    indent = indent + '    '
                self.insert('insert', indent)
            self.see('input_end')
            if res:
                self.mark_set('input', index)
            elif code:
                match = self._re_console_run.match(code.strip())
                if match:
                    path = match.groups()[0]
                    with open(path) as file:
                        self._jedi_comp_extra += f"\n\n{file.read()}\n\n"
                if add_to_hist:
                    self.history.add_history(code)
                    self._hist_item = self.history.get_length()
            self._poll_id = self.after(100, self._poll_output)

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
            self._clear_highlight()
            self.insert('insert', event.char, ['Token.Punctuation', 'matching_brackets'])
            if not self._find_matching_par():
                self.tag_remove('unmatched_bracket', 'insert-1c')
                self.insert('insert', self._autoclose[event.char], ['Token.Punctuation', 'matching_brackets'])
                self.mark_set('insert', 'insert-1c')
        self.edit_separator()
        return 'break'

    def auto_close_string(self, event):
        self._clear_highlight()
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
        self._clear_highlight()
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
        self.console.bind("<Control-Tab>", self.traversal_next)
        self.console.bind('<Shift-Control-ISO_Left_Tab>', self.traversal_prev)

        self.menu = tk.Menu(self)
        self.menu.add_command(label='Clear console', accelerator='Ctrl+L',
                              command=self.console.shell_clear)
        self.menu.add_command(label='Restart console', command=self.console.restart_shell)

        self.update_style = self.console.update_style

    def focus_set(self):
        self.console.focus_set()

    def busy(self, busy):
        if busy:
            self.configure(cursor='watch')
            self.console.configure(cursor='watch')
        else:
            self.console.configure(cursor='xterm')
            self.configure(cursor='')

