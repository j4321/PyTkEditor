from tkeditorlib.editornotebook import EditorNotebook
from tkeditorlib.syntax_check import check_file
from tkeditorlib.filestructure import CodeStructure
from tkeditorlib.constants import ICON, CONFIG, save_config, IMG_PATH
from tkeditorlib import constants as cst
from tkeditorlib.textconsole import TextConsole
from tkeditorlib.config import Config
from tkeditorlib.autoscrollbar import AutoHideScrollbar
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror
from tkfilebrowser import askopenfilenames, asksaveasfilename
import traceback
import os


class App(tk.Tk):
    def __init__(self, file=None):
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

        self.option_add('*Menu.borderWidth', 1)
        self.option_add('*Menu.activeBorderWidth', 0)
        self.option_add('*Menu.relief', 'sunken')

        recent_files = CONFIG.get('General', 'recent_files', fallback='').split(', ')
        self.recent_files = [f for f in recent_files if f and os.path.exists(f)]

        self.file = ''

        self.menu = tk.Menu(self, tearoff=False, relief='flat')
        self.menu_file = tk.Menu(self.menu, tearoff=False)
        self.menu_recent_files = tk.Menu(self.menu_file, tearoff=False)
        self.menu_edit = tk.Menu(self.menu, tearoff=False)

        # -- style
        for seq in self.bind_class('TButton'):
            self.bind_class('Notebook.Tab.Close', seq, self.bind_class('TButton', seq), True)
        style = ttk.Style(self)
        style.element_create('close', 'image', self._im_close,
                             sticky='')
        self._setup_style()

        pane = ttk.PanedWindow(self, orient='horizontal')
        self.codestruct = CodeStructure(pane)
        self.editor = EditorNotebook(pane)
        console_frame = ttk.Frame(pane, style='border.TFrame', padding=1)
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        sy = AutoHideScrollbar(console_frame, orient='vertical')
        self.console = TextConsole(console_frame, promptcolor='skyblue',
                                   yscrollcommand=sy.set, relief='flat',
                                   borderwidth=0, highlightthickness=0)
        sy.configure(command=self.console.yview)
        sy.grid(row=0, column=1, sticky='ns')
        self.console.grid(row=0, column=0, sticky='nswe')
        # placement
        pane.add(self.codestruct, weight=1)
        pane.add(self.editor, weight=3)
        pane.add(console_frame, weight=2)
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

        self.menu.add_cascade(label='File', menu=self.menu_file)
        self.menu.add_cascade(label='Edit', menu=self.menu_edit)
        self.menu.add_command(image=self._im_run, command=self.run, compound='center')
        self.configure(menu=self.menu)

        # --- bindings
        self.codestruct.bind('<<Populate>>', self._on_populate)
        self.editor.bind('<<NotebookEmpty>>', self.codestruct.clear)
        self.editor.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        self.editor.bind('<<Modified>>', lambda e: self._edit_modified())

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

        files = CONFIG.get('General', 'opened_files').split(', ')
        for f in files:
            if os.path.exists(f):
                self.open_file(f)

        if file:
            self.open_file(file)
        self.protocol('WM_DELETE_WINDOW', self.quit)

    def _setup_style(self):

        FONT = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))

        if CONFIG.get('General', 'theme') == 'dark':
            BG = '#454545'
            ACTIVEBG = '#525252'
            PRESSEDBG = '#262626'
            FG = '#E6E6E6'
            FIELDBG = '#303030'
            LIGHTCOLOR = BG
            DARKCOLOR = BG
            BORDERCOLOR = '#131313'
            FOCUSBORDERCOLOR = '#353535'
            SELECTBG = '#1f1f1f'
            SELECTFG = FG
            UNSELECTEDFG = '#999999'
            DISABLEDFG = '#666666'
            DISABLEDBG = BG
            IM_CLOSE = os.path.join(IMG_PATH, 'close_dark.png')
        #    DISABLEDBG = '#595959'
        else:
            BG = '#dddddd'
            ACTIVEBG = '#efefef'
            PRESSEDBG = '#c1c1c1'
            FG = 'black'
            FIELDBG = 'white'
            LIGHTCOLOR = '#ededed'
            DARKCOLOR = '#cfcdc8'
            BORDERCOLOR = '#888888'
            FOCUSBORDERCOLOR = '#5E5E5E'
            SELECTBG = PRESSEDBG
            SELECTFG = 'black'
            UNSELECTEDFG = '#666666'
            DISABLEDFG = '#999999'
            DISABLEDBG = BG
            IM_CLOSE = os.path.join(IMG_PATH, 'close.png')
        #    DISABLEDBG = ''
        self._im_close.configure(file=IM_CLOSE)

        BUTTON_STYLE_CONFIG = {'bordercolor': BORDERCOLOR,
                               'background': BG,
                               'fieldbackground': FIELDBG,
                               'indicatorbackground': FIELDBG,
                               'indicatorforeground': FG,
                               'foreground': FG,
                               'arrowcolor': FG,
                               'insertcolor': FG,
                               'upperbordercolor': BORDERCOLOR,
                               'lowerbordercolor': BORDERCOLOR,
                               'lightcolor': LIGHTCOLOR,
                               'darkcolor': DARKCOLOR}

        BUTTON_STYLE_MAP = {'background': [('active', ACTIVEBG),
                                           ('disabled', DISABLEDBG),
                                           ('pressed', PRESSEDBG)],
                            'lightcolor': [('pressed', DARKCOLOR)],
                            'darkcolor': [('pressed', LIGHTCOLOR)],
                            'bordercolor': [('focus', FOCUSBORDERCOLOR)],
                            'foreground': [('disabled', DISABLEDFG)],
                            'arrowcolor': [('disabled', DISABLEDFG)],
                            'fieldbackground': [('disabled', FIELDBG)],
                            'selectbackground': [('focus', SELECTBG)],
                            'selectforeground': [('focus', SELECTFG)]}

        STYLE_CONFIG = {'bordercolor': BORDERCOLOR,
                        'background': BG,
                        'foreground': FG,
                        'arrowcolor': FG,
                        'gripcount': 0,
                        'lightcolor': LIGHTCOLOR,
                        'darkcolor': DARKCOLOR,
                        'troughcolor': PRESSEDBG}

        STYLE_MAP = {'background': [('active', ACTIVEBG), ('disabled', BG)],
                     'lightcolor': [('pressed', DARKCOLOR)],
                     'darkcolor': [('pressed', LIGHTCOLOR)],
                     'foreground': [('disabled', DISABLEDFG)]}

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', **STYLE_CONFIG)
        style.configure('TSeparator', **STYLE_CONFIG)
        style.configure('TLabel', **STYLE_CONFIG)
        style.configure('Sash', **STYLE_CONFIG)
        style.configure('TPanedwindow', **STYLE_CONFIG)
        style.configure('TScrollbar', **STYLE_CONFIG)
        style.map('TFrame', **STYLE_MAP)
        style.map('TLabel', **STYLE_MAP)
        style.map('Sash', **STYLE_MAP)
        style.map('TScrollbar', **STYLE_MAP)
        style.map('TPanedwindow', **STYLE_MAP)
        style.configure('TButton', **BUTTON_STYLE_CONFIG)
        style.configure('TMenubutton', **BUTTON_STYLE_CONFIG)
        style.configure('TCheckbutton', **BUTTON_STYLE_CONFIG)
        style.configure('TRadiobutton', **BUTTON_STYLE_CONFIG)
        style.configure('TEntry', **BUTTON_STYLE_CONFIG)
        style.configure('TCombobox', **BUTTON_STYLE_CONFIG)
        style.configure('TNotebook', **BUTTON_STYLE_CONFIG)
        style.configure('TNotebook.Tab', **BUTTON_STYLE_CONFIG)
        style.configure('Treeview', **BUTTON_STYLE_CONFIG)
        style.configure('Treeview.Heading', **BUTTON_STYLE_CONFIG)
        style.configure('Treeview.Item', foreground=FG)
        style.map('TButton', **BUTTON_STYLE_MAP)
        style.map('TMenubutton', **BUTTON_STYLE_MAP)
        style.map('TCheckbutton', **BUTTON_STYLE_MAP)
        style.map('TRadiobutton', **BUTTON_STYLE_MAP)
        style.map('TEntry', **BUTTON_STYLE_MAP)
        style.map('TCombobox', **BUTTON_STYLE_MAP)
        style.map('TNotebook', **BUTTON_STYLE_MAP)
        style.map('TNotebook.Tab', **BUTTON_STYLE_MAP)
        style.map('Treeview', **BUTTON_STYLE_MAP)
        style.map('Treeview', background=[('selected', SELECTBG)],
                  foreground=[('selected', SELECTFG)])
        style.map('Treeview.Heading', **BUTTON_STYLE_MAP)
        self.option_add('*TCombobox*Listbox.selectBackground', SELECTBG)
        self.option_add('*TCombobox*Listbox.selectForeground', FG)
        self.option_add('*TCombobox*Listbox.foreground', FG)
        self.option_add('*TCombobox*Listbox.background', FIELDBG)
        self.option_add('*Text.foreground', UNSELECTEDFG)
        self.option_add('*Text.selectForeground', UNSELECTEDFG)
        self.option_add('*Text.background', BG)
        self.option_add('*Text.selectBackground', BG)
        self.option_add('*Text.inactiveSelectBackground', BG)
        self.option_add('*Text.relief', 'flat')
        self.option_add('*Text.highlightThickness', 0)
        self.option_add('*Text.borderWidth', 0)
        self.option_add('*Text.font', FONT)
        self.option_add('*Canvas.background', BG)
        self.option_add('*Canvas.fill', ACTIVEBG)
        self.option_add('*Canvas.relief', 'flat')
        self.option_add('*Canvas.highlightThickness', 0)
        self.option_add('*Canvas.borderWidth', 0)
        self.option_add('*Toplevel.background', BG)

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
        style.configure('separator.TFrame', background=BORDERCOLOR, padding=1)
        style.configure('Up.TButton', arrowsize=20)
        style.configure('Down.TButton', arrowsize=20)
        style.configure('close.TButton', borderwidth=1, relief='flat')
        style.map('close.TButton', relief=[('active', 'raised')])
        style.layout('flat.Treeview',
                     [('Treeview.padding',
                       {'sticky': 'nswe',
                        'children': [('Treeview.treearea', {'sticky': 'nswe'})]})])
        style.configure('flat.Treeview', background=FIELDBG)
        self.configure(bg=BG, padx=6, pady=2)
        self.menu.configure(bg=BG, fg=FG,
                            borderwidth=0, activeborderwidth=0,
                            activebackground=SELECTBG,
                            activeforeground=SELECTFG)
        self.menu_file.configure(bg=FIELDBG, activebackground=SELECTBG,
                                 fg=FG, activeforeground=FG,
                                 disabledforeground=DISABLEDFG,
                                 selectcolor=FG)
        self.menu_recent_files.configure(bg=FIELDBG, activebackground=SELECTBG,
                                         fg=FG, activeforeground=FG,
                                         disabledforeground=DISABLEDFG,
                                         selectcolor=FG)
        self.menu_edit.configure(bg=FIELDBG, activebackground=SELECTBG,
                                 fg=FG, activeforeground=FG,
                                 disabledforeground=DISABLEDFG,
                                 selectcolor=FG)
        self.option_add('*Menu.background', FIELDBG)
        self.option_add('*Menu.activeBackground', SELECTBG)
        self.option_add('*Menu.activeForeground', FG)
        self.option_add('*Menu.disabledForeground', DISABLEDFG)
        self.option_add('*Menu.foreground', FG)
        self.option_add('*Menu.selectColor', FG)
        # --- notebook
        style.layout('Notebook', style.layout('TFrame'))
        style.layout('Notebook.TMenubutton',
                     [('Menubutton.border',
                       {'sticky': 'nswe',
                        'children': [('Menubutton.focus',
                                      {'sticky': 'nswe',
                                       'children': [('Menubutton.indicator', {'side': 'right', 'sticky': ''}),
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
        style.layout('Notebook.Left.TButton',
                     [('Button.padding',
                       {'sticky': 'nswe',
                        'children': [('Button.leftarrow', {'sticky': 'nswe'})]})])
        style.layout('Notebook.Right.TButton',
                     [('Button.padding',
                       {'sticky': 'nswe',
                        'children': [('Button.rightarrow', {'sticky': 'nswe'})]})])
        style.configure('Notebook', **STYLE_CONFIG)
        style.configure('Notebook.Tab', relief='raised', borderwidth=1,
                        **STYLE_CONFIG)
        style.configure('Notebook.Tab.Frame', relief='flat', borderwidth=0,
                        **STYLE_CONFIG)
        style.configure('Notebook.Tab.Label', relief='flat', borderwidth=1,
                        padding=0, **STYLE_CONFIG)
        style.configure('Notebook.Tab.Label', foreground=UNSELECTEDFG)
        style.configure('Notebook.Tab.Close', relief='flat', borderwidth=1,
                        padding=0, **STYLE_CONFIG)
        style.configure('Notebook.Tab.Frame', background=BG)
        style.configure('Notebook.Tab.Label', background=BG)
        style.configure('Notebook.Tab.Close', background=BG)

        style.map('Notebook.Tab.Frame',
                  **{'background': [('selected', '!disabled', ACTIVEBG)]})
        style.map('Notebook.Tab.Label',
                  **{'background': [('selected', '!disabled', ACTIVEBG)],
                     'foreground': [('selected', '!disabled', FG)]})
        style.map('Notebook.Tab.Close',
                  **{'background': [('selected', ACTIVEBG),
                                    ('pressed', DARKCOLOR),
                                    ('active', ACTIVEBG)],
                     'relief': [('hover', '!disabled', 'raised'),
                                ('active', '!disabled', 'raised'),
                                ('pressed', '!disabled', 'sunken')],
                     'lightcolor': [('pressed', DARKCOLOR)],
                     'darkcolor': [('pressed', LIGHTCOLOR)]})
        style.map('Notebook.Tab',
                  **{'background': [('selected', '!disabled', ACTIVEBG)]})

        style.configure('Notebook.Left.TButton', padding=0)
        style.configure('Notebook.Right.TButton', padding=0)

    def _on_populate(self, event):
        cells = self.codestruct.get_cells()
        self.editor.set_cells(cells)

    def _on_tab_changed(self, event):
        self.codestruct.set_callback(self.editor.goto_item)
        self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))

    def _edit_modified(self, *args, tab=None):
        self.editor.edit_modified(*args, tab=tab)
        if self.editor.edit_modified(tab=tab):
            self.menu_file.entryconfigure('Save', state='normal')
        else:
            self.menu_file.entryconfigure('Save', state='disabled')

    def config(self):
        c = Config(self)
        self.wait_window(c)
        self._setup_style()
        self.editor.update_config()
        self.console.update_config()

    def quit(self):
        files = ', '.join([f for f in self.editor.files.values() if f])
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

    def open_file(self, file):
        files = list(self.editor.files.values())
        if file in files:
            self.editor.select(list(self.editor.files.keys())[files.index(file)])
            self._update_recent_files(file)
        else:
            try:
                with open(file) as f:
                    txt = f.read()
            except FileNotFoundError:
                pass
            except Exception:
                showerror('Error', traceback.format_exc())
            else:
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
        initialdir, initialfile = os.path.split(os.path.abspath(self.file))
        name = asksaveasfilename(self, initialfile=initialfile,
                                 initialdir=initialdir, defaultext='.py',
                                 filetypes=[('Python', '*.py'), ('All files', '*')])
        if name:
            tab = self.editor.select()
            self.editor.files[tab] = name
            self.save()
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
            self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))
            self.check_syntax()
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
