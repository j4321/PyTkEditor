# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2020 Juliette Monsel <j_4321 at protonmail dot com>

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


Code editor text widget
"""
import re
from glob import glob
from os.path import sep
import tkinter as tk
import logging

import jedi

from pytkeditorlib.gui_utils import RichEditor
from pytkeditorlib.utils.constants import CONFIG, PathCompletion
from pytkeditorlib.dialogs import showerror


class EditorText(RichEditor):
    """Code editor text widget."""
    def __init__(self, master, **kwargs):
        RichEditor.__init__(self, master, 'Editor', **kwargs)
        self.parse = self._parse

        self.filetype = 'Python'

        self.menu = tk.Menu(self)
        self.menu.add_command(label='Cut',
                              command=lambda: self.event_generate('<<Cut>>'),
                              accelerator='Ctrl+X')
        self.menu.add_command(label='Copy',
                              command=lambda: self.event_generate('<<Copy>>'),
                              accelerator='Ctrl+C')
        self.menu.add_command(label='Paste',
                              command=lambda: self.event_generate('<<Paste>>'),
                              accelerator='Ctrl+V')
        self.menu.add_command(label='Select all',
                              command=self.select_all, accelerator='Ctrl+A')
        self.menu.add_separator()
        self.menu.add_command(label='Toggle comment',
                              command=self.toggle_comment,
                              accelerator='Ctrl+E')


        self._tcl_error_msg = ''

        # --- bindings
        self.bind('<3>', self._post_menu)
        self.bind("<<Paste>>", self.on_paste)
        self.bind("<Tab>", self.on_tab)
        self.bind("<ISO_Left_Tab>", self.unindent)
        self.bind("<Return>", self.on_return)
        self.bind("<Control-d>", self.duplicate_lines)
        self.bind("<Control-k>", self.delete_lines)
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        self.bind("<Control-a>", self.select_all)
        self.bind('<Control-e>', self.toggle_comment)
        self.bind("<BackSpace>", self.on_backspace)
        self.bind("<Control-u>", self.upper_case)
        self.bind("<Control-Shift-U>", self.lower_case)

        # --- regexp
        self._re_paths = re.compile(rf'("|\')(\{sep}\w+)+\{sep}?$')
        self._re_indents = re.compile(r'^( *)(?=.*\S+.*$)', re.MULTILINE)
        self._re_tab = re.compile(r' {4}$')
        self._re_colon = re.compile(r':( *)$')

    def _proxy(self, *args):
        """Proxy between tkinter widget and tcl interpreter."""
        cmd = (self._orig,) + args
        insert_moved = (args[0] in ("insert", "delete")) or (args[0:3] == ("mark", "set", "insert"))
        if insert_moved:
            self.clear_highlight()
            self._tooltip.withdraw()

        try:
            result = self.tk.call(cmd)
        except tk.TclError as e:
            logging.exception('TclError')
            tcl_error_msg = str(e)
            print(tcl_error_msg)
            if tcl_error_msg.startswith("couldn't compile regular expression pattern"):
                showerror("Error", f"Invalid regular expression: {tcl_error_msg.split(':')[1]}.")
            return ''

        if args[0] == 'delete':
            self.master.update_nb_lines()
        if insert_moved:
            self.event_generate("<<CursorChange>>", when="tail")
            self.find_matching_par()
        return result

    def _post_menu(self, event):
        """Display right click menu."""
        if self.tag_ranges('sel'):
            self.menu.entryconfigure('Cut', state='normal')
            self.menu.entryconfigure('Copy', state='normal')
        else:
            self.menu.entryconfigure('Cut', state='disabled')
            self.menu.entryconfigure('Copy', state='disabled')
        self.menu.tk_popup(event.x_root, event.y_root)

    def _on_key_release(self, event):
        key = event.keysym
        if key in ('Return',) + tuple(self.autoclose):
            return
        elif self._comp.winfo_ismapped():
            if len(key) == 1 and key.isalnum():
                self._comp_display()
            elif key not in ['Tab', 'Down', 'Up']:
                self._comp.withdraw()
        elif (event.char in [' ', ':', ',', ';', '(', '[', '{', ')', ']', '}']
              or key in ['BackSpace', 'Left', 'Right']):
            self.edit_separator()
            self.parse(self.get("insert linestart", "insert lineend"),
                                "insert linestart")

    def _comp_generate(self):
        """Generate autocompletion list."""
        index = self.index('insert wordend')
        if index[-2:] != '.0':
            self.mark_set('insert', 'insert-1c wordend')

        # --- path autocompletion
        line = self.get('insert linestart', 'insert')
        match_path = self._re_paths.search(line)
        comp = []
        if match_path:
            before_completion = match_path.group()[1:]
            paths = glob(before_completion + '*')
            if len(paths) == 1 and paths[0] == before_completion:
                return
            comp = [PathCompletion(before_completion, path) for path in paths]
        # --- jedi code autocompletion
        if not comp:
            row, col = str(self.index('insert')).split('.')
            try:
                script = jedi.Script(self.get('1.0', 'end'), int(row), int(col), self.master.file)
                comp = script.completions()
            except Exception as e:
                print(e)
                pass # jedi raised an exception
        return comp

    def _indent_forward(self):
        """Return the adequate indentation."""
        line_nb, col = map(int, str(self.index('insert')).split('.'))
        if line_nb == 1:
            return '    '
        line_nb -= 1
        prev_line = self.get('%i.0' % line_nb, '%i.end' % line_nb)
        line = self.get('insert linestart', 'insert lineend')
        indent_prev = len(prev_line) - len(prev_line.lstrip())
        indent = len(line) - len(line.lstrip())
        if indent < indent_prev:
            return ' ' * (indent_prev - indent)
        return '    '

    def undo(self, event=None):
        try:
            self.tk.call(self._orig, 'edit', 'undo')
        except tk.TclError:
            pass
        else:
            self.parse_part(nblines=100)
        return "break"

    def redo(self, event=None):
        try:
            self.tk.call(self._orig, 'edit', 'redo')
        except tk.TclError:
            pass
        else:
            self.parse_part(nblines=100)
        return "break"

    def auto_close_string(self, event):
        RichEditor.auto_close_string(self, event)
        self.parse_part()
        return 'break'

    def parse_part(self, current='insert', nblines=10):
        start = f"{current} - {nblines} lines linestart"
        text = self.get(start, f"{current} + {nblines} lines lineend")
        if '"""' in text or "'''" in text:
            self.parse_all()
        else:
            self.parse(text, start)

    def parse_all(self):
        self.parse(self.get('1.0', 'end'), '1.0')

    def update_style(self):
        """Load and update widget style."""
        fg, bg, highlight_bg, font, syntax_highlighting = self._load_style()
        theme = f"{CONFIG.get('General', 'theme').capitalize()} Theme"
        selectbg = CONFIG.get(theme, 'textselectbg')
        selectfg = CONFIG.get(theme, 'textselectfg')
        self._update_style(fg, bg, selectfg, selectbg, font, syntax_highlighting)

    def on_paste(self, event):
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            self.delete(*sel)
        txt = self.clipboard_get()
        self.insert("insert", txt)
        self.master.update_nb_lines()
        lines = len(txt.splitlines())//2
        self.parse_part(f'insert linestart - {lines} lines', nblines=lines + 10)
        self.master.see('insert')
        return "break"

    def on_tab(self, event=None, force_indent=False):
        if self._comp.winfo_ismapped():
            self._comp_sel()
            return "break"

        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            start = str(self.index('sel.first'))
            end = str(self.index('sel.last'))
            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0]) + 1
            for line in range(start_line, end_line):
                self.insert('%i.0' % line, '    ')
        elif self.filetype == 'Python':
            txt = self.get('insert linestart', 'insert')
            if force_indent:
                self.insert('insert linestart', self._indent_forward())
            elif txt == ' ' * len(txt):
                self.insert('insert', self._indent_forward())
            else:
                self._comp_display()
        else:
            self.insert('insert', '\t')
        return "break"

    def _unindent_single_line(self, line_nb):
        if line_nb == 1:
            line = self.get('%i.0' % line_nb, '%i.end' % line_nb)
            indent_prev = -5
        else:
            prev_line, line = self.get('%i.0' % (line_nb - 1), '%i.end' % line_nb).splitlines()
            indent_prev = len(prev_line) - len(prev_line.lstrip())
        indent = len(line) - len(line.lstrip())
        if not indent:
            return
        diff = indent - indent_prev
        if 0 < diff <= 4:  # align current line with above line
            self.delete('%i.0' % line_nb, '%i.%i' % (line_nb, diff))
        else:
            dedent = indent % 4  # if indent not multiple of 4, correct it
            if not dedent:  # ident is a multiple of 4
                dedent = 4
            self.delete('%i.0' % line_nb, '%i.%i' % (line_nb, dedent))

    def _unindent_block(self, start_line, end_line):
        text = self.get('%i.0' % start_line, '%i.end' % end_line)
        # minimal indent of the block (neglecting non indented lines):
        try:
            indent = len(min(self._re_indents.findall(text)))
        except ValueError:
            return  # no line is indented
        dedent = indent % 4  # fix indent if not multiple of 4
        if not dedent:  # indent is a multiple of 4
            dedent = 4
        for line_nb, line in enumerate(text.splitlines(), start_line):
            nb_spaces = min(len(line) - len(line.lstrip()), dedent)
            self.delete('%i.0' % line_nb, '%i.%i' % (line_nb, nb_spaces))

    def unindent(self, event=None):
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if not sel:
            self._unindent_single_line(int(str(self.index('insert')).split('.')[0]))
            return "break"

        start_line = int(str(self.index('sel.first')).split('.')[0])
        end_line = int(str(self.index('sel.last')).split('.')[0])

        if end_line > start_line:  # block unindent
            self._unindent_block(start_line, end_line)
        else:
            self._unindent_single_line(start_line)
        return "break"

    def on_return(self, event):
        self.edit_separator()
        if self._comp.winfo_ismapped():
            self._comp_sel()
            return "break"

        sel = self.tag_ranges('sel')
        if sel:
            self.delete('sel.first', 'sel.last')
        line_start = self.get("insert linestart", "insert")
        line_end = self.get("insert", "insert lineend").lstrip() # remove leading spaces
        self.parse(line_start, self.index('insert linestart'))
        # find opening bracket if any on the line
        line_start_r = line_start[::-1]
        bracket_index = None
        for match in re.finditer(r'(\(|\[|\{)', line_start_r):
            open_char = match.group()
            close_char = self.autoclose[open_char]
            sub_str = line_start_r[:match.start() + 1]
            if sub_str.count(open_char) > sub_str.count(close_char):
                bracket_index = len(line_start_r) - match.start()
                break
        if bracket_index is not None:
            indent = bracket_index * ' '
        else:
            indent = (len(line_start) - len(line_start.lstrip())) * ' '
            colon = self._re_colon.search(line_start)
            if colon:
                nb_spaces = len(colon.groups()[0])
                if len(colon.group()) > 1:
                    self.delete(f'insert-{nb_spaces}c', 'insert')
                indent = indent + '    '


        self.replace('insert', 'insert lineend', f'\n{indent}')
        index = self.index('insert')
        self.insert('insert', line_end)
        self.mark_set('insert', index)
        self.master.update_nb_lines()
        # update whole syntax highlighting
        self.parse_part()
        self.master.see(self.index('insert'))
        return "break"

    def on_backspace(self, event):
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            self.delete('sel.first', 'sel.last')

        else:
            text = self.get('insert-1c', 'insert+1c')
            linestart = self.get('insert linestart', 'insert')
            if self._re_tab.search(linestart):
                self.delete('insert-4c', 'insert')
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
        self.find_matching_par()
        self.master.update_nb_lines()
        return "break"

    def duplicate_lines(self, event=None):
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            index = 'sel.last'
            line = self.get('sel.first linestart', 'sel.last lineend')
        else:
            index = 'insert'
            line = self.get('insert linestart', 'insert lineend')
        start = self.index('%s lineend +1c' % index)
        self.insert('%s lineend' % index, '\n%s' % line)
        self.parse(line, start)
        self.master.update_nb_lines()
        return "break"

    def delete_lines(self, event=None):
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            self.delete('sel.first linestart', 'sel.last lineend +1c')
        else:
            self.delete('insert linestart', 'insert lineend +1c')
        self.master.update_nb_lines()
        return "break"

    def select_all(self, event=None):
        self.tag_add('sel', '1.0', 'end')
        return "break"

    # --- comment blocks
    def toggle_comment(self, event=None):
        if CONFIG.get('Editor', 'toggle_comment_mode', fallback='line_by_line') == 'line_by_line':
            self.toggle_comment_linebyline()
        else:
            self.toggle_comment_block()

    def toggle_comment_linebyline(self):
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            text = self.get('sel.first linestart', 'sel.last lineend')
            index = self.index('sel.first linestart')
            self.delete('sel.first linestart', 'sel.last lineend')
        else:
            text = self.get('insert linestart', 'insert lineend')
            index = self.index('insert linestart')
            self.delete('insert linestart', 'insert lineend')

        marker = CONFIG.get('Editor', 'comment_marker', fallback='~')
        re_comment = re.compile(rf'^( *)(?=.*\S+.*$)(?P<comment>#{re.escape(marker)})?', re.MULTILINE)

        def subs(match):
            indent = match.group(1)
            return indent if match.group('comment') else rf'{indent}#{marker}'

        text = re_comment.sub(subs, text)

        self.insert(index, text)
        self.parse(text, index)

    def toggle_comment_block(self):
        self.edit_separator()
        sel = self.tag_ranges('sel')
        if sel:
            text = self.get('sel.first linestart', 'sel.last lineend')
            index = self.index('sel.first linestart')
            self.delete('sel.first linestart', 'sel.last lineend')
        else:
            text = self.get('insert linestart', 'insert lineend')
            index = self.index('insert linestart')
            self.delete('insert linestart', 'insert lineend')

        marker = CONFIG.get('Editor', 'comment_marker', fallback='~')
        re_comments = re.compile(rf'^( *)(#{re.escape(marker)}|$)', re.MULTILINE)
        lines = text.rstrip().splitlines()
        if len(re_comments.findall(text.rstrip())) == len(lines):
            # fully commented block -> uncomment
            text = re_comments.sub(r'\1', text)
        else:
            # at least one line is not commented: comment block
            try:
                indent = min(self._re_indents.findall(text))
            except ValueError:
                indent = ''
            re_com = re.compile(rf'^{indent}(?=.*\S+.*$)', re.MULTILINE)
            pref = rf'{indent}#{marker}'
            text = re_com.sub(pref, text)
        self.insert(index, text)
        self.parse(text, index)

    # --- change case
    def upper_case(self, event=None):
        sel = self.tag_ranges('sel')
        if sel:
            self.edit_separator()
            self.replace('sel.first', 'sel.last',
                         self.get('sel.first', 'sel.last').upper())

    def lower_case(self, event=None):
        sel = self.tag_ranges('sel')
        if sel:
            self.edit_separator()
            self.replace('sel.first', 'sel.last',
                         self.get('sel.first', 'sel.last').lower())






