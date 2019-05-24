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


Code editor text widget
"""
import jedi
from pygments import lex
import tkinter as tk
from tkinter import ttk
from pytkeditorlib import messagebox
from tkinter.font import Font
import re
from pytkeditorlib.autoscrollbar import AutoHideScrollbar
from pytkeditorlib.constants import IM_WARN, IM_ERR, get_screen,\
    load_style, PYTHON_LEX, CONFIG, valide_entree_nb
from pytkeditorlib.complistbox import CompListbox
from pytkeditorlib.tooltip import TooltipTextWrapper, Tooltip
from pytkeditorlib.filebar import FileBar


class Editor(ttk.Frame):
    def __init__(self, master=None, filetype='Python'):
        ttk.Frame.__init__(self, master, class_='Editor')

        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        self._filetype = filetype

        self._valid_nb = self.register(valide_entree_nb)

        self._syntax_icons = {'warning': tk.PhotoImage(master=self, file=IM_WARN),
                              'error': tk.PhotoImage(master=self, file=IM_ERR)}

        self._syntax_highlighting_tags = []

        self._paste = False
        self._autoclose = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        self._search_count = tk.IntVar(self)

        self.cells = []

        self._highlights = []

        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)

        self._tooltip = Tooltip(self, title='Arguments',
                                titlestyle='args.title.tooltip.TLabel')
        self._tooltip.withdraw()
        self._tooltip.bind('<FocusOut>', lambda e: self._tooltip.withdraw())

        self.file = ''

        self.text = tk.Text(self, undo=True, autoseparators=False,
                            width=81, height=45, wrap='none')

        self.sep = tk.Frame(self.text)
        self._sep_x = 0

        self.line_nb = tk.Text(self, width=1, cursor='arrow')
        self.line_nb.insert('1.0', '1')
        self.line_nb.tag_configure('right', justify='right')
        self.line_nb.tag_add('right', '1.0', 'end')
        self.line_nb.configure(state='disabled')

        self.syntax_checks = tk.Text(self, width=2, cursor='arrow',
                                     state='disabled')
        self.textwrapper = TooltipTextWrapper(self.syntax_checks, title='Syntax',
                                              titlestyle='syntax.title.tooltip.TLabel')
        self.syntax_issues_menuentries = []  # [(category, msg, command)]

        sx = AutoHideScrollbar(self, orient='horizontal', command=self.text.xview)
        sy = AutoHideScrollbar(self, orient='vertical', command=self.yview)

        def xscroll(x0, x1):
            sx.set(x0, x1)
            self.sep.place_configure(relx=self._sep_x / self.text.winfo_width() - float(x0))

        self.filebar = FileBar(self, self, width=10)
        self.text.configure(xscrollcommand=xscroll, yscrollcommand=sy.set)
        self.line_nb.configure(yscrollcommand=sy.set)
        self.syntax_checks.configure(yscrollcommand=sy.set)

        # --- search and replace
        self.frame_search = ttk.Frame(self, padding=2)
        self.frame_search.columnconfigure(1, weight=1)
        self.entry_search = ttk.Entry(self.frame_search)
        self.entry_search.bind('<Return>', self.search)
        self.entry_search.bind('<Escape>', lambda e: self.frame_search.grid_remove())
        self.entry_search.bind('<Control-r>', self.replace)
        self.entry_replace = ttk.Entry(self.frame_search)
        self.entry_replace.bind('<Control-f>', self.find)
        self.entry_replace.bind('<Escape>', lambda e: self.frame_search.grid_remove())
        search_buttons = ttk.Frame(self.frame_search)
        ttk.Button(search_buttons, style='Up.TButton', padding=0,
                   command=lambda: self.search(backwards=True)).pack(side='left', padx=2, pady=4)
        ttk.Button(search_buttons, style='Down.TButton', padding=0,
                   command=lambda: self.search(forwards=True)).pack(side='left', padx=2, pady=4)
        self.case_sensitive = ttk.Checkbutton(search_buttons, text='aA')
        self.case_sensitive.state(['selected', '!alternate'])
        self.case_sensitive.pack(side='left', padx=2, pady=4)
        self.regexp = ttk.Checkbutton(search_buttons, text='regexp')
        self.regexp.state(['!selected', '!alternate'])
        self.regexp.pack(side='left', padx=2, pady=4)
        self.full_word = ttk.Checkbutton(search_buttons, text='[-]')
        self.full_word.state(['!selected', '!alternate'])
        self.full_word.pack(side='left', padx=2, pady=4)
        self.replace_buttons = ttk.Frame(self.frame_search)
        ttk.Button(self.replace_buttons, text='Replace', padding=0,
                   command=self.replace_sel).pack(side='left', padx=2, pady=4)
        ttk.Button(self.replace_buttons, text='Replace and Find', padding=0,
                   command=self.replace_find).pack(side='left', padx=2, pady=4)
        ttk.Button(self.replace_buttons, text='Replace All', padding=0,
                   command=self.replace_all).pack(side='left', padx=2, pady=4)

        frame_find = ttk.Frame(self.frame_search)
        ttk.Button(frame_find, padding=0,
                   command=lambda: self.frame_search.grid_remove(),
                   style='close.TButton').pack(side='left')
        ttk.Label(frame_find, text='Find:').pack(side='right')
        # ------- placement
        ttk.Frame(self.frame_search, style='separator.TFrame',
                  height=1).grid(row=0, column=0, columnspan=3, sticky='ew')
        frame_find.grid(row=1, column=0, padx=2, pady=4, sticky='ew')
        self.label_replace = ttk.Label(self.frame_search, text='Replace by:')
        self.label_replace.grid(row=2, column=0, sticky='e', pady=4, padx=4)
        self.entry_search.grid(row=1, column=1, sticky='ew', pady=4, padx=2)
        self.entry_replace.grid(row=2, column=1, sticky='ew', pady=4, padx=2)
        search_buttons.grid(row=1, column=2, sticky='w')
        self.replace_buttons.grid(row=2, column=2, sticky='w')

        # --- grid
        self.text.grid(row=0, column=2, sticky='ewns')
        self.line_nb.grid(row=0, column=1, sticky='ns')
        self.syntax_checks.grid(row=0, column=0, sticky='ns')
        sx.grid(row=1, column=2, columnspan=2, sticky='ew')
        sy.grid(row=0, column=4, sticky='ns')
        self.filebar.grid(row=0, column=3, sticky='ns')
        self.frame_search.grid(row=2, column=0, columnspan=5, sticky='ew')
        self.frame_search.grid_remove()

        self.update_style()

        # --- bindings
        self.text.bind("<KeyPress>", self._on_keypress)
        self.text.bind("<KeyRelease>", self.on_key)
        self.text.bind("<ButtonPress>", self._on_press)
        self.text.bind("<KeyRelease-Up>", self._find_matching_par)
        self.text.bind("<KeyRelease-Down>", self._find_matching_par)
        self.text.bind("<KeyRelease-Left>", self._on_key_release_Left_Right)
        self.text.bind("<KeyRelease-Right>", self._on_key_release_Left_Right)
        self.text.bind("<ButtonRelease-1>", self._find_matching_par)
        self.text.bind("<Down>", self.on_down)
        self.text.bind("<Up>", self.on_up)
        self.text.bind("<<Paste>>", self.on_paste)
        self.text.bind("<apostrophe>", self.auto_close_string)
        self.text.bind("<quotedbl>", self.auto_close_string)
        self.text.bind('<parenleft>', self._args_hint)
        self.text.bind('<parenleft>', self.auto_close, True)
        self.text.bind("<bracketleft>", self.auto_close)
        self.text.bind("<braceleft>", self.auto_close)
        self.text.bind("<parenright>", self.close_brackets)
        self.text.bind("<bracketright>", self.close_brackets)
        self.text.bind("<braceright>", self.close_brackets)
        self.text.bind("<Control-z>", self.undo)
        self.text.bind("<Control-y>", self.redo)
        self.text.bind("<Control-d>", self.duplicate_lines)
        self.text.bind("<Control-k>", self.delete_lines)
        self.text.bind("<Control-a>", self.select_all)
        self.text.bind("<Control-Return>", self.on_ctrl_return)
        self.text.bind("<Return>", self.on_return)
        self.text.bind("<BackSpace>", self.on_backspace)
        self.text.bind("<Tab>", self.on_tab)
        self.text.bind("<ISO_Left_Tab>", self.unindent)
        self.text.bind('<Control-f>', self.find)
        self.text.bind('<Control-r>', self.replace)
        self.text.bind('<Control-l>', self.goto_line)
        self.text.bind('<Control-e>', self.toggle_comment)
        self.text.bind('<Configure>', self.filebar.update_positions)
        self.text.bind('<4>', self._on_b4)
        self.line_nb.bind('<4>', self._on_b4)
        self.text.bind('<5>', self._on_b5)
        self.line_nb.bind('<5>', self._on_b5)
        self.bind('<FocusOut>', self._on_focusout)

        self.text.focus_set()
        self.text.edit_modified(0)

    def _on_focusout(self, event):
        self._clear_highlights()
        self._comp.withdraw()
        self._tooltip.withdraw()

    def _on_press(self, event):
        self._clear_highlights()
        self._comp.withdraw()
        self._tooltip.withdraw()

    def _on_keypress(self, event):
        self._clear_highlights()
        self._tooltip.withdraw()

    def _on_key_release_Left_Right(self, event):
        self._comp.withdraw()
        self._find_matching_par()

    def _on_b4(self, event):
        self.yview('scroll', -3, 'units')
        return "break"

    def _on_b5(self, event):
        self.yview('scroll', 3, 'units')
        return "break"

    @property
    def filetype(self):
        return self._filetype

    @filetype.setter
    def filetype(self, filetype):
        self.reset_syntax_issues()
        self._filetype = filetype
        if filetype == 'Python':
            self.parse_all()
        else:
            for tag in self.text.tag_names():
                self.text.tag_remove(tag, '1.0', 'end')

    def update_style(self):
        FONT = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        font = Font(self, FONT)
        self._sep_x = font.measure(' ' * 79)
        self.sep.place(y=0, relheight=1, relx=self._sep_x / self.text.winfo_width(), width=1)

        EDITOR_BG, EDITOR_HIGHLIGHT_BG, EDITOR_SYNTAX_HIGHLIGHTING = load_style(CONFIG.get('Editor', 'style'))
        EDITOR_FG = EDITOR_SYNTAX_HIGHLIGHTING.get('Token.Name', {}).get('foreground', 'black')

        self._syntax_highlighting_tags = list(EDITOR_SYNTAX_HIGHLIGHTING.keys())

        self.text.configure(fg=EDITOR_FG, bg=EDITOR_BG, font=FONT,
                            selectbackground=EDITOR_HIGHLIGHT_BG,
                            inactiveselectbackground=EDITOR_HIGHLIGHT_BG,
                            insertbackground=EDITOR_FG)
        fg = self.line_nb.option_get('foreground', '*Text')
        bg = self.line_nb.option_get('background', '*Text')
        comment_fg = EDITOR_SYNTAX_HIGHLIGHTING['Token.Comment'].get('foreground', EDITOR_FG)
        self.sep.configure(bg=comment_fg)
        self.line_nb.configure(fg=fg, bg=bg, font=FONT,
                               selectbackground=bg, selectforeground=fg,
                               inactiveselectbackground=bg)
        self.syntax_checks.configure(fg=fg, bg=bg, font=FONT,
                                     selectbackground=bg, selectforeground=fg,
                                     inactiveselectbackground=bg)
        self.filebar.update_style(comment_fg=comment_fg)

        # --- syntax highlighting
        tags = list(self.text.tag_names())
        tags.remove('sel')
        tag_props = {key: '' for key in self.text.tag_configure('sel')}
        for tag in tags:
            self.text.tag_configure(tag, **tag_props)
        EDITOR_SYNTAX_HIGHLIGHTING['Token.Comment.Cell'] = EDITOR_SYNTAX_HIGHLIGHTING['Token.Comment'].copy()
        EDITOR_SYNTAX_HIGHLIGHTING['Token.Comment.Cell']['underline'] = True
        for tag, opts in EDITOR_SYNTAX_HIGHLIGHTING.items():
            self.text.tag_configure(tag, **opts)
        self.text.tag_configure('highlight', background=EDITOR_HIGHLIGHT_BG)

    def set_cells(self, cells):
        self.cells = cells
        self.filebar.clear_cells()
        for i in cells:
            self.filebar.add_mark(i, 'sep')

    def undo(self, event=None):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass
        finally:
            self.update_nb_line()
            self.parse_all()
        return "break"

    def redo(self, event=None):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass
        finally:
            self.update_nb_line()
            self.parse_all()
        return "break"

    def parse(self, text, start):
        if self.filetype != 'Python':
            return
        data = text
        while data and '\n' == data[0]:
            start = self.text.index('%s+1c' % start)
            data = data[1:]
        self.text.mark_set('range_start', start)
        for t in self._syntax_highlighting_tags:
            self.text.tag_remove(t, start, "range_start +%ic" % len(data))
        for token, content in lex(data, PYTHON_LEX):
            self.text.mark_set("range_end", "range_start + %ic" % len(content))
            for t in token.split():
                self.text.tag_add(str(t), "range_start", "range_end")
            if str(token) == 'Token.Comment.Cell':
                line, col = tuple(map(int, self.text.index("range_end").split(".")))
                if col < 79:
                    self.text.insert("range_end", " " * (79 - col), "Token.Comment.Cell")
            self.text.mark_set("range_start", "range_end")

    def parse_all(self):
        self.parse(self.text.get('1.0', 'end'), '1.0')

    def on_down(self, event):
        if self._comp.winfo_ismapped():
            self._comp.sel_next()
            return "break"
        else:
            self._clear_highlights()
            self.parse(self.text.get('insert linestart', 'insert lineend'), 'insert linestart')

    def on_up(self, event):
        if self._comp.winfo_ismapped():
            self._comp.sel_prev()
            return "break"
        else:
            self._clear_highlights()
            self.parse(self.text.get('insert linestart', 'insert lineend'), 'insert linestart')

    def on_key(self, event):
        key = event.keysym
        if key in ('Return',) + tuple(self._autoclose):
            return
        elif self._comp.winfo_ismapped():
            print(key, '%r' % event.char)
            if len(key) == 1 and key.isalnum():
                self._comp_display()
            elif key not in ['Tab', 'Down', 'Up']:
                self._comp.withdraw()
        elif (event.char in [' ', ':', ',', ';', '(', '[', '{', ')', ']', '}']
              or key in ['BackSpace', 'Left', 'Right']):
            self.text.edit_separator()
            self.parse(self.text.get("insert linestart", "insert lineend"),
                       "insert linestart")
        elif key == 'x':
            self.update_nb_line()

    def select_all(self, event):
        self.text.tag_add('sel', '1.0', 'end')
        return "break"

    def auto_close(self, event):
        sel = self.text.tag_ranges('sel')
        if sel:
            text = self.text.get('sel.first', 'sel.last')
            index = self.text.index('sel.first')
            self.text.insert('sel.first', event.char)
            self.text.insert('sel.last', self._autoclose[event.char])
            self.text.mark_set('insert', 'sel.last+1c')
            self.text.tag_remove('sel', 'sel.first', 'sel.last')
            self.parse(event.char + text + self._autoclose[event.char], index)
        else:
            self._clear_highlights()
            self.text.insert('insert', event.char, ['Token.Punctuation', 'highlight'])
            if not self._find_matching_par():
                self._highlights.append(self.text.index('insert-1c'))
                self._highlights.append(self.text.index('insert'))
                self.text.insert('insert', self._autoclose[event.char], ['Token.Punctuation', 'highlight'])
                self.text.mark_set('insert', 'insert-1c')
        self.text.edit_separator()
        return 'break'

    def auto_close_string(self, event):
        self._clear_highlights()
        sel = self.text.tag_ranges('sel')
        if sel:
            text = self.text.get('sel.first', 'sel.last')
            if len(text.splitlines()) > 1:
                char = event.char * 3
            else:
                char = event.char
            self.text.insert('sel.first', char)
            self.text.insert('sel.last', char)
            self.text.mark_set('insert', 'sel.last+%ic' % (len(char)))
            self.text.tag_remove('sel', 'sel.first', 'sel.last')
        elif self.text.get('insert') == event.char:
            self.text.mark_set('insert', 'insert+1c')
        else:
            self.text.insert('insert', event.char * 2)
            self.text.mark_set('insert', 'insert-1c')
        self.parse_all()
        self.text.edit_separator()
        return 'break'

    def close_brackets(self, event):
        self._clear_highlights()
        if self.text.get('insert') == event.char:
            self.text.mark_set('insert', 'insert+1c')
        else:
            self.text.insert('insert', event.char, 'Token.Punctuation')
        self._find_opening_par(event.char)
        return 'break'

    def on_paste(self, event):
        self._clear_highlights()
        self.text.edit_separator()
        self._paste = True
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete(*sel)
        txt = self.clipboard_get()
        self.text.insert("insert", txt)
        self.update_nb_line()
        self.parse_all()
        self.see('insert')
        return "break"

    def toggle_comment(self, event):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            lines = self.text.get('sel.first linestart', 'sel.last lineend').splitlines()
            index = self.text.index('sel.first linestart')
            self.text.delete('sel.first linestart', 'sel.last lineend')
        else:
            lines = self.text.get('insert linestart', 'insert lineend').splitlines()
            index = self.text.index('insert linestart')
            self.text.delete('insert linestart', 'insert lineend')

        for i, line in enumerate(lines):
            res = re.match(r'^( )*# ', line)
            if res:
                lines[i] = res.group()[:-2] + line[len(res.group()):]
            elif not re.match(r'^( )*$', line):
                lines[i] = re.match(r'( )*', line).group() + '# ' + line.lstrip(' ')
        txt = '\n'.join(lines)
        self.text.insert(index, txt)
        self.parse(txt, index)

    def duplicate_lines(self, event):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            index = 'sel.last'
            line = self.text.get('sel.first linestart', 'sel.last lineend')
        else:
            index = 'insert'
            line = self.text.get('insert linestart', 'insert lineend')
        start = self.text.index('%s lineend +1c' % index)
        self.text.insert('%s lineend' % index, '\n%s' % line)
        self.parse(line, start)
        self.update_nb_line()
        return "break"

    def delete_lines(self, event):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete('sel.first linestart', 'sel.last lineend +1c')
        else:
            self.text.delete('insert linestart', 'insert lineend +1c')
        self.update_nb_line()
        return "break"

    def _get_indent(self):
        line_nb, col = [int(i) for i in str(self.text.index('insert')).split('.')]
        if line_nb == 1:
            return '    '
        line_nb -= 1
        prev_line = self.text.get('%i.0' % line_nb, '%i.end' % line_nb)
        line = self.text.get('insert linestart', 'insert lineend')
        res = re.match(r'( )*', line)
        if res.span()[-1] < col:
            return '    '
        indent_prev = len(re.match(r'( )*', prev_line).group())
        indent = len(res.group())
        if indent < indent_prev:
            return ' ' * (indent_prev - indent)
        else:
            return '    '

    def on_tab(self, event):
        self._clear_highlights()
        if self._comp.winfo_ismapped():
            self._comp_sel()
            return "break"

        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            start = str(self.text.index('sel.first'))
            end = str(self.text.index('sel.last'))
            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0]) + 1
            for line in range(start_line, end_line):
                self.text.insert('%i.0' % line, '    ')
        else:
            txt = self.text.get('insert-1c')
            if not txt.isalnum() and txt != '.':
                self.text.insert('insert', self._get_indent())
            else:
                self._comp_display()
        return "break"

    def _clear_highlights(self):
        for i in self._highlights:
            self.text.tag_remove('highlight', i)
        self._highlights.clear()

    def _find_matching_par(self, event=None):
        """Highlight matching brackets."""
        char = self.text.get('insert-1c')
        if char in ['(', '{', '[']:
            return self._find_closing_par(char)
        elif char in [')', '}', ']']:
            return self._find_opening_par(char)
        else:
            return False

    def _find_closing_par(self, char):
        """Highlight the closing bracket of CHAR if it is on the same line."""
        line = self.text.get('insert', 'insert lineend')
        if not line:
            return False
        length = len(line)
        close_char = self._autoclose[char]
        stack = 1
        i = 0
        while stack > 0 and i < length:
            if line[i] == char:
                stack += 1
            elif line[i] == close_char:
                stack -= 1
            i += 1
        if stack:
            return False
        else:
            i -= 1
            self.text.tag_add('highlight', 'insert-1c')
            self.text.tag_add('highlight', 'insert+%ic' % i)
            self._highlights.append(self.text.index('insert-1c'))
            self._highlights.append(self.text.index('insert+%ic' % i))
            return True

    def _find_opening_par(self, char):
        """Highlight the opening bracket of CHAR if it is on the same line."""
        line = self.text.get('insert linestart', 'insert-1c')
        if not line:
            return False
        length = len(line)
        open_char = '(' if char == ')' else ('{' if char == '}' else '[')
        stack = 1
        i = length - 1
        while stack > 0 and i >= 0:
            if line[i] == char:
                stack += 1
            elif line[i] == open_char:
                stack -= 1
            i -= 1
        if stack:
            return False
        else:
            i += 1
            self.text.tag_add('highlight', 'insert-1c')
            self.text.tag_add('highlight', 'insert linestart+%ic' % i)
            self._highlights.append(self.text.index('insert-1c'))
            self._highlights.append(self.text.index('insert linestart+%ic' % i))
            return True

    def _args_hint(self, event=None):
        index = self.text.index('insert')
        row, col = str(index).split('.')
        script = jedi.Script(self.text.get('1.0', 'end'), int(row), int(col), self.file)
        res = script.goto_definitions()
        if res:
            try:
                args = res[-1].docstring().splitlines()[0]
            except IndexError:
                pass
            else:
                self._tooltip.configure(text=args)
                xb, yb, w, h = self.text.bbox('insert')
                xr = self.text.winfo_rootx()
                yr = self.text.winfo_rooty()
                ht = self._tooltip.winfo_reqheight()
                screen = get_screen(xr, yr)
                y = yr + yb + h
                x = xr + xb
                if y + ht > screen[3]:
                    y = yr + yb - ht
                self._tooltip.geometry('+%i+%i' % (x, y))
                self._tooltip.deiconify()

    def _comp_display(self):
        index = self.text.index('insert wordend')
        if index[-2:] != '.0':
            line = self.text.get('insert-1c wordstart', 'insert-1c wordend')
            self.text.mark_set('insert', 'insert-1c wordend')
            # i = len(line) - 1
            # while i > -1 and line[i] in self._autoclose.values():
                # i -= 1
            # self.text.mark_set('insert', 'insert wordstart +%ic' % (i))
            # print('%r' % self.text.get('insert linestart', 'insert'))
        row, col = str(self.text.index('insert')).split('.')
        script = jedi.Script(self.text.get('1.0', 'end'), int(row), int(col), self.file)
        # script = jedi.Script(self.text.get('1.0', 'insert'), int(row), int(col), self.file)

        comp = script.completions()
        self._comp.withdraw()
        if len(comp) == 1:
            self.text.insert('insert', comp[0].complete)
        elif len(comp) > 1:
            self._comp.update(comp)
            xb, yb, w, h = self.text.bbox('insert')
            xr = self.text.winfo_rootx()
            yr = self.text.winfo_rooty()
            hcomp = self._comp.winfo_reqheight()
            screen = get_screen(xr, yr)
            y = yr + yb + h
            x = xr + xb
            if y + hcomp > screen[3]:
                y = yr + yb - hcomp
            self._comp.geometry('+%i+%i' % (x, y))
            self._comp.deiconify()

    def _comp_sel(self):
        txt = self._comp.get()
        self._comp.withdraw()
        self.text.insert('insert', txt)

    def on_ctrl_return(self, event):
        self._clear_highlights()
        self.text.edit_separator()
        self.master.event_generate('<<CtrlReturn>>')
        return 'break'

    def on_return(self, event):
        self._clear_highlights()
        self.text.edit_separator()
        if self._comp.winfo_ismapped():
            self._comp_sel()
            return "break"

        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete('sel.first', 'sel.last')
        index = self.text.index('insert linestart')
        t = self.text.get("insert linestart", "insert")
        self.parse(t, index)
        indent = re.match(r'( )*', t).group()
        colon = re.search(r':( )*$', t)
        if colon:
            if len(colon.group()) > 1:
                self.text.delete('insert-%ic' % (len(colon.group()) - 1), 'insert')
            indent = indent + '    '

        self.text.insert('insert', '\n' + indent)
        self.update_nb_line()
        # update whole syntax highlighting
        self.parse_all()
        self.see('insert')
        return "break"

    def update_nb_line(self):
        row = int(str(self.text.index('end')).split('.')[0]) - 1
        row_old = int(str(self.line_nb.index('end')).split('.')[0]) - 1
        self.line_nb.configure(state='normal')
        self.syntax_checks.configure(state='normal')
        if row_old < row:
            self.syntax_checks.insert('end', '\n')
            self.line_nb.insert('end',
                                '\n' + '\n'.join([str(i) for i in range(row_old + 1, row + 1)]),
                                'right')
        elif row_old > row:
            self.line_nb.delete('%i.0' % (row + 1), 'end')
            self.syntax_checks.delete('%i.0' % (row + 1), 'end')
        self.line_nb.configure(width=len(str(row)), state='disabled')
        self.syntax_checks.configure(state='disabled')
        self.filebar.update_positions()

    def on_backspace(self, event):
        self._clear_highlights()
        self.text.edit_separator()
        txt = event.widget
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete('sel.first', 'sel.last')
        else:
            linestart = txt.get('insert linestart', 'insert')
            if re.search(r'    $', linestart):
                txt.delete('insert-4c', 'insert')
            elif txt.get('insert-1c', 'insert+1c') in [c1 + c2 for c1, c2 in self._autoclose.items()]:
                txt.delete('insert-1c', 'insert+1c')
            else:
                txt.delete('insert-1c')
        self.update_nb_line()
        return "break"

    def unindent(self, event):
        self.text.edit_separator()
        txt = event.widget
        sel = txt.tag_ranges('sel')
        if sel:
            start = str(txt.index('sel.first'))
            end = str(txt.index('sel.last'))
        else:
            start = str(txt.index('insert'))
            end = str(txt.index('insert'))
        start_line = int(start.split('.')[0])
        end_line = int(end.split('.')[0]) + 1
        for line in range(start_line, end_line):
            if txt.get('%i.0' % line, '%i.4' % line) == '    ':
                txt.delete('%i.0' % line, '%i.4' % line)
        return "break"

    def yview(self, *args):
        self.line_nb.yview(*args)
        self.syntax_checks.yview(*args)
        res = self.text.yview(*args)
        if args:
            self.filebar.update_positions()
        return res

    # --- find and replace
    def find(self, event=None):
        self.label_replace.grid_remove()
        self.entry_replace.grid_remove()
        self.replace_buttons.grid_remove()
        self.frame_search.grid()
        self.entry_search.focus_set()
        sel = self.text.tag_ranges('sel')
        if sel:
            self.entry_search.delete(0, 'end')
            self.entry_search.insert(0, self.text.get('sel.first', 'sel.last'))
        self.entry_search.selection_range(0, 'end')
        return "break"

    def replace(self, event=None):
        self.entry_replace.grid()
        self.label_replace.grid()
        self.replace_buttons.grid()
        self.frame_search.grid()
        self.entry_search.focus_set()
        sel = self.text.tag_ranges('sel')
        if sel:
            self.entry_search.delete(0, 'end')
            self.entry_search.insert(0, self.text.get('sel.first', 'sel.last'))
        self.entry_search.selection_range(0, 'end')
        return "break"

    def replace_sel(self, notify_no_match=True):
        self.text.edit_separator()
        pattern = self.entry_search.get()
        new_text = self.entry_replace.get()
        sel = self.text.tag_ranges('sel')
        if not sel:
            self.search(notify_no_match=notify_no_match)
            return False
        else:
            sel_text = self.text.get('sel.first', 'sel.last')
            regexp = 'selected' in self.regexp.state()
            if ((regexp and re.search('^' + pattern + '$', sel_text))
               or (not regexp and pattern == sel_text)):
                self.text.replace('sel.first', 'sel.last', new_text)
                return True
            else:
                self.search(notify_no_match=notify_no_match)
                return False

    def replace_find(self):
        if self.replace_sel():
            self.search()

    def replace_all(self):
        self.text.edit_separator()
        res = True
        self.text.mark_set('insert', '1.0')
        # replace all occurences in text
        while res:
            self.search(notify_no_match=False, stopindex='end')
            res = self.replace_sel(notify_no_match=False)

    def search(self, event=None, backwards=False, notify_no_match=True, **kw):
        pattern = self.entry_search.get()
        full_word = 'selected' in self.full_word.state()
        options = {'regexp': 'selected' in self.regexp.state(),
                   'nocase': 'selected' not in self.case_sensitive.state(),
                   'count': self._search_count}
        options.update(kw)
        if backwards:
            options['backwards'] = True
        else:  # forwards
            options['forwards'] = True

        res = self.text.search(pattern, 'insert', **options)

        if res and full_word:
            index = 'start'
            end_word = self.text.index(res + ' wordend')
            end_res = self.text.index(res + '+%ic' % self._search_count.get())

            while index and index != res and end_word != end_res:
                index = self.text.search(pattern, end_res, **options)
                end_word = self.text.index(index + ' wordend')
                end_res = self.text.index(index + '+%ic' % self._search_count.get())

            if index != 'start':
                res = index

        self.text.tag_remove('sel', '1.0', 'end')
        if res:
            self.text.tag_add('sel', res, '%s+%ic' % (res, self._search_count.get()))
            if backwards:
                self.text.mark_set('insert', '%s-1c' % (res))
            else:
                self.text.mark_set('insert', '%s+%ic' % (res, self._search_count.get()))
            self.see(res)
        else:
            if notify_no_match:
                messagebox.showinfo("Search complete", "No match found", self)

    # --- goto
    def goto_line(self, event=None):

        def goto(event):
            try:
                line = int(e.get())
                self.see('%i.0' % line)
                self.text.mark_set('insert', '%i.0' % line)
            except ValueError:
                pass
            finally:
                top.destroy()

        top = tk.Toplevel(self)
        top.transient(self)
        top.geometry('+%i+%i' % self.winfo_pointerxy())
        top.grab_set()
        top.title('Go to')

        ttk.Label(top, text='Line: ').pack(side='left', padx=4, pady=4)
        e = ttk.Entry(top, width=5, justify='center', validate='key',
                      validatecommand=(self._valid_nb, '%d', "%S"))
        e.pack(side='left', padx=4, pady=4)
        e.focus_set()
        e.bind('<Escape>', lambda e: top.destroy())
        e.bind('<Return>', goto)

    def goto_item(self, start, end):
        self.see(start)
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_add('sel', start, end)

    def get(self, strip=True):
        txt = self.text.get('1.0', 'end')
        if strip:
            yview = self.text.yview()[0]
            index = self.text.index('insert')
            txt = txt.splitlines()
            for i, line in enumerate(txt):
                txt[i] = line[:re.search(r'( )*$', line).span()[0]]
            txt = '\n'.join(txt)
            self.text.delete('1.0', 'end')
            self.text.insert('1.0', txt)
            self.parse_all()
            self.text.mark_set('insert', index)
            self.yview('moveto', yview)
        self.text.edit_separator()
        return txt

    def get_end(self):
        return str(self.text.index('end'))

    def get_docstring(self, obj):
        txt = self.text.get('1.0', 'end')
        script = jedi.Script(txt + obj, len(txt.splitlines()) + 1,
                             len(obj), self.file)
        res = script.goto_definitions()
        if res:
            return res[-1]
        else:
            return None

    def delete(self, index1, index2=None):
        self.text.edit_separator()
        self.text.delete(index1, index2=index2)
        self.update_nb_line()
        self.parse_all()

    def insert(self, index, text):
        self.text.edit_separator()
        self.text.insert(index, text)
        self.update_nb_line()
        self.parse_all()

    def see(self, index):
        i = self.text.index(index)
        self.text.see(i)
        self.line_nb.see(i)
        self.syntax_checks.see(i)

    # --- syntax issues highlighting
    def show_line(self, line):
        self.see('%i.0' % line)
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_add('sel', '%i.0' % line, '%i.end' % line)

    def reset_syntax_issues(self):
        self.syntax_checks.configure(state='normal')
        self.syntax_checks.delete('1.0', 'end')
        self.syntax_issues_menuentries.clear()
        self.textwrapper.reset()
        self.filebar.clear_syntax_issues()
        end = int(str(self.text.index('end')).split('.')[0]) - 2
        self.syntax_checks.insert('end', '\n' * end)

    def show_syntax_issues(self, results):
        self.reset_syntax_issues()
        for line, (category, msgs, msg) in results.items():
            self.syntax_checks.image_create('%i.0' % line,
                                            image=self._syntax_icons[category])
            self.syntax_checks.tag_add(str(line), '%i.0' % line)
            self.filebar.add_mark(line, category)
            self.textwrapper.add_tooltip(str(line), msg)
            for m in msgs:
                self.syntax_issues_menuentries.append((category, m, lambda l=line: self.show_line(l)))
        self.syntax_checks.configure(state='disabled')
        self.syntax_checks.yview_moveto(self.line_nb.yview()[0])
