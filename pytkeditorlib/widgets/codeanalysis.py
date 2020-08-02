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


Code Analysis widget
"""
from tkinter import ttk
from tkinter.font import Font

from pytkeditorlib.utils.constants import CONFIG
from pytkeditorlib.gui_utils import AutoHideScrollbar
from pytkeditorlib.utils.syntax_check import pylint_check
from .base_widget import BaseWidget


class CodeAnalysis(BaseWidget):
    """Widegt to display the static code analysis with pylint."""
    def __init__(self, master, **kw):
        BaseWidget.__init__(self, master, 'Code analysis', **kw)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(self)
        header.columnconfigure(0, weight=1)
        self.filename = ttk.Label(header, padding=(4, 0))
        self.filename.grid(row=0, column=0, sticky='w')
        self.start_btn = ttk.Button(header, text='Analyze', image='img_run',
                                    padding=0, width=7,
                                    command=self.analyze, compound='left')
        self.stop_btn = ttk.Button(header, image='img_stop', padding=0,
                                   command=self.interrupt)
        self.start_btn.grid(row=0, column=1, sticky='e', padx=2)
        self.stop_btn.grid(row=0, column=2, padx=(0, 4))
        self.stop_btn.state(['disabled'])

        # --- result tree
        self.tree = ttk.Treeview(self, show='tree', selectmode='none',
                                 columns=['line'], displaycolumns=[],
                                 style='flat.Treeview', padding=4)
        self._sx = AutoHideScrollbar(self, orient='horizontal', command=self.tree.xview)
        self._sy = AutoHideScrollbar(self, orient='vertical', command=self.tree.yview)

        self.tree.configure(xscrollcommand=self._sx.set,
                            yscrollcommand=self._sy.set)
        self.update_style()
        self.tree.tag_configure('heading', font="TkDefaultFont 9 bold")

        self.font = Font(self, font="TkDefaultFont 9")
        self.font_heading = Font(self, font="TkDefaultFont 9 bold")
        self.callback = None
        self.file = ''
        self._process = None
        self._queue = None
        self._check_id = None

        self._records = {}  # keep in memory old results

        self.min_width = self.font.measure('Global evaluation:') + 20

        self.tree.bind('<1>', self._on_click)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        self.clear()

        # --- placement
        header.grid(row=0, columnspan=2, sticky='ew', pady=2)
        self.tree.grid(row=1, column=0, sticky='ewns')
        self._sx.grid(row=2, column=0, sticky='ew')
        self._sy.grid(row=1, column=1, sticky='ns')

    def _on_click(self, event):
        if 'indicator' not in self.tree.identify_element(event.x, event.y):
            self.tree.selection_remove(*self.tree.selection())
            self.tree.selection_set(self.tree.identify_row(event.y))

    def update_style(self):
        theme = f"{CONFIG.get('General', 'theme').capitalize()} Theme"
        self.tree.tag_configure('empty', foreground=CONFIG.get(theme, 'disabledfg'))

    def set_callback(self, fct):
        """Set click callback."""
        self.callback = fct

    def set_file(self, filename, file):
        """Set analyzed file."""
        if file != self.file:
            self.interrupt()
            if file in self._records:
                data = self._records[file]
                self.populate(data['msgs'], data['stats'], data['label'])
            else:
                self.clear()
        self.filename.configure(text=filename)
        self.file = file

    def clear(self):
        """Clear display."""
        self.tree.delete(*self.tree.get_children())
        self.tree.insert('', 'end', 'global_ev', text='Global evaluation:', tag='heading')

    def _on_select(self, event):
        sel = self.tree.selection()
        if self.callback is not None and sel:
            val = self.tree.item(sel[0], 'values')
            if val:
                self.callback(*val)

    def _check_finished(self):
        if self._process.is_alive():
            self._check_id = self.after(100, self._check_finished)
        else:
            msgs = []
            while not self._queue.empty():
                msgs.append(self._queue.get(False))
            try:
                stats, old_stats = msgs.pop(-1)
            except ValueError:
                pass
            else:
                try:
                    prev = '(previous run: {global_note:.1f})'.format(**old_stats)
                except (ValueError, KeyError):
                    prev = ''
                try:
                    ev = 'Global evaluation: {global_note:.1f} '.format(**stats)
                except (ValueError, KeyError):
                    ev = 'Global evaluation: ?? '
                label = f'{ev} {prev}'
                self.populate(msgs, stats, label)
                nbs = {elt: stats.get(elt, 0)
                       for elt in ['error', 'warning', 'convention', 'refactor']}
                self._records[self.file] = {'msgs': msgs, 'stats': nbs, 'label': label}
            self.stop_btn.state(['disabled'])
            self.start_btn.state(['!disabled'])
            self.busy(False)

    def analyze(self):
        """Start code analysis."""
        if self.file:
            self.start_btn.state(['disabled'])
            self.busy(True)
            self.stop_btn.state(['!disabled'])
            self.update_idletasks()
            self._queue, self._process = pylint_check(self.file)
            self._check_finished()

    def interrupt(self):
        """Interrupt code analysis."""
        if self._process:
            self._process.kill()

    def populate(self, msgs, stats, label):
        """Display analysis results."""
        self.tree.delete(*self.tree.get_children())
        self.tree.insert('', 'end', 'global_ev', text=label, tag='heading')
        max_width = max(self.min_width, self.font_heading.measure(label) + 20)

        for elt in ['error', 'warning', 'convention', 'refactor', 'info']:
            nb = stats.get(elt, 0)
            tags = () if nb else ('empty',)
            self.tree.insert('', 'end', elt, text=f' {elt.capitalize()} ({nb})',
                             open=True, image=f'img_{elt}', tags=tags)

        for mtype, msg, line_nb in msgs:
            message = msg.splitlines()[0]
            max_width = max(max_width, self.font.measure(message) + 40)
            line = f'{line_nb}.0'
            if mtype not in self.tree.get_children():
                self.tree.insert('', 'end', mtype, text=f' {mtype.capitalize()} ({nb})',
                                 open=True, image='img_menu_dummy')
            self.tree.insert(mtype, 'end', text=message, values=(line,))
        self.tree.column('#0', width=max_width, minwidth=max_width)





