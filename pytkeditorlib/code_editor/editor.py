
#! /usr/bin/python3
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
import jedi
import re
from glob import glob
from os.path import sep
from pygments import lex
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font

from pytkeditorlib.dialogs.complistbox import CompListbox
from pytkeditorlib.dialogs import showerror, showinfo, \
    TooltipTextWrapper, Tooltip, ColorPicker
from pytkeditorlib.gui_utils import AutoHideScrollbar, EntryHistory
from pytkeditorlib.utils.constants import PYTHON_LEX, CONFIG, IMAGES, \
    get_screen, load_style, valide_entree_nb, PathCompletion
from .filebar import FileBar


class Editor(ttk.Frame):
    def __init__(self, master=None, filetype='Python'):
        ttk.Frame.__init__(self, master, class_='Editor')

        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        # --- regexp
        self._re_paths = re.compile(rf'("|\')(\{sep}\w+)+\{sep}?$')
        self._re_empty = re.compile(r'^ *$')
        self._re_indent = re.compile(r'^( *)')
        self._re_indents = re.compile(r'^( *)(?=.*\S+.*$)', re.MULTILINE)
        self._re_tab = re.compile(r' {4}$')
        self._re_colon = re.compile(r':( *)$')

        self._filetype = filetype

        self._valid_nb = self.register(valide_entree_nb)

        self._syntax_icons = {'warning': tk.PhotoImage(master=self, file=IMAGES['warning']),
                              'error': tk.PhotoImage(master=self, file=IMAGES['error'])}

        self._syntax_highlighting_tags = []

        self._paste = False
        self._autoclose = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        self._search_count = tk.IntVar(self)

        self.cells = []

        # --- GUI elements
        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)

        self._tooltip = Tooltip(self, title='Arguments',
                                titlestyle='args.title.tooltip.TLabel')
        self._tooltip.withdraw()
        self._tooltip.bind('<FocusOut>', lambda e: self._tooltip.withdraw())

        self.file = ''

        self.text = tk.Text(self, undo=True, autoseparators=False,
                            width=81, height=45, wrap='none', cursor='watch')

        self.sep = tk.Frame(self.text)
        self._sep_x = 0

        self.line_nb = tk.Text(self, width=1, cursor='watch')
        self.line_nb.insert('1.0', '1')
        self.line_nb.tag_configure('right', justify='right')
        self.line_nb.tag_add('right', '1.0', 'end')
        self.line_nb.configure(state='disabled')

        self.syntax_checks = tk.Text(self, width=2, cursor='watch',
                                     state='disabled')
        self.textwrapper = TooltipTextWrapper(self.syntax_checks, title='Syntax',
                                              titlestyle='syntax.title.tooltip.TLabel')
        self.syntax_issues_menuentries = []  # [(category, msg, command)]

        sx = AutoHideScrollbar(self, orient='horizontal', command=self.text.xview)
        sy = AutoHideScrollbar(self, orient='vertical', command=self.yview)

        def xscroll(x0, x1):
            sx.set(x0, x1)
            self.sep.place_configure(relx=self._sep_x / self.text.winfo_width() - float(x0))

        self.filebar = FileBar(self, self, width=10, cursor='watch')
        self.text.configure(xscrollcommand=xscroll, yscrollcommand=sy.set)
        self.line_nb.configure(yscrollcommand=sy.set)
        self.syntax_checks.configure(yscrollcommand=sy.set)
        self.update_idletasks()

        # --- search and replace
        self._highlighted = ''
        self.frame_search = ttk.Frame(self, padding=2)
        self.frame_search.columnconfigure(1, weight=1)
        self.entry_search = EntryHistory(self.frame_search)
        self.entry_search.bind('<Return>', self.search)
        self.entry_search.bind('<Escape>', lambda e: self.frame_search.grid_remove())
        self.entry_search.bind('<Control-r>', self.replace)
        self.entry_search.bind('<Control-f>', self.find)
        self.entry_replace = EntryHistory(self.frame_search)
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
        self._highlight_btn = ttk.Checkbutton(search_buttons, image='img_highlight',
                                              padding=0, style='toggle.TButton',
                                              command=self.highlight_all)
        self._highlight_btn.pack(side='left', padx=2, pady=4)
        self.replace_buttons = ttk.Frame(self.frame_search)
        ttk.Button(self.replace_buttons, text='Replace', padding=0,
                   command=self.replace_sel).pack(side='left', padx=2, pady=4)
        ttk.Button(self.replace_buttons, text='Replace and Find', padding=0,
                   command=self.replace_find).pack(side='left', padx=2, pady=4)
        ttk.Button(self.replace_buttons, text='Replace All', padding=0,
                   command=self.replace_all).pack(side='left', padx=2, pady=4)

        frame_find = ttk.Frame(self.frame_search)
        ttk.Button(frame_find, padding=0,
                   command=self.hide_search,
                   style='close.TButton').pack(side='left')
        ttk.Label(frame_find, text='Find:').pack(side='right')
        # --- --- placement
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
        self.text.bind("<Control-w>", lambda e: "break")
        self.text.bind("<Control-h>", lambda e: "break")
        self.text.bind("<Control-i>", self.inspect)
        self.text.bind("<Control-b>", lambda e: "break")
        self.text.bind("<Control-t>", lambda e: "break")
        self.text.bind("<Control-z>", self.undo)
        self.text.bind("<Control-y>", self.redo)
        self.text.bind("<Control-d>", self.duplicate_lines)
        self.text.bind("<Control-k>", self.delete_lines)
        self.text.bind("<Control-a>", self.select_all)
        self.text.bind("<Control-u>", self.upper_case)
        self.text.bind("<Control-Shift-U>", self.lower_case)
        self.text.bind("<Control-Shift-C>", self.choose_color)
        self.text.bind("<Control-Return>", self.on_ctrl_return)
        self.text.bind("<Shift-Return>", self.on_shift_return)
        self.text.bind("<Return>", self.on_return)
        self.text.bind("<BackSpace>", self.on_backspace)
        self.text.bind("<Tab>", self.on_tab)
        self.text.bind("<ISO_Left_Tab>", self.unindent)
        self.text.bind('<Control-f>', self.find)
        self.text.bind('<Control-r>', self.replace)
        self.text.bind('<Control-l>', self.goto_line)
        self.text.bind('<Control-Down>', self.goto_next_cell)
        self.text.bind('<Control-Up>', self.goto_prev_cell)
        self.text.bind('<Control-e>', self.toggle_comment)
        self.text.bind('<Configure>', self.filebar.update_positions)
        # vertical scrolling
        self.text.bind('<4>', self._on_b4)
        self.line_nb.bind('<4>', self._on_b4)
        self.text.bind('<5>', self._on_b5)
        self.line_nb.bind('<5>', self._on_b5)
        # horizontal scrolling
        self.text.bind('<Shift-4>', self._on_sb4)
        self.text.bind('<Shift-5>', self._on_sb5)
        self.bind('<FocusOut>', self._on_focusout)

        self.text.focus_set()
        self.text.edit_modified(0)

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

    def update_cells(self):
        count = tk.IntVar(self)
        pattern = r'^#( In\[.*\]| ?%%).*$'
        options = {'regexp': True,
                   'nocase': False,
                   'count': count,
                   'stopindex': 'end'}
        cells = []
        res = self.text.search(pattern, '1.0', **options)
        while res:
            cells.append(int(res.split(".")[0]))
            end = f"{res}+{count.get()}c"
            res = self.text.search(pattern, end, **options)
        self.set_cells(cells)

    def set_cells(self, cells):
        self.cells = cells
        self.filebar.clear_cells()
        for i in cells:
            self.filebar.add_mark(i, 'sep')

    # --- keyboard bindings
    def _on_focusout(self, event):
        self._clear_highlight()
        self._comp.withdraw()
        self._tooltip.withdraw()

    def _on_press(self, event):
        self._clear_highlight()
        self._comp.withdraw()
        self._tooltip.withdraw()

    def _on_keypress(self, event):
        self._clear_highlight()
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

    def _on_sb4(self, event):
        self.text.xview('scroll', -3, 'units')
        return "break"

    def _on_sb5(self, event):
        self.text.xview('scroll', 3, 'units')
        return "break"

    def undo(self, event=None):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass
        else:
            self.update_nb_line()
            self.parse_part(nblines=100)
        return "break"

    def redo(self, event=None):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass
        else:
            self.update_nb_line()
            self.parse_part(nblines=100)
        return "break"

    def on_down(self, event):
        if self._comp.winfo_ismapped():
            self._comp.sel_next()
            return "break"
        else:
            self._clear_highlight()
            self.parse(self.text.get('insert linestart', 'insert lineend'), 'insert linestart')

    def on_up(self, event):
        if self._comp.winfo_ismapped():
            self._comp.sel_prev()
            return "break"
        else:
            self._clear_highlight()
            self.parse(self.text.get('insert linestart', 'insert lineend'), 'insert linestart')

    def on_key(self, event):
        key = event.keysym
        if key in ('Return',) + tuple(self._autoclose):
            return
        elif self._comp.winfo_ismapped():
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

    def select_all(self, event=None):
        self.text.tag_add('sel', '1.0', 'end')
        return "break"

    def on_paste(self, event):
        self._clear_highlight()
        self.text.edit_separator()
        self._paste = True
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete(*sel)
        txt = self.clipboard_get()
        self.text.insert("insert", txt)
        self.update_nb_line()
        lines = len(txt.splitlines())//2
        self.parse_part(f'insert linestart - {lines} lines', nblines=lines + 10)
        self.see('insert')
        return "break"


    def toggle_comment(self, event=None):
        if CONFIG.get('Editor', 'toggle_comment_mode', fallback='line_by_line') == 'line_by_line':
            self.toggle_comment_linebyline()
        else:
            self.toggle_comment_block()

    def toggle_comment_linebyline(self):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            text = self.text.get('sel.first linestart', 'sel.last lineend')
            index = self.text.index('sel.first linestart')
            self.text.delete('sel.first linestart', 'sel.last lineend')
        else:
            text = self.text.get('insert linestart', 'insert lineend')
            index = self.text.index('insert linestart')
            self.text.delete('insert linestart', 'insert lineend')

        marker = CONFIG.get('Editor', 'comment_marker', fallback='~')
        re_comment = re.compile(rf'^( *)(?=.*\S+.*$)(?P<comment>#{re.escape(marker)})?', re.MULTILINE)

        def subs(match):
            indent = match.group(1)
            return indent if match.group('comment') else rf'{indent}#{marker}'

        text = re_comment.sub(subs, text)

        self.text.insert(index, text)
        self.parse(text, index)

    def toggle_comment_block(self):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            text = self.text.get('sel.first linestart', 'sel.last lineend')
            index = self.text.index('sel.first linestart')
            self.text.delete('sel.first linestart', 'sel.last lineend')
        else:
            text = self.text.get('insert linestart', 'insert lineend')
            index = self.text.index('insert linestart')
            self.text.delete('insert linestart', 'insert lineend')

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
        self.text.insert(index, text)
        self.parse(text, index)

    def duplicate_lines(self, event=None):
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

    def delete_lines(self, event=None):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete('sel.first linestart', 'sel.last lineend +1c')
        else:
            self.text.delete('insert linestart', 'insert lineend +1c')
        self.update_nb_line()
        return "break"

    def on_tab(self, event=None, force_indent=False):
        self._clear_highlight()
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
            txt = self.text.get('insert linestart', 'insert')
            if force_indent:
                self.text.insert('insert linestart', self._get_indent())
            elif txt == ' ' * len(txt):
                self.text.insert('insert', self._get_indent())
            else:
                self._comp_display()
        return "break"

    def on_ctrl_return(self, event):
        self._clear_highlight()
        self.text.edit_separator()
        self.master.event_generate('<<CtrlReturn>>')
        return 'break'

    def on_shift_return(self, event):
        self._clear_highlight()
        self.text.edit_separator()
        self.master.event_generate('<<ShiftReturn>>')
        return 'break'

    def on_return(self, event):
        self._clear_highlight()
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
        indent = self._re_indent.match(t).group()
        colon = self._re_colon.search(t)
        if colon:
            nb_spaces = len(colon.groups()[0])
            if len(colon.group()) > 1:
                self.text.delete(f'insert-{nb_spaces}c', 'insert')
            indent = indent + '    '

        self.text.insert('insert', '\n' + indent)
        self.update_nb_line()
        # update whole syntax highlighting
        self.parse_part()
        self.see('insert')
        return "break"

    def on_backspace(self, event):
        self._clear_highlight()
        self.text.edit_separator()
        txt = event.widget
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete('sel.first', 'sel.last')
        else:
            text = txt.get('insert-1c', 'insert+1c')
            linestart = txt.get('insert linestart', 'insert')
            if self._re_tab.search(linestart):
                txt.delete('insert-4c', 'insert')
            elif text in ["()", "[]", "{}"]:
                txt.delete('insert-1c', 'insert+1c')
            elif text in ["''"]:
                if 'Token.Literal.String.Single' not in self.text.tag_names('insert-2c'):
                    # avoid situation where deleting the 2nd quote in '<text>'' result in deletion of both the 2nd and 3rd quotes
                    txt.delete('insert-1c', 'insert+1c')
                else:
                    txt.delete('insert-1c')
            elif text in ['""']:
                if 'Token.Literal.String.Double' not in self.text.tag_names('insert-2c'):
                    # avoid situation where deleting the 2nd quote in "<text>"" result in deletion of both the 2nd and 3rd quotes
                    txt.delete('insert-1c', 'insert+1c')
                else:
                    txt.delete('insert-1c')
            else:
                txt.delete('insert-1c')
        self.update_nb_line()
        self._find_matching_par()
        return "break"

    def unindent(self, event=None):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            start = str(self.text.index('sel.first'))
            end = str(self.text.index('sel.last'))
        else:
            start = str(self.text.index('insert'))
            end = str(self.text.index('insert'))
        start_line = int(start.split('.')[0])
        end_line = int(end.split('.')[0]) + 1
        for line in range(start_line, end_line):
            if self.text.get('%i.0' % line, '%i.4' % line) == '    ':
                self.text.delete('%i.0' % line, '%i.4' % line)
        return "break"

    # --- style and syntax highlighting
    def busy(self, busy):
        if busy:
            self.text.configure(cursor='watch')
            self.line_nb.configure(cursor='watch')
            self.syntax_checks.configure(cursor='watch')
            self.filebar.configure(cursor='watch')
        else:
            self.text.configure(cursor='xterm')
            self.line_nb.configure(cursor='arrow')
            self.syntax_checks.configure(cursor='arrow')
            self.filebar.configure(cursor='arrow')

    def update_style(self):
        FONT = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        font = Font(self, FONT)
        self._sep_x = font.measure(' ' * 79)
        self.sep.place(y=0, relheight=1, relx=self._sep_x / self.text.winfo_width(), width=1)

        EDITOR_BG, EDITOR_HIGHLIGHT_BG, EDITOR_SYNTAX_HIGHLIGHTING = load_style(CONFIG.get('Editor', 'style'))
        EDITOR_FG = EDITOR_SYNTAX_HIGHLIGHTING.get('Token.Name', {}).get('foreground', 'black')

        self._syntax_highlighting_tags = list(EDITOR_SYNTAX_HIGHLIGHTING.keys())

        theme = f"{CONFIG.get('General', 'theme').capitalize()} Theme"
        selectbg = CONFIG.get(theme, 'textselectbg')
        selectfg = CONFIG.get(theme, 'textselectfg')
        self.text.configure(fg=EDITOR_FG, bg=EDITOR_BG, font=FONT,
                            selectbackground=selectbg,
                            selectforeground=selectfg,
                            inactiveselectbackground=selectbg,
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
            opts['selectbackground'] = selectbg
            opts['selectforeground'] = selectfg
            self.text.tag_configure(tag, **opts)
        self.text.tag_configure('highlight_find', background=EDITOR_HIGHLIGHT_BG)
        # bracket matching:  fg;bg;font formatting
        mb = CONFIG.get('Editor', 'matching_brackets', fallback='#00B100;;bold').split(';')
        opts = {'foreground': mb[0], 'background': mb[1], 'font': FONT + tuple(mb[2:])}
        self.text.tag_configure('matching_brackets', **opts)
        umb = CONFIG.get('Editor', 'unmatched_bracket', fallback='#FF0000;;bold').split(';')
        opts = {'foreground': umb[0], 'background': umb[1], 'font': FONT + tuple(umb[2:])}
        self.text.tag_configure('unmatched_bracket', **opts)
        self.text.tag_raise('sel')

    def parse(self, text, start):
        """Apply syntax highlighting to text at index start"""
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

    def parse_part(self, current='insert', nblines=10):
        start = f"{current} - {nblines} lines linestart"
        self.parse(self.text.get(start, f"{current} + {nblines} lines lineend"), start)

    def parse_all(self):
        self.parse(self.text.get('1.0', 'end'), '1.0')

    def strip(self):
        res = self.text.search(r' +$', '1.0', regexp=True)
        while res:
            end = f"{res} lineend"
            self.text.delete(res, end)
            res = self.text.search(r' +$', end, regexp=True)

    # --- brackets
    def _clear_highlight(self):
        self.text.tag_remove('matching_brackets', '1.0', 'end')
        self.text.tag_remove('unmatched_bracket', '1.0', 'end')

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
            self._clear_highlight()
            self.text.insert('insert', event.char, ['Token.Punctuation', 'matching_brackets'])
            if not self._find_matching_par():
                self.text.tag_remove('unmatched_bracket', 'insert-1c')
                self.text.insert('insert', self._autoclose[event.char], ['Token.Punctuation', 'matching_brackets'])
                self.text.mark_set('insert', 'insert-1c')
        self.text.edit_separator()
        return 'break'

    def auto_close_string(self, event):
        self._clear_highlight()
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
        self.parse_part()
        self.text.edit_separator()
        return 'break'

    def close_brackets(self, event):
        self._clear_highlight()
        if self.text.get('insert') == event.char:
            self.text.mark_set('insert', 'insert+1c')
        else:
            self.text.insert('insert', event.char, 'Token.Punctuation')
        self._find_opening_par(event.char)
        return 'break'

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
        close_char = self._autoclose[char]
        index = 'insert'
        close_index = self.text.search(close_char, 'insert', 'end')
        stack = 1
        while stack > 0 and close_index:
            stack += self.text.get(index, close_index).count(char) - 1
            index = close_index + '+1c'
            close_index = self.text.search(close_char, index, 'end')
        if stack == 0:
            self.text.tag_add('matching_brackets', 'insert-1c')
            self.text.tag_add('matching_brackets', index + '-1c')
            return True
        else:
            self.text.tag_add('unmatched_bracket', 'insert-1c')
            return False

    def _find_opening_par(self, char):
        """Highlight the opening bracket of CHAR if it is on the same line."""
        open_char = '(' if char == ')' else ('{' if char == '}' else '[')
        index = 'insert-1c'
        open_index = self.text.search(open_char, 'insert', '1.0', backwards=True)
        stack = 1
        while stack > 0 and open_index:
            stack += self.text.get(open_index + '+1c', index).count(char) - 1
            index = open_index
            open_index = self.text.search(open_char, index, '1.0', backwards=True)
        if stack == 0:
            self.text.tag_add('matching_brackets', 'insert-1c')
            self.text.tag_add('matching_brackets', index)
            return True
        else:
            self.text.tag_add('unmatched_bracket', 'insert-1c')
            return False

    # --- autocompletion and help tooltips
    def _args_hint(self, event=None):
        index = self.text.index('insert')
        row, col = str(index).split('.')
        try:
            script = jedi.Script(self.text.get('1.0', 'end'), int(row), int(col), self.file)
            res = script.goto_definitions()
        except Exception:
            # jedi raised an exception
            return
        if res:
            try:
                args = res[-1].docstring().splitlines()[0]
            except Exception:
                # usually caused by an exception raised in Jedi
                return
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
            self.text.mark_set('insert', 'insert-1c wordend')

        # --- path autocompletion
        line = self.text.get('insert linestart', 'insert')
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
            row, col = str(self.text.index('insert')).split('.')
            try:
                script = jedi.Script(self.text.get('1.0', 'end'), int(row), int(col), self.file)
                comp = script.completions()
            except Exception:
                # jedi raised an exception
                return
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

    # --- find and replace
    def hide_search(self):
        self.text.tag_remove('highlight_find', '1.0', 'end')
        self._highlight_btn.state(['!selected'])
        self.frame_search.grid_remove()

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
        self.entry_search.add_to_history(pattern)
        new_text = self.entry_replace.get()
        self.entry_replace.add_to_history(new_text)
        sel = self.text.tag_ranges('sel')
        if not sel:
            self.search(notify_no_match=notify_no_match)
            return False
        else:
            sel_text = self.text.get('sel.first', 'sel.last')
            regexp = 'selected' in self.regexp.state()
            if regexp:
                if 'selected' in self.full_word.state():
                    # full word: \b at the end
                    pattern = r"\b{}\b".format(pattern)
                if 'selected' not in self.case_sensitive.state():
                    # ignore case: (?i) at the start
                    pattern = r"(?i)" + pattern
                cpattern = re.compile('^' + pattern + '$')
                if cpattern.match(sel_text):
                    try:
                        replacement = re.sub(pattern, new_text, sel_text)
                    except re.error as e:
                        showerror("Error", f"Replacement error: {e.msg}", parent=self)
                        return False
                    self.text.replace('sel.first', 'sel.last', replacement)
                    return True
            elif pattern == sel_text:
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

    def replace_text(self, start, end, pattern, repl):
        self.text.edit_separator()
        new_text = pattern.sub(repl, self.text.get(start, end))
        self.text.delete(start, end)
        self.text.insert(start, new_text)

    def search(self, event=None, backwards=False, notify_no_match=True, **kw):
        pattern = self.entry_search.get()
        self.entry_search.add_to_history(pattern)
        full_word = 'selected' in self.full_word.state()
        options = {'regexp': 'selected' in self.regexp.state(),
                   'nocase': 'selected' not in self.case_sensitive.state(),
                   'count': self._search_count}
        options.update(kw)
        if backwards:
            options['backwards'] = True
        else:  # forwards
            options['forwards'] = True

        if full_word:
            pattern = r'\y%s\y' % pattern
            options['regexp'] = True

        self.highlight_all()
        res = self.text.search(pattern, 'insert', **options)

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
                showinfo("Search complete", "No match found", self)

    def highlight_all(self):
        if 'selected' in self._highlight_btn.state():
            pattern = self.entry_search.get()
            self.entry_search.add_to_history(pattern)

            if not pattern:
                self._highlight_btn.state(['!selected'])
                return
            if self._highlighted == pattern and self.text.tag_ranges('highlight_find'):
                return

            self._highlighted = pattern
            self.text.tag_remove('highlight_find', '1.0', 'end')

            full_word = 'selected' in self.full_word.state()
            options = {'regexp': 'selected' in self.regexp.state(),
                       'nocase': 'selected' not in self.case_sensitive.state(),
                       'count': self._search_count, 'stopindex': 'end'}

            if full_word:
                pattern = r'\y%s\y' % pattern
                options['regexp'] = True
            res = self.text.search(pattern, '1.0', **options)
            while res:
                end = f"{res}+{self._search_count.get()}c"
                self.text.tag_add('highlight_find', res, end)
                res = self.text.search(pattern, end, **options)
        else:
            self.text.tag_remove('highlight_find', '1.0', 'end')

    def find_all(self, pattern, options={}):
        results = []
        res = self.text.search(pattern, '1.0', count=self._search_count, **options)
        while res:
            end = f"{res}+{self._search_count.get()}c"
            results.append((res, end, self.text.get(res + " linestart", end + " lineend")))
            res = self.text.search(pattern, end, count=self._search_count,
                                   **options)
        return results

    # --- change case
    def upper_case(self, event=None):
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.edit_separator()
            self.text.replace('sel.first', 'sel.last',
                              self.text.get('sel.first', 'sel.last').upper())

    def lower_case(self, event=None):
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.edit_separator()
            self.text.replace('sel.first', 'sel.last',
                              self.text.get('sel.first', 'sel.last').lower())

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

    def goto_prev_cell(self, event):
        if not self.cells:
            return
        line = int(str(self.text.index('insert')).split('.')[0])
        i = 0
        while i < len(self.cells) and self.cells[i] < line:
            i += 1
        if i == 1:
            self.text.mark_set('insert', "1.0")
        elif i > 1:
            self.text.mark_set('insert', f"{self.cells[i - 2]}.0 + 1 lines")
            self.text.see('insert')
        return "break"

    def goto_next_cell(self, event):
        if not self.cells:
            return
        line = int(str(self.text.index('insert')).split('.')[0])
        i = 0
        while i < len(self.cells) and self.cells[i] < line:
            i += 1
        if i < len(self.cells):
            self.text.mark_set('insert', f"{self.cells[i]}.0 + 1 lines")
            self.text.see('insert')
        return "break"

    # --- get
    def get(self, strip=True):
        txt = self.text.get('1.0', 'end')
        if strip:
            self.strip()
        self.text.edit_separator()
        return txt

    def get_selection(self):
        sel = self.text.tag_ranges('sel')
        if sel:
            return self.text.get('sel.first', 'sel.last')

    def _get_indent(self):
        line_nb, col = [int(i) for i in str(self.text.index('insert')).split('.')]
        if line_nb == 1:
            return '    '
        line_nb -= 1
        prev_line = self.text.get('%i.0' % line_nb, '%i.end' % line_nb)
        line = self.text.get('insert linestart', 'insert lineend')
        res = self._re_indent.match(line)
        if res.end() < col:
            return '    '
        indent_prev = len(self._re_indent.match(prev_line).group())
        indent = len(res.group())
        if indent < indent_prev:
            return ' ' * (indent_prev - indent)
        else:
            return '    '

    def get_end(self):
        return str(self.text.index('end'))

    def get_cell(self, goto_next=False):
        self.update_cells()
        if not self.cells:
            return ''
        line = int(str(self.text.index('insert')).split('.')[0])
        i = 0
        while i < len(self.cells) and self.cells[i] < line:
            i += 1
        if i == len(self.cells):
            start = '%i.0' % self.cells[-1]
            end = self.text.index('end')
        elif i > 0:
            start = '%i.0' % self.cells[i - 1]
            end = '%i.0' % self.cells[i]
        else:
            start = '1.0'
            end = '%i.0' % self.cells[i]
        if goto_next:
            self.text.mark_set('insert', f"{end} + 1 lines")
            self.text.see("insert")
        return self.text.get(start, end)

    # --- docstrings
    def get_docstring(self, obj):
        txt = self.text.get('1.0', 'end')
        script = jedi.Script(txt + obj, len(txt.splitlines()) + 1,
                             len(obj), self.file)
        res = script.goto_definitions()
        if res:
            return res[-1]
        else:
            return None

    def inspect(self, event):
        try:
            self._inspect_obj = self.text.get('sel.first', "sel.last"), "Editor"
        except tk.TclError:
            return "break"
        self.event_generate('<<Inspect>>')
        return "break"

    # --- text edit
    def delete(self, index1, index2=None):
        self.text.edit_separator()
        self.text.delete(index1, index2=index2)
        self.update_nb_line()
        self.parse_part()

    def insert(self, index, text, replace_sel=False):
        self.text.edit_separator()
        if replace_sel:
            sel = self.text.tag_ranges('sel')
            if sel:
                self.text.delete('sel.first', 'sel.last')
        self.text.insert(index, text)
        self.update_nb_line()
        lines = len(text.splitlines())//2
        self.parse_part(f'insert linestart - {lines} lines', nblines=lines + 10)

    def choose_color(self, event=None):

        def insert(event):
            color = picker.get_color()
            if color:
                self.insert("insert", color, True)

        picker = ColorPicker(color=self.get_selection(), parent=self)
        picker.bind("<<ColorSelected>>", insert)

    # --- view
    def see(self, index):
        i = self.text.index(index)
        self.text.see(i)
        self.line_nb.see(i)
        self.syntax_checks.see(i)

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

    def yview(self, *args):
        self.line_nb.yview(*args)
        self.syntax_checks.yview(*args)
        res = self.text.yview(*args)
        if args:
            self.filebar.update_positions()
        return res

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
