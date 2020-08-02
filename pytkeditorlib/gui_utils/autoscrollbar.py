#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2019 Juliette Monsel <j_4321 at protonmail dot com>
based on code by Fredrik Lundh copyright 1998
<http://effbot.org/zone/tkinter-autoscrollbar.htm>

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


Auto hiding scrollbar
"""
from tkinter import ttk


class AutoHideScrollbar(ttk.Scrollbar):
    """Scrollbar that automatically hides when not needed."""
    def __init__(self, *args, threshold=2, **kwargs):
        """
        Create the scrollbar.

        Take the same arguments as ttk.Scrollbar
        """
        ttk.Scrollbar.__init__(self, *args, **kwargs)
        self._pack_kw = {}
        self._place_kw = {}
        self._layout = 'place'
        self.timer = threshold + 1
        self.threshold = threshold
        self._visible = False
        self._incr_timer()

    def set(self, first, last):
        if self.timer > self.threshold:
            if float(first) <= 0.0 and float(last) >= 1.0:
                if self._layout == 'place':
                    self.place_forget()
                elif self._layout == 'pack':
                    self.pack_forget()
                else:
                    self.grid_remove()
                if self._visible:
                    self.timer = 0
                self._visible = False
            else:
                if self._layout == 'place':
                    self.place(**self._place_kw)
                elif self._layout == 'pack':
                    self.pack(**self._pack_kw)
                else:
                    self.grid()
                if not self._visible:
                    self.timer = 0
                self._visible = True
        ttk.Scrollbar.set(self, first, last)

    def _incr_timer(self):
        self.timer += 1
        self.after(10, self._incr_timer)

    def _get_info(self, layout):
        """Alternative to pack_info and place_info in case of bug."""
        info = str(self.tk.call(layout, 'info', self._w)).split("-")
        dic = {}
        for i in info:
            if i:
                key, val = i.strip().split()
                dic[key] = val
        return dic

    def place(self, **kw):
        ttk.Scrollbar.place(self, **kw)
        try:
            self._place_kw = self.place_info()
        except TypeError:
            # bug in some tkinter versions
            self._place_kw = self._get_info("place")
        self._layout = 'place'

    def pack(self, **kw):
        ttk.Scrollbar.pack(self, **kw)
        try:
            self._pack_kw = self.pack_info()
        except TypeError:
            # bug in some tkinter versions
            self._pack_kw = self._get_info("pack")
        self._layout = 'pack'

    def grid(self, **kw):
        ttk.Scrollbar.grid(self, **kw)
        self._layout = 'grid'
