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
from tkcolorpicker import askcolor

from pytkeditorlib.utils.constants import CONFIG, PATH_TEMPLATE, JUPYTER
from pytkeditorlib.gui_utils import AutoCompleteCombobox
from .messagebox import askokcancel


class ColorFrame(ttk.Frame):
    def __init__(self, master=None, color='white', label='Color'):
        ttk.Frame.__init__(self, master, padding=(4, 0))
        self.label = ttk.Label(self, text=label)
        self.label.pack(side='left')
        self.entry = ttk.Entry(self, width=8)
        self.entry.insert(0, color)
        self.entry.pack(side='left', padx=4)
        self.button = ttk.Button(self, image='img_color', padding=0,
                                 command=self.askcolor)
        self.button.pack(side='left')

    def state(self, statespec=None):
        self.button.state(statespec)
        self.label.state(statespec)
        return ttk.Frame.state(self, statespec)

    def askcolor(self):
        icolor = self.entry.get()
        try:
            self.winfo_rgb(icolor)
        except tk.TclError:
            icolor = "red"
        color = askcolor(icolor, parent=self, title='Color')[1]
        self.update_idletasks()
        if color is not None:
            self.entry.delete(0, 'end')
            self.entry.insert(0, color)

    def get_color(self):
        color = self.entry.get()
        if color:
            try:
                self.winfo_rgb(color)
            except tk.TclError:
                color = None
        return color



class FormattingFrame(ttk.Frame):
    def __init__(self, master=None, fg='black', bg='white', *font_formatting):
        ttk.Frame.__init__(self, master, padding=4)
        style = ttk.Style(self)
        style.configure('bold.TCheckbutton', font='TkDefaultFont 9 bold')
        style.configure('italic.TCheckbutton', font='TkDefaultFont 9 italic')
        style.configure('underline.TCheckbutton', font='TkDefaultFont 9 underline')
        self._init_fg = fg
        self._init_bg = bg
        # fg
        self.fg = ColorFrame(self, fg, 'foreground')
        # bg
        self.bg = ColorFrame(self, bg, 'background')

        # font formatting
        bold = ttk.Checkbutton(self, text='B', style='bold.TCheckbutton')
        bold.state(['!alternate', '!'*('bold' not in font_formatting) + 'selected'])
        italic = ttk.Checkbutton(self, text='I', style='italic.TCheckbutton')
        italic.state(['!alternate', '!'*('italic' not in font_formatting) + 'selected'])
        underline = ttk.Checkbutton(self, text='U', style='underline.TCheckbutton')
        underline.state(['!alternate', '!'*('underline' not in font_formatting) + 'selected'])
        self.formatting = [bold, italic, underline]

        # placement
        self.fg.pack(side='left')
        self.bg.pack(side='left')
        bold.pack(side='left', padx=(4, 1))
        italic.pack(side='left', padx=1)
        underline.pack(side='left', padx=(1, 0))

    def state(self, statespec=None):
        self.bg.state(statespec)
        self.fg.state(statespec)
        for cb in self.formatting:
            cb.state(statespec)
        return ttk.Frame.state(self, statespec)

    def get_formatting(self):
        fg = self.fg.get_color()
        if fg is None:
            fg = self._init_fg
        bg = self.bg.get_color()
        if bg is None:
            bg = self._init_bg
        formatting = ['bold', 'italic', 'underline']
        font_formatting = ';'.join([f for f, cb in zip(formatting, self.formatting) if 'selected' in cb.state()])
        return f"{fg};{bg};{font_formatting}"


