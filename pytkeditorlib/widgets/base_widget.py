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


Base widget
"""
from tkinter import BooleanVar, Text
from tkinter.ttk import Frame

from tkcolorpicker.functions import rgb_to_hsv, hexa_to_rgb

from pytkeditorlib.gui_utils import Notebook
from pytkeditorlib.utils.constants import CONFIG, save_config, load_style


class BaseWidget(Frame):
    def __init__(self, master, name, **kw):
        kw.setdefault('padding', 2)
        Frame.__init__(self, master, **kw)

        self.name = name

        self.menu = None

        self.visible = BooleanVar(self)
        self.visible.trace_add('write', self._visibility_trace)

    def update_style(self):
        pass  # to be overriden in subclass

    def _visibility_trace(self, *args):
        visible = self.visible.get()
        if visible:
            self.master.add(self)
            self.master.select(self)
        else:
            self.master.hide(self)
        CONFIG.set(self.name, 'visible', str(visible))
        save_config()

    def set_order(self, order):
        CONFIG.set(self.name, 'order', str(order))


class RichText(Text):
    def __init__(self, master, **kw):
        Text.__init__(self, master, **kw)

        self._syntax_highlighting_tags = []
        self.update_style()

    def update_style(self):
        FONT = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        CONSOLE_BG, CONSOLE_HIGHLIGHT_BG, CONSOLE_SYNTAX_HIGHLIGHTING = load_style(CONFIG.get('Console', 'style'))
        CONSOLE_FG = CONSOLE_SYNTAX_HIGHLIGHTING.get('Token.Name', {}).get('foreground', 'black')

        if rgb_to_hsv(*hexa_to_rgb(CONSOLE_HIGHLIGHT_BG))[2] > 50:
            selectfg = 'black'
        else:
            selectfg = 'white'
        self._syntax_highlighting_tags = list(CONSOLE_SYNTAX_HIGHLIGHTING.keys())
        self.configure(fg=CONSOLE_FG, bg=CONSOLE_BG, font=FONT,
                       selectbackground=CONSOLE_HIGHLIGHT_BG,
                       selectforeground=selectfg,
                       inactiveselectbackground=CONSOLE_HIGHLIGHT_BG,
                       insertbackground=CONSOLE_FG)
        CONSOLE_SYNTAX_HIGHLIGHTING['Token.Generic.Prompt'].setdefault('foreground', CONSOLE_FG)
        # --- syntax highlighting
        tags = list(self.tag_names())
        tags.remove('sel')
        tag_props = {key: '' for key in self.tag_configure('sel')}
        for tag in tags:
            self.tag_configure(tag, **tag_props)
        for tag, opts in CONSOLE_SYNTAX_HIGHLIGHTING.items():
            props = tag_props.copy()
            props.update(opts)
            self.tag_configure(tag, **props)
        self.tag_configure('prompt', **CONSOLE_SYNTAX_HIGHLIGHTING['Token.Generic.Prompt'])
        self.tag_configure('output', foreground=CONSOLE_FG)
        self.tag_configure('highlight_find', background=CONSOLE_HIGHLIGHT_BG)
        self.tag_raise('sel')
        self.tag_raise('prompt')


class WidgetNotebook(Notebook):
    """Notebook containing the widgets"""

    def __init__(self, master, **kw):
        Notebook.__init__(self, master, tabmenu=False, closecommand=self.close, **kw)
        self.bind('<Destroy>', self._save_order)

    def _save_order(self, event):
        for i, tab in enumerate(self._visible_tabs):
            self._tabs[tab].set_order(i)
        save_config()

    def _popup_menu(self, event, tab):
        widget = self._tabs[tab]
        if widget.menu is not None:
            widget.menu.tk_popup(event.x_root, event.y_root)

    def hide(self, tabId):
        Notebook.hide(self, tabId)
        if not self._visible_tabs:
            self.master.forget(self)

    def add(self, child, **kw):
        if not self._visible_tabs:
            self.master.insert('end', self, weight=5)
        Notebook.add(self, child, **kw)

    def close(self, tabId):
        tab = self.index(tabId)
        if tab in self._visible_tabs:
            self._tabs[tab].visible.set(False)

    def select_first_tab(self):
        if self._visible_tabs:
            self.select(self._visible_tabs[0])
