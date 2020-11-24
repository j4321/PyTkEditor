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


Code editor tab
"""
import re
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font

import jedi
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, ClassNotFound

from pytkeditorlib.dialogs import showerror, showinfo, \
    TooltipTextWrapper, ColorPicker, TooltipWrapper
from pytkeditorlib.gui_utils import AutoHideScrollbar, EntryHistory
from pytkeditorlib.utils.constants import PYTHON_LEX, CONFIG, IMAGES, \
    valide_entree_nb
from .filebar import FileBar
from .editortext import EditorText



class Editor(ttk.Frame):
    """
    Code editor tab.

    Includes a text editor, line numbers, search & replace bar
    and code and style checking info.
    """
    def __init__(self, master=None, file=''):
        ttk.Frame.__init__(self, master, class_='Editor')

        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        self._valid_nb = self.register(valide_entree_nb)

        self._syntax_icons = {'warning': tk.PhotoImage(master=self, file=IMAGES['warning']),
                              'error': tk.PhotoImage(master=self, file=IMAGES['error'])}

        self._syntax_highlighting_tags = []

        self._search_count = tk.IntVar(self)

        self.cells = []

        # --- GUI elements
        self.text = EditorText(self, undo=True, autoseparators=False,
                               width=81, height=45, wrap='none', cursor='watch')

        self.sep = tk.Frame(self.text)
        self._sep_x = 1

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
            x0, x1 = float(x0), float(x1)
            width = round((self.text.winfo_width() - 2) / (x1 - x0))
            self.sep.place_configure(x=self._sep_x - width*x0)

        def yscroll(y0, y1):
            sy.set(y0, y1)
            self.line_nb.yview_moveto(y0)
            self.syntax_checks.yview_moveto(y0)
            self.filebar.update_positions()

        self.filebar = FileBar(self, self, width=10, cursor='watch')
        self.text.configure(xscrollcommand=xscroll, yscrollcommand=yscroll)
        self.update_idletasks()

        # --- search and replace
        tooltips = TooltipWrapper(self)
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
        btn_up = ttk.Button(search_buttons, style='Up.TButton', padding=0,
                            command=lambda: self.search(backwards=True))
        btn_up.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(btn_up, 'Find previous')
        btn_down = ttk.Button(search_buttons, style='Down.TButton', padding=0,
                              command=lambda: self.search(forwards=True))
        btn_down.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(btn_down, 'Find next')
        self.case_sensitive = ttk.Checkbutton(search_buttons, text='aA')
        self.case_sensitive.state(['selected', '!alternate'])
        self.case_sensitive.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(self.case_sensitive, 'Case sensitive')
        self.regexp = ttk.Checkbutton(search_buttons, text='regexp')
        self.regexp.state(['!selected', '!alternate'])
        self.regexp.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(self.regexp, 'Regular expression')
        self.full_word = ttk.Checkbutton(search_buttons, text='[-]')
        self.full_word.state(['!selected', '!alternate'])
        self.full_word.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(self.full_word, 'Whole words')
        self._highlight_btn = ttk.Checkbutton(search_buttons, image='img_highlight',
                                              padding=0, style='toggle.TButton',
                                              command=self.highlight_all)
        self._highlight_btn.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(self._highlight_btn, 'Highlight matches')
        self.replace_buttons = ttk.Frame(self.frame_search)
        btn_rup = ttk.Button(self.replace_buttons, style='red.Up.TButton', padding=0,
                             command=lambda: self.replace_find(backwards=True))
        btn_rup.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(btn_rup, 'Replace and find previous')
        btn_rdown = ttk.Button(self.replace_buttons, style='red.Down.TButton', padding=0,
                               command=self.replace_find)
        btn_rdown.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(btn_rdown, 'Replace and find next')
        btn_rall = ttk.Button(self.replace_buttons, padding=0,
                              command=self.replace_all, image='img_replace_all')
        btn_rall.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(btn_rall, 'Replace all')
        btn_rall_sel = ttk.Button(self.replace_buttons, padding=0,
                                  command=self.replace_all_in_sel,
                                  image='img_replace_selection')
        btn_rall_sel.pack(side='left', padx=2, pady=4)
        tooltips.add_tooltip(btn_rall_sel, 'Replace all in selection')

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
        self.file = file
        self.filetype = 'Python' if (not file or file.endswith('.py')) else 'Other'

        # --- bindings
        #~self.text.bind("<Control-i>", self.inspect)
        self.text.bind("<Control-Shift-C>", self.choose_color)
        self.text.bind("<Control-Return>", self.on_ctrl_return)
        self.text.bind("<Shift-Return>", self.on_shift_return)
        self.text.bind('<Control-f>', self.find)
        self.text.bind('<Control-r>', self.replace)
        self.text.bind('<Control-l>', self.goto_line)
        self.text.bind('<Control-Down>', self.goto_next_cell)
        self.text.bind('<Control-Up>', self.goto_prev_cell)
        self.text.bind('<Configure>', self.filebar.update_positions)
        self.text.bind("<<CursorChange>>", self._highlight_current_line)
        # vertical scrolling
        self.text.bind('<4>', self._on_b4)
        self.line_nb.bind('<4>', self._on_b4)
        self.syntax_checks.bind('<4>', self._on_b4)
        self.text.bind('<5>', self._on_b5)
        self.line_nb.bind('<5>', self._on_b5)
        self.syntax_checks.bind('<5>', self._on_b5)
        # horizontal scrolling
        self.text.bind('<Shift-4>', self._on_sb4)
        self.text.bind('<Shift-5>', self._on_sb5)

        self.line_nb.bind('<1>', self._highlight_line)
        self.syntax_checks.bind('<1>', self._highlight_line)

        self.text.focus_set()
        self.text.edit_modified(0)

    def __getattr__(self, name):
        """Fallback to the text's attributes."""
        return getattr(self.text, name)

    @property
    def filetype(self):
        return self._filetype

    @filetype.setter
    def filetype(self, filetype):
        self.reset_syntax_issues()
        self._filetype = filetype
        if filetype == 'Python':
            self.text.lexer = PYTHON_LEX
        else:
            try:
                self.text.lexer = get_lexer_for_filename(self.file)
            except ClassNotFound:
                self.text.lexer = get_lexer_by_name('text')
        self.text.parse_all()

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

    def on_ctrl_return(self, event):
        self.text.edit_separator()
        self.master.event_generate('<<CtrlReturn>>')
        return 'break'

    def on_shift_return(self, event):
        self.text.edit_separator()
        self.master.event_generate('<<ShiftReturn>>')
        return 'break'

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
        self.text.update_style()

        font = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        tkfont = Font(self, font)
        self._sep_x = tkfont.measure(' ' * 79)
        x0, x1 = self.text.xview()
        width = round((self.text.winfo_width() - 2) / (x1 - x0))
        self.sep.place(y=0, relheight=1, width=1, x=self._sep_x - width*x0)

        theme = f"{CONFIG.get('General', 'theme').capitalize()} Theme"

        fg = self.line_nb.option_get('foreground', '*Text')
        bg = self.line_nb.option_get('background', '*Text')
        comment_fg = self.text.tag_cget('Token.Comment', 'foreground')
        if not comment_fg:
            comment_fg = self.text.cget('foreground')

        self.sep.configure(bg=comment_fg)
        self.line_nb.configure(fg=fg, bg=bg, font=font,
                               selectbackground=bg, selectforeground=fg,
                               inactiveselectbackground=bg)
        self.line_nb.tag_configure('current_line', font=font + ('bold',),
                                   foreground=CONFIG.get(theme, 'fg'))
        self.syntax_checks.configure(fg=fg, bg=bg, font=font,
                                     selectbackground=bg, selectforeground=fg,
                                     inactiveselectbackground=bg)
        self.filebar.update_style(comment_fg=comment_fg)

    def strip(self):
        res = self.text.search(r' +$', '1.0', regexp=True)
        while res:
            end = f"{res} lineend"
            self.text.delete(res, end)
            res = self.text.search(r' +$', end, regexp=True)

    # --- autocompletion and help tooltips
    def _highlight_current_line(self, event):
        insert = self.text.index('insert linestart')
        self.line_nb.tag_remove('current_line', '1.0', 'end')
        self.line_nb.tag_add('current_line', insert, f'{insert} lineend')

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
        """
        Replace selection if it matches search pattern.

        Return True if the selection was replaced
        """
        self.text.edit_separator()
        pattern = self.entry_search.get()
        self.entry_search.add_to_history(pattern)
        new_text = self.entry_replace.get()
        self.entry_replace.add_to_history(new_text)
        sel = self.text.tag_ranges('sel')
        if not sel:
            self.search(notify_no_match=notify_no_match)
            return False
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
        self.search(notify_no_match=notify_no_match)
        return False

    def replace_find(self, backwards=False):
        if self.replace_sel():
            self.search(backwards=backwards)

    def replace_all_in_sel(self):
        self.text.edit_separator()
        res = True
        if not self.text.tag_ranges('sel'):
            return
        index_stop = self.text.index('sel.last')
        self.text.mark_set('insert', 'sel.first')
        # replace all occurences in selection
        while res:
            self.search(notify_no_match=False, stopindex=index_stop)
            res = self.replace_sel(notify_no_match=False)

    def replace_all(self):
        self.text.edit_separator()
        res = True
        self.text.mark_set('insert', '1.0')
        # replace all occurences in text
        nb = -1
        while res:
            nb += 1
            self.search(notify_no_match=False, stopindex='end')
            res = self.replace_sel(notify_no_match=False)
        showinfo("Information", f"{nb} occurrence(s) have been replaced.")

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
            self.text.see(res)
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

    # --- goto
    def goto_line(self, event=None):

        def goto(event):
            try:
                line = int(e.get())
                self.text.see('%i.0' % line)
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
        self.mark_set('insert', start)
        self.text.see(start)
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_add('sel', start, end)
        self.text.focus_set()

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
        if strip:
            self.text.parse_part()
            self.strip()
        txt = self.text.get('1.0', 'end-1c') # remove final space
        self.text.edit_separator()
        return txt

    def get_selection(self):
        sel = self.text.tag_ranges('sel')
        if sel:
            return self.text.get('sel.first', 'sel.last')

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
        script = jedi.Script(code=txt + obj, path=self.file)
        res = script.infer(len(txt.splitlines()) + 1, len(obj))
        if res:
            return res[-1]
        else:
            return None

    # --- text edit
    def delete(self, index1, index2=None):
        self.text.edit_separator()
        self.text.delete(index1, index2=index2)
        self.text.parse_part()
        self.update_nb_lines()

    def insert(self, index, text, replace_sel=False):
        self.text.edit_separator()
        if replace_sel:
            sel = self.text.tag_ranges('sel')
            if sel:
                self.text.delete('sel.first', 'sel.last')
        self.text.insert(index, text)
        lines = len(text.splitlines())//2
        self.text.parse_part(f'insert linestart - {lines} lines', nblines=lines + 10)
        self.update_nb_lines()

    def choose_color(self, event=None):
        """Display color picker."""

        def insert(event):
            color = picker.get_color()
            if color:
                self.insert("insert", color, True)

        picker = ColorPicker(color=self.get_selection(), parent=self)
        picker.bind("<<ColorSelected>>", insert)

    # --- view
    def highlight_line(self, line):
        self.text.mark_set('insert', line)
        self.goto_item(line, f'{line} lineend')

    def _highlight_line(self, event):
        line = event.widget.index('current linestart')
        self.highlight_line(line)

    def update_nb_lines(self, event=None):
        row = int(str(self.text.index('end')).split('.')[0]) - 1
        row_old = int(str(self.line_nb.index('end')).split('.')[0]) - 1
        self.line_nb.configure(state='normal')
        self.syntax_checks.configure(state='normal')
        if row_old < row:
            self.syntax_checks.insert('end', '\n'*(row - row_old))
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
        self.text.see('%i.0' % line)
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_add('sel', '%i.0' % line, '%i.end' % line)

    def reset_syntax_issues(self):
        self.syntax_checks.configure(state='normal')
        self.syntax_checks.delete('1.0', 'end')
        self.syntax_issues_menuentries.clear()
        self.textwrapper.remove_all()
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

