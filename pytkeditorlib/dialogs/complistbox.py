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


Code completion listbox
"""
import tkinter as tk
from tkinter import ttk

from pytkeditorlib.gui_utils import AutoHideScrollbar


class CompListbox(tk.Toplevel):
    """Toplevel to display autocompletion results."""
    def __init__(self, master):
        tk.Toplevel.__init__(self, master, class_='PyTkEditor')
        self.overrideredirect(True)
        self.attributes('-type', '_NET_WM_WINDOW_TYPE_POPUP_MENU')

        self._completions = []
        self.callback = lambda: None

        frame = ttk.Frame(self, style='border.TFrame', padding=1)
        frame.pack(fill='both')

        self.listbox = tk.Listbox(frame, selectmode='browse', height=2,
                                  activestyle='none', bd=0, relief='flat',
                                  highlightthickness=0)
        scroll_y = AutoHideScrollbar(frame, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side='right', fill='y')
        self.listbox.pack(side='left', fill='both')
        self.withdraw()

        self.listbox.bind('<1>', self.validate)
        self.listbox.bind('<Escape>', lambda e: self.withdraw())

    def sel_next(self):
        """Select next value."""
        sel = self.listbox.curselection()
        sel = (sel[0] + 1) % self.listbox.index('end')
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set(sel)
        self.listbox.see(sel)

    def sel_prev(self):
        """Select previous value."""
        sel = self.listbox.curselection()
        sel = (sel[0] - 1) % self.listbox.index('end')
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set(sel)
        self.listbox.see(sel)

    def set_callback(self, fct):
        """Set callback function called upon validation."""
        self.callback = fct

    def update_completion(self, completions):
        """Update completion list."""
        self.listbox.delete(0, 'end')
        self._completions = {}
        for comp in completions:
            self.listbox.insert('end', comp.name)
            self._completions[comp.name] = comp.complete
        self.listbox.selection_set(0)
        self.listbox.configure(height=min(5, len(completions)))
        self.update_idletasks()

    def get(self):
        """Get completion corresponding to selected value."""
        return self._completions[self.listbox.selection_get()]

    def validate(self, event):
        """Validate selection."""
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set('@%i,%i' % (event.x, event.y))
        self.callback()
