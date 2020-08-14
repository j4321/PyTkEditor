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


GUI widget to get an overview of names in file
"""
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import jedi

from pytkeditorlib.gui_utils import AutoHideScrollbar as Scrollbar
from pytkeditorlib.utils.constants import CONFIG
from pytkeditorlib.dialogs import TooltipWrapper
from .base_widget import BaseWidget


class NameOverview(BaseWidget):
    def __init__(self, master, **kw):
        BaseWidget.__init__(self, master, 'Namespace', padding=2, **kw)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        tooltips = TooltipWrapper(self)
        self.callback = None
        self.font = Font(self, font="TkDefaultFont 9")
        self.style = ttk.Style(self)

        # --- treeview
        self.treeview = ttk.Treeview(self, selectmode='none',
                                     columns=('Type', 'Full name', 'Index'),
                                     displaycolumns=('Full name', 'Type'),
                                     style='flat.Treeview', padding=4)
        self._sx = Scrollbar(self, orient='horizontal', command=self.treeview.xview)
        self._sy = Scrollbar(self, orient='vertical', command=self.treeview.yview)
        self._module = ''

        self.treeview.heading('Type', text='Type',
                              command=lambda: self._sort_column('Type', False))
        self.treeview.heading('Full name', text='Full name',
                              command=lambda: self._sort_column('Full name', False))
        self.treeview.heading('#0', text='Name',
                              command=lambda: self._sort_column0(False))
        self.treeview.column('Type', width=self.font.measure('statement') + 2)

        self.treeview.configure(xscrollcommand=self._sx.set,
                                yscrollcommand=self._sy.set)

        # --- header
        header = ttk.Frame(self)
        header.columnconfigure(3, weight=1)
        btn_exp = ttk.Button(header, padding=0, command=self.expand_all,
                             image='img_expand_all')
        btn_exp.grid(row=0, column=0)
        tooltips.add_tooltip(btn_exp, 'Expand all')
        btn_col = ttk.Button(header, padding=0, command=self.collapse_all,
                             image='img_collapse_all')
        btn_col.grid(row=0, column=1, padx=4)
        tooltips.add_tooltip(btn_col, 'Collapse all')
        self.btn_refresh = ttk.Button(header, padding=0,
                                      command=lambda: self.event_generate('<<Refresh>>'),
                                      image='img_refresh')
        self.btn_refresh.grid(row=0, column=2)
        self.all_scopes = ttk.Checkbutton(header, text='All scopes',
                                          command=self._toggle_scopes)
        self.all_scopes.grid(row=0, column=3, sticky='e')
        self.all_scopes.state(['!alternate',
                               '!'*(not CONFIG.getboolean('Namespace', 'all_scopes', fallback=False)) + 'selected'])
        tooltips.add_tooltip(self.btn_refresh, 'Refresh')


        self.treeview.bind('<1>', self._on_click)
        self.treeview.bind('<<TreeviewSelect>>', self._on_select)
        self.treeview.bind('<<TreeviewOpen>>', self._on_item_open)
        self.treeview.bind('<<TreeviewClose>>', self._on_item_close)

        self.update_style()

        # --- placement
        header.grid(row=0, columnspan=2, sticky='ew')
        self.treeview.grid(row=1, column=0, sticky='ewns')
        self._sx.grid(row=2, column=0, sticky='ew')
        self._sy.grid(row=1, column=1, sticky='ns')

    def update_style(self):
        self.treeview.tag_configure('0', background=self.style.lookup('flat.Treeview', 'background'))
        self.treeview.tag_configure('1', background=self.style.lookup('flat.Treeview.Heading', 'background'))

    def _toggle_scopes(self):
        CONFIG.set('Namespace', 'all_scopes', str('selected' in self.all_scopes.state()))
        self.event_generate('<<Refresh>>')

    def _on_click(self, event):
        if 'indicator' not in self.treeview.identify_element(event.x, event.y):
            self.treeview.selection_remove(*self.treeview.selection())
            self.treeview.selection_set(self.treeview.identify_row(event.y))

    def _row_tag(self, item, tag=0):
        """
        Set row tag of item and if opened, its children.

        Return last row tag
        """
        self.treeview.item(item, tags=str(tag % 2))
        row_tag = tag
        if self.treeview.item(item, 'open'):
            for ch in self.treeview.get_children(item):
                row_tag = self._row_tag(ch, row_tag + 1)
        return row_tag

    def _on_item_close(self, event):
        item = self.treeview.focus()
        row_tag = int(self.treeview.item(item, 'tags')[0])
        if row_tag != int(self.treeview.item(self.treeview.get_children(item)[-1], 'tags')[0]):
            item = self.treeview.next(item)
            while item:
                row_tag = self._row_tag(item, row_tag + 1)
                item = self.treeview.next(item)

    def _on_item_open(self, event):
        item = self.treeview.focus()
        tag = int(self.treeview.item(item, 'tags')[0])
        row_tag = tag
        for ch in self.treeview.get_children(item):
            row_tag = self._row_tag(ch, row_tag + 1)
        if row_tag % 2 != tag:  # change coloring of next items
            item = self.treeview.next(item)
            while item:
                row_tag = self._row_tag(item, row_tag + 1)
                item = self.treeview.next(item)

    def set_callback(self, fct):
        self.callback = fct

    def _on_select(self, event):
        sel = self.treeview.selection()
        if self.callback is not None and sel:
            index = self.treeview.set(sel[0], 'Index')
            self.callback(index, f'{index} wordend')

    def clear(self, event=None):
        self.treeview.delete(*self.treeview.get_children())

    def _expand(self, item):
        """Expand item and all its children recursively."""
        self.treeview.item(item, open=True)
        for c in self.treeview.get_children(item):
            self._expand(c)

    def expand_all(self):
        """Expand all items."""
        for c in self.treeview.get_children(""):
            self._expand(c)

    def _collapse(self, item):
        """Collapse item and all its children recursively."""
        self.treeview.item(item, open=False)
        for c in self.treeview.get_children(item):
            self._collapse(c)

    def collapse_all(self):
        """Collapse all items."""
        for c in self.treeview.get_children(""):
            self._collapse(c)

    def _sort_column0(self, reverse):
        l = [(self.treeview.item(k, 'text'), k) for k in self.treeview.get_children(self._module)]
        l.sort(reverse=reverse)
        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.treeview.move(k, self._module, index)
        # reverse sort next time
        self.treeview.heading('#0', command=lambda: self._sort_column0(not reverse))
        self._row_tag(self._module, 0)

    def _sort_column(self, col, reverse):
        l = [(self.treeview.set(k, col), k) for k in self.treeview.get_children(self._module)]
        l.sort(reverse=reverse)
        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.treeview.move(k, self._module, index)
        # reverse sort next time
        self.treeview.heading(col, command=lambda: self._sort_column(col, not reverse))
        self._row_tag(self._module, 0)

    def populate(self, filepath=None, code=None):
        self.treeview.delete(*self.treeview.get_children())
        if filepath is None and code is None:
            return
        script = jedi.Script(code=code, path=filepath)
        names = script.get_names(all_scopes='selected' in self.all_scopes.state())
        if not names:
            return
        self._module = names[0].parent().full_name
        self.treeview.insert('', 0, self._module, text=self._module, open=True, tags='0')
        row_tag = 0
        for name in names:
            if name.full_name is None:
                continue
            parent = name.parent().full_name
            if not parent:
                parent = name.parent().name
            if parent == self._module:
                row_tag += 1
            try:
                self.treeview.insert(parent, 'end', name.full_name, text=name.name,
                                     tags=str(row_tag % 2),
                                     values=(name.type, name.full_name, f'{name.line}.{name.column}'))
            except tk.TclError:
                pass

