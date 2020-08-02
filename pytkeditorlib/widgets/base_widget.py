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


Base widgets
"""
from tkinter import BooleanVar, TclError
from tkinter.ttk import Frame

from pytkeditorlib.gui_utils import Notebook
from pytkeditorlib.utils.constants import CONFIG


class BaseWidget(Frame):
    """Base class for the side widgets."""
    def __init__(self, master, name, **kw):
        kw.setdefault('padding', 2)
        Frame.__init__(self, master, **kw)

        self.name = name

        self.menu = None

        self.visible = BooleanVar(self)
        self.visible.trace_add('write', self._visibility_trace)

    def traversal_next(self, event):
        """Display next widget."""
        self.master.traversal_next(event)
        return "break"

    def traversal_prev(self, event):
        """Display previous widget."""
        self.master.traversal_prev(event)
        return "break"

    def update_style(self):
        """Update widget style."""
        pass  # to be overriden in subclass

    def busy(self, busy):
        """Toggle busy cursor."""
        if busy:
            self.configure(cursor='watch')
        else:
            self.configure(cursor='')

    def _visibility_trace(self, *args):
        """Callback when widget's visibilty changes."""
        visible = self.visible.get()
        if visible:
            self.master.add(self)
            self.master.select(self)
        else:
            self.master.hide(self)
        CONFIG.set(self.name, 'visible', str(visible))
        CONFIG.save()

    def set_order(self, order):
        """Write widget's order in config."""
        CONFIG.set(self.name, 'order', str(order))


class WidgetNotebook(Notebook):
    """Notebook containing the widgets"""

    def __init__(self, master, **kw):
        Notebook.__init__(self, master, tabmenu=False, closecommand=self.close, **kw)
        self.bind('<Destroy>', self._save_order)
        self._manager = master
        self.bind("<Control-Tab>", self.traversal_next)
        self.bind('<Shift-Control-ISO_Left_Tab>', self.traversal_prev)

    @property
    def manager(self):
        """Notebook's manager, namely the GUI element in which it is displayed."""
        return self._manager

    @manager.setter
    def manager(self, new_manager):
        if self._visible_tabs:
            try:
                self._manager.forget(self)
            except TclError:
                pass
            new_manager.insert('end', self, weight=2)
        self._manager = new_manager

    def traversal_next(self, event):
        """Display next tab."""
        self.select_next(True)
        return "break"

    def traversal_prev(self, event):
        """Display previous tab."""
        self.select_prev(True)
        return "break"

    def _save_order(self, event):
        for i, tab in enumerate(self._visible_tabs):
            self._tabs[tab].set_order(i)
        CONFIG.save()

    def _popup_menu(self, event, tab):
        widget = self._tabs[tab]
        if widget.menu is not None:
            widget.menu.tk_popup(event.x_root, event.y_root)

    def hide(self, tab_id):
        Notebook.hide(self, tab_id)
        if not self._visible_tabs:
            self.manager.forget(self)

    def add(self, widget, **kwargs):
        if not self._visible_tabs:
            self.manager.insert('end', self, weight=1)
        return Notebook.add(self, widget, **kwargs)

    def close(self, tab_id):
        """Hide tab."""
        tab = self.index(tab_id)
        if tab in self._visible_tabs:
            self._tabs[tab].visible.set(False)

    def select_first_tab(self):
        """Display first tab."""
        if self._visible_tabs:
            self.select(self._visible_tabs[0])

    def select(self, tab_id=None):
        tab = Notebook.select(self, tab_id)
        if tab:
            return tab
        self._tabs[self.index(tab_id)].visible.set(True)
