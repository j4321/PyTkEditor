#from tkeditorlib.editor import Editor
from tkeditorlib.editornotebook import EditorNotebook
from tkeditorlib.syntax_check import check_file
from tkeditorlib.filestructure import CodeStructure
#from tkeditorlib.notebook import Notebook
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesnocancel, showerror
from tkfilebrowser import askopenfilename, asksaveasfilename
import traceback
import os
from subprocess import Popen


class App(tk.Tk):
    def __init__(self, file=None):
        tk.Tk.__init__(self, className='TkEditor')
        self.title('TkEditor')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('border.TFrame', borderwidth=1, relief='sunken')
        style.layout('flat.Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        bg = style.lookup('TFrame', 'background', default='light grey')
        self.configure(bg=bg)
        self.file = ''

        pane = ttk.PanedWindow(self, orient='horizontal')
        self.codestruct = CodeStructure(pane)
#        self.editor = Editor(pane)
        self.editor = EditorNotebook(pane)
        # placement
        pane.add(self.codestruct, weight=1)
        pane.add(self.editor, weight=3)
        pane.pack(fill='both', expand=True)

        # --- menu
        menu = tk.Menu(self, tearoff=False, bg=bg)
        # file
        self.menu_file = tk.Menu(menu, tearoff=False, bg=bg)
        self.menu_file.add_command(label='New', command=self.new,
                                   accelerator='Ctrl+N')
        self.menu_file.add_command(label='Open', command=self.open,
                                   accelerator='Ctrl+O')
        self.menu_file.add_command(label='Save', command=self.save, state='disabled',
                                   accelerator='Ctrl+S')
        self.menu_file.add_command(label='Save As', command=self.saveas,
                                   accelerator='Ctrl+Shift+S')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Quit', command=self.quit)
        # edit
        menu_edit = tk.Menu(menu, tearoff=False, bg=bg)
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

        self.editor.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        self.editor.bind('<<Modified>>', lambda e: self._edit_modified())

        self.bind('<Control-n>', self.new)
        self.bind('<Control-s>', self.save)
        self.bind('<Control-o>', lambda e: self.open())
        self.bind('<Control-Shift-S>', self.saveas)
        self.bind('<F5>', self.run)
        if file:
            self.open(file)
        self.protocol('WM_DELETE_WINDOW', self.quit)

    def _on_tab_changed(self, event):
        self.codestruct.set_callback(self.editor.goto_item)
        self.codestruct.populate(self.editor.get())

    def _edit_modified(self, *args):
        # TODO: adapt to notebook
        self.editor.edit_modified(*args)
        file = self.file if self.file else 'TkEditor'
        if self.editor.edit_modified():
            self.title('%s*' % file)
            self.menu_file.entryconfigure(2, state='normal')
        else:
            self.title('%s' % file)
            self.menu_file.entryconfigure(2, state='disabled')

    def quit(self):
        # to adapt
        for tab in self.editor.tabs():
            self.editor.close(tab)
        self.destroy()

    def new(self, event=None):
        self.editor.new()
        self.editor.edit_reset()
        self._edit_modified(0)
        self.codestruct.populate('')

    def open(self, file=None):
        if file is None:
            tab = self.editor.select()
            file = self.editor.files.get(tab, '')
            initialdir, initialfile = os.path.split(os.path.abspath(file))
            file = askopenfilename(self, initialfile=initialfile,
                                   initialdir=initialdir,
                                   filetypes=[('Python', '*.py'), ('All files', '*')])
        if not file:
            return
        try:
            with open(file) as f:
                txt = f.read()
        except Exception:
            showerror('Error', traceback.format_exc())
        else:
            self.editor.new(file)
            self.editor.insert('1.0', txt)
            self.editor.edit_reset()
            self._edit_modified(0)
            self.codestruct.populate(self.editor.get())
            self.check_syntax()

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

    def save(self, event=None, tab=None):
        update = False
        if tab is None:
            tab = self.editor.select()
            update = True
        saved = self.editor.save(tab)
        if update and saved:
            self._edit_modified(0)
            self.codestruct.populate(self.editor.get(strip=False))
            self.check_syntax()
        return saved

    def run(self, event=None):
        if self.save():
            self.editor.run()

    def check_syntax(self, tab=None):
        if tab is None:
            tab = self.editor.select()
        if self.editor.files[tab]:
            results = check_file(self.editor.files[tab])
            self.editor.show_syntax_issues(results)
