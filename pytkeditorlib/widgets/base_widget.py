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
from tkinter import BooleanVar, Text, TclError
from tkinter.ttk import Frame

from tkcolorpicker.functions import rgb_to_hsv, hexa_to_rgb

from pytkeditorlib.gui_utils import Notebook
from pytkeditorlib.utils.constants import CONFIG, load_style, ANSI_COLORS_DARK, \
    ANSI_COLORS_LIGHT


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


class RichText(Text):
    def __init__(self, master, **kw):
        Text.__init__(self, master, **kw)

        self._syntax_highlighting_tags = []
        self.update_style()
        self._autoclose = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}

        self.bind("<KeyRelease-Up>", self._find_matching_par)
        self.bind("<KeyRelease-Down>", self._find_matching_par)
        self.bind("<KeyRelease-Left>", self._find_matching_par)
        self.bind("<KeyRelease-Right>", self._find_matching_par)
        self.bind("<KeyRelease>", self._clear_highlight)
        self.bind("<FocusOut>", self._clear_highlight)
        self.bind("<ButtonPress>", self._clear_highlight)
        self.bind("<ButtonRelease-1>", self._find_matching_par)

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
        # bracket matching:  fg;bg;font formatting
        mb = CONFIG.get('Console', 'matching_brackets', fallback='#00B100;;bold').split(';')
        opts = {'foreground': mb[0], 'background': mb[1], 'font': FONT + tuple(mb[2:])}
        self.tag_configure('matching_brackets', **opts)
        umb = CONFIG.get('Console', 'unmatched_bracket', fallback='#FF0000;;bold').split(';')
        opts = {'foreground': umb[0], 'background': umb[1], 'font': FONT + tuple(umb[2:])}
        self.tag_configure('unmatched_bracket', **opts)
        # --- ansi tags
        self.tag_configure('foreground default', foreground='')
        self.tag_configure('background default', background='')
        self.tag_configure('underline', underline=True)
        self.tag_configure('overstrike', overstrike=True)
        for c in ANSI_COLORS_LIGHT:
            self.tag_configure('foreground ' + c, foreground=c)
            self.tag_configure('background ' + c, background=c)
        for c in ANSI_COLORS_DARK:
            self.tag_configure('foreground ' + c, foreground=c)
            self.tag_configure('background ' + c, background=c)
        self.tag_configure('bold', font=FONT + ('bold',))
        self.tag_configure('italic', font=FONT + ('italic',))

        self.tag_raise('sel')

    def _clear_highlight(self, event=None):
        self.tag_remove('matching_brackets', '1.0', 'end')
        self.tag_remove('unmatched_bracket', '1.0', 'end')

    def _find_matching_par(self, event=None):
        """Highlight matching brackets."""
        char = self.get('insert-1c')
        if char in ['(', '{', '[']:
            return self._find_closing_par(char)
        elif char in [')', '}', ']']:
            return self._find_opening_par(char)
        else:
            return False

    def _find_closing_par(self, char):
        """Highlight the closing bracket of CHAR if it is on the same line."""
        close_char = self._autoclose[char]
        index = 'insert'
        close_index = self.search(close_char, 'insert', 'end')
        stack = 1
        while stack > 0 and close_index:
            stack += self.get(index, close_index).count(char) - 1
            index = close_index + '+1c'
            close_index = self.search(close_char, index, 'end')
        if stack == 0:
            self.tag_add('matching_brackets', 'insert-1c')
            self.tag_add('matching_brackets', index + '-1c')
            return True
        else:
            self.tag_add('unmatched_bracket', 'insert-1c')
            return False

    def _find_opening_par(self, char):
        """Highlight the opening bracket of CHAR if it is on the same line."""
        open_char = '(' if char == ')' else ('{' if char == '}' else '[')
        index = 'insert-1c'
        open_index = self.search(open_char, 'insert', '1.0', backwards=True)
        stack = 1
        while stack > 0 and open_index:
            stack += self.get(open_index + '+1c', index).count(char) - 1
            index = open_index
            open_index = self.search(open_char, index, '1.0', backwards=True)
        if stack == 0:
            self.tag_add('matching_brackets', 'insert-1c')
            self.tag_add('matching_brackets', index)
            return True
        else:
            self.tag_add('unmatched_bracket', 'insert-1c')
            return False


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


