from tkeditorlib.editornotebook import EditorNotebook
from tkeditorlib.syntax_check import check_file
from tkeditorlib.filestructure import CodeStructure
from tkeditorlib.constants import ICON, CONFIG, save_config, BG, FG, SELECTBG,\
    SELECTFG, FIELDBG, BORDERCOLOR, DISABLEDFG,\
    BUTTON_STYLE_CONFIG, BUTTON_STYLE_MAP, STYLE_CONFIG, STYLE_MAP
from tkeditorlib.textconsole import TextConsole
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
        self.iconphoto(True, self._icon)

        recent_files = CONFIG.get('General', 'recent_files', fallback='').split(', ')
        self.recent_files = [f for f in recent_files if f and os.path.exists(f)]

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
        self.option_add('*Menu.background', FIELDBG)
        self.option_add('*Menu.activeBackground', SELECTBG)
        self.option_add('*Menu.activeForeground', FG)
        self.option_add('*Menu.disabledForeground', DISABLEDFG)
        self.option_add('*Menu.activeBorderWidth', 0)
        self.option_add('*Menu.foreground', FG)
        self.option_add('*Menu.selectColor', FG)
        self.option_add('*Menu.relief', 'sunken')

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
                                       'children': [('Button.label', {'sticky': 'nswe'})]})]})])
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
        self.file = ''

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
        menu = tk.Menu(self, tearoff=False, bg=BG, relief='flat')
        # file
        self.menu_file = tk.Menu(menu, tearoff=False)
        self.menu_file.add_command(label='New', command=self.new,
                                   accelerator='Ctrl+N')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Open', command=self.open,
                                   accelerator='Ctrl+O')
        self.menu_file.add_command(label='Restore last closed', command=self.restore_last_closed,
                                   accelerator='Ctrl+Shift+T')
        # file --- recent
        self.menu_recent_files = tk.Menu(self.menu_file, tearoff=False)
        for f in self.recent_files:
            self.menu_recent_files.add_command(label=f, command=lambda file=f: self.open_file(file))

        self.menu_file.add_cascade(label='Recent files', menu=self.menu_recent_files)

        self.menu_file.add_separator()
        self.menu_file.add_command(label='Save', command=self.save, state='disabled',
                                   accelerator='Ctrl+S')
        self.menu_file.add_command(label='Save As', command=self.saveas,
                                   accelerator='Ctrl+Alt+S')
        self.menu_file.add_command(label='Save all', command=self.saveall,
                                   accelerator='Ctrl+Shift+S')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Close all files', command=self.editor.closeall)
        self.menu_file.add_command(label='Quit', command=self.quit)
        # edit
        menu_edit = tk.Menu(menu, tearoff=False)
        menu_edit.add_command(label='Undo', command=self.editor.undo, accelerator='Ctrl+Z')
        menu_edit.add_command(label='Redo', command=self.editor.redo, accelerator='Ctrl+Y')
        menu_edit.add_separator()
        menu_edit.add_command(label='Find', command=self.editor.find,
                              accelerator='Ctrl+F')
        menu_edit.add_command(label='Replace', command=self.editor.replace,
                              accelerator='Ctrl+R')

        menu.add_cascade(label='File', menu=self.menu_file)
        menu.add_cascade(label='Edit', menu=menu_edit)
        menu.add_command(label='Run', command=self.run)
        self.configure(menu=menu)

        # --- bindings
        self.editor.bind('<<NotebookEmpty>>', self.codestruct.clear)
        self.editor.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        self.editor.bind('<<Modified>>', lambda e: self._edit_modified())

        self.bind_class('Text', '<Control-o>', lambda e: None)
        self.bind('<Control-Shift-T>', self.restore_last_closed)
        self.bind('<Control-n>', self.new)
        self.bind('<Control-s>', self.save)
        self.bind('<Control-o>', lambda e: self.open())
        self.bind('<Control-Shift-S>', self.saveall)
        self.bind('<Control-Alt-S>', self.saveas)
        self.bind('<F5>', self.run)
        self.bind('<F9>', lambda e: self.console.execute(self.editor.get_selection()))

        files = CONFIG.get('General', 'opened_files').split(', ')
        for f in files:
            if os.path.exists(f):
                self.open_file(f)

        if file:
            self.open_file(file)
        self.protocol('WM_DELETE_WINDOW', self.quit)

    def _on_tab_changed(self, event):
        self.codestruct.set_callback(self.editor.goto_item)
        self.codestruct.populate(self.editor.filename, self.editor.get(strip=False))

    def _edit_modified(self, *args, tab=None):
        self.editor.edit_modified(*args, tab=tab)
        if self.editor.edit_modified(tab=tab):
            self.menu_file.entryconfigure('Save', state='normal')
        else:
            self.menu_file.entryconfigure('Save', state='disabled')

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

    def open_file(self, file):
        files = list(self.editor.files.values())
        if file in files:
            self.editor.select(list(self.editor.files.keys())[files.index(file)])
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
                if file in self.recent_files:
                    ind = self.recent_files.index(file)
                    del self.recent_files[ind]
                    self.menu_recent_files.delete(ind)
                self.recent_files.append(file)
                self.menu_recent_files.add_command(label=file, command=lambda: self.open_file(file))
                if len(self.recent_files) > 10:
                    del self.recent_files[0]
                    self.menu_recent_files.delete(0)
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
