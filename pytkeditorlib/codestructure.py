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


GUI widget to display the code structure
"""
from tkinter import PhotoImage
from tkinter.ttk import Treeview, Frame, Label
from tkinter.font import Font
import tokenize
from io import BytesIO
import re

from pytkeditorlib.autoscrollbar import AutoHideScrollbar as Scrollbar
from pytkeditorlib.autocomplete import AutoCompleteCombobox2
from pytkeditorlib.constants import IM_CLASS, IM_FCT, IM_HFCT, IM_SEP, IM_CELL


class CodeTree(Treeview):
    def __init__(self, master):
        Treeview.__init__(self, master, show='tree', selectmode='none',
                          style='flat.Treeview', padding=4)
        self._img_class = PhotoImage(file=IM_CLASS, master=self)
        self._img_fct = PhotoImage(file=IM_FCT, master=self)
        self._img_hfct = PhotoImage(file=IM_HFCT, master=self)
        self._img_sep = PhotoImage(file=IM_SEP, master=self)
        self._img_cell = PhotoImage(file=IM_CELL, master=self)

        self.font = Font(self, font="TkDefaultFont 9")

        self.tag_configure('class', image=self._img_class)
        self.tag_configure('def', image=self._img_fct)
        self.tag_configure('_def', image=self._img_hfct)
        self.tag_configure('#', image=self._img_sep)
        self.tag_configure('cell', image=self._img_cell)
        self.callback = None
        self.cells = []

        self.bind('<1>', self._on_click)
        self.bind('<<TreeviewSelect>>', self._on_select)

    def _on_click(self, event):
        if 'indicator' not in self.identify_element(event.x, event.y):
            self.selection_remove(*self.selection())
            self.selection_set(self.identify_row(event.y))

    def set_callback(self, fct):
        self.callback = fct

    def _on_select(self, event):
        sel = self.selection()
        if self.callback is not None and sel:
            self.callback(*self.item(sel[0], 'values'))

    def populate(self, text):
        self.delete(*self.get_children())
        tokens = tokenize.tokenize(BytesIO(text.encode()).readline)
        names = set()
        self.cells.clear()
        max_length = 20
        while True:
            try:
                token = tokens.send(None)
            except StopIteration:
                break
            except (tokenize.TokenError, IndentationError):
                continue
            add = False
            if token.type == tokenize.NAME and token.string in ['class', 'def']:
                obj_type = token.string
                index = token.start[1] // 4
                token = tokens.send(None)
                name = token.string
                names.add(name)
                if name[0] == '_' and obj_type == 'def':
                    obj_type = '_def'
                add = True
            elif token.type == tokenize.COMMENT:
                if token.string[:5] == '# ---' or 'TODO' in token.string:
                    obj_type = '#'
                    index = token.start[1] // 4
                    name = token.string[1:]
                    add = True
                elif re.match(r'#( )*In\[.*\]', token.string):
                    res = re.match(r'#( )*In', token.string)
                    obj_type = 'cell'
                    index = token.start[1] // 4
                    name = token.string[len(res.group()):].strip()
                    add = True
                    self.cells.append(token.start[0])

            if add:
                parent = ''
                i = 0
                children = self.get_children(parent)

                while i < index and children:
                    # avoid errors due to over indentation
                    parent = children[-1]
                    children = self.get_children(parent)
                    i += 1

                max_length = max(max_length, self.font.measure(name) + 20 + (i + 1) * 20)
                self.insert(parent, 'end', text=name,
                            tag=(obj_type, name),
                            values=('%i.%i' % token.start, '%i.%i' % token.end))
        self.column('#0', width=max_length, minwidth=max_length)
        for item in self.get_children(''):
            self.item(item, open=True)
        return names


class CodeStructure(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, style='border.TFrame',
                       padding=2)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.filename = Label(self, padding=(4, 2))
        self.codetree = CodeTree(self)
        self._sx = Scrollbar(self, orient='horizontal', command=self.codetree.xview)
        self._sy = Scrollbar(self, orient='vertical', command=self.codetree.yview)

        self.goto_frame = Frame(self)
        Label(self.goto_frame, text='Go to:').pack(side='left')
        self.goto_entry = AutoCompleteCombobox2(self.goto_frame, completevalues=[])
        self.goto_entry.pack(side='left', fill='x', pady=4, padx=4)
        self._goto_index = 0

        self.codetree.configure(xscrollcommand=self._sx.set,
                                yscrollcommand=self._sy.set)

        self.filename.grid(row=0, column=0, sticky='w')
        self.codetree.grid(row=1, column=0, sticky='ewns')
        self._sx.grid(row=2, column=0, sticky='ew')
        self._sy.grid(row=1, column=1, sticky='ns')
        Frame(self, style='separator.TFrame', height=1).grid(row=3, column=0, columnspan=2, sticky='ew')
        self.goto_frame.grid(row=4, column=0, columnspan=2, sticky='nsew')

        self.set_callback = self.codetree.set_callback

        self.goto_entry.bind('<Return>', self.goto)
        self.goto_entry.bind('<<ComboboxSelected>>', self.goto)
        self.goto_entry.bind('<Key>', self._reset_goto)

    def _reset_goto(self, event):
        self._goto_index = 0

    def get_cells(self):
        return self.codetree.cells

    def clear(self, event=None):
        self.codetree.delete(*self.codetree.get_children())
        self.filename.configure(text='')

    def populate(self, title, text):
        self.filename.configure(text=title)
        self._sx.timer = self._sx.threshold + 1
        self._sy.timer = self._sy.threshold + 1
        names = list(self.codetree.populate(text))
        names.sort()
        self.goto_entry.delete(0, "end")
        self.goto_entry.set_completion_list(names)
        self.event_generate('<<Populate>>')

    def goto(self, event):
        name = self.goto_entry.get()
        res = self.codetree.tag_has(name)
        if res:
            if self._goto_index >= len(res):
                self._goto_index = 0
            self.codetree.see(res[self._goto_index])
            self.codetree.selection_remove(*self.codetree.selection())
            self.codetree.selection_set(res[self._goto_index])
            self._goto_index += 1
