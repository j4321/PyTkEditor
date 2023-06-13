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


GUI widget to browse local files
"""
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import os
import re

from pytkeditorlib.gui_utils import AutoHideScrollbar as Scrollbar
from pytkeditorlib.utils.constants import CONFIG
from pytkeditorlib.dialogs import TooltipWrapper
from .base_widget import BaseWidget


class Filebrowser(BaseWidget):
    def __init__(self, master, callback, **kw):
        BaseWidget.__init__(self, master, 'File browser', padding=2, **kw)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.history = []
        self.history_index = -1

        self._path = ''

        tooltips = TooltipWrapper(self)

        self.load_filters()
        # --- browsing buttons
        frame_btn = ttk.Frame(self)
        self.b_up = ttk.Button(frame_btn, image='img_up', padding=0,
                               command=self.browse_up)
        self.b_backward = ttk.Button(frame_btn, image='img_left', padding=0,
                                     command=self.browse_backward)
        self.b_forward = ttk.Button(frame_btn, image='img_right', padding=0,
                                    command=self.browse_forward)
        self.b_backward.pack(side='left')
        self.b_forward.pack(side='left', padx=4)
        self.b_up.pack(side='left')
        tooltips.add_tooltip(self.b_up, 'Parent')
        tooltips.add_tooltip(self.b_forward, 'Next')
        tooltips.add_tooltip(self.b_backward, 'Previous')
        self.b_forward.state(['disabled'])
        self.b_backward.state(['disabled'])

        btn_prop = ttk.Button(frame_btn, image='img_properties', padding=0,
                              command=self.edit_filter)
        btn_prop.pack(side='right')
        tooltips.add_tooltip(btn_prop, 'Edit filename filters')

        # --- filetree
        self.filetree = ttk.Treeview(self, show='tree', selectmode='none',
                                     style='flat.Treeview', padding=4)
        self._sx = Scrollbar(self, orient='horizontal', command=self.filetree.xview)
        self._sy = Scrollbar(self, orient='vertical', command=self.filetree.yview)

        self.filetree.configure(xscrollcommand=self._sx.set,
                                yscrollcommand=self._sy.set)

        self.font = Font(self, font="TkDefaultFont 9")
        self.callback = callback

        self.filetree.tag_configure('file', image='img_file')
        self.filetree.tag_configure('folder', image='img_folder')
        self.filetree.tag_bind('file', '<Double-1>', self._on_db_click_file)
        self.filetree.tag_bind('folder', '<Double-1>', self._on_db_click_folder)
        self.filetree.tag_bind('folder', '<<TreeviewOpen>>', self._on_folder_open)

        self.filetree.bind('<1>', self._on_click)

        # --- placement
        frame_btn.grid(row=0, columnspan=2, sticky='ew', pady=2)
        self.filetree.grid(row=1, column=0, sticky='ewns')
        self._sx.grid(row=2, column=0, sticky='ew')
        self._sy.grid(row=1, column=1, sticky='ns')

    def _on_click(self, event):
        if 'indicator' not in self.filetree.identify_element(event.x, event.y):
            self.filetree.selection_remove(*self.filetree.selection())
            self.filetree.selection_set(self.filetree.identify_row(event.y))

    def _on_db_click_file(self, event):
        item = self.filetree.focus()
        if self.callback is not None and item:
            self.callback(item)

    def _on_db_click_folder(self, event):
        item = self.filetree.focus()
        if item:
            self.populate(item)

    def load_filters(self):
        filters = CONFIG.get('File browser', 'filename_filter',
                             fallback='README, *.py, *.rst').split(', ')
        filters = ['^' + ext.strip().replace('.', '\.').replace('*', '.*') + '$' for ext in filters]
        self.filter = re.compile('|'.join(filters))

    def edit_filter(self):

        def ok(event=None):
            CONFIG.set('File browser', 'filename_filter', filters.get('1.0', 'end').strip())
            CONFIG.save()
            self.load_filters()
            self.populate(self.filetree.get_children()[0], history=False)
            top.destroy()

        top = tk.Toplevel(self, padx=4, pady=4)
        style = ttk.Style(self)
        top.title('Filename filters')
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)
        top.rowconfigure(1, weight=1)
        ttk.Label(top, text='Name filters:').grid(columnspan=2, sticky='w')
        frame = ttk.Frame(top, style='txt.TFrame', padding=1, relief='sunken', borderwidth=1)
        filters = tk.Text(frame, wrap='word', height=5,
                          bg=style.lookup('TEntry', 'fieldbackground'),
                          fg=style.lookup('TEntry', 'foreground'))
        filters.pack(expand=True, fill='both')
        yscroll = Scrollbar(top, orient='vertical', command=filters.yview, threshold=0)
        filters.configure(yscrollcommand=yscroll.set)
        frame.grid(columnspan=2, sticky='ewns', pady=4)
        yscroll.grid(row=1, column=2, sticky='ns', pady=4)
        filters.insert('1.0', CONFIG.get('File browser', 'filename_filter',
                                         fallback='README, *.py, *.rst'))
        filters.bind('<Return>', ok)
        filters.bind('<Escape>', lambda e: top.destroy())
        filters.focus_set()
        ttk.Button(top, text='Ok', command=ok).grid(row=2, column=0, padx=4, sticky='e')
        ttk.Button(top, text='Cancel',
                   command=top.destroy).grid(row=2, column=1, padx=4, sticky='w')
        top.transient(self)
        top.grab_set()

    def history_add(self, path):
        self.history_index += 1
        self.history = self.history[:self.history_index]
        self.history.append(path)
        if self.history_index > 0:
            self.b_backward.state(['!disabled'])
        self.b_forward.state(['disabled'])

    def browse_up(self):
        path = os.path.dirname(self.filetree.get_children()[0])
        self.populate(path)

    def browse_backward(self):
        self.history_index -= 1
        path = self.history[self.history_index]
        self.populate(path, history=False)
        self.b_forward.state(['!disabled'])
        if self.history_index == 0:
            self.b_backward.state(['disabled'])

    def browse_forward(self):
        self.history_index += 1
        path = self.history[self.history_index]
        self.populate(path, history=False)
        self.b_backward.state(['!disabled'])
        if self.history_index == len(self.history) - 1:
            self.b_forward.state(['disabled'])

    def clear(self, event=None):
        self.filetree.delete(*self.filetree.get_children())

    @staticmethod
    def _key_sort_files(item):
        return item.is_file(), item.name.lower()

    def _on_folder_open(self, event):
        """Display folder content when opened by user."""
        item = self.filetree.focus()
        self.filetree.delete(*self.filetree.get_children(item))
        self._lazy_populate(item)

    def _lazy_populate(self, path):
        """
        Populate file tree of path only to the first level.

        Add dummy items inside folders so that they can be expanded but
        display their actual content only if the user opens them.
        """
        try:
            content = sorted(os.scandir(path), key=self._key_sort_files)
        except PermissionError:
            return
        for item in content:
            is_dir = item.is_dir()
            ipath = item.path
            name = item.name
            if is_dir:
                if not name[0] == '.':
                    self.filetree.insert(path, 'end', ipath, text=name, tags='folder')
                    self.filetree.insert(ipath, 'end', text='')
            elif self.filter.search(name):
                self.filetree.insert(path, 'end', ipath, text=name, tags='file')

    def _display(self):
        if not self.visible.get():
            return

        p = os.path.abspath(self._path)
        root = self.filetree.get_children('')
        if root and p == root[0]:
            return

        self.configure(cursor='watch')
        self.update_idletasks()
        self._sx.timer = self._sx.threshold + 1
        self._sy.timer = self._sy.threshold + 1

        self.filetree.delete(*self.filetree.get_children())
        self.filetree.insert('', 0, p, text=p, image='img_folder', open=True)

        self._lazy_populate(p)

        self.configure(cursor='')

    def populate(self, path, history=True, reset=False):
        self._path = path
        self._display()
        if reset:
            self.history = []
            self.history_index = -1
        if history:
            self.history_add(path)
