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

from tkfilebrowser import asksaveasfilename

from pytkeditorlib.gui_utils import AutoCompleteEntryListbox, Notebook
from pytkeditorlib.dialogs import askyesnocancel, askoptions, showerror, \
    TooltipNotebookWrapper
from pytkeditorlib.utils.constants import CONFIG
from .editor import Editor


class EditorNotebook(Notebook):
    def __init__(self, master, **kw):
        Notebook.__init__(self, master, **kw)
        self._closecommand = self.close
        self.files = {}      # tab: file_path
        self.wrapper = TooltipNotebookWrapper(self)
        self.last_closed = []
        self.menu = Menu(self, tearoff=False)
        self.menu.add_command(label='Set Console working directory',
                              command=self.set_console_wdir)
        self.menu.add_separator()
        self.menu.add_command(label='Close all other tabs',
                              command=self.close_other_tabs)
        self.menu.add_command(label='Close tabs to the right',
                              command=self.close_tabs_right)
        self.menu.add_command(label='Close tabs to the left',
                              command=self.close_tabs_left)
        self._files_mtime = {}           # file_path: mtime
        self._files_check_deletion = {}  # file_path: bool

    def _popup_menu(self, event, tab):
        self._show(tab)
        if self.menu is not None:
            self.menu.tk_popup(event.x_root, event.y_root)

    def _check_modif(self, tab):
        """Check if file has been modified outside PyTkEditor."""
        file = self.files[tab]
        try:
            mtime = os.stat(file).st_mtime
            if mtime > self._files_mtime[tab]:
                # the file has been modified
                logging.info(f'{file} has been modified')
                self.edit_modified(True, tab=tab, generate=True)
                self.update_idletasks()
                ans = askoptions('Warning',
                                 f'{file} has been modified outside PyTkEditor. What do you want to do?',
                                 self, 'warning', 'Reload', 'Overwrite', 'Cancel')
                if ans == 'Reload':
                    self.select(tab)
                    self.event_generate('<<Reload>>')
                elif ans == 'Overwrite':
                    self.save(tab=tab)
                    self.edit_modified(False, tab=tab, generate=True)
                self._files_mtime[tab] = os.stat(file).st_mtime
        except (FileNotFoundError, NotADirectoryError):
            # the file has been deleted
            try:
                if self._files_check_deletion[tab]:
                    logging.info(f'{file} has been deleted')
                    self.edit_modified(True, tab=tab, generate=True)
                    self.update_idletasks()
                    ans = askoptions('Warning',
                                     f'{file} has been deleted. What do you want to do?',
                                     self, 'warning', 'Save', 'Close', 'Cancel')
                    if ans == 'Save':
                        self.save(tab=tab)
                        self.edit_modified(False, tab=tab, generate=True)
                        self._files_check_deletion[tab] = True
                    elif ans == 'Close':
                        self._close(tab)
                    else:
                        self._files_check_deletion[tab] = False
            except KeyError:
                # the file does not exist yet
                return

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

    # --- undo / redo
    def undo(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].undo()

    def redo(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].redo()

    # --- cut / copy / paste
    def cut(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].event_generate("<Control-x>")

    def copy(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].event_generate("<Control-c>")

    def paste(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].event_generate("<Control-v>")

    # --- edit
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

    def delete_lines(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].delete_lines()

    def duplicate_lines(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].duplicate_lines()

    # --- filetype
    def get_filetype(self):
        if self.current_tab >= 0:
            return self._tabs[self.current_tab].filetype

    def set_filetype(self, filetype):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].filetype = filetype
            self.event_generate('<<FiletypeChanged>>')

    def set_console_wdir(self):
        self.event_generate('<<SetConsoleWDir>>')

    # --- formatting
    def toggle_comment(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].toggle_comment()

    def upper_case(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].upper_case()

    def lower_case(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].lower_case()

    def set_cells(self, cells):
        self._tabs[self.current_tab].set_cells(cells)

    # --- indent
    def indent(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].on_tab(force_indent=True)

    def unindent(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].unindent()

    # --- select
    def select(self, tab_id=None):
        res = Notebook.select(self, tab_id)
        tab = self.current_tab
        if tab >= 0:
            self._tabs[tab].focus_set()
        return res

    def select_all(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].select_all()

    def focus_tab(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].text.focus_set()

    # --- find / replace
    def find(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].find()

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

    # --- syntax check
    def show_syntax_issues(self, results):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].show_syntax_issues(results)

    def get_syntax_issues(self):
        if self.current_tab >= 0:
            return self._tabs[self.current_tab].syntax_issues_menuentries
        else:
            return []

    # --- get
    def get(self, tab=None, strip=True):
        if tab is None:
            tab = self.current_tab
        return self._tabs[tab].get(strip)

    def get_lexer(self, tab=None):
        if tab is None:
            tab = self.current_tab
        return self._tabs[tab].lexer

    def get_selection(self):
        if self._current_tab < 0:
            return ''
        sel = self._tabs[self._current_tab].text.tag_ranges('sel')
        if sel:
            return self._tabs[self._current_tab].text.get('sel.first', 'sel.last')
        else:
            return ''

    def get_cell(self, goto_next=False):
        if self._current_tab >= 0:
            return self._tabs[self._current_tab].get_cell(goto_next)
        else:
            return ''

    def get_last_closed(self):
        if self.last_closed:
            return self.last_closed.pop()

    def get_docstring(self, obj):
        if self.current_tab >= 0:
            return self._tabs[self.current_tab].get_docstring(obj)
        else:
            return ("", "")

    # --- close
    def _close(self, tab):
        """Close a tab."""
        self.wrapper.remove_tooltip(self._tab_labels[tab])
        ed = self._tabs[tab]
        if self.files[tab]:
            self.last_closed.append(self.files[tab])
        try:
            del self._files_check_deletion[tab]
            del self._files_mtime[tab]
        except KeyError:
            pass
        del self.files[tab]
        self.forget(tab)
        if not self._visible_tabs:
            self.event_generate('<<NotebookEmpty>>')
        ed.destroy()

    def close(self, tab):
        """Close tab and ask before dropping modifications."""
        rep = False
        if self.edit_modified(widget=self._tabs[tab]):
            rep = askyesnocancel('Confirmation', 'The file %r has been modified. Do you want to save it?' % self.files[tab])
        if rep:
            self.save(tab)
        elif rep is None:
            return False
        self._close(tab)
        return True

    def closeall(self, event=None):
        """Close all tabs."""
        b = True
        tabs = self.tabs()
        i = 0
        while b and i < len(tabs):
            b = self.close(tabs[i])
            i += 1
        return b

    def close_other_tabs(self):
        """Close all tabs except current one."""
        for tab in self.tabs():
            if tab != self.current_tab:
                self.close(tab)

    def close_tabs_right(self):
        """Close all tabs on the right of current one."""
        ind = self._visible_tabs.index(self.current_tab)
        for tab in self._visible_tabs[ind + 1:]:
            self.close(tab)

    def close_tabs_left(self):
        """Close all tabs on the left of current one."""
        ind = self._visible_tabs.index(self.current_tab)
        for tab in self._visible_tabs[:ind]:
            self.close(tab)

    # --- save
    def save(self, tab=None, force=False):
        if tab is None:
            tab = self.current_tab
        if tab < 0:
            return False
        if not self.files[tab]:
            res = self.saveas(tab)
        else:
            if force or self.edit_modified(tab=tab):
                file = self.files[tab]
                try:
                    with open(file, 'w') as f:
                        f.write(self.get(tab))
                except PermissionError as e:
                    showerror("Error", f"PermissionError: {e.strerror}: {file}", parent=self)
                self._files_mtime[tab] = os.stat(file).st_mtime
                self._files_check_deletion[tab] = True
                res = True
            else:
                res = True
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
                self._files_check_deletion[tab] = False
            self.files[tab] = name
            self._tabs[tab].file = name
            self.tab(tab, text=os.path.split(name)[1])
            self.wrapper.set_tooltip_text(tab, os.path.abspath(name))
            self.save(tab, force=True)
            self._files_check_deletion[tab] = True
            return True
        else:
            return False

    # --- goto
    def goto_line(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].goto_line()

    def goto_start(self):
        if self._current_tab >= 0:
            self._tabs[self._current_tab].text.mark_set('insert', '1.0')
            self._tabs[self._current_tab].see('1.0')

    def goto_item(self, *args):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].goto_item(*args)

    # --- misc
    def run(self, interactive=True):
        """Run file in external console"""
        if self.current_tab >= 0:
            file = self.files[self.current_tab]
            if file:
                filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'console.py')
                external_console = CONFIG.get('Run', 'external_console', fallback='').split()
                try:

                    Popen(external_console + [f"python {filename} {file} {interactive}"])
                except Exception:
                    showerror("Error",
                              "PyTkEditor failed to run the file, please check \
the external terminal configuration in the settings.",
                              parent=self)

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

        editor = Editor(self, file)
        if len(self._visible_tabs) == 0:
            self.event_generate('<<NotebookFirstTab>>')
        tab = self.add(editor, text=title)
        editor.bind('<FocusIn>', lambda e: self._check_modif(tab))
        if file in self.last_closed:
            self.last_closed.remove(file)
        self.files[tab] = file
        if file:
            self._files_mtime[tab] = os.stat(file).st_mtime
            self._files_check_deletion[tab] = True

        self._tab_menu.entryconfigure(self._tab_menu_entries[tab],
                                      label="{} - {}".format(title, os.path.dirname(file)))
        #~self._tabs[tab].file = file
        self.wrapper.add_tooltip(tab, file if file else title)
        editor.text.bind('<<Modified>>', lambda e: self.edit_modified(widget=editor, generate=True))
        editor.text.bind('<Control-Tab>', self._select_next)
        editor.text.bind('<Shift-Control-ISO_Left_Tab>', self._select_prev)
        editor.busy(False)

    def _select_next(self, event):
        self.select_next(True)
        return "break"

    def _select_prev(self, event):
        self.select_prev(True)
        return "break"

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
        return "break"

    def choose_color(self):
        tab = self.current_tab
        if tab >= 0:
            self._tabs[self.current_tab].choose_color()



