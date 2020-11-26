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
from tkinter import TclError, Menu
from tkinter.ttk import Treeview, Frame, Label, Button
from tkinter.font import Font
import tokenize
from io import BytesIO
import re
import logging

from pytkeditorlib.gui_utils import AutoHideScrollbar, AutoCompleteCombobox2
from pytkeditorlib.utils.constants import CONFIG
from pytkeditorlib.dialogs import TooltipWrapper
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
    def __init__(self, master, click_callback=None):
        Treeview.__init__(self, master, show='tree', selectmode='none',
                          style='mono.flat.Treeview', padding=4)

        self.font = Font(self, font="TkFixedFont")

        self.tag_configure('class', image='img_c')
        self.tag_configure('def', image='img_f')
        self.tag_configure('_def', image="img_hf")
        self.tag_configure('#', image='img_sep')
        self.tag_configure('cell', image='img_cell')
        self.callback = click_callback
        self.cells = []

        self._re_cell1 = re.compile(r'^# In(\[.*\].*)$')
        self._re_cell2 = re.compile(r'^# ?%% ?(.*)$')

        # right click menu
        self.menu = Menu(self)
        self.menu.add_command(label='Expand section', command=self._expand_section)
        self.menu.add_command(label='Collapse section', command=self._collapse_section)
        self._row_menu = ''  # row where the pointer was when the menu was opened

        # bindings
        self.bind('<3>', self._post_menu)
        self.bind('<1>', self._on_click)
        self.bind('<<TreeviewSelect>>', self._on_select)

    def _on_click(self, event):
        if 'indicator' not in self.identify_element(event.x, event.y):
            self.selection_remove(*self.selection())
            self.selection_set(self.identify_row(event.y))

    def _on_select(self, event):
        sel = self.selection()
        if self.callback is not None and sel:
            self.callback(*self.item(sel[0], 'values'))

    def _get_opened(self):
        opened = []

        def rec(item):
            if self.item(item, 'open'):
                opened.append(self.item(item, 'tags'))
                for child in self.get_children(item):
                    rec(child)

        for item in self.get_children():
            rec(item)
        return opened


    def _post_menu(self, event):
        self._row_menu = self.identify_row(event.y_root - self.winfo_rooty())
        if self._row_menu:
            self.menu.tk_popup(event.x_root, event.y_root)

    def _collapse_section(self):
        self.collapse(self._row_menu)

    def _expand_section(self):
        self.expand(self._row_menu)

    def expand(self, item):
        """Expand item and all its children recursively."""
        self.item(item, open=True)
        for c in self.get_children(item):
            self.expand(c)

    def expand_all(self):
        """Expand all items."""
        for c in self.get_children(""):
            self.expand(c)

    def collapse(self, item):
        """Collapse item and all its children recursively."""
        self.item(item, open=False)
        for c in self.get_children(item):
            self.collapse(c)

    def collapse_all(self):
        """Collapse all items."""
        for c in self.get_children(""):
            self.collapse(c)

    def get_cells(self, text):
        self.cells.clear()

        for i, line in enumerate(text.splitlines(), 1):
            match = self._re_cell1.match(line)
            if match:
                self.cells.append(i)
            else:
                match = self._re_cell2.match(line)
                if match:
                    self.cells.append(i)

    def populate(self, text, reset):
        if reset:
            opened = []
        else:
            opened = self._get_opened()
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
                indent = token.start[1] + 4
                token = tokens.send(None)
                name = token.string
                names.add(name)
                if name[0] == '_' and obj_type == 'def':
                    obj_type = '_def'
                add = True
            elif token.type == tokenize.COMMENT:
                if token.string[:5] == '# ---' or 'TODO' in token.string:
                    obj_type = '#'
                    indent = token.start[1] + 4
                    name = token.string[1:]
                    add = True
                else:
                    match = self._re_cell1.match(token.string)
                    if match:
                        obj_type = 'cell'
                        indent = 0
                        name = match.groups()[0].strip()
                        add = True
                        self.cells.append(token.start[0])
                    else:
                        match = self._re_cell2.match(token.string)
                        if match:
                            obj_type = 'cell'
                            indent = 0
                            name = match.groups()[0].strip()
                            add = True
                            self.cells.append(token.start[0])

            if add:
                tree_index += 1
                parent = tree.insert('I-%i' % tree_index, indent)
                max_length = max(max_length, self.font.measure(name) + 20 + (indent//4 + 1) * 20)
                tags = (obj_type, name)
                self.insert(parent, 'end', f'I-{tree_index}', text=name,
                            tags=tags, open=tags in opened,
                            values=('%i.%i' % token.start, '%i.%i' % token.end))

        self.column('#0', width=max_length, minwidth=max_length)
        for item in self.get_children(''):
            self.item(item, open=True)
        return names

    def update_style(self):
        fg = self.menu.option_get('foreground', '*Menu')
        bg = self.menu.option_get('background', '*Menu')
        activebackground = self.menu.option_get('activeBackground', '*Menu')
        disabledforeground = self.menu.option_get('disabledForeground', '*Menu')
        self.menu.configure(bg=bg, activebackground=activebackground,
                            fg=fg, selectcolor=fg, activeforeground=fg,
                            disabledforeground=disabledforeground)


class CodeStructure(BaseWidget):
    def __init__(self, master, manager, click_callback):
        BaseWidget.__init__(self, master, 'Code structure', style='border.TFrame')
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        self._manager = manager

        self._text = ''
        self._title = ''

        tooltips = TooltipWrapper(self)

        # tree
        self.codetree = CodeTree(self, click_callback=click_callback)
        self._sx = AutoHideScrollbar(self, orient='horizontal', command=self.codetree.xview)
        self._sy = AutoHideScrollbar(self, orient='vertical', command=self.codetree.yview)
        self.codetree.configure(xscrollcommand=self._sx.set,
                                yscrollcommand=self._sy.set)
        # header
        header = Frame(self, padding=(1, 2, 1, 1))
        header.columnconfigure(3, weight=1)
        btn_exp = Button(header, padding=0, command=self.codetree.expand_all,
                         image='img_expand_all')
        btn_exp.grid(row=0, column=0)
        tooltips.add_tooltip(btn_exp, 'Expand all')
        btn_col = Button(header, padding=0, command=self.codetree.collapse_all,
                         image='img_collapse_all')
        btn_col.grid(row=0, column=1, padx=4)
        tooltips.add_tooltip(btn_col, 'Collapse all')
        self.btn_refresh = Button(header, padding=0, command=lambda: self.event_generate('<<Refresh>>'),
                                  image='img_refresh')
        self.btn_refresh.grid(row=0, column=2)
        tooltips.add_tooltip(self.btn_refresh, 'Refresh')
        self._close_btn = Button(header, style='close.TButton', padding=1,
                                 command=lambda: self.visible.set(False))
        self._close_btn.grid(row=0, column=3, sticky='e')

        self.filename = Label(self, style='txt.TLabel', padding=(4, 0))

        # goto bar
        self.goto_frame = Frame(self)
        Label(self.goto_frame, text='Go to:').pack(side='left')
        self.goto_entry = AutoCompleteCombobox2(self.goto_frame, completevalues=[])
        self.goto_entry.pack(side='left', fill='x', expand=True, pady=4, padx=4)
        self._goto_index = 0

        # placement
        header.grid(row=0, columnspan=2, sticky='we')
        self.filename.grid(row=1, columnspan=2, sticky='we')
        self.codetree.grid(row=2, column=0, sticky='ewns')
        self._sx.grid(row=3, column=0, sticky='ew')
        self._sy.grid(row=2, column=1, sticky='ns')
        Frame(self, style='separator.TFrame', height=1).grid(row=4, column=0, columnspan=2, sticky='ew')
        self.goto_frame.grid(row=5, column=0, columnspan=2, sticky='nsew')

        self.update_style = self.codetree.update_style

        # bindings
        self.filename.bind('<1>', self._header_callback)
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

    def _header_callback(self, event):
        if self.codetree.callback is not None:
            self.codetree.callback('1.0', '1.0')

    def focus_set(self):
        self.goto_entry.focus_set()

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
            self._display()
        else:
            self.hide()
        CONFIG.set('Code structure', 'visible', str(visible))
        CONFIG.save()

    def get_cells(self):
        return self.codetree.cells

    def clear(self, event=None):
        self.codetree.delete(*self.codetree.get_children())
        self.filename.configure(text='')
        self.btn_refresh.state(['disabled'])

    def _display(self):
        """Display code structure."""
        reset = self.filename.cget('text') != self._title
        self.filename.configure(text=self._title)
        self._sx.timer = self._sx.threshold + 1
        self._sy.timer = self._sy.threshold + 1
        try:
            names = list(self.codetree.populate(self._text, reset))
        except TclError:
            logging.exception('CodeStructure Error')
            self.codetree.delete(*self.codetree.get_children())
            return
        names.sort()
        self.goto_entry.delete(0, "end")
        self.goto_entry.set_completion_list(names)
        self.btn_refresh.state(['!disabled'])

    def populate(self, title, text):
        self._text = text
        self._title = title
        if not self.visible.get():
            self.codetree.get_cells(text)
        else:
            self._display()
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


