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
from tkinter import PhotoImage
from tkinter.ttk import Treeview
from tkinter.font import Font
import os

from pytkeditorlib.autoscrollbar import AutoHideScrollbar as Scrollbar
from pytkeditorlib.constants import IMAGES
from pytkeditorlib.base_widget import BaseWidget


class FileTree(Treeview):
    def __init__(self, master, callback=print):
        Treeview.__init__(self, master, show='tree', selectmode='none',
                          style='flat.Treeview', padding=4)

        self._im_file = PhotoImage(master=self, file=IMAGES['file'])
        self._im_folder = PhotoImage(master=self, file=IMAGES['folder'])

        self.font = Font(self, font="TkDefaultFont 9")
        self.callback = callback

        self.tag_configure('file', image=self._im_file)
        self.tag_configure('folder', image=self._im_folder)
        self.tag_bind('file', '<Double-1>', self._on_db_click_file)
        self.tag_bind('folder', '<Double-1>', self._on_db_click_folder)
        self.tag_bind('prev', '<Double-1>', self._on_db_click_prev)

        self.bind('<1>', self._on_click)

    def _on_click(self, event):
        if 'indicator' not in self.identify_element(event.x, event.y):
            self.selection_remove(*self.selection())
            self.selection_set(self.identify_row(event.y))

    def _on_db_click_file(self, event):
        sel = self.selection()
        if self.callback is not None and sel:
            item = sel[0]
            self.callback(item)

    def _on_db_click_folder(self, event):
        sel = self.selection()
        if sel:
            self.populate(sel[0])

    def _on_db_click_prev(self, event):
        sel = self.selection()
        if sel:
            self.populate(os.path.dirname(self.get_children()[1]))

    def populate(self, path):
        self.delete(*self.get_children())
        p = os.path.abspath(path)
        self.insert('', 0, '..', text='..', tags='prev')
        self.insert('', 1, p, text=p, image=self._im_folder, open=True)
        for (root, folders, files) in os.walk(p):
            for f in sorted(folders):
                self.insert(root, 'end', os.path.join(root, f), text=f,
                            tags='folder')
            for f in sorted(files):
                self.insert(root, 'end', os.path.join(root, f), text=f,
                            tags='file')


class Filebrowser(BaseWidget):
    def __init__(self, master, callback):
        BaseWidget.__init__(self, master, 'File browser', padding=2)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.filetree = FileTree(self, callback=callback)
        self._sx = Scrollbar(self, orient='horizontal', command=self.filetree.xview)
        self._sy = Scrollbar(self, orient='vertical', command=self.filetree.yview)

        self.filetree.configure(xscrollcommand=self._sx.set,
                                yscrollcommand=self._sy.set)

        self.filetree.grid(row=1, column=0, sticky='ewns')
        self._sx.grid(row=2, column=0, sticky='ew')
        self._sy.grid(row=1, column=1, sticky='ns')

    def clear(self, event=None):
        self.filetree.delete(*self.filetree.get_children())

    def populate(self, path):
        self._sx.timer = self._sx.threshold + 1
        self._sy.timer = self._sy.threshold + 1
        self.filetree.populate(path)
