#! /usr/bin/python3
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


Menu with several columns if too long
"""
from tkinter import Menu


class LongMenu(Menu):
    def __init__(self, master=None, max_height=20, **kwargs):
        Menu.__init__(self, master, **kwargs)
        self.max_height = max_height

    def add(self, itemType, cnf={}, **kw):
        end = self.index('end')
        if end is None:
            end = 1
        else:
            end += 2  # end is the index of the last item starting from 0 so the
                      # nb of items after the addition is end + 2
        if not end % self.max_height:
            kw['columnbreak'] = True
        Menu.add(self, itemType, cnf, **kw)
