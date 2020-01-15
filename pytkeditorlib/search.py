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

from .autoscrollbar import AutoHideScrollbar
from .constants import RE_NEWLINE


class SearchDialog(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master, class_=master.winfo_class(), padx=4, pady=4)
        self.title('Find')
        frame_find = ttk.Frame(self)
        frame_find.columnconfigure(1, weight=1)

        # --- search entry
        self.entry_search = ttk.Entry(frame_find)
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
        self.results = ttk.Treeview(result_frame, show='tree',
                                    columns=('tab', 'line'), displaycolumns=())
        self.results.tag_bind('result', '<ButtonRelease-1>', self._show_file)
        scroll = AutoHideScrollbar(result_frame, orient='vertical',
                                   command=self.results.yview)
        self.results.configure(yscrollcommand=scroll.set)
        ttk.Label(result_frame, text='Results:').grid(row=0, column=0, sticky='w')
        self.results.grid(row=1, column=0, sticky='ewns')
        scroll.grid(row=1, column=1, sticky='ns')

        # --- placement
        frame_find.pack(fill='x', padx=4)
        result_frame.pack(fill='both', expand=True, pady=4, padx=4)
        self.entry_search.focus_set()

    def _show_file(self, event):
        item = self.results.focus()
        tab, line = self.results.item(item, 'values')
        self.master.editor.select(int(tab))
        self.master.editor.goto_item(f"{line}.0", f"{line}.end")
        self.master.update_idletasks()

    def find(self, event=None):
        self.results.delete(*self.results.get_children(''))
        # --- get search pattern
        pattern = self.entry_search.get()
        flags = 0
        if not self.regexp.get():
            pattern = re.escape(pattern)
        if self.full_word.get():
            # full word: \b at the end
            pattern = r"\b{}\b".format(pattern)
        if self.case_sensitive.get():
            # ignore case: (?i) at the start
            flags = re.IGNORECASE
        pattern = re.compile(pattern, flags)

        # --- search
        files = self.master.editor.get_all_files()
        for tab, (file, text) in files.items():
            results = list(pattern.finditer(text))
            if results:
                self.results.insert('', 'end', file, text=file, tags='file',
                                    values=(tab,))
                lines = text.splitlines()
                for match in results:
                    start = match.start()
                    line_nb = len(RE_NEWLINE.findall(text, 0, start)) + 1
                    self.results.insert(file, 'end', text=f"{line_nb}: {lines[line_nb - 1]}",
                                        values=(tab, line_nb), tags='result')
