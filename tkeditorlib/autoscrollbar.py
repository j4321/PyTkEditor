#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from tkinter import ttk


class AutoHideScrollbar(ttk.Scrollbar):
    """Scrollbar that automatically hides when not needed."""
    def __init__(self, *args, **kwargs):
        """
        Create the scrollbar.

        Take the same arguments as ttk.Scrollbar
        """
        ttk.Scrollbar.__init__(self, *args, **kwargs)
        self._pack_kw = {}
        self._place_kw = {}
        self._layout = 'place'
        self._timer = 0
        self._visible = False
        self._incr_timer()

    def set(self, lo, hi):
        if self._timer > 10:
            if float(lo) <= 0.0 and float(hi) >= 1.0:
                if self._layout == 'place':
                    self.place_forget()
                elif self._layout == 'pack':
                    self.pack_forget()
                else:
                    self.grid_remove()
                if self._visible:
                    self._timer = 0
                self._visible = False
            else:
                if self._layout == 'place':
                    self.place(**self._place_kw)
                elif self._layout == 'pack':
                    self.pack(**self._pack_kw)
                else:
                    self.grid()
                if not self._visible:
                    self._timer = 0
                self._visible = True
        ttk.Scrollbar.set(self, lo, hi)

    def _incr_timer(self):
        self._timer += 1
        self.after(100, self._incr_timer)

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
