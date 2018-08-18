#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 18 15:04:09 2018

@author: juliette
"""
from tkinter import PhotoImage
from tkinter.ttk import Treeview, Frame, Label, Combobox
from tokenize import tokenize
from tkeditorlib.autoscrollbar import AutoHideScrollbar as Scrollbar
from tkeditorlib.autocomplete import AutoCompleteCombobox
from io import BytesIO
import os

IM_CLASS = os.path.join(os.path.dirname(__file__), 'images', 'c.png')
IM_FCT = os.path.join(os.path.dirname(__file__), 'images', 'f.png')
IM_HFCT = os.path.join(os.path.dirname(__file__), 'images', 'hf.png')


class CodeTree(Treeview):
    def __init__(self, master):
        Treeview.__init__(self, master, show='tree', selectmode='none')
        self._img_class = PhotoImage(file=IM_CLASS, master=self)
        self._img_fct = PhotoImage(file=IM_FCT, master=self)
        self._img_hfct = PhotoImage(file=IM_HFCT, master=self)

        self.tag_configure('class', image=self._img_class)
        self.tag_configure('def', image=self._img_fct)
        self.tag_configure('_def', image=self._img_hfct)
        self.callback = None

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
        tokens = tokenize(BytesIO(text.encode()).readline)
        names = set()
        while True:
            try:
                token = tokens.send(None)
            except StopIteration:
                break
            if token.type == 1:  # name
                if token.string in ['class', 'def']:
                    obj_type = token.string
                    index = token.start[1] // 4
                    token = tokens.send(None)
                    name = token.string
                    names.add(name)
                    if name[0] == '_' and obj_type == 'def':
                        obj_type = '_def'
                    parent = ''
                    for i in range(index):
                        parent = self.get_children(parent)[-1]
                    self.insert(parent, 'end', text=name,
                                tag=(obj_type, name),
                                values=('%i.%i' % token.start, '%i.%i' % token.end))
        return names


class CodeStructure(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, padding=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.codetree = CodeTree(self)
        sx = Scrollbar(self, orient='horizontal', command=self.codetree.xview)
        sy = Scrollbar(self, orient='vertical', command=self.codetree.yview)

        self.goto_frame = Frame(self)
        Label(self.goto_frame, text='Go to: ').pack(side='left')
        self.goto_entry = AutoCompleteCombobox(self.goto_frame, completevalues=[])
        self.goto_entry.pack(side='left', fill='x')
        self._goto_index = 0

        self.codetree.configure(xscrollcommand=sx.set,
                                yscrollcommand=sy.set)

        self.codetree.grid(row=0, column=0, sticky='ewns')
        sx.grid(row=1, column=0, sticky='ew')
        sy.grid(row=0, column=1, sticky='ns')
        self.goto_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=4)

        self.set_callback = self.codetree.set_callback

        self.goto_entry.bind('<Return>', self.goto)
        self.goto_entry.bind('<<ComboboxSelected>>', self.goto)
        self.goto_entry.bind('<Key>', self._reset_goto)

    def _reset_goto(self, event):
        self._goto_index = 0

    def populate(self, text):
        names = list(self.codetree.populate(text))
        names.sort()
        self.goto_entry.set_completion_list(names)

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
