#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 11:08:56 2018

@author: juliette
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkeditorlib.constants import load_style, CONFIG, HISTFILE
from tkeditorlib.autoscrollbar import AutoHideScrollbar
from pygments import lex
from pygments.lexers import Python3Lexer
import pickle


class History(tk.Text):
    """Python console command history."""

    def __init__(self, master=None, histfile=HISTFILE, max_size=10000, **kw):
        """ Crée un historique vide """
        tk.Text.__init__(self, master, **kw)
        self._syntax_highlighting_tags = []
        self.update_style()
        self.histfile = histfile
        self.maxsize = max_size
        self.history = []

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
        self.insert('1.0', '\n'.join(self.history))
        self.parse()
        self.configure(state='disabled')

    def select_all(self, event):
        self.tag_add('sel', '1.0', 'end')
        return "break"

    def update_style(self):
        FONT = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        CONSOLE_BG, CONSOLE_HIGHLIGHT_BG, CONSOLE_SYNTAX_HIGHLIGHTING = load_style(CONFIG.get('Console', 'style'))
        CONSOLE_FG = CONSOLE_SYNTAX_HIGHLIGHTING.get('Token.Name', {}).get('foreground', 'black')

        self._syntax_highlighting_tags = list(CONSOLE_SYNTAX_HIGHLIGHTING.keys())
        self.configure(fg=CONSOLE_FG, bg=CONSOLE_BG, font=FONT,
                       selectbackground=CONSOLE_HIGHLIGHT_BG,
                       inactiveselectbackground=CONSOLE_HIGHLIGHT_BG,
                       insertbackground=CONSOLE_FG)
        self.tag_configure('error', background=CONSOLE_BG)
        self.tag_configure('output', foreground=CONSOLE_FG,
                           background=CONSOLE_BG)
        # --- syntax highlighting
        tags = list(self.tag_names())
        tags.remove('sel')
        tag_props = {key: '' for key in self.tag_configure('sel')}
        for tag in tags:
            self.tag_configure(tag, **tag_props)
        for tag, opts in CONSOLE_SYNTAX_HIGHLIGHTING.items():
            self.tag_configure(tag, **opts)

    def parse(self):
        data = self.get('1.0', 'end')
        start = '1.0'
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
        self.configure(state='normal')
        self.insert('end', line)
        self.parse()
        self.configure(state='disabled')

    def replace_history_item(self, pos, line):
        self.history[pos] = line
        self.configure(state='normal')
        self.delete('1.0', 'end')
        self.insert('1.0', '\n'.join(self.history))
        self.parse()
        self.configure(state='disabled')

    def remove_history_item(self, pos):
        del self.history[pos]
        self.configure(state='normal')
        self.delete('1.0', 'end')
        self.insert('1.0', '\n'.join(self.history))
        self.parse()
        self.configure(state='disabled')

    def get_history_item(self, pos):
        try:
            return self.history[pos]
        except IndexError:
            return None

    def get_length(self):
        return len(self.history)

    def set_max_size(self, maxsize):
        self.maxsize = maxsize

    def get_max_size(self):
        return self.maxsize

    def get_session_hist(self):
        return self.history[self._session_start:]


class HistoryFrame(ttk.Frame):

    def __init__(self, master=None, histfile=HISTFILE, **kw):
        ttk.Frame.__init__(self, master, **kw)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._search_count = tk.IntVar(self)

        syh = AutoHideScrollbar(self, orient='vertical')
        self.history = History(self, HISTFILE, yscrollcommand=syh.set,
                               relief='flat', borderwidth=0, highlightthickness=0)
        syh.configure(command=self.history.yview)

        # --- search bar
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

    def find(self, event=None):
        self.frame_search.grid()
        self.entry_search.focus_set()
        sel = self.history.tag_ranges('sel')
        if sel:
            self.entry_search.delete(0, 'end')
            self.entry_search.insert(0, self.history.get('sel.first', 'sel.last'))
        self.entry_search.selection_range(0, 'end')
        return "break"

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
                messagebox.showinfo("Search complete", "No match found")
