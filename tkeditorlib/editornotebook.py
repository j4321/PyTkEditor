#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 20:25:11 2018

@author: juliette
"""
from tkeditorlib.notebook import Notebook
from tkeditorlib.editor import Editor
from tkeditorlib.tooltip import TooltipNotebookWrapper
import os
from tkinter.messagebox import askyesnocancel
from tkfilebrowser import asksaveasfilename
from subprocess import Popen


class EditorNotebook(Notebook):
    def __init__(self, master):
        Notebook.__init__(self, master)
        self.files = {}
        self.wrapper = TooltipNotebookWrapper(self, background='light yellow',
                                              foreground='black')
        self.last_closed = []

    @property
    def filename(self):
        return self.tab(self.current_tab, 'text')

    def insert(self, index, text):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].insert(index, text)

    def edit_reset(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].text.edit_reset()

    def undo(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].undo()

    def redo(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].redo()

    def find(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].find()

    def replace(self):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].replace()

    def show_syntax_issues(self, results):
        if self.current_tab >= 0:
            self._tabs[self.current_tab].show_syntax_issues(results)

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
        self._tab_labels[tab].tab_configure(text=title + '*' * b)
        if generate:
            self.event_generate('<<Modified>>')
        return b

    def new(self, file=None):
        if file is None:
            title = 'new.py'
            file = ''
        else:
            title = os.path.split(file)[-1]
        editor = Editor(self)
        tab = self.add(editor, text=title)
        self.tab(tab, closecmd=lambda: self.close(tab))
        if file in self.last_closed:
            self.last_closed.remove(file)
        self.files[tab] = file
        self._tabs[tab].file = file
        self.wrapper.add_tooltip(tab, file if file else title)
        editor.text.bind('<<Modified>>', lambda e: self.edit_modified(widget=editor, generate=True))

    def get(self, tab=None, strip=True):
        if tab is None:
            tab = self.current_tab
        return self._tabs[tab].get(strip)

    def get_selection(self):
        if self._current_tab >= 0:
            sel = self._tabs[self._current_tab].text.tag_ranges('sel')
            if sel:
                return self._tabs[self._current_tab].text.get('sel.first', 'sel.last')
            else:
                return ''

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
            return
        self.wrapper.remove_tooltip(self._tab_labels[tab])
        ed = self._tabs[tab]
        if self.files[tab]:
            self.last_closed.append(self.files[tab])
        del self.files[tab]
        self.forget(tab)
        if not self._visible_tabs:
            self.event_generate('<<NotebookEmpty>>')
        ed.destroy()

    def closeall(self):
        for tab in self.tabs():
            self.close(tab)

    def save(self, tab=None):
        if tab is None:
            tab = self.current_tab
        if not self.files[tab]:
            res = self.saveas(tab)
        else:
            with open(self.files[tab], 'w') as f:
                f.write(self.get(tab))
            res = True
        return res

    def saveas(self, tab=None):
        if tab is None:
            tab = self.current_tab
        initialdir, initialfile = os.path.split(os.path.abspath(self.files[tab]))
        name = asksaveasfilename(self, initialfile=initialfile,
                                 initialdir=initialdir, defaultext='.py',
                                 filetypes=[('Python', '*.py'), ('All files', '*')])
        if name:
            self.files[tab] = name
            self._tabs[tab].file = name
            self._tab_labels[tab].tab_configure(text=os.path.split(name)[1])
            self.wrapper.set_tooltip_text(self._tab_labels[tab], name)
            self.save(tab)
            return True
        else:
            return False

    def run(self):
        tab = self.current_tab
        file = self.files[tab]
        if file:
            filename = os.path.join(os.path.dirname(__file__), 'console.py')
            Popen(['xfce4-terminal', '-e', 'python {} {}'.format(filename, file)])

    def goto_start(self):
        if self._current_tab >= 0:
            self._tabs[self._current_tab].text.mark_set('insert', '1.0')
            self._tabs[self._current_tab].see('1.0')
