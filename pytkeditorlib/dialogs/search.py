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


Search in session dialog
"""

import tkinter as tk
from tkinter import ttk
import re

from pytkeditorlib.gui_utils import AutoHideScrollbar


class SearchDialog(tk.Toplevel):
    def __init__(self, master, text=''):
        tk.Toplevel.__init__(self, master, class_=master.winfo_class(), padx=4, pady=4)
        self.title('Find & replace')
        frame_find = ttk.Frame(self)
        frame_find.columnconfigure(1, weight=1)

        # --- search entry
        self.entry_search = ttk.Entry(frame_find, width=40)
        self.entry_search.insert(0, text)
        self.entry_search.bind('<Return>', self.find)
        ttk.Label(frame_find, text='Find: ').grid(row=0, column=0, pady=4)
        self.entry_search.grid(row=0, column=1, sticky='ew', pady=4)
        ttk.Button(frame_find, image='img_find', padding=0,
                   command=self.find).grid(row=0, column=2, pady=4, padx=(4, 0))
        # --- search options
        opt_frame = ttk.Frame(frame_find)
        self.case_sensitive = tk.BooleanVar(self, False)
        self.full_word = tk.BooleanVar(self, False)
        self.regexp = tk.BooleanVar(self, False)
        cb_case = ttk.Checkbutton(opt_frame, text='aA', variable=self.case_sensitive)
        cb_word = ttk.Checkbutton(opt_frame, text='[-]', variable=self.full_word)
        cb_regexp = ttk.Checkbutton(opt_frame, text='regexp', variable=self.regexp)
        cb_case.pack(side='left', padx=4)
        cb_word.pack(side='left', padx=4)
        cb_regexp.pack(side='left', padx=4)
        cb_case.state(['!alternate'])
        cb_word.state(['!alternate'])
        cb_regexp.state(['!alternate'])
        opt_frame.grid(row=1, columnspan=3, pady=(0, 4))
        # --- display results
        result_frame = ttk.Frame(self)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(1, weight=1)
        self._search_pattern = None
        self.results = ttk.Treeview(result_frame, show='tree',
                                    columns=('tab', 'index_start', 'index_end'), displaycolumns=())
        self.results.tag_bind('result', '<ButtonRelease-1>', self._show_file)
        scroll = AutoHideScrollbar(result_frame, orient='vertical',
                                   command=self.results.yview)
        self.results.configure(yscrollcommand=scroll.set)
        ttk.Label(result_frame, text='Results:').grid(row=0, column=0, sticky='w')
        self.results.grid(row=1, column=0, sticky='ewns')
        scroll.grid(row=1, column=1, sticky='ns')

        # --- replace
        replace_frame = ttk.Frame(self)
        ttk.Label(replace_frame, text="Replace by: ").pack(side="left")
        self.entry_replace = ttk.Entry(replace_frame)
        self.entry_replace.pack(side="left", fill="x", expand=True)
        ttk.Button(replace_frame, text="Find & Replace all", padding=1,
                   command=self.replace).pack(side='left', padx=4)

        # --- placement
        frame_find.pack(fill='x', padx=4)
        replace_frame.pack(side="bottom", fill='x', padx=4, pady=4)
        result_frame.pack(fill='both', expand=True, pady=4, padx=4)
        self.entry_search.focus_set()

    def _show_file(self, event):
        item = self.results.focus()
        try:
            tab, start, end = self.results.item(item, 'values')
        except ValueError:
            return
        try:
            self.master.editor.select(int(tab))
            self.master.editor.goto_item(start, end)
            self.master.update_idletasks()
        except (tk.TclError, KeyError, ValueError):
            return

    def find(self, event=None):
        self.results.delete(*self.results.get_children(''))
        pattern = self.entry_search.get()
        case_sensitive = self.case_sensitive.get()
        full_word = self.full_word.get()
        regexp = self.regexp.get()
        # get regexp for replacement
        search_pattern = pattern
        if not regexp:
            search_pattern = re.escape(search_pattern)
        if full_word:
            # full word: \b at the end
            search_pattern = r"\b{}\b".format(search_pattern)
        if not case_sensitive:
            # ignore case: (?i) at the start
            search_pattern = r"(?i)" + search_pattern
        self._search_pattern = re.compile("^" + search_pattern + "$")
        # populate tree
        results = self.master.editor.find_all(pattern, case_sensitive, regexp, full_word)
        for tab, (file, matches) in results.items():
            if matches:
                self.results.insert('', 'end', file, text=file, tags='file',
                                    values=(tab,), open=True)
                for start, end, line in matches:
                    start_line, start_col = start.split(".")
                    self.results.insert(file, 'end', text=f"{start_line}:{start_col}: {line}",
                                        values=(tab, start, end),
                                        tags='result')

    def replace(self):
        self.find()
        text = self.entry_replace.get()
        files = self.results.get_children()
        replacements = {}
        for file in files:
            tab = int(self.results.item(file, 'values')[0])
            matches = self.results.get_children(file)
            replacements[tab] = [self.results.item(iid, "values")[1:] for iid in matches]
        self.master.editor.replace_all(self._search_pattern, text, replacements)
        self.results.delete(*self.results.get_children(''))
