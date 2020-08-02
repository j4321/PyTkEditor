# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2019 Juliette Monsel <j_4321 at protonmail dot com>

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


Entry with history in the form of a Combobox
"""
from tkinter import ttk


class EntryHistory(ttk.Combobox):
    """Entry with history."""

    def __init__(self, master=None, max_length=20, **kw):
        ttk.Combobox.__init__(self, master, **kw)

        self.max_length = max_length

    def add_to_history(self, value):
        """Add value to history."""
        values = list(self['values'])
        try:
            if values[0] == value:
                return
            values.remove(value)
        except (IndexError, ValueError):
            pass
        values.insert(0, value)
        self['values'] = values[:self.max_length]
