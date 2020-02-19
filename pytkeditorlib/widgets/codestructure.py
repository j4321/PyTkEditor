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


GUI widget to display the code structure
"""
from tkinter import TclError
from tkinter.ttk import Treeview, Frame, Label, Button
from tkinter.font import Font
import tokenize
from io import BytesIO
import re
import logging

from pytkeditorlib.gui_utils import AutoHideScrollbar, AutoCompleteCombobox2
from pytkeditorlib.utils.constants import CONFIG
from .base_widget import BaseWidget


class Tree:
    def __init__(self, node, branches=[], level=0):
        self.node = node
        self.branches = branches
        self.level = level

    def insert(self, node, level):

        def rec(t):
            if t.level < level:
                if not t.branches:
                    t.branches.append(Tree(node, [], level))
                    return t.node
                else:
                    res = rec(t.branches[-1])
                    if res == "reached":
                        t.branches.append(Tree(node, [], level))
                        return t.node
                    else:
                        return res
            else:
                return "reached"
        return rec(self)


class CodeTree(Treeview):
    def __init__(self, master):
        Treeview.__init__(self, master, show='tree', selectmode='none',
                          style='flat.Treeview', padding=4)

        self.font = Font(self, font="TkDefaultFont 9")

        self.tag_configure('class', image='img_c')
        self.tag_configure('def', image='img_f')
        self.tag_configure('_def', image="img_hf")
        self.tag_configure('#', image='img_sep')
        self.tag_configure('cell', image='img_cell')
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
        tree = Tree('', [], -1)
        tree_index = 0
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
                indent = token.start[1]
                token = tokens.send(None)
                name = token.string
                names.add(name)
                if name[0] == '_' and obj_type == 'def':
                    obj_type = '_def'
                add = True
            elif token.type == tokenize.COMMENT:
                if token.string[:5] == '# ---' or 'TODO' in token.string:
                    obj_type = '#'
                    indent = token.start[1]
                    name = token.string[1:]
                    add = True
                else:
                    match = re.match(r'^# In(\[.*\].*)$', token.string)
                    if match:
                        obj_type = 'cell'
                        indent = token.start[1]
                        name = match.groups()[0].strip()
                        add = True
                        self.cells.append(token.start[0])
                    else:
                        match = re.match(r'^# ?%% ?(.*)$', token.string)
                        if match:
                            obj_type = 'cell'
                            indent = token.start[1]
                            name = match.groups()[0].strip()
                            add = True
                            self.cells.append(token.start[0])

            if add:
                tree_index += 1
                parent = tree.insert('I-%i' % tree_index, indent)
                max_length = max(max_length, self.font.measure(name) + 20 + (indent//4 + 1) * 20)
                self.insert(parent, 'end', f'I-{tree_index}', text=name,
                            tags=(obj_type, name),
                            values=('%i.%i' % token.start, '%i.%i' % token.end))

        self.column('#0', width=max_length, minwidth=max_length)
        for item in self.get_children(''):
            self.item(item, open=True)
        return names


class CodeStructure(BaseWidget):
    def __init__(self, master, manager):
        BaseWidget.__init__(self, master, 'Code structure', style='border.TFrame')
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._manager = manager

        header = Frame(self)
        header.columnconfigure(0, weight=1)
        self._close_btn = Button(header, style='close.TButton', padding=0,
                                 command=lambda: self.visible.set(False))
        self._close_btn.grid(row=0, column=1)
        self.filename = Label(header, padding=(4, 0))
        self.filename.grid(row=0, column=0, sticky='w')

        self.codetree = CodeTree(self)
        self._sx = AutoHideScrollbar(self, orient='horizontal', command=self.codetree.xview)
        self._sy = AutoHideScrollbar(self, orient='vertical', command=self.codetree.yview)

        self.goto_frame = Frame(self)
        Label(self.goto_frame, text='Go to:').pack(side='left')
        self.goto_entry = AutoCompleteCombobox2(self.goto_frame, completevalues=[])
        self.goto_entry.pack(side='left', fill='x', pady=4, padx=4)
        self._goto_index = 0

        self.codetree.configure(xscrollcommand=self._sx.set,
                                yscrollcommand=self._sy.set)

        header.grid(row=0, columnspan=2, sticky='we')
        self.codetree.grid(row=1, column=0, sticky='ewns')
        self._sx.grid(row=2, column=0, sticky='ew')
        self._sy.grid(row=1, column=1, sticky='ns')
        Frame(self, style='separator.TFrame', height=1).grid(row=3, column=0, columnspan=2, sticky='ew')
        self.goto_frame.grid(row=4, column=0, columnspan=2, sticky='nsew')

        self.set_callback = self.codetree.set_callback

        self.goto_entry.bind('<Return>', self.goto)
        self.goto_entry.bind('<<ComboboxSelected>>', self.goto)
        self.goto_entry.bind('<Key>', self._reset_goto)

    @property
    def manager(self):
        return self._manager

    @manager.setter
    def manager(self, new_manager):
        if CONFIG.get("General", "layout") in ["vertical", "horizontal2"]:
            self.configure(style='TFrame')
            self._close_btn.grid_remove()
        else:
            self.configure(style='border.TFrame')
            self._close_btn.grid()
        if self.visible.get():
            try:
                self._manager.forget(self)
            except TclError:
                pass
            self._manager = new_manager
            self.show()
        else:
            self._manager = new_manager

    def _reset_goto(self, event):
        self._goto_index = 0

    def hide(self):
        try:
            layout = CONFIG.get("General", "layout")
            if layout in ["vertical", "horizontal2"]:
                self.manager.hide(self)
            else:
                # save layout
                old = CONFIG.get("Layout", layout).split()
                w = self.master.winfo_width()
                pos = '%.3f' % (self.master.sashpos(0)/w)
                CONFIG.set("Layout", layout, f"{pos} {old[1]}")
                CONFIG.save()
                self.manager.forget(self)
        except TclError:
            pass

    def show(self):
        layout = CONFIG.get("General", "layout")
        if layout in ["vertical", "horizontal2"]:
            self.manager.add(self, text=self.name)
            self.manager.select(self)
        else:
            self.manager.insert(0, self, weight=1)
            w = self.master.winfo_width()
            pos = int(float(CONFIG.get("Layout", layout).split()[0]) * w)
            self.master.sashpos(0, pos)

    def _visibility_trace(self, *args):
        visible = self.visible.get()
        if visible:
            self.show()
        else:
            self.hide()
        CONFIG.set('Code structure', 'visible', str(visible))
        CONFIG.save()

    def get_cells(self):
        return self.codetree.cells

    def clear(self, event=None):
        self.codetree.delete(*self.codetree.get_children())
        self.filename.configure(text='')

    def populate(self, title, text):
        self.filename.configure(text=title)
        self._sx.timer = self._sx.threshold + 1
        self._sy.timer = self._sy.threshold + 1
        try:
            names = list(self.codetree.populate(text))
        except TclError:
            logging.exception('CodeStructure Error')
            self.codetree.delete(*self.codetree.get_children())
            return
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
