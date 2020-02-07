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


Console history with text display
"""
import tkinter as tk
from tkinter import ttk
import pickle

from pygments import lex
from pygments.lexers import Python3Lexer

from pytkeditorlib.utils.constants import CONFIG, HISTFILE
from pytkeditorlib.gui_utils import AutoHideScrollbar
from pytkeditorlib.dialogs import showinfo
from .base_widget import BaseWidget, RichText


class History(RichText):
    """Python console command history."""

    def __init__(self, master=None, histfile=HISTFILE, current_session=False, **kw):
        """ Crée un historique vide """
        kw.setdefault('width', 1)
        RichText.__init__(self, master, **kw)

        self.histfile = histfile
        self.maxsize = CONFIG.getint('History', 'max_size', fallback=10000)
        self.history = []
        self.current_session = current_session

        # --- bindings
        self.bind('<1>', lambda e: self.focus_set())
        self.bind('<Control-a>', self.select_all)

        # --- load previous session history
        try:
            with open(histfile, 'rb') as file:
                dp = pickle.Unpickler(file)
                self.history = dp.load()
            self._session_start = len(self.history)
        except (FileNotFoundError, pickle.UnpicklingError, EOFError):
            self._session_start = 0
        self.reset_text()

    def new_session(self):
        self._session_start = len(self.history)

    def select_all(self, event):
        self.tag_add('sel', '1.0', 'end')
        return "break"

    def update_style(self):
        RichText.update_style(self)
        self.maxsize = CONFIG.getint('History', 'max_size', fallback=10000)

    def parse(self, start='1.0'):
        data = self.get(start, 'end')
        while data and '\n' == data[0]:
            start = self.index('%s+1c' % start)
            data = data[1:]
        self.mark_set('range_start', start)
        for t in self._syntax_highlighting_tags:
            self.tag_remove(t, start, "range_start +%ic" % len(data))
        for token, content in lex(data, Python3Lexer()):
            self.mark_set("range_end", "range_start + %ic" % len(content))
            for t in token.split():
                self.tag_add(str(t), "range_start", "range_end")
            self.mark_set("range_start", "range_end")

    def save(self):
        try:
            with open(self.histfile, 'rb') as file:
                dp = pickle.Unpickler(file)
                prev = dp.load()
        except (FileNotFoundError, pickle.UnpicklingError, EOFError):
            prev = []
        with open(self.histfile, 'wb') as file:
            pick = pickle.Pickler(file)
            hist = prev + self.history[self._session_start:]
            l = len(hist)
            if l > self.maxsize:
                hist = hist[l - self.maxsize:]
            pick.dump(hist)

    def add_history(self, line):
        self.history.append(line)
        index = self.index('end-1c')
        self.configure(state='normal')
        self.insert('end', line + '\n')
        self.parse(index)
        self.configure(state='disabled')
        self.see('end')

    def reset_text(self):
        self.configure(cursor='watch')
        self.update_idletasks()
        self.configure(state='normal')
        self.delete('1.0', 'end')
        if self.current_session:
            self.insert('1.0', '\n'.join(self.history[self._session_start:]))
        else:
            self.insert('1.0', '\n'.join(self.history))
        self.parse()
        self.configure(state='disabled', cursor='')

    def replace_history_item(self, pos, line):
        self.history[pos] = line

        self.reset_text()

    def remove_history_item(self, pos):
        del self.history[pos]
        self.reset_text()

    def get_history_item(self, pos):
        try:
            return self.history[pos]
        except IndexError:
            return None

    def get_length(self):
        return len(self.history)

    def get_session_hist(self):
        return self.history[self._session_start:]


class HistoryFrame(BaseWidget):

    def __init__(self, master=None, histfile=HISTFILE, **kw):
        BaseWidget.__init__(self, master, 'History', **kw)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._search_count = tk.IntVar(self)

        current_session = CONFIG.getboolean('History', 'current_session', fallback=False)
        self._current_session = tk.BooleanVar(self, current_session)
        # --- menu
        self.menu = tk.Menu(self)
        self.menu.add_checkbutton(label='Current session only',
                                  command=self._current_session_toggle,
                                  variable=self._current_session)
        self.menu.add_command(label='Find', command=self.find)

        syh = AutoHideScrollbar(self, orient='vertical')
        self.history = History(self, HISTFILE, current_session,
                               yscrollcommand=syh.set,
                               relief='flat', borderwidth=0, highlightthickness=0)
        syh.configure(command=self.history.yview)

        # --- search bar
        self._highlighted = ''
        self.frame_search = ttk.Frame(self, padding=2)
        self.frame_search.columnconfigure(1, weight=1)
        self.entry_search = ttk.Entry(self.frame_search)
        self.entry_search.bind('<Return>', self.search)
        self.entry_search.bind('<Escape>', lambda e: self.frame_search.grid_remove())
        search_buttons = ttk.Frame(self.frame_search)
        ttk.Button(search_buttons, style='Up.TButton', padding=0,
                   command=lambda: self.search(backwards=True)).pack(side='left', padx=2, pady=4)
        ttk.Button(search_buttons, style='Down.TButton', padding=0,
                   command=self.search).pack(side='left', padx=2, pady=4)
        self.case_sensitive = ttk.Checkbutton(search_buttons, text='aA')
        self.case_sensitive.state(['selected', '!alternate'])
        self.case_sensitive.pack(side='left', padx=2, pady=4)
        self.regexp = ttk.Checkbutton(search_buttons, text='regexp')
        self.regexp.state(['!selected', '!alternate'])
        self.regexp.pack(side='left', padx=2, pady=4)
        self.full_word = ttk.Checkbutton(search_buttons, text='[-]')
        self.full_word.state(['!selected', '!alternate'])
        self.full_word.pack(side='left', padx=2, pady=4)
        self._highlight_btn = ttk.Checkbutton(search_buttons, image='img_highlight',
                                              padding=0, style='toggle.TButton',
                                              command=self.highlight_all)
        self._highlight_btn.pack(side='left', padx=2, pady=4)

        frame_find = ttk.Frame(self.frame_search)
        ttk.Button(frame_find, padding=0,
                   command=lambda: self.frame_search.grid_remove(),
                   style='close.TButton').pack(side='left')
        ttk.Label(frame_find, text='Find:').pack(side='right')
        frame_find.grid(row=1, column=0, padx=2, pady=4, sticky='ew')
        self.entry_search.grid(row=1, column=1, sticky='ew', pady=4, padx=2)
        search_buttons.grid(row=1, column=2, sticky='w')

        self.bind('<Control-f>', self.find)
        self.history.bind('<Control-f>', self.find)

        # --- placement
        syh.grid(row=0, column=1, sticky='ns')
        self.history.grid(row=0, column=0, sticky='nswe')
        self.frame_search.grid(row=1, columnspan=2, sticky='we')
        self.frame_search.grid_remove()

        self.update_style = self.history.update_style

    def _current_session_toggle(self):
        val = self._current_session.get()
        self.history.current_session = val
        self.history.reset_text()
        CONFIG.set('History', 'current_session', str(val))
        CONFIG.save()

    def find(self, event=None):
        self.frame_search.grid()
        self.entry_search.focus_set()
        sel = self.history.tag_ranges('sel')
        if sel:
            self.entry_search.delete(0, 'end')
            self.entry_search.insert(0, self.history.get('sel.first', 'sel.last'))
        self.entry_search.selection_range(0, 'end')
        return "break"

    def highlight_all(self):
        if 'selected' in self._highlight_btn.state():
            pattern = self.entry_search.get()

            if not pattern:
                self._highlight_btn.state(['!selected'])
                return
            if self._highlighted == pattern and self.history.tag_ranges('highlight_find'):
                return

            self._highlighted = pattern
            self.history.tag_remove('highlight_find', '1.0', 'end')

            full_word = 'selected' in self.full_word.state()
            options = {'regexp': 'selected' in self.regexp.state(),
                       'nocase': 'selected' not in self.case_sensitive.state(),
                       'count': self._search_count, 'stopindex': 'end'}

            if full_word:
                pattern = r'\y%s\y' % pattern
                options['regexp'] = True
            res = self.history.search(pattern, '1.0', **options)
            while res:
                end = f"{res}+{self._search_count.get()}c"
                self.history.tag_add('highlight_find', res, end)
                res = self.history.search(pattern, end, **options)
        else:
            self.history.tag_remove('highlight_find', '1.0', 'end')

    def search(self, event=None, backwards=False, notify_no_match=True, **kw):
        pattern = self.entry_search.get()
        full_word = 'selected' in self.full_word.state()
        options = {'regexp': 'selected' in self.regexp.state(),
                   'nocase': 'selected' not in self.case_sensitive.state(),
                   'count': self._search_count}
        options.update(kw)
        if backwards:
            options['backwards'] = True
        else:  # forwards
            options['forwards'] = True

        self.highlight_all()
        res = self.history.search(pattern, 'insert', **options)

        if res and full_word:
            index = 'start'
            end_word = self.history.index(res + ' wordend')
            end_res = self.history.index(res + '+%ic' % self._search_count.get())

            while index and index != res and end_word != end_res:
                index = self.history.search(pattern, end_res, **options)
                end_word = self.history.index(index + ' wordend')
                end_res = self.history.index(index + '+%ic' % self._search_count.get())

            if index != 'start':
                res = index

        self.history.tag_remove('sel', '1.0', 'end')
        if res:
            self.history.tag_add('sel', res, '%s+%ic' % (res, self._search_count.get()))
            self.history.see(res)
            if backwards:
                self.history.mark_set('insert', '%s-1c' % (res))
            else:
                self.history.mark_set('insert', '%s+%ic' % (res, self._search_count.get()))
        else:
            if notify_no_match:
                showinfo("Search complete", "No match found")
