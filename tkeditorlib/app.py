from tkeditorlib.editornotebook import EditorNotebook
from tkeditorlib.syntax_check import check_file
from tkeditorlib.filestructure import CodeStructure
from tkeditorlib.constants import ICON, CONFIG, save_config, IM_CLOSE
from tkeditorlib import constants as cst
from tkeditorlib.textconsole import TextConsole
from tkeditorlib.history import HistoryFrame
from tkeditorlib.config import Config
from tkeditorlib.autoscrollbar import AutoHideScrollbar
from tkeditorlib.menu import LongMenu
from tkeditorlib.help import Help
from tkeditorlib.messagebox import showerror
import tkinter as tk
from tkinter import ttk
from tkfilebrowser import askopenfilenames, asksaveasfilename
import traceback
import os
import signal
from ewmh import ewmh, EWMH
import logging


class App(tk.Tk):
    def __init__(self, *files):
        tk.Tk.__init__(self, className='TkEditor')
        self.title('TkEditor')
        self._icon = tk.PhotoImage(file=ICON, master=self)
        self._im_run = tk.PhotoImage(file=cst.IM_RUN, master=self)
        self._im_new = tk.PhotoImage(file=cst.IM_NEW, master=self)
        self._im_open = tk.PhotoImage(file=cst.IM_OPEN, master=self)
        self._im_reopen = tk.PhotoImage(file=cst.IM_REOPEN, master=self)
        self._im_save = tk.PhotoImage(file=cst.IM_SAVE, master=self)
        self._im_saveall = tk.PhotoImage(file=cst.IM_SAVEALL, master=self)
        self._im_saveas = tk.PhotoImage(file=cst.IM_SAVEAS, master=self)
        self._im_undo = tk.PhotoImage(file=cst.IM_UNDO, master=self)
        self._im_redo = tk.PhotoImage(file=cst.IM_REDO, master=self)
        self._im_recents = tk.PhotoImage(file=cst.IM_RECENTS, master=self)
        self._im_close = tk.PhotoImage(master=self)
        self._im_quit = tk.PhotoImage(file=cst.IM_QUIT, master=self)
        self._im_find = tk.PhotoImage(file=cst.IM_FIND, master=self)
        self._im_replace = tk.PhotoImage(file=cst.IM_REPLACE, master=self)
        self._im_settings = tk.PhotoImage(file=cst.IM_SETTINGS, master=self)
        self.iconphoto(True, self._icon)
        self._syntax_icons = {'warning': tk.PhotoImage(master=self, file=cst.IM_WARN),
                              'error': tk.PhotoImage(master=self, file=cst.IM_ERR)}

        self.option_add('*Menu.borderWidth', 1)
        self.option_add('*Menu.activeBorderWidth', 0)
        self.option_add('*Menu.relief', 'sunken')
        self.option_add('*Menu.tearOff', False)

        self.menu = tk.Menu(self, tearoff=False, relief='flat')
        self.menu_file = tk.Menu(self.menu, tearoff=False)
        self.menu_recent_files = tk.Menu(self.menu_file, tearoff=False)
        self.menu_edit = tk.Menu(self.menu, tearoff=False)
        self.menu_errors = LongMenu(self.menu, 40, tearoff=False)

        recent_files = CONFIG.get('General', 'recent_files', fallback='').split(', ')
        self.recent_files = [f for f in recent_files if f and os.path.exists(f)]

        # -- style
        for seq in self.bind_class('TButton'):
            self.bind_class('Notebook.Tab.Close', seq, self.bind_class('TButton', seq), True)
        style = ttk.Style(self)
        style.element_create('close', 'image', self._im_close,
                             sticky='')
        self._setup_style()

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
        # -------- placement
        self.right_nb.add(console_frame, text='Console')
        self.right_nb.add(self.history, text='History')
        self.right_nb.add(self.help, text='Help')

        # ----- placement
        pane.add(self.codestruct, weight=1)
        pane.add(self.editor, weight=50)
        pane.add(self.right_nb, weight=5)
        pane.pack(fill='both', expand=True, pady=(0, 4))

        # --- menu
        # file
        self.menu_file.add_command(label='New', command=self.new, image=self._im_new,
                                   accelerator='Ctrl+N', compound='left')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Open', command=self.open,
                                   image=self._im_open,
                                   accelerator='Ctrl+O', compound='left')
        self.menu_file.add_command(label='Restore last closed',
                                   command=self.restore_last_closed,
                                   image=self._im_reopen, compound='left',
                                   accelerator='Ctrl+Shift+T')
        # file --- recent
        for f in self.recent_files:
            self.menu_recent_files.add_command(label=f,
                                               command=lambda file=f: self.open_file(file))

        self.menu_file.add_cascade(label='Recent files', image=self._im_recents,
                                   menu=self.menu_recent_files, compound='left')

        self.menu_file.add_separator()
        self.menu_file.add_command(label='Save', command=self.save,
                                   state='disabled', image=self._im_save,
                                   accelerator='Ctrl+S', compound='left')
        self.menu_file.add_command(label='Save as', command=self.saveas,
                                   image=self._im_saveas,
                                   accelerator='Ctrl+Alt+S', compound='left')
        self.menu_file.add_command(label='Save all', command=self.saveall,
                                   image=self._im_saveall,
                                   accelerator='Ctrl+Shift+S', compound='left')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Close all files', image=self._im_close,
                                   command=self.editor.closeall, compound='left')
        self.menu_file.add_command(label='Quit', command=self.quit,
                                   image=self._im_quit, compound='left')
        # edit
        self.menu_edit.add_command(label='Undo', command=self.editor.undo,
                                   image=self._im_undo,
                                   accelerator='Ctrl+Z', compound='left')
        self.menu_edit.add_command(label='Redo', command=self.editor.redo,
                                   image=self._im_redo,
                                   accelerator='Ctrl+Y', compound='left')
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Find', command=self.editor.find,
                                   accelerator='Ctrl+F', compound='left',
                                   image=self._im_find)
        self.menu_edit.add_command(label='Replace', command=self.editor.replace,
                                   accelerator='Ctrl+R', compound='left',
                                   image=self._im_replace)
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Settings', command=self.config,
                                   compound='left', image=self._im_settings)

        self.menu.add_cascade(label='File', underline=0, menu=self.menu_file)
        self.menu.add_cascade(label='Edit', underline=0, menu=self.menu_edit)
        self.menu.add_cascade(label='Error list', underline=6, menu=self.menu_errors)
        self.menu.add_command(image=self._im_run, command=self.run,
                              compound='left', label='Run', underline=0)
        self.configure(menu=self.menu)

        # --- bindings
        self.codestruct.bind('<<Populate>>', self._on_populate)
        self.editor.bind('<<NotebookEmpty>>', self.codestruct.clear)
        self.editor.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        self.editor.bind('<<Modified>>', lambda e: self._edit_modified())
        self.editor.bind('<<Reload>>', self.reload)

        self.right_nb.bind('<ButtonRelease-3>', self._show_menu_nb)

        self.bind_class('Text', '<Control-o>', lambda e: None)
        self.bind('<Control-Shift-T>', self.restore_last_closed)
        self.bind('<Control-n>', self.new)
        self.bind('<Control-s>', self.save)
        self.bind('<Control-o>', lambda e: self.open())
        self.bind('<Control-Shift-S>', self.saveall)
        self.bind('<Control-Alt-s>', self.saveas)
        self.editor.bind('<<CtrlReturn>>', lambda e: self.console.execute(self.editor.get_cell()))
        self.bind('<F5>', self.run)
        self.bind('<F9>', lambda e: self.console.execute(self.editor.get_selection()))

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

        self.protocol('WM_DELETE_WINDOW', self.quit)
        signal.signal(signal.SIGUSR1, self._on_signal)

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
        style.configure('border.TFrame', borderwidth=1, relief='sunken')
        style.configure('separator.TFrame', background=theme['bordercolor'], padding=1)
        style.configure('Up.TButton', arrowsize=20)
        style.configure('Down.TButton', arrowsize=20)
        style.configure('close.TButton', borderwidth=1, relief='flat')
        style.map('close.TButton', relief=[('active', 'raised')])
        style.layout('flat.Treeview',
                     [('Treeview.padding',
                       {'sticky': 'nswe',
                        'children': [('Treeview.treearea', {'sticky': 'nswe'})]})])
        style.configure('flat.Treeview', background=theme['fieldbg'])
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
        self.codestruct.set_callback(self.editor.goto_item)
        self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
        self.update_menu_errors()

    def _edit_modified(self, *args, tab=None):
        self.editor.edit_modified(*args, tab=tab)
        if self.editor.edit_modified(tab=tab):
            self.menu_file.entryconfigure('Save', state='normal')
        else:
            self.menu_file.entryconfigure('Save', state='disabled')

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
        self.editor.closeall()
        self.destroy()

    def new(self, event=None):
        self.editor.new()
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
            if isinstance(e, FileNotFoundError):
                return
            elif isinstance(e, UnicodeDecodeError):
                msg = 'Invalid file format: {}.'.format(file)
                showerror('Error', msg, parent=self)
                logging.error(msg)
            else:
                err = traceback.format_exc()
                logging.exception(str(e))
                showerror('Error', "{}: {}".format(type(e), e), err, parent=self)

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

    def save(self, event=None, tab=None, update=False):
        if tab is None:
            tab = self.editor.select()
            update = True
        saved = self.editor.save(tab)
        if update and saved:
            self._edit_modified(0, tab=tab)
            self.check_syntax()
            self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
        return saved

    def saveall(self, event=None):
        for tab in self.editor.tabs():
            self.save(tab=tab, update=True)

    def run(self, event=None):
        if self.save():
            self.editor.run()

    def check_syntax(self, tab=None):
        if tab is None:
            tab = self.editor.select()
        if self.editor.files[tab]:
            results = check_file(self.editor.files[tab])
            self.editor.show_syntax_issues(results)
            self.update_menu_errors()

    def update_menu_errors(self):
        self.menu.entryconfigure('Error list', state='normal')
        self.menu_errors.delete(0, 'end')
        errors = self.editor.get_syntax_issues()
        if not errors:
            self.menu.entryconfigure('Error list', state='disabled')
        else:
            for (category, msg, cmd) in errors:
                self.menu_errors.add_command(label=msg,
                                             image=self._syntax_icons[category],
                                             compound='left', command=cmd)
