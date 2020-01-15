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


Main app
"""
import tkinter as tk
from tkinter import ttk
import traceback
import os
import signal
import logging
from subprocess import Popen
from getpass import getuser
from datetime import datetime

from ewmh import ewmh, EWMH
from tkfilebrowser import askopenfilenames, asksaveasfilename
from tkcolorpicker import askcolor

from pytkeditorlib.editornotebook import EditorNotebook
from pytkeditorlib.syntax_check import check_file
from pytkeditorlib.codestructure import CodeStructure
from pytkeditorlib.filebrowser import Filebrowser
from pytkeditorlib.constants import IMAGES, CONFIG, save_config, IM_CLOSE
from pytkeditorlib import constants as cst
from pytkeditorlib.textconsole import TextConsole
from pytkeditorlib.history import HistoryFrame
from pytkeditorlib.search import SearchDialog
from pytkeditorlib.config import Config
from pytkeditorlib.autoscrollbar import AutoHideScrollbar
from pytkeditorlib.menu import LongMenu
from pytkeditorlib.help import Help
from pytkeditorlib.messagebox import showerror
from pytkeditorlib.about import About


class App(tk.Tk):
    def __init__(self, *files):
        tk.Tk.__init__(self, className='PyTkEditor')
        self.title('PyTkEditor')
        # --- images
        self._images = {name: tk.PhotoImage(f'img_{name}', file=IMAGES[name], master=self)
                        for name, path in IMAGES.items()}
        self._images['menu_dummy'] = tk.PhotoImage('img_menu_dummy', width=18, height=18, master=self)
        self._im_close = tk.PhotoImage(master=self)
        self.iconphoto(True, self._images['icon'])

        self.option_add('*Menu.borderWidth', 1)
        self.option_add('*Menu.activeBorderWidth', 0)
        self.option_add('*Menu.relief', 'sunken')
        self.option_add('*Menu.tearOff', False)

        self.menu = tk.Menu(self, relief='flat')
        self.menu_file = tk.Menu(self.menu)
        self.menu_recent_files = tk.Menu(self.menu_file)
        self.menu_edit = tk.Menu(self.menu)
        self.menu_search = tk.Menu(self.menu)
        self.menu_doc = tk.Menu(self.menu)
        self.menu_filetype = tk.Menu(self.menu_doc)
        self.menu_errors = LongMenu(self.menu_doc, 40)

        recent_files = CONFIG.get('General', 'recent_files', fallback='').split(', ')
        self.recent_files = [f for f in recent_files if f and os.path.exists(f)]

        # --- style
        for seq in self.bind_class('TButton'):
            self.bind_class('Notebook.Tab.Close', seq, self.bind_class('TButton', seq), True)
        style = ttk.Style(self)
        style.element_create('close', 'image', self._im_close,
                             sticky='')
        self._setup_style()

        # --- jupyter kernel
        self._init_kernel()
        self._qtconsole_process = None

        # --- GUI elements
        pane = ttk.PanedWindow(self, orient='horizontal')
        # ----- code structure tree
        self.codestruct = CodeStructure(pane)
        # ----- editor notebook
        self.editor = EditorNotebook(pane, width=696)
        # ----- right pane
        self.right_nb = ttk.Notebook(pane)
        # -------- command history
        self.history = HistoryFrame(self.right_nb, padding=1)
        # -------- python console
        console_frame = ttk.Frame(self.right_nb, padding=1)
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        sy = AutoHideScrollbar(console_frame, orient='vertical')
        self.console = TextConsole(console_frame, self.history.history,
                                   yscrollcommand=sy.set, relief='flat',
                                   borderwidth=0, highlightthickness=0)
        sy.configure(command=self.console.yview)
        sy.grid(row=0, column=1, sticky='ns')
        self.console.grid(row=0, column=0, sticky='nswe')
        # -------- help
        self.help = Help(self.right_nb,
                         help_cmds={'Editor': self.editor.get_docstring,
                                    'Console': self.console.get_docstring},
                         padding=1)
        # -------- filebrowser
        self.filebrowser = Filebrowser(self, self.open_file)
        # -------- placement
        self.right_nb.add(console_frame, text='Console')
        self.right_nb.add(self.history, text='History')
        self.right_nb.add(self.help, text='Help')
        self.right_nb.add(self.filebrowser, text='Filebrowser')

        # ----- placement
        pane.add(self.codestruct, weight=1)
        pane.add(self.editor, weight=50)
        pane.add(self.right_nb, weight=5)
        pane.pack(fill='both', expand=True, pady=(0, 4))

        # --- menu
        # ------- file
        self.menu_file.add_command(label='New', command=self.new,
                                   image=self._images['new'],
                                   accelerator='Ctrl+N', compound='left')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Open', command=self.open,
                                   image=self._images['open'],
                                   accelerator='Ctrl+O', compound='left')
        self.menu_file.add_command(label='Restore last closed',
                                   command=self.restore_last_closed,
                                   image=self._images['reopen'], compound='left',
                                   accelerator='Ctrl+Shift+T')
        self.menu_file.add_command(label='File switcher', accelerator='Ctrl+P',
                                   command=self.editor.file_switch,
                                   image=self._images['menu_dummy'], compound='left')
        # ------- file --- recent
        for f in self.recent_files:
            self.menu_recent_files.add_command(label=f,
                                               command=lambda file=f: self.open_file(file))

        self.menu_file.add_cascade(label='Recent files', image=self._images['recents'],
                                   menu=self.menu_recent_files, compound='left')

        self.menu_file.add_separator()
        self.menu_file.add_command(label='Save', command=self.save,
                                   state='disabled', image=self._images['save'],
                                   accelerator='Ctrl+S', compound='left')
        self.menu_file.add_command(label='Save as', command=self.saveas,
                                   image=self._images['saveas'],
                                   accelerator='Ctrl+Alt+S', compound='left')
        self.menu_file.add_command(label='Save all', command=self.saveall,
                                   image=self._images['saveall'],
                                   accelerator='Ctrl+Shift+S', compound='left')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Close all files', image=self._im_close,
                                   command=self.editor.closeall, compound='left')
        self.menu_file.add_command(label='Quit', command=self.quit,
                                   image=self._images['quit'], compound='left')
        # ------- edit
        self.menu_edit.add_command(label='Undo', command=self.editor.undo,
                                   image=self._images['undo'],
                                   accelerator='Ctrl+Z', compound='left')
        self.menu_edit.add_command(label='Redo', command=self.editor.redo,
                                   image=self._images['redo'],
                                   accelerator='Ctrl+Y', compound='left')
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Cut', command=self.editor.cut,
                                   image=self._images['cut'],
                                   accelerator='Ctrl+X', compound='left')
        self.menu_edit.add_command(label='Copy', command=self.editor.copy,
                                   image=self._images['copy'],
                                   accelerator='Ctrl+C', compound='left')
        self.menu_edit.add_command(label='Paste', command=self.editor.paste,
                                   image=self._images['paste'],
                                   accelerator='Ctrl+V', compound='left')
        self.menu_edit.add_command(label='Select all', command=self.editor.select_all,
                                   image=self._images['menu_dummy'],
                                   accelerator='Ctrl+A', compound='left')
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Duplicate lines',
                                   command=self.editor.duplicate_lines,
                                   image=self._images['menu_dummy'],
                                   accelerator='Ctrl+D', compound='left')
        self.menu_edit.add_command(label='Delete lines',
                                   command=self.editor.delete_lines,
                                   image=self._images['menu_dummy'],
                                   accelerator='Ctrl+K', compound='left')
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Toggle comment',
                                   command=self.editor.toggle_comment,
                                   image=self._images['menu_dummy'],
                                   accelerator='Ctrl+E', compound='left')
        self.menu_edit.add_command(label='Indent',
                                   command=self.editor.indent,
                                   image=self._images['indent'],
                                   accelerator='Tab', compound='left')
        self.menu_edit.add_command(label='Dedent',
                                   command=self.editor.unindent,
                                   image=self._images['dedent'],
                                   accelerator='Shift+Tab', compound='left')
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Color chooser',
                                   command=self.editor.choose_color,
                                   image=self._images['color'],
                                   compound='left')
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Settings', command=self.config,
                                   compound='left', image=self._images['settings'])
        # ------- search
        self.menu_search.add_command(label='Find', command=self.editor.find,
                                     accelerator='Ctrl+F', compound='left',
                                     image=self._images['find'])
        self.menu_search.add_command(label='Find in session', image=self._images['find'],
                                     compound='left', command=self.search)
        self.menu_search.add_separator()
        self.menu_search.add_command(label='Replace', command=self.editor.replace,
                                     accelerator='Ctrl+R', compound='left',
                                     image=self._images['replace'])
        self.menu_search.add_separator()
        self.menu_search.add_command(label='Goto line', accelerator='Ctrl+L', compound='left',
                                     command=self.editor.goto_line, image=self._images['menu_dummy'])

        # ------- doc
        self.menu_doc.add_cascade(label='Filetype', menu=self.menu_filetype,
                                  image=self._images['menu_dummy'], compound='left')
        self.menu_doc.add_separator()
        self.menu_doc.add_cascade(label='Error list', menu=self.menu_errors,
                                  image=self._images['menu_dummy'], compound='left')
        self.menu_doc.add_separator()
        self.menu_doc.add_command(image=self._images['run'], command=self.run,
                                  compound='left', label='Run',
                                  accelerator='F5')
        self.menu_doc.add_command(image=self._images['run'],
                                  command=self.run_selection,
                                  compound='left', label='Run selected code in console',
                                  accelerator='F9')
        if cst.JUPYTER:
            self.menu_doc.add_command(image=self._images['run'],
                                      command=self.execute_in_jupyter,
                                      compound='left', label='Run selected code in Jupyter QtConsole',
                                      accelerator='F10')
        # ------- doc --- filetypes
        self.filetype = tk.StringVar(self, 'Python')
        self.menu_filetype.add_radiobutton(label='Python', value='Python',
                                           variable=self.filetype,
                                           command=self.set_filetype)
        self.menu_filetype.add_radiobutton(label='Text', value='Text',
                                           variable=self.filetype,
                                           command=self.set_filetype)

        self.menu.add_cascade(label='File', underline=0, menu=self.menu_file)
        self.menu.add_cascade(label='Edit', underline=0, menu=self.menu_edit)
        self.menu.add_cascade(label='Search', underline=0, menu=self.menu_search)
        self.menu.add_cascade(label='Document', underline=0, menu=self.menu_doc)
        self.menu.add_command(label='About', underline=0,
                              command=lambda: About(self))

        self.configure(menu=self.menu)

        # --- bindings
        self.bind_class('TEntry', '<Control-a>', self._select_all)
        self.bind_class('TCombobox', '<Control-a>', self._select_all)
        self.codestruct.bind('<<Populate>>', self._on_populate)
        self.editor.bind('<<NotebookEmpty>>', self._on_empty_notebook)
        self.editor.bind('<<NotebookFirstTab>>', self._on_first_tab_creation)
        self.editor.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        self.editor.bind('<<FiletypeChanged>>', self._filetype_change)
        self.editor.bind('<<Modified>>', lambda e: self._edit_modified())
        self.editor.bind('<<Reload>>', self.reload)
        self.editor.bind('<<Filebrowser>>', self.view_in_filebrowser)

        self.right_nb.bind('<ButtonRelease-3>', self._show_menu_nb)

        self.bind_class('Text', '<Control-o>', lambda e: None)
        self.bind('<Control-Shift-T>', self.restore_last_closed)
        self.bind('<Control-n>', self.new)
        self.bind('<Control-p>', self.editor.file_switch)
        self.bind('<Control-s>', self.save)
        self.bind('<Control-o>', lambda e: self.open())
        self.bind('<Control-Shift-S>', self.saveall)
        self.bind('<Control-Alt-s>', self.saveas)
        self.editor.bind('<<CtrlReturn>>', lambda e: self.console.execute(self.editor.get_cell()))
        self.bind('<F5>', self.run)
        self.bind('<F9>', self.run_selection)
        if cst.JUPYTER:
            self.bind('<F10>', self.execute_in_jupyter)

        # --- maximize window
        self.update_idletasks()
        e = EWMH()
        try:
            for w in e.getClientList():
                if w.get_wm_name() == self.title():
                    e.setWmState(w, 1, '_NET_WM_STATE_MAXIMIZED_VERT')
                    e.setWmState(w, 1, '_NET_WM_STATE_MAXIMIZED_HORZ')
            e.display.flush()
        except ewmh.display.error.BadWindow:
            pass

        # --- restore opened files
        ofiles = CONFIG.get('General', 'opened_files').split(', ')
        for f in ofiles:
            if os.path.exists(f):
                self.open_file(os.path.abspath(f))
        # --- open files passed in argument
        for f in files:
            self.open_file(os.path.abspath(f))

        if ofiles == [''] and not files:
            self._on_empty_notebook()

        self.protocol('WM_DELETE_WINDOW', self.quit)
        signal.signal(signal.SIGUSR1, self._on_signal)

    @staticmethod
    def _select_all(event):
        """Select all entry content."""
        event.widget.selection_range(0, "end")

    def _show_menu_nb(self, event):
        tab = self.right_nb.index('@%i,%i' % (event.x, event.y))
        if tab is not None:
            if self.right_nb.tab(tab, 'text') == 'Console':
                self.console.menu.tk_popup(event.x_root, event.y_root)

    def _on_signal(self, *args):
        self.lift()
        self.focus_get()
        if os.path.exists(cst.OPENFILE_PATH):
            with open(cst.OPENFILE_PATH) as f:
                files = f.read().splitlines()
            os.remove(cst.OPENFILE_PATH)
            for f in files:
                self.open_file(os.path.abspath(f))

    def _setup_style(self):
        # --- load theme
        font = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        theme_name = CONFIG.get('General', 'theme')
        theme = dict(CONFIG.items('{} Theme'.format(theme_name.capitalize())))
        self._im_close.configure(file=IM_CLOSE.format(theme=theme_name))

        # --- configuration dict
        button_style_config = {'bordercolor': theme['bordercolor'],
                               'background': theme['bg'],
                               'fieldbackground': theme['fieldbg'],
                               'indicatorbackground': theme['fieldbg'],
                               'indicatorforeground': theme['fg'],
                               'foreground': theme['fg'],
                               'arrowcolor': theme['fg'],
                               'insertcolor': theme['fg'],
                               'upperbordercolor': theme['bordercolor'],
                               'lowerbordercolor': theme['bordercolor'],
                               'lightcolor': theme['lightcolor'],
                               'darkcolor': theme['darkcolor']}

        button_style_map = {'background': [('active', theme['activebg']),
                                           ('disabled', theme['disabledbg']),
                                           ('pressed', theme['pressedbg'])],
                            'lightcolor': [('pressed', theme['darkcolor'])],
                            'darkcolor': [('pressed', theme['lightcolor'])],
                            'bordercolor': [('focus', theme['focusbordercolor'])],
                            'foreground': [('disabled', theme['disabledfg'])],
                            'arrowcolor': [('disabled', theme['disabledfg'])],
                            'fieldbackground': [('disabled', theme['fieldbg'])],
                            'selectbackground': [('focus', theme['selectbg'])],
                            'selectforeground': [('focus', theme['selectfg'])]}

        style_config = {'bordercolor': theme['bordercolor'],
                        'background': theme['bg'],
                        'foreground': theme['fg'],
                        'arrowcolor': theme['fg'],
                        'gripcount': 0,
                        'lightcolor': theme['lightcolor'],
                        'darkcolor': theme['darkcolor'],
                        'troughcolor': theme['pressedbg']}

        style_map = {'background': [('active', theme['activebg']), ('disabled', theme['bg'])],
                     'lightcolor': [('pressed', theme['darkcolor'])],
                     'darkcolor': [('pressed', theme['lightcolor'])],
                     'foreground': [('disabled', theme['disabledfg'])]}
        # --- update style
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', **style_config)
        style.configure('TSeparator', **style_config)
        style.configure('TLabel', **style_config)
        style.configure('Sash', **style_config)
        style.configure('TPanedwindow', **style_config)
        style.configure('TScrollbar', **style_config)
        style.map('TFrame', **style_map)
        style.map('TLabel', **style_map)
        style.map('Sash', **style_map)
        style.map('TScrollbar', **style_map)
        style.map('TPanedwindow', **style_map)
        style.configure('TButton', **button_style_config)
        style.configure('TMenubutton', **button_style_config)
        style.configure('TCheckbutton', **button_style_config)
        style.configure('TRadiobutton', **button_style_config)
        style.configure('TEntry', **button_style_config)
        style.configure('TCombobox', **button_style_config)
        style.configure('TNotebook', **style_config)
        style.configure('TNotebook.Tab', **style_config)
        style.configure('Treeview', **button_style_config)
        style.configure('Treeview.Heading', **button_style_config)
        style.configure('Treeview.Item', foreground=theme['fg'])
        style.map('TButton', **button_style_map)
        style.map('TMenubutton', **button_style_map)
        style.map('TCheckbutton', **button_style_map)
        style.map('TRadiobutton', **button_style_map)
        style.map('TEntry', **button_style_map)
        style.map('TCombobox', **button_style_map)
        style.map('TNotebook', **button_style_map)
        style.map('TNotebook.Tab', **button_style_map)
        style.map('Treeview', **button_style_map)
        style.map('Treeview', background=[('selected', theme['selectbg'])],
                  foreground=[('selected', theme['selectfg'])])
        style.map('Treeview.Heading', **button_style_map)
        # --- set options
        self.option_add('*TCombobox*Listbox.selectBackground', theme['selectbg'])
        self.option_add('*TCombobox*Listbox.selectForeground', theme['fg'])
        self.option_add('*TCombobox*Listbox.foreground', theme['fg'])
        self.option_add('*TCombobox*Listbox.background', theme['fieldbg'])
        self.option_add('*Listbox.selectBackground', theme['selectbg'])
        self.option_add('*Listbox.selectForeground', theme['fg'])
        self.option_add('*Listbox.foreground', theme['fg'])
        self.option_add('*Listbox.background', theme['fieldbg'])
        self.option_add('*Text.foreground', theme['unselectedfg'])
        self.option_add('*Text.selectForeground', theme['unselectedfg'])
        self.option_add('*Text.background', theme['bg'])
        self.option_add('*Text.selectBackground', theme['bg'])
        self.option_add('*Text.inactiveSelectBackground', theme['bg'])
        self.option_add('*Text.relief', 'flat')
        self.option_add('*Text.highlightThickness', 0)
        self.option_add('*Text.borderWidth', 0)
        self.option_add('*Text.font', font)
        self.option_add('*Canvas.background', theme['bg'])
        self.option_add('*Canvas.fill', theme['activebg'])
        self.option_add('*Canvas.relief', 'flat')
        self.option_add('*Canvas.highlightThickness', 0)
        self.option_add('*Canvas.borderWidth', 0)
        self.option_add('*Toplevel.background', theme['bg'])
        self.option_add(f'*{self.winfo_class()}.background', theme['bg'])
        # --- special themes
        style.configure('tooltip.TLabel', background=theme['tooltip_bg'],
                        foreground=theme['fg'])
        style.configure('tooltip.TFrame', background=theme['tooltip_bg'])
        style.configure('title.tooltip.TLabel', font='TkDefaultFont 9 bold')
        style.configure('syntax.title.tooltip.TLabel', foreground='#FF4D00')
        style.configure('args.title.tooltip.TLabel', foreground='#4169E1')
        style.configure("url.TLabel",
                        foreground="light" * (theme_name == 'dark') + "blue")
        style.configure("txt.TFrame", background=theme['fieldbg'])
        style.layout('Down.TButton',
                     [('Button.padding',
                       {'sticky': 'nswe',
                        'children': [('Button.downarrow', {'sticky': 'nswe'})]})])
        style.layout('Up.TButton',
                     [('Button.padding',
                       {'sticky': 'nswe',
                        'children': [('Button.uparrow', {'sticky': 'nswe'})]})])
        style.layout('close.TButton',
                     [('Button.border',
                       {'sticky': 'nswe',
                        'border': '1',
                        'children': [('Button.padding',
                                      {'sticky': 'nswe',
                                       'children': [('Button.close', {'sticky': 'nswe'})]})]})])
        style.layout('toggle.TButton',
                     [('Button.border',
                       {'sticky': 'nswe',
                        'border': '1',
                        'children': [('Button.padding',
                                      {'sticky': 'nswe',
                                       'children': [('Button.label', {'sticky': 'nswe'})]})]})])
        style.configure('border.TFrame', borderwidth=1, relief='sunken')
        style.configure('separator.TFrame', background=theme['bordercolor'], padding=1)
        style.configure('Up.TButton', arrowsize=20)
        style.configure('Down.TButton', arrowsize=20)
        style.configure('close.TButton', borderwidth=1, relief='flat')
        style.map('close.TButton', relief=[('active', 'raised')])
        style.map('toggle.TButton', relief=[('selected', 'sunken'), ('!selected', 'flat')])
        style.layout('flat.Treeview',
                     [('Treeview.padding',
                       {'sticky': 'nswe',
                        'children': [('Treeview.treearea', {'sticky': 'nswe'})]})])
        style.configure('flat.Treeview', background=theme['fieldbg'])
        style.configure('Treeview', background=theme['fieldbg'])
        self.configure(bg=theme['bg'], padx=6, pady=2)
        # --- menu
        self.menu.configure(bg=theme['bg'], fg=theme['fg'],
                            borderwidth=0, activeborderwidth=0,
                            activebackground=theme['selectbg'],
                            activeforeground=theme['selectfg'])
        self.menu_file.configure(bg=theme['fieldbg'], activebackground=theme['selectbg'],
                                 fg=theme['fg'], activeforeground=theme['fg'],
                                 disabledforeground=theme['disabledfg'],
                                 selectcolor=theme['fg'])
        self.menu_recent_files.configure(bg=theme['fieldbg'], activebackground=theme['selectbg'],
                                         fg=theme['fg'], activeforeground=theme['fg'],
                                         disabledforeground=theme['disabledfg'],
                                         selectcolor=theme['fg'])
        self.menu_edit.configure(bg=theme['fieldbg'], activebackground=theme['selectbg'],
                                 fg=theme['fg'], activeforeground=theme['fg'],
                                 disabledforeground=theme['disabledfg'],
                                 selectcolor=theme['fg'])
        self.menu_errors.configure(bg=theme['fieldbg'],
                                   activebackground=theme['selectbg'],
                                   fg=theme['fg'],
                                   activeforeground=theme['fg'],
                                   disabledforeground=theme['disabledfg'],
                                   selectcolor=theme['fg'])
        self.menu_search.configure(bg=theme['fieldbg'],
                                   activebackground=theme['selectbg'],
                                   fg=theme['fg'],
                                   activeforeground=theme['fg'],
                                   disabledforeground=theme['disabledfg'],
                                   selectcolor=theme['fg'])
        self.menu_doc.configure(bg=theme['fieldbg'],
                                activebackground=theme['selectbg'],
                                fg=theme['fg'],
                                activeforeground=theme['fg'],
                                disabledforeground=theme['disabledfg'],
                                selectcolor=theme['fg'])
        self.menu_filetype.configure(bg=theme['fieldbg'],
                                     activebackground=theme['selectbg'],
                                     fg=theme['fg'],
                                     activeforeground=theme['fg'],
                                     disabledforeground=theme['disabledfg'],
                                     selectcolor=theme['fg'])
        self.option_add('*Menu.background', theme['fieldbg'])
        self.option_add('*Menu.activeBackground', theme['selectbg'])
        self.option_add('*Menu.activeForeground', theme['fg'])
        self.option_add('*Menu.disabledForeground', theme['disabledfg'])
        self.option_add('*Menu.foreground', theme['fg'])
        self.option_add('*Menu.selectColor', theme['fg'])
        # --- notebook
        style.layout('Notebook', style.layout('TFrame'))
        style.layout('Notebook.TMenubutton',
                     [('Menubutton.border',
                       {'sticky': 'nswe',
                        'children': [('Menubutton.focus',
                                      {'sticky': 'nswe',
                                       'children': [('Menubutton.indicator',
                                                     {'side': 'right', 'sticky': ''}),
                                                    ('Menubutton.padding',
                                                     {'expand': '1',
                                                      'sticky': 'we'})]})]})])
        style.layout('Notebook.Tab', style.layout('TFrame'))
        style.layout('Notebook.Tab.Frame', style.layout('TFrame'))
        style.layout('Notebook.Tab.Label', style.layout('TLabel'))
        style.layout('Notebook.Tab.Close',
                     [('Close.padding',
                       {'sticky': 'nswe',
                        'children': [('Close.border',
                                      {'border': '1',
                                       'sticky': 'nsew',
                                       'children': [('Close.close',
                                                     {'sticky': 'ewsn'})]})]})])
        style.layout('Left.Notebook.TButton',
                     [('Button.padding',
                       {'sticky': 'nswe',
                        'children': [('Button.leftarrow', {'sticky': 'nswe'})]})])
        style.layout('Right.Notebook.TButton',
                     [('Button.padding',
                       {'sticky': 'nswe',
                        'children': [('Button.rightarrow', {'sticky': 'nswe'})]})])
        style.configure('Notebook', **style_config)
        style.configure('Notebook.Tab', relief='raised', borderwidth=1,
                        **style_config)
        style.configure('Notebook.Tab.Frame', relief='flat', borderwidth=0,
                        **style_config)
        style.configure('Notebook.Tab.Label', relief='flat', borderwidth=1,
                        padding=0, **style_config)
        style.configure('Notebook.Tab.Label', foreground=theme['unselectedfg'])
        style.configure('Notebook.Tab.Close', relief='flat', borderwidth=1,
                        padding=0, **style_config)
        style.configure('Notebook.Tab.Frame', background=theme['bg'])
        style.configure('Notebook.Tab.Label', background=theme['bg'])
        style.configure('Notebook.Tab.Close', background=theme['bg'])

        style.map('Notebook.Tab.Frame',
                  **{'background': [('selected', '!disabled', theme['activebg'])]})
        style.map('Notebook.Tab.Label',
                  **{'background': [('selected', '!disabled', theme['activebg'])],
                     'foreground': [('selected', '!disabled', theme['fg'])]})
        style.map('Notebook.Tab.Close',
                  **{'background': [('selected', theme['activebg']),
                                    ('pressed', theme['darkcolor']),
                                    ('active', theme['activebg'])],
                     'relief': [('hover', '!disabled', 'raised'),
                                ('active', '!disabled', 'raised'),
                                ('pressed', '!disabled', 'sunken')],
                     'lightcolor': [('pressed', theme['darkcolor'])],
                     'darkcolor': [('pressed', theme['lightcolor'])]})
        style.map('Notebook.Tab',
                  **{'ba.ckground': [('selected', '!disabled', theme['activebg'])]})

        style.configure('Left.Notebook.TButton', padding=0)
        style.configure('Right.Notebook.TButton', padding=0)

        style.configure('TNotebook.Tab', background=theme['bg'],
                        foreground=theme['unselectedfg'])
        style.map('TNotebook.Tab',
                  **{'background': [('selected', '!disabled', theme['activebg'])],
                     'foreground': [('selected', '!disabled', theme['fg'])]})

    def _on_populate(self, event):
        cells = self.codestruct.get_cells()
        self.editor.set_cells(cells)

    def _on_tab_changed(self, event):
        self.filetype.set(self.editor.get_filetype())
        self.codestruct.set_callback(self.editor.goto_item)
        self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
        self.update_menu_errors()
        self.editor.focus_tab()

    def _filetype_change(self, event):
        filetype = self.filetype.get()
        if filetype == 'Python':
            self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
            self.check_syntax()
        else:
            self.codestruct.populate(self.editor.filename, '')
            self.update_menu_errors()

    def _edit_modified(self, *args, tab=None):
        self.editor.edit_modified(*args, tab=tab)
        if self.editor.edit_modified(tab=tab):
            self.menu_file.entryconfigure('Save', state='normal')
        else:
            self.menu_file.entryconfigure('Save', state='disabled')

    def _init_kernel(self):
        """Initialize Jupyter kernel"""
        if not cst.JUPYTER:
            return
        cfm = cst.ConnectionFileMixin(connection_file=cst.JUPYTER_KERNEL_PATH)
        cfm.write_connection_file()
        self.jupyter_kernel = cst.BlockingKernelClient(connection_file=cst.JUPYTER_KERNEL_PATH)
        self.jupyter_kernel.load_connection_file()

    def _on_empty_notebook(self, event=None):
        """Disable irrelevant menus when no file is opened"""
        self.codestruct.clear()
        self.menu.entryconfigure('Document', state='disabled')
        self.menu.entryconfigure('Search', state='disabled')
        for entry in range(self.menu_edit.index('end') - 1):
            try:
                self.menu_edit.entryconfigure(entry, state='disabled')
            except tk.TclError:
                pass
        for entry in ['Save as', 'Save all', 'Close all files']:
            self.menu_file.entryconfigure(entry, state='disabled')

    def _on_first_tab_creation(self, event):
        """Enable menus when fisrt file is opened"""
        self.menu.entryconfigure('Document', state='normal')
        self.menu.entryconfigure('Search', state='normal')
        for entry in range(self.menu_edit.index('end') - 1):
            try:
                self.menu_edit.entryconfigure(entry, state='normal')
            except tk.TclError:
                pass
        for entry in ['Save as', 'Save all', 'Close all files']:
            self.menu_file.entryconfigure(entry, state='normal')

    def report_callback_exception(self, *args):
        """Log exceptions."""
        err = "".join(traceback.format_exception(*args))
        logging.error(err)
        showerror("Error", str(args[1]), err, True)

    def config(self):
        c = Config(self)
        self.wait_window(c)
        self._setup_style()
        self.editor.update_style()
        self.console.update_style()
        self.history.update_style()
        self.help.load_stylesheet()

    def quit(self):
        files = ', '.join(self.editor.get_open_files())
        CONFIG.set('General', 'opened_files', files)
        save_config()
        res = self.editor.closeall()
        if res:
            self.destroy()

    def new(self, event=None):
        try:
            with open(cst.PATH_TEMPLATE) as file:
                txt = file.read()
        except Exception:
            txt = ""
        self.editor.new()
        self.editor.insert('1.0', txt.format(date=datetime.now().strftime('%c'), author=getuser()))
        self.editor.edit_reset()
        self._edit_modified(0)
        self.codestruct.populate('new.py', '')

    def restore_last_closed(self, event=None):
        file = self.editor.get_last_closed()
        if file:
            self.open_file(file)

    def _update_recent_files(self, file):
        if file in self.recent_files:
            ind = self.recent_files.index(file)
            del self.recent_files[ind]
            self.menu_recent_files.delete(ind)
        self.recent_files.insert(0, file)
        self.menu_recent_files.insert_command(0, label=file, command=lambda: self.open_file(file))
        if len(self.recent_files) > 10:
            del self.recent_files[-1]
            self.menu_recent_files.delete(self.menu_recent_files.index('end'))

    def set_filetype(self):
        self.editor.set_filetype(self.filetype.get())

    def load_file(self, file):
        try:
            with open(file) as f:
                txt = f.read()
            return txt
        except Exception as e:
            if file in self.recent_files:
                ind = self.recent_files.index(file)
                del self.recent_files[ind]
                self.menu_recent_files.delete(ind)
            if isinstance(e, FileNotFoundError) or isinstance(e, IsADirectoryError):
                return
            elif isinstance(e, UnicodeDecodeError):
                msg = 'Invalid file format: {}.'.format(file)
                showerror('Error', msg, parent=self)
                logging.error(msg)
            else:
                err = traceback.format_exc()
                logging.exception(str(e))
                showerror('Error', "{}: {}".format(type(e), e), err, parent=self)

    def view_in_filebrowser(self, event):
        file = self.editor.files[self.editor.current_tab]
        self.filebrowser.populate(os.path.dirname(file))
        self.right_nb.select(3)

    def reload(self, event):
        file = self.editor.files[self.editor.current_tab]
        txt = self.load_file(file)
        if txt is not None:
            self.editor.delete('1.0', 'end')
            self.editor.insert('1.0', txt)
            self.editor.edit_reset()
            self._edit_modified(0)
            self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
            self.check_syntax()
            self.editor.goto_start()

    def open_file(self, file):
        files = list(self.editor.files.values())
        if file in files:
            self.editor.select(list(self.editor.files.keys())[files.index(file)])
            self._update_recent_files(file)
        else:
            txt = self.load_file(file)
            self.filebrowser.populate(os.path.dirname(file))
            if txt is not None:
                self.editor.new(file)
                self.editor.insert('1.0', txt)
                self.editor.edit_reset()
                self._edit_modified(0)
                self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
                self.check_syntax()
                self.editor.goto_start()
                self._update_recent_files(file)
                CONFIG.set('General', 'recent_files', ', '.join(self.recent_files))
                save_config()

    def open(self, file=None):
        if file:
            self.open_file(file)
        else:
            tab = self.editor.select()
            file = self.editor.files.get(tab, '')
            initialdir, initialfile = os.path.split(os.path.abspath(file))
            files = askopenfilenames(self, initialfile=initialfile,
                                     initialdir=initialdir,
                                     filetypes=[('Python', '*.py'), ('All files', '*')])
            for file in files:
                self.open_file(file)

    def saveas(self, event=None):
        tab = self.editor.select()
        if tab < 0:
            return False
        file = self.editor.files.get(tab, '')
        if file:
            initialdir, initialfile = os.path.split(file)
        else:
            initialdir, initialfile = '', 'new.py'
        name = asksaveasfilename(self, initialfile=initialfile,
                                 initialdir=initialdir, defaultext='.py',
                                 filetypes=[('Python', '*.py'), ('All files', '*')])
        if name:
            tab = self.editor.select()
            self.editor.saveas(tab=tab, name=name)
            self._edit_modified(0, tab=tab)
            self.check_syntax()
            self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
            return True
        else:
            return False

    def search(self):
        SearchDialog(self)

    def save(self, event=None, tab=None, update=False):
        if tab is None:
            tab = self.editor.select()
            update = True
        saved = self.editor.save(tab)
        if update and saved:
            self._edit_modified(0, tab=tab)
            self.check_syntax()
            self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
        self.editor.focus_tab()
        return saved

    def saveall(self, event=None):
        for tab in self.editor.tabs():
            self.save(tab=tab, update=True)

    def run(self, event=None):
        if self.save():
            self.editor.run()

    def run_selection(self, event=None):
        code = self.editor.get_selection()
        if code:
            self.console.execute(code)

    def execute_in_jupyter(self, event=None):
        if not cst.JUPYTER:
            return
        code = self.editor.get_selection()
        if not code:
            return
        if self._qtconsole_process is None or self._qtconsole_process.poll() is not None:
            self._init_kernel()
            self._qtconsole_process = Popen(['jupyter-qtconsole', '-f', cst.JUPYTER_KERNEL_PATH])
        self.jupyter_kernel.execute(code)
        return "break"

    def check_syntax(self, tab=None):
        if tab is None:
            tab = self.editor.select()
        if tab and self.editor.files[tab] and self.filetype.get() == 'Python':
            results = check_file(self.editor.files[tab])
            self.editor.show_syntax_issues(results)
            self.update_menu_errors()

    def update_menu_errors(self):
        self.menu_doc.entryconfigure('Error list', state='normal')
        self.menu_errors.delete(0, 'end')
        errors = self.editor.get_syntax_issues()
        if not errors:
            self.menu_doc.entryconfigure('Error list', state='disabled')
        else:
            for (category, msg, cmd) in errors:
                self.menu_errors.add_command(label=msg,
                                             image=self._images[category],
                                             compound='left', command=cmd)
