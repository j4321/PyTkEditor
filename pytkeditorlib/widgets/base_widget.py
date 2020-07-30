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

from pygments import lex
from pygments.lexers import Python3Lexer
from tkcolorpicker.functions import rgb_to_hsv, hexa_to_rgb

from pytkeditorlib.gui_utils import Notebook, RichText
from pytkeditorlib.utils.constants import CONFIG, load_style


class BaseWidget(Frame):
    def __init__(self, master, name, **kw):
        kw.setdefault('padding', 2)
        Frame.__init__(self, master, **kw)

        self.name = name

        self.menu = None

        self.visible = BooleanVar(self)
        self.visible.trace_add('write', self._visibility_trace)

    def traversal_next(self, event):
        self.master.traversal_next(event)
        return "break"

    def traversal_prev(self, event):
        self.master.traversal_prev(event)
        return "break"

    def update_style(self):
        pass  # to be overriden in subclass

    def busy(self, busy):
        if busy:
            self.configure(cursor='watch')
        else:
            self.configure(cursor='')

    def _visibility_trace(self, *args):
        visible = self.visible.get()
        if visible:
            self.master.add(self)
            self.master.select(self)
        else:
            self.master.hide(self)
        CONFIG.set(self.name, 'visible', str(visible))
        CONFIG.save()

    def set_order(self, order):
        CONFIG.set(self.name, 'order', str(order))


class WidgetText(RichText):
    """RichText widget with syntax highlighting."""
    def __init__(self, master, **kw):
        RichText.__init__(self, master, **kw)
        self.update_style()

    def parse(self, start='1.0', end='end'):
        """Syntax highlighting between start and end."""
        data = self.get(start, end)
        while data and '\n' == data[0]:
            start = self.index('%s+1c' % start)
            data = data[1:]
        self.mark_set('range_start', start)
        for t in self.syntax_highlighting_tags:
            self.tag_remove(t, start, "range_start +%ic" % len(data))
        for token, content in lex(data, Python3Lexer()):
            self.mark_set("range_end", "range_start + %ic" % len(content))
            for t in token.split():
                self.tag_add(str(t), "range_start", "range_end")
            self.mark_set("range_start", "range_end")

    def update_style(self):
        FONT = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        CONSOLE_BG, CONSOLE_HIGHLIGHT_BG, CONSOLE_SYNTAX_HIGHLIGHTING = load_style(CONFIG.get('Console', 'style'))
        CONSOLE_FG = CONSOLE_SYNTAX_HIGHLIGHTING.get('Token.Name', {}).get('foreground', 'black')

        if rgb_to_hsv(*hexa_to_rgb(CONSOLE_HIGHLIGHT_BG))[2] > 50:
            selectfg = 'black'
        else:
            selectfg = 'white'
        self.syntax_highlighting_tags = list(CONSOLE_SYNTAX_HIGHLIGHTING.keys())
        CONSOLE_SYNTAX_HIGHLIGHTING['Token.Generic.Prompt'].setdefault('foreground', CONSOLE_FG)

        # --- syntax highlighting
        CONSOLE_SYNTAX_HIGHLIGHTING['prompt'] = CONSOLE_SYNTAX_HIGHLIGHTING['Token.Generic.Prompt']
        CONSOLE_SYNTAX_HIGHLIGHTING['output'] = {'foreground': CONSOLE_FG}
        CONSOLE_SYNTAX_HIGHLIGHTING['highlight_find'] = {'background': CONSOLE_HIGHLIGHT_BG}
        # bracket matching:  fg;bg;font formatting
        mb = CONFIG.get('Console', 'matching_brackets', fallback='#00B100;;bold').split(';')
        CONSOLE_SYNTAX_HIGHLIGHTING['matching_brackets'] = {'foreground': mb[0],
                                                            'background': mb[1],
                                                            'font': FONT + tuple(mb[2:])}
        umb = CONFIG.get('Console', 'unmatched_bracket', fallback='#FF0000;;bold').split(';')
        CONSOLE_SYNTAX_HIGHLIGHTING['unmatched_bracket'] = {'foreground': umb[0],
                                                            'background': umb[1],
                                                            'font': FONT + tuple(umb[2:])}

        RichText.update_style(self, CONSOLE_FG, CONSOLE_BG, selectfg,
                              CONSOLE_HIGHLIGHT_BG, FONT, CONSOLE_SYNTAX_HIGHLIGHTING)



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
        self.select_next(True)
        return "break"

    def traversal_prev(self, event):
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

    def hide(self, tabId):
        Notebook.hide(self, tabId)
        if not self._visible_tabs:
            self.manager.forget(self)

    def add(self, child, **kw):
        if not self._visible_tabs:
            self.manager.insert('end', self, weight=1)
        return Notebook.add(self, child, **kw)

    def close(self, tabId):
        tab = self.index(tabId)
        if tab in self._visible_tabs:
            self._tabs[tab].visible.set(False)

    def select_first_tab(self):
        if self._visible_tabs:
            self.select(self._visible_tabs[0])

    def select(self, tab_id=None):
        tab = Notebook.select(self, tab_id)
        if tab:
            return tab
        self._tabs[self.index(tab_id)].visible.set(True)