class Config(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.transient(master)
        self.minsize(529, 381)
        self.grab_set()
        self.configure(padx=8, pady=4)
        self.title('PyTkEditor - Settings')

        self.notebook = ttk.Notebook(self)

        # --- ok / cancel buttons
        frame_btn = ttk.Frame(self)
        ttk.Button(frame_btn, text='Ok', command=self.validate).pack(side='left', padx=4)
        ttk.Button(frame_btn, text='Cancel', command=self.destroy).pack(side='left', padx=4)

        self._init_general()
        self._init_editor()
        self._init_console()
        self._init_run()

        self.notebook.pack(fill='both', expand=True)
        frame_btn.pack(pady=8)

    def _init_general(self):
        frame_general = ttk.Frame(self.notebook, padding=4)
        self.notebook.add(frame_general, text='General')

        # --- theme
        self.theme = tk.StringVar(self, CONFIG.get('General', 'theme'))
        ctheme = ttk.Combobox(frame_general, textvariable=self.theme, state='readonly',
                              values=['dark', 'light'], width=5)
        ttk.Label(frame_general, text='Theme:').grid(row=0, column=0, sticky='e', padx=4, pady=8)
        ctheme.grid(row=0, column=1, sticky='w', padx=4, pady=8)

        # --- font
        families = list(font.families())
        families.sort()
        length = max([len(f) for f in families])
        self.family = AutoCompleteCombobox(frame_general, values=families, width=length - 1)
        self.family.insert(0, CONFIG.get('General', 'fontfamily'))
        self.size = AutoCompleteCombobox(frame_general, values=[str(i) for i in range(6, 20)],
                                         allow_other_values=True, width=3)
        self.size.insert(0, CONFIG.get('General', 'fontsize'))

        ttk.Label(frame_general, text='Font:').grid(row=1, column=0, sticky='e', padx=4, pady=8)
        self.family.grid(row=1, column=1, sticky='w', padx=4, pady=8)
        self.size.grid(row=1, column=2, sticky='w', padx=4, pady=8)

        # --- new file template
        frame_template = ttk.Frame(frame_general)
        ttk.Label(frame_template,
                  text='Edit new file template').pack(side='left', padx=4, pady=8)
        ttk.Button(frame_template, image='img_edit', padding=1,
                   command=self.edit_template).pack(side='left', padx=4, pady=8)
        frame_template.grid(row=2, columnspan=2, sticky='w')

        # --- confirm quit
        self.confirm_quit = ttk.Checkbutton(frame_general, text="Show confirmation dialog before exiting")
        if CONFIG.getboolean("General", "confirm_quit", fallback=False):
            self.confirm_quit.state(('selected', '!alternate'))
        else:
            self.confirm_quit.state(('!selected', '!alternate'))
        self.confirm_quit.grid(row=3, columnspan=2, sticky='w', padx=4, pady=4)

    def _init_editor(self):
        frame_editor = ttk.Frame(self.notebook, padding=4)
        self.notebook.add(frame_editor, text='Editor')

        frame_editor.columnconfigure(1, weight=1)


        # --- --- comment marker
        self.comment_marker = ttk.Entry(frame_editor, width=3)
        self.comment_marker.insert(0, CONFIG.get("Editor", "comment_marker", fallback="~"))

        # --- code checking
        self.code_check = ttk.Checkbutton(frame_editor, text='Check code')
        if CONFIG.getboolean("Editor", "code_check", fallback=True):
            self.code_check.state(('selected', '!alternate'))
        else:
            self.code_check.state(('!selected', '!alternate'))
        self.style_check = ttk.Checkbutton(frame_editor,
                                           text='Check style - PEP8 guidelines')
        if CONFIG.getboolean("Editor", "style_check", fallback=True):
            self.style_check.state(('selected', '!alternate'))
        else:
            self.style_check.state(('!selected', '!alternate'))

        # --- syntax highlighting
        frame_s_h = ttk.Frame(frame_editor)
        frame_s_h.columnconfigure(1, weight=1)
        styles = list(get_all_styles())
        styles.sort()
        w = len(max(styles, key=lambda x: len(x)))

        self.editor_style = AutoCompleteCombobox(frame_s_h, values=styles, width=w)
        self.editor_style.insert(0, CONFIG.get('Editor', 'style'))
        mb = CONFIG.get('Editor', 'matching_brackets', fallback='#00B100;;bold').split(';')
        self.editor_matching_brackets = FormattingFrame(frame_s_h, *mb)
        umb = CONFIG.get('Editor', 'unmatched_bracket', fallback='#FF0000;;bold').split(';')
        self.editor_unmatched_bracket = FormattingFrame(frame_s_h, *umb)

        ttk.Label(frame_s_h, text='Theme:').grid(row=1, column=0, sticky='e', pady=(0, 10))
        self.editor_style.grid(row=1, column=1, sticky='w', padx=8, pady=(0, 10))
        ttk.Label(frame_s_h, text='Matching brackets:').grid(row=2, column=0, columnspan=2, sticky='w')
        self.editor_matching_brackets.grid(row=3, column=0, columnspan=2, sticky='w', padx=4)
        ttk.Label(frame_s_h, text='Unmatched bracket:').grid(row=4, column=0, columnspan=2, sticky='w', pady=(8, 0))
        self.editor_unmatched_bracket.grid(row=5, column=0, columnspan=2, sticky='w', padx=4)

        # --- placement
        ttk.Label(frame_editor,
                  text='Comment toggle marker:').grid(row=0, column=0, sticky='e', padx=4, pady=4)
        self.comment_marker.grid(row=0, column=1, sticky='w', padx=4, pady=4)
        ttk.Label(frame_editor,
                  text='Code checking (on file saving):').grid(row=1, column=0,
                                                               sticky='e', padx=4, pady=4)
        self.code_check.grid(row=1, column=1, sticky='w', padx=3, pady=4)
        self.style_check.grid(row=2, column=1, sticky='w', padx=3, pady=4)
        ttk.Separator(frame_editor, orient='horizontal').grid(row=3, columnspan=2, sticky='ew', pady=4)
        ttk.Label(frame_editor,
                  text='Syntax Highlighting:').grid(row=4, columnspan=2,
                                                    sticky='w', pady=4, padx=4)
        frame_s_h.grid(row=5, columnspan=2, sticky='ew', pady=(4, 8), padx=12)

    def _init_console(self):
        frame_console = ttk.Frame(self.notebook, padding=4)
        self.notebook.add(frame_console, text='Console')

        frame_console.columnconfigure(1, weight=1)

        # --- history
        self.history_size = ttk.Entry(frame_console, width=6)
        self.history_size.insert(0, CONFIG.get('History', 'max_size', fallback='10000'))

        # --- syntax highlighting
        frame_s_h = ttk.Frame(frame_console)
        frame_s_h.columnconfigure(1, weight=1)
        styles = list(get_all_styles())
        styles.sort()
        w = len(max(styles, key=lambda x: len(x)))

        self.console_style = AutoCompleteCombobox(frame_s_h, values=styles, width=w)
        self.console_style.insert(0, CONFIG.get('Console', 'style'))
        mb = CONFIG.get('Console', 'matching_brackets', fallback='#00B100;;bold').split(';')
        self.console_matching_brackets = FormattingFrame(frame_s_h, *mb)
        umb = CONFIG.get('Console', 'unmatched_bracket', fallback='#FF0000;;bold').split(';')
        self.console_unmatched_bracket = FormattingFrame(frame_s_h, *umb)

        ttk.Label(frame_s_h, text='Theme:').grid(row=1, column=0, sticky='e', pady=(0, 10))
        self.console_style.grid(row=1, column=1, sticky='w', padx=8, pady=(0, 10))
        ttk.Label(frame_s_h, text='Matching brackets:').grid(row=2, column=0, columnspan=2, sticky='w')
        self.console_matching_brackets.grid(row=3, column=0, columnspan=2, sticky='w', padx=4)
        ttk.Label(frame_s_h, text='Unmatched bracket:').grid(row=4, column=0, columnspan=2, sticky='w', pady=(8, 0))
        self.console_unmatched_bracket.grid(row=5, column=0, columnspan=2, sticky='w', padx=4)

        # --- Jupyter QtConsole
        frame_qtconsole = ttk.Frame(frame_console)
        ttk.Label(frame_qtconsole, text='options to pass to jupyter-qtconsole').pack(side='left')
        self.jupyter_options = ttk.Entry(frame_qtconsole)
        self.jupyter_options.pack(side='right', fill='x', expand=True, padx=(4, 0))
        self.jupyter_options.insert(0, CONFIG.get('Console', 'jupyter_options', fallback=''))
        if not JUPYTER:
            self.jupyter_options.state(['disabled'])

        # --- placement
        ttk.Label(frame_console,
                  text='Maximum history size (truncated when quitting):').grid(row=0, column=0,
                                                                               sticky='e',
                                                                               padx=4, pady=4)
        self.history_size.grid(row=0, column=1, sticky='w', padx=4, pady=4)
        ttk.Separator(frame_console, orient='horizontal').grid(row=1, columnspan=2,
                                                               sticky='ew', pady=4)
        ttk.Label(frame_console,
                  text='Syntax Highlighting:').grid(row=2, columnspan=2,
                                                    sticky='w', pady=4, padx=4)
        frame_s_h.grid(row=3, columnspan=2, sticky='ew', pady=(4, 8), padx=12)

        ttk.Separator(frame_console, orient='horizontal').grid(row=4, columnspan=2,
                                                               sticky='ew', pady=4)
        ttk.Label(frame_console,
                  text='Jupyter Qtconsole:').grid(row=5, columnspan=2,
                                                  sticky='w', pady=4, padx=4)
        frame_qtconsole.grid(row=6, columnspan=2, sticky='ew', pady=(4, 8), padx=12)


    def _init_run(self):
        frame_run = ttk.Frame(self.notebook, padding=4)
        self.notebook.add(frame_run, text='Run')

        frame_run.columnconfigure(2, weight=1)
        # --- run
        self.run_console = tk.StringVar(self, CONFIG.get('Run', 'console'))

        self.external_interactive = ttk.Checkbutton(frame_run,
                                                    text='Interact with the Python console after execution')
        self.external_interactive.state(['!alternate',
                                         '!' * (self.run_console.get() == 'external') + 'disabled',
                                         '!' * (not CONFIG.getboolean('Run', 'external_interactive')) + 'selected'])

        self.external_console = ttk.Entry(frame_run)
        self.external_console.insert(0, CONFIG.get('Run', 'external_console', fallback=''))

        ttk.Label(frame_run, text='Execute in:').grid(row=1, column=0,
                                                      padx=(4, 8), pady=4, sticky='w')
        ttk.Radiobutton(frame_run, text='external terminal:', value='external',
                        command=self._run_setting,
                        variable=self.run_console).grid(row=1, column=1,
                                                        pady=4, sticky='w')
        ttk.Radiobutton(frame_run, text='embedded console', value='console',
                        command=self._run_setting,
                        variable=self.run_console).grid(row=2, column=1,
                                                        pady=4, sticky='w')

        jqt = ttk.Radiobutton(frame_run, text='Jupyter QtConsole', value='qtconsole',
                              command=self._run_setting,
                              variable=self.run_console)
        jqt.grid(row=3, column=1, pady=4, sticky='w')
        self.external_console.grid(row=1, column=2, sticky='ew', padx=(0, 4), pady=4)
        self.external_interactive.grid(row=4, columnspan=3, padx=4, pady=4, sticky='w')

        ttk.Separator(frame_run, orient='horizontal').grid(row=5, columnspan=3,
                                                           sticky='ew', pady=4)
        # --- run cell
        self.run_cell_in = tk.StringVar(self, CONFIG.get('Run', 'cell', fallback="console"))
        ttk.Label(frame_run, text='Execute cells in:').grid(row=6, column=0,
                                                            padx=(4, 8), pady=4, sticky='w')
        ttk.Radiobutton(frame_run, text='embedded console', value='console',
                        variable=self.run_cell_in).grid(row=6, column=1,
                                                        pady=4, sticky='w')

        jqt2 = ttk.Radiobutton(frame_run, text='Jupyter QtConsole', value='qtconsole',
                               variable=self.run_cell_in)
        jqt2.grid(row=7, column=1, pady=4, sticky='w')

        if not JUPYTER:
            jqt.state(['disabled'])
            jqt2.state(['disabled'])

    def _run_setting(self):
        if self.run_console.get() == 'external':
            self.external_interactive.state(['!disabled'])
        else:
            self.external_interactive.state(['disabled'])

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
        CONFIG.set('General', 'confirm_quit',
                   str('selected' in self.confirm_quit.state()))

        # --- editor
        # --- --- syntax highlighting
        estyle = self.editor_style.get()
        if estyle:
            CONFIG.set('Editor', 'style', estyle)
        CONFIG.set('Editor', 'matching_brackets', self.editor_matching_brackets.get_formatting())
        CONFIG.set('Editor', 'unmatched_bracket', self.editor_unmatched_bracket.get_formatting())
        cstyle = self.console_style.get()
        # --- --- code checking
        CONFIG.set('Editor', 'code_check',
                   str('selected' in self.code_check.state()))
        CONFIG.set('Editor', 'style_check',
                   str('selected' in self.style_check.state()))
        # --- console
        # --- --- history
        try:
            size = int(self.history_size.get())
            assert size > 0
        except (ValueError, AssertionError):
            pass
        else:
            CONFIG.set('History', 'max_size', str(size))
        # --- --- syntax highlighting
        cstyle = self.console_style.get()
        if cstyle:
            CONFIG.set('Console', 'style', cstyle)
        CONFIG.set('Console', 'matching_brackets', self.console_matching_brackets.get_formatting())
        CONFIG.set('Console', 'unmatched_bracket', self.console_unmatched_bracket.get_formatting())
        CONFIG.set('Console', 'jupyter_options', self.jupyter_options.get())
        # --- run
        console = self.run_console.get()
        CONFIG.set('Run', 'console', console)
        CONFIG.set('Run', 'external_interactive',
                   str('selected' in self.external_interactive.state()))
        external_console = self.external_console.get()
        CONFIG.set('Run', 'external_console', external_console)
        CONFIG.set('Run', 'cell', self.run_cell_in.get())
        if not external_console and console:
            ans = askokcancel("Warning",
                              'No external terminal is set so executing code in an external terminal will fail.',
                              self)
            if not ans:
                return
        CONFIG.save()
        self.destroy()
