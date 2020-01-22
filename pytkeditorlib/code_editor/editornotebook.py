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


Notebook containing the code editors for each opened file
"""
import logging
import os
import re
from tkinter import Menu, Toplevel
from subprocess import Popen
from threading import Thread, Event
from time import sleep

from tkfilebrowser import asksaveasfilename

from pytkeditorlib.gui_utils import AutoCompleteEntryListbox
from pytkeditorlib.dialogs import askyesnocancel, askyesno, showerror, \
    TooltipNotebookWrapper
from pytkeditorlib.gui_utils import Notebook
from .editor import Editor


class EditorNotebook(Notebook):
    def __init__(self, master, **kw):
        Notebook.__init__(self, master, **kw)
        self._closecommand = self.close
        self.files = {}      # tab: file_path
        self.wrapper = TooltipNotebookWrapper(self)
        self.last_closed = []
        self.menu = Menu(self, tearoff=False)
        self.menu.add_command(label='View in filebrowser',
                              command=self.view_in_filebrowser)
        self.menu.add_command(label='Close all other tabs',
                              command=self.close_other_tabs)
        self.menu.add_command(label='Close tabs to the right',
                              command=self.close_tabs_right)
        self.menu.add_command(label='Close tabs to the left',
                              command=self.close_tabs_left)

        self._files_mtime = {}  # file_path: mtime
        self._files_check_deletion = {}  # file_path: bool
        self._modif_watchers = {}  # file_path: thread
        self._is_modified = {}  # file_path: event
        self._is_deleted = {}  # file_path: event
        self._stop_thread = {}  # file_path: bool
        self._modif_polling_id = self.after(10000, self._modif_poll)

        self.bind('<Destroy>', self._on_destroy)

    def _popup_menu(self, event, tab):
        self._show(tab)
        if self.menu is not None:
            self.menu.tk_popup(event.x_root, event.y_root)

    def _watch_modif(self, file):
        sleep(5)
        while not self._stop_thread[file]:
            try:
                mtime = os.stat(file).st_mtime
                if mtime > self._files_mtime[file]:
                    self._is_modified[file].set()
            except FileNotFoundError:
                self._is_deleted[file].set()
            sleep(5)
        del self._stop_thread[file]

    def _start_watching(self, file):
        self._files_mtime[file] = os.stat(file).st_mtime
        self._files_check_deletion[file] = True
        self._stop_thread[file] = False
        self._is_modified[file] = Event()
        self._is_deleted[file] = Event()
        self._modif_watchers[file] = Thread(target=self._watch_modif,
                                            args=(file,), daemon=True)
        self._modif_watchers[file].start()

    def _stop_watching(self, file):
        if file in self._modif_watchers:
            self._stop_thread[file] = True
            del self._modif_watchers[file]
            del self._files_check_deletion[file]
            del self._is_modified[file]
            del self._is_deleted[file]
            del self._files_mtime[file]

    def _modif_poll(self):
        rev_files = {path: tab for tab, path in self.files.items()}
        for file, modif, deletion in zip(self._is_modified.keys(), self._is_modified.values(), self._is_deleted.values()):
            if modif.is_set():
                logging.info(file + ' has been modified')
                tab = rev_files[file]
                self.edit_modified(True, tab=tab, generate=True)
                self.update_idletasks()
                rep = askyesno('Warning',
                               '{} has been modified outside PyTkEditor. Do you want to reload it?'.format(file),
                               icon='warning')
                if rep:
                    self.select(tab)
                    self.event_generate('<<Reload>>')
                self._files_mtime[file] = os.stat(file).st_mtime
                modif.clear()
            elif deletion.is_set():
                logging.info(file + 'has been deleted')
                if self._files_check_deletion[file]:
                    tab = rev_files[file]
                    self.edit_modified(True, tab=tab, generate=True)
                    self.update_idletasks()
                    rep = askyesno('Warning',
                                   '{} has been deleted. Do you want to save it?'.format(file),
                                   icon='warning')
                    if rep:
                        self.save(tab=tab)
                        self.edit_modified(False, tab=tab, generate=True)
                    self._files_check_deletion[file] = rep
                deletion.clear()
        self._modif_polling_id = self.after(2000, self._modif_poll)

    def _on_destroy(self, event):
        self.after_cancel(self._modif_polling_id)

    def _menu_insert(self, tab, text):
        label = '{} - {}'.format(text, self.files.get(tab, ''))
        menu = []
        for t in self._tabs.keys():
            menu.append((self.tab(t, 'text'), t))
        menu.sort()
        ind = menu.index((text, tab))
        self._tab_menu.insert_radiobutton(ind, label=label,
                                          variable=self._tab_var, value=tab,
                                          command=lambda t=tab: self._show(t))
        for i, (text, tab) in enumerate(menu):
            self._tab_menu_entries[tab] = i

    def get_open_files(self):
        return [self.files[tab] for tab in self._visible_tabs]

    @property
    def filename(self):
        return self.tab(self.current_tab, 'text')

    def update_style(self):
        for editor in self._tabs.values():
            editor.update_style()

        fg = self.menu.option_get('foreground', '*Menu')
        bg = self.menu.option_get('background', '*Menu')
        activebackground = self.menu.option_get('activeBackground', '*Menu')
        disabledforeground = self.menu.option_get('disabledForeground', '*Menu')
        self.menu.configure(bg=bg, activebackground=activebackground,
                            fg=fg, selectcolor=fg, activeforeground=fg,
                            disabledforeground=disabledforeground)
        self._tab_menu.configure(bg=bg, activebackground=activebackground,
                                 fg=fg, selectcolor=fg, activeforeground=fg,
                                 disabledforeground=disabledforeground)
        self._canvas.configure(bg=self._canvas.option_get('background', '*Canvas'))

    def insert(self, index, text, tab=None):
        if tab is None:
            tab = self.current_tab
        if tab >= 0:
            self._tabs[tab].insert(index, text)

    def delete(self, index1, index2=None, tab=None):
        if tab is None:
            tab = self.current_tab
        if tab >= 0:
            self._tabs[tab].delete(index1, index2)

    def edit_reset(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].text.edit_reset()

    def get_filetype(self):
        if self.current_tab >= 0:
            return self._tabs[self.current_tab].filetype

    def set_filetype(self, filetype):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].filetype = filetype
            self.event_generate('<<FiletypeChanged>>')

    def view_in_filebrowser(self):
        self.event_generate('<<Filebrowser>>')

    def undo(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].undo()

    def redo(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].redo()

    def cut(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].event_generate("<Control-x>")

    def copy(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].event_generate("<Control-c>")

    def paste(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].event_generate("<Control-v>")

    def select_all(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].select_all()

    def toggle_comment(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].toggle_comment()

    def upper_case(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].upper_case()

    def lower_case(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].lower_case()

    def indent(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].on_tab(force_indent=True)

    def unindent(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].unindent()

    def delete_lines(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].delete_lines()

    def duplicate_lines(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].duplicate_lines()

    def choose_color(self):
        print(self.focus_get())
        tab = self.current_tab
        if tab >= 0:
            self._tabs[self.current_tab].choose_color()

    def get_docstring(self, obj):
        if self.current_tab >= 0:
            return self._tabs[self.current_tab].get_docstring(obj)
        else:
            return ("", "")

    def select(self, tab_id=None):
        res = Notebook.select(self, tab_id)
        tab = self.current_tab
        if tab >= 0:
            self._tabs[tab].focus_set()
        return res

    def file_switch(self, event=None):

        def ok(event):
            file = c.get()
            if file not in files:
                top.destroy()
            else:
                self.select(list(self.files.keys())[files.index(file)])
                top.destroy()

        def sel(event):
            self.select(list(self.files.keys())[files.index(c.get())])
            self.after(2, c.entry.focus_set)

        top = Toplevel(self)
        top.geometry('+%i+%i' % self.winfo_pointerxy())
        top.transient(self)
        top.title('File switcher')
        top.grab_set()

        files = ["{1} - {0}".format(*os.path.split(file)) for file in self.files.values()]
        c = AutoCompleteEntryListbox(top, completevalues=sorted(files), width=60)
        c.pack(fill='both', expand=True)
        c.entry.bind('<Escape>', lambda e: top.destroy())
        c.listbox.bind('<Escape>', lambda e: top.destroy())
        c.entry.bind('<Return>', ok)
        c.listbox.bind('<Return>', ok)
        c.bind('<<ItemSelect>>', sel)
        c.focus_set()

    def goto_line(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].goto_line()

    def find(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].find()

    def replace(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].replace()

    def replace_all(self, pattern, new_text, replacements):
        try:
            for tab, matches in replacements.items():
                for start, end in reversed(matches):
                    self._tabs[tab].replace_text(start, end, pattern, new_text)
                self._tabs[tab].update_nb_line()
                self._tabs[tab].parse_all()
        except re.error as e:
            showerror("Error", f"Replacement error: {e.msg}", parent=self)

    def show_syntax_issues(self, results):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].show_syntax_issues(results)

    def get_syntax_issues(self):
        if self.current_tab >= 0:
            return self._tabs[self.current_tab].syntax_issues_menuentries
        else:
            return []

    def goto_item(self, *args):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].goto_item(*args)

    def edit_modified(self, *args, widget=None, generate=False, tab=None):
        if widget is None:
            if tab is None:
                tab = self.current_tab
            widget = self._tabs[tab]
        else:
            tab = self.index(widget)
        widget.text.edit_modified(*args)
        b = widget.text.edit_modified()
        title = self._tab_labels[tab].tab_cget('text').strip('*')
        # self._tab_labels[tab].tab_configure(text=title + '*' * b)
        self.tab(tab, text=title + '*' * b)
        if generate:
            self.event_generate('<<Modified>>')
        return b

    def set_cells(self, cells):
        self._tabs[self.current_tab].set_cells(cells)

    def new(self, file=None):
        if file is None:
            new_files = [-1]
            pattern = re.compile(r"^new(\d+).py - $")
            for i in self._tab_menu_entries.values():
                name = self._tab_menu.entrycget(i, 'label')
                match = pattern.search(name)
                if match:
                    new_files.append(int(match.groups()[0]))
            title = f'new{max(new_files) + 1}.py'
            file = ''
        else:
            title = os.path.split(file)[-1]
            self._start_watching(file)

        editor = Editor(self, 'Python' if title.endswith('.py') else 'Text')
        if len(self._visible_tabs) == 0:
            self.event_generate('<<NotebookFirstTab>>')
        tab = self.add(editor, text=title)
        if file in self.last_closed:
            self.last_closed.remove(file)
        self.files[tab] = file
        self._tab_menu.entryconfigure(self._tab_menu_entries[tab],
                                      label="{} - {}".format(title, os.path.dirname(file)))
        self._tabs[tab].file = file
        self.wrapper.add_tooltip(tab, file if file else title)
        editor.text.bind('<<Modified>>', lambda e: self.edit_modified(widget=editor, generate=True))

    def get(self, tab=None, strip=True):
        if tab is None:
            tab = self.current_tab
        return self._tabs[tab].get(strip)

    def find_all(self, pattern, case_sensitive, regexp, full_word):
        options = {'regexp': regexp,
                   'nocase': not case_sensitive,
                   'stopindex': 'end'}

        if full_word:
            pattern = r'\y%s\y' % pattern
            options['regexp'] = True
        results = {}
        for tab in self._visible_tabs:
            path = self.files[tab]
            name = self.tab(tab, 'text')
            results[tab] = f"{name} - {path}", self._tabs[tab].find_all(pattern, options)

        return results

    def get_selection(self):
        if self._current_tab < 0:
            return ''
        sel = self._tabs[self._current_tab].text.tag_ranges('sel')
        if sel:
            return self._tabs[self._current_tab].text.get('sel.first', 'sel.last')
        else:
            return ''

    def get_cell(self):
        if self._current_tab >= 0:
            editor = self._tabs[self._current_tab]
            line = int(str(editor.text.index('insert')).split('.')[0])
            if not editor.cells:
                return ''
            i = 0
            while i < len(editor.cells) and editor.cells[i] < line:
                i += 1
            if i == len(editor.cells):
                start = '%i.0' % editor.cells[-1]
                end = editor.text.index('end')
            elif i > 0:
                start = '%i.0' % editor.cells[i - 1]
                end = '%i.0' % editor.cells[i]
            else:
                start = '1.0'
                end = '%i.0' % editor.cells[i]
            return editor.text.get(start, end)

    def get_last_closed(self):
        if self.last_closed:
            return self.last_closed.pop()

    def close(self, tab):
        rep = False
        if self.edit_modified(widget=self._tabs[tab]):
            rep = askyesnocancel('Confirmation', 'The file %r has been modified. Do you want to save it?' % self.files[tab])
        if rep:
            self.save(tab)
        elif rep is None:
            return False
        self.wrapper.remove_tooltip(self._tab_labels[tab])
        ed = self._tabs[tab]
        if self.files[tab]:
            self.last_closed.append(self.files[tab])
        self._stop_watching(self.files[tab])
        del self.files[tab]
        self.forget(tab)
        if not self._visible_tabs:
            self.event_generate('<<NotebookEmpty>>')
        ed.destroy()
        return True

    def closeall(self):
        b = True
        tabs = self.tabs()
        i = 0
        while b and i < len(tabs):
            b = self.close(tabs[i])
            i += 1
        return b

    def close_other_tabs(self):
        for tab in self.tabs():
            if tab != self.current_tab:
                self.close(tab)

    def close_tabs_right(self):
        ind = self._visible_tabs.index(self.current_tab)
        for tab in self._visible_tabs[ind + 1:]:
            self.close(tab)

    def close_tabs_left(self):
        ind = self._visible_tabs.index(self.current_tab)
        for tab in self._visible_tabs[:ind]:
            self.close(tab)

    def focus_tab(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].text.focus_set()

    def save(self, tab=None):
        if tab is None:
            tab = self.current_tab
        if tab < 0:
            return False
        if not self.files[tab]:
            res = self.saveas(tab)
        else:
            file = self.files[tab]
            try:
                with open(file, 'w') as f:
                    f.write(self.get(tab))
            except PermissionError as e:
                showerror("Error", f"PermissionError: {e.strerror}: {file}", parent=self)
            self._files_mtime[file] = os.stat(file).st_mtime
            try:
                self._is_modified[file].clear()
                self._is_deleted[file].clear()
            except KeyError:
                self._start_watching(file)
            res = True
            self._files_check_deletion[file] = True
        return res

    def saveas(self, tab=None, name=None):
        if tab is None:
            tab = self.current_tab
        if name is None:
            file = self.files.get(tab, '')
            if file:
                initialdir, initialfile = os.path.split(file)
            else:
                initialdir, initialfile = '', 'new.py'
            name = asksaveasfilename(self, initialfile=initialfile,
                                     initialdir=initialdir, defaultext='.py',
                                     filetypes=[('Python', '*.py'), ('All files', '*')])
        if name:
            if self.files[tab]:
                self._stop_watching(self.files[tab])
            self.files[tab] = name
            self._tabs[tab].file = name
            self.tab(tab, text=os.path.split(name)[1])
            self.wrapper.set_tooltip_text(tab, os.path.abspath(name))
            self.save(tab)
            return True
        else:
            return False

    def run(self):
        if self.current_tab >= 0:
            file = self.files[self.current_tab]
            if file:
                filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'console.py')
                Popen(['xfce4-terminal', '-e', 'python {} {}'.format(filename, file)])

    def goto_start(self):
        if self._current_tab >= 0:
            self._tabs[self._current_tab].text.mark_set('insert', '1.0')
            self._tabs[self._current_tab].see('1.0')
