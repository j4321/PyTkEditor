#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 17 19:32:16 2018

@author: juliette
"""
import tkinter as tk
from tkinter import ttk
from tkeditorlib.autoscrollbar import AutoHideScrollbar


class CompListbox(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master, class_='TkEditor')
        self.overrideredirect(True)
        self.attributes('-type', '_NET_WM_WINDOW_TYPE_POPUP_MENU')

        self._completions = []

        frame = ttk.Frame(self, style='border.TFrame', padding=1)
        frame.pack(fill='both')

        self.listbox = tk.Listbox(frame, selectmode='browse', height=2,
                                  activestyle='none', bd=0, relief='flat',
                                  highlightthickness=0)
        sy = AutoHideScrollbar(frame, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sy.set)
        sy.pack(side='right', fill='y')
        self.listbox.pack(side='left', fill='both')
        self.withdraw()

        self.listbox.bind('<1>', self.validate)
        self.listbox.bind('<Escape>', lambda e: self.withdraw())

    def sel_next(self):
        sel = self.listbox.curselection()
        sel = (sel[0] + 1) % self.listbox.index('end')
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set(sel)
        self.listbox.see(sel)

    def sel_prev(self):
        sel = self.listbox.curselection()
        sel = (sel[0] - 1) % self.listbox.index('end')
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set(sel)
        self.listbox.see(sel)

    def set_callback(self, fct):
        self.callback = fct

    def update(self, completions):
        self.listbox.delete(0, 'end')
        self._completions = {}
        for c in completions:
            self.listbox.insert('end', c.name)
            self._completions[c.name] = c.complete
        self.listbox.selection_set(0)
        self.listbox.configure(height=min(5, len(completions)))
        self.update_idletasks()

    def get(self):
        return self._completions[self.listbox.selection_get()]

    def validate(self, event):
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set('@%i,%i' % (event.x, event.y))
        self.callback()