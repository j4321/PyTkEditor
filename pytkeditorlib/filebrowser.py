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
from tkinter.ttk import Treeview, Frame, Button
from tkinter.font import Font
import os

from pytkeditorlib.autoscrollbar import AutoHideScrollbar as Scrollbar
from pytkeditorlib.base_widget import BaseWidget

# TODO: browsing history
# TODO: filename filter


class Filebrowser(BaseWidget):
    def __init__(self, master, callback):
        BaseWidget.__init__(self, master, 'File browser', padding=2)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.history = []
        self.history_index = -1

        # --- browsing buttons
        frame_btn = Frame(self)
        self.b_up = Button(frame_btn, image='img_up', padding=0,
                           command=self.browse_up)
        self.b_backward = Button(frame_btn, image='img_left', padding=0,
                                 command=self.browse_backward)
        self.b_forward = Button(frame_btn, image='img_right', padding=0,
                                command=self.browse_forward)
        self.b_backward.pack(side='left', padx=2)
        self.b_forward.pack(side='left', padx=2)
        self.b_up.pack(side='left', padx=2)
        self.b_forward.state(['disabled'])
        self.b_backward.state(['disabled'])

        # --- filetree
        # self.filetree = FileTree(self, callback=callback)
        self.filetree = Treeview(self, show='tree', selectmode='none',
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

        self.filetree.bind('<1>', self._on_click)

        # --- placement
        frame_btn.grid(row=0, column=0, sticky='ew', pady=2)
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

    def _rec_populate(self, path):
        content = sorted(os.scandir(path), key=self._key_sort_files)
        tags = ['file', 'folder']
        for item in content:
            is_dir = item.is_dir()
            ipath = item.path
            self.filetree.insert(path, 'end', ipath, text=item.name, tags=tags[is_dir])
            if is_dir:
                self._rec_populate(ipath)

    def populate(self, path, history=True, reset=False):
        self.configure(cursor='watch')
        self.update_idletasks()
        self._sx.timer = self._sx.threshold + 1
        self._sy.timer = self._sy.threshold + 1

        self.filetree.delete(*self.filetree.get_children())
        p = os.path.abspath(path)
        self.filetree.insert('', 1, p, text=p, image='img_folder', open=True)

        self._rec_populate(p)

        self.configure(cursor='')
        if reset:
            self.history = []
            self.history_index = -1
        if history:
            self.history_add(path)
