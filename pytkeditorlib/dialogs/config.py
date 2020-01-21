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


Config dialog
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font

from pygments.styles import get_all_styles

from pytkeditorlib.utils.constants import CONFIG, save_config, PATH_TEMPLATE
from pytkeditorlib.gui_utils import AutoCompleteCombobox


class Config(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.transient(master)
        self.grab_set()
        self.configure(padx=8, pady=4)
        self.title('PyTkEditor - Config')

        # --- General
        frame_general = ttk.Frame(self)
        ttk.Label(frame_general, text='General',
                  font=('TkDefaultFont', 10, 'bold')).grid(row=0, columnspan=3,
                                                           sticky='w', pady=4)
        # --- --- theme
        menu_theme = tk.Menu(frame_general, tearoff=False)
        self.theme = tk.StringVar(frame_general, CONFIG.get('General', 'theme'))
        menu_theme.add_radiobutton(label='light', variable=self.theme,
                                   value='light')
        menu_theme.add_radiobutton(label='dark', variable=self.theme,
                                   value='dark')
        ttk.Label(frame_general, text='Theme:').grid(row=1, column=0, sticky='e',
                                                     padx=4, pady=4)
        ttk.Menubutton(frame_general, menu=menu_theme, width=5,
                       textvariable=self.theme).grid(row=1, column=1, padx=4,
                                                     pady=4, sticky='w')
        # --- --- font
        families = list(font.families())
        families.sort()
        length = max([len(f) for f in families])
        self.family = AutoCompleteCombobox(frame_general, values=families, width=length - 1)
        self.family.insert(0, CONFIG.get('General', 'fontfamily'))
        self.size = AutoCompleteCombobox(frame_general, values=[str(i) for i in range(6, 20)],
                                         allow_other_values=True, width=3)
        self.size.insert(0, CONFIG.get('General', 'fontsize'))

        ttk.Label(frame_general, text='Font:').grid(row=2, column=0, sticky='e', padx=4, pady=4)
        self.family.grid(row=2, column=1, sticky='w', padx=4, pady=4)
        self.size.grid(row=2, column=2, sticky='w', padx=4, pady=4)

        # --- --- new file template
        ttk.Button(frame_general, text='Edit new file template',
                   command=self.edit_template).grid(row=3, columnspan=3, sticky='w', padx=6, pady=4)

        # --- syntax highlighting
        frame_s_h = ttk.Frame(self)
        styles = list(get_all_styles())
        styles.extend(['perso', 'persolight'])
        styles.sort()
        self.editor_style = AutoCompleteCombobox(frame_s_h, values=styles)
        self.editor_style.insert(0, CONFIG.get('Editor', 'style'))
        self.console_style = AutoCompleteCombobox(frame_s_h, values=styles)
        self.console_style.insert(0, CONFIG.get('Console', 'style'))

        ttk.Label(frame_s_h, text='Syntax Highlighting',
                  font=('TkDefaultFont', 10, 'bold')).grid(row=0, columnspan=2,
                                                           sticky='w', pady=4)
        ttk.Label(frame_s_h, text='Editor:').grid(row=1, column=0, sticky='e', padx=4, pady=4)
        self.editor_style.grid(row=1, column=1, sticky='w', padx=4, pady=4)
        ttk.Label(frame_s_h, text='Console:').grid(row=2, column=0, sticky='e', padx=4, pady=4)
        self.console_style.grid(row=2, column=1, sticky='w', padx=4, pady=4)

        # --- code checking
        frame_check = ttk.Frame(self)
        frame_check.columnconfigure(1, weight=1)
        self.code_check = ttk.Checkbutton(frame_check,
                                          text='Check code')
        if CONFIG.getboolean("Editor", "code_check", fallback=True):
            self.code_check.state(('selected', '!alternate'))
        else:
            self.code_check.state(('!selected', '!alternate'))
        self.style_check = ttk.Checkbutton(frame_check,
                                           text='Check style - PEP8 guidelines')
        if CONFIG.getboolean("Editor", "style_check", fallback=True):
            self.style_check.state(('selected', '!alternate'))
        else:
            self.style_check.state(('!selected', '!alternate'))

        ttk.Label(frame_check, text='Code checking (on file saving)',
                  font=('TkDefaultFont', 10, 'bold')).grid(row=0, columnspan=2,
                                                           sticky='w', pady=4)
        self.code_check.grid(row=1, columnspan=2, sticky='w', padx=4, pady=4)
        self.style_check.grid(row=2, columnspan=2, sticky='w', padx=4, pady=4)

        # --- History
        frame_history = ttk.Frame(self)
        frame_history.columnconfigure(1, weight=1)
        ttk.Label(frame_history, text='History',
                  font=('TkDefaultFont', 10, 'bold')).grid(row=0, columnspan=2,
                                                           sticky='w', pady=4)
        ttk.Label(frame_history,
                  text='Maximum size (truncated when quitting):').grid(row=1, column=0, sticky='e',
                                                                       padx=4, pady=4)
        self.history_size = ttk.Entry(frame_history)
        self.history_size.insert(0, CONFIG.get('History', 'max_size', fallback='10000'))
        self.history_size.grid(row=1, column=1, sticky='ew', padx=4, pady=4)

        # --- ok / cancel buttons
        frame_btn = ttk.Frame(self)
        ttk.Button(frame_btn, text='Ok', command=self.validate).pack(side='left', padx=4)
        ttk.Button(frame_btn, text='Cancel', command=self.destroy).pack(side='left', padx=4)

        # --- placement
        frame_general.pack(side='top', anchor='w')
        ttk.Separator(self, orient='horizontal').pack(side='top', fill='x', pady=8)
        frame_s_h.pack(side='top', anchor='w')
        ttk.Separator(self, orient='horizontal').pack(side='top', fill='x', pady=8)
        frame_check.pack(side='top', fill='x')
        ttk.Separator(self, orient='horizontal').pack(side='top', fill='x', pady=8)
        frame_history.pack(side='top', fill='x')
        frame_btn.pack(side='top', pady=8)

    def edit_template(self):
        self.master.open(PATH_TEMPLATE)

    def validate(self):
        # --- general
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
        # --- syntax highlighting
        estyle = self.editor_style.get()
        if estyle:
            CONFIG.set('Editor', 'style', estyle)
        cstyle = self.console_style.get()
        if cstyle:
            CONFIG.set('Console', 'style', cstyle)
        # --- code checking
        if 'selected' in self.code_check.state():
            CONFIG.set('Editor', 'code_check', 'True')
        else:
            CONFIG.set('Editor', 'code_check', 'False')
        if 'selected' in self.style_check.state():
            CONFIG.set('Editor', 'style_check', 'True')
        else:
            CONFIG.set('Editor', 'style_check', 'False')
        # --- history
        try:
            size = int(self.history_size.get())
            assert size > 0
        except (ValueError, AssertionError):
            pass
        else:
            CONFIG.set('History', 'max_size', str(size))
        save_config()
        self.destroy()
