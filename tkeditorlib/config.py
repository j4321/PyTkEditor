#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 09:57:50 2018

@author: juliette
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font
from pygments.styles import get_all_styles
from tkeditorlib.constants import CONFIG, save_config
from tkeditorlib.autocomplete import AutoCompleteCombobox


class Config(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.transient(master)
        self.grab_set()
        self.configure(padx=4, pady=4)
        self.title('TkEditor - Config')

        ttk.Label(self, text='General', font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=4, pady=4)
        # --- theme
        menu_theme = tk.Menu(self, tearoff=False)
        self.theme = tk.StringVar(self, CONFIG.get('General', 'theme'))
        menu_theme.add_radiobutton(label='light', variable=self.theme,
                                   value='light')
        menu_theme.add_radiobutton(label='dark', variable=self.theme,
                                   value='dark')
        ttk.Label(self, text='Theme:').grid(row=1, column=0, sticky='e',
                                            padx=4, pady=4)
        ttk.Menubutton(self, menu=menu_theme,
                       textvariable=self.theme).grid(row=1, column=1, padx=4,
                                                     pady=4, sticky='w')
        # --- font
        families = list(font.families())
        families.sort()
        self.family = AutoCompleteCombobox(self, values=families)
        self.family.insert(0, CONFIG.get('General', 'fontfamily'))
        self.size = AutoCompleteCombobox(self, values=[str(i) for i in range(6, 20)],
                                         allow_other_values=True, width=3)
        self.size.insert(0, CONFIG.get('General', 'fontsize'))

        ttk.Label(self, text='Font:').grid(row=2, column=0, sticky='e', padx=4, pady=4)
        self.family.grid(row=2, column=1, sticky='w', padx=4, pady=4)
        self.size.grid(row=2, column=2, sticky='w', padx=4, pady=4)

        ttk.Separator(self, orient='horizontal').grid(row=3, columnspan=3,
                                                      sticky='ew', pady=8, padx=4)
        # --- syntax highlighting
        styles = list(get_all_styles())
        styles.extend(['perso', 'persolight'])
        styles.sort()
        self.editor_style = AutoCompleteCombobox(self, values=styles)
        self.editor_style.insert(0, CONFIG.get('Editor', 'style'))
        self.console_style = AutoCompleteCombobox(self, values=styles)
        self.console_style.insert(0, CONFIG.get('Console', 'style'))

        ttk.Label(self, text='Syntax Highlighting', font=('TkDefaultFont', 10, 'bold')).grid(row=4, column=0, sticky='w', padx=4, pady=4)
        ttk.Label(self, text='Editor').grid(row=5, column=0, sticky='e', padx=4, pady=4)
        self.editor_style.grid(row=5, column=1, sticky='w', padx=4, pady=4)
        ttk.Label(self, text='Console').grid(row=6, column=0, sticky='e', padx=4, pady=4)
        self.console_style.grid(row=6, column=1, sticky='w', padx=4, pady=4)

        frame = ttk.Frame(self)
        ttk.Button(frame, text='Ok', command=self.validate).pack(side='left', padx=4)
        ttk.Button(frame, text='Cancel', command=self.destroy).pack(side='left', padx=4)
        frame.grid(row=7, columnspan=3, pady=8)

    def validate(self):
        CONFIG.set('General', 'theme', self.theme.get())
        family = self.family.get()
        if family:
            CONFIG.set('General', 'fontfamily', family)
        try:
            size = int(self.size.get())
            assert size > 0
        except (ValueError, AssertionError):
            pass
        else:
            CONFIG.set('General', 'fontsize', str(size))
        estyle = self.editor_style.get()
        if estyle:
            CONFIG.set('Editor', 'style', estyle)
        cstyle = self.console_style.get()
        if cstyle:
            CONFIG.set('Console', 'style', cstyle)
        save_config()
        self.destroy()
