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


Rich text widget
"""
from tkinter import Text, TclError


class RichText(Text):
    """Rich text widget with bracket autoclosing and matching."""
    def __init__(self, master, **kw):
        Text.__init__(self, master, **kw)

        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

        self.syntax_highlighting_tags = []
        self.autoclose = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}

        self.bind("<FocusOut>", self.clear_highlight)
        self.bind("<Control-w>", lambda e: "break")
        self.bind("<Control-h>", lambda e: "break")
        self.bind("<Control-b>", lambda e: "break")
        self.bind("<Control-f>", lambda e: "break")
        self.bind("<Control-t>", lambda e: "break")

    def _proxy(self, *args):
        """Proxy between tkinter widget and tcl interpreter."""
        cmd = (self._orig,) + args
        insert_moved = (args[0] in ("insert", "delete") or args[0:3] == ("mark", "set", "insert"))
        if insert_moved:
            self.clear_highlight()

        try:
            result = self.tk.call(cmd)
        except TclError:
            return

        if insert_moved:
            self.event_generate("<<CursorChange>>", when="tail")
            self.find_matching_par()

        return result

    def update_style(self, fg, bg, selectfg, selectbg, font, syntax_highlighting):
        self.configure(fg=fg, bg=bg, font=font,
                       selectbackground=selectbg,
                       selectforeground=selectfg,
                       inactiveselectbackground=selectbg,
                       insertbackground=fg)
        # reset tags
        tags = list(self.tag_names())
        tags.remove('sel')
        tag_props = {key: '' for key in self.tag_configure('sel')}
        for tag in tags:
            self.tag_configure(tag, **tag_props)
        self.tag_configure('bold', font=font + ('bold',))
        self.tag_configure('italic', font=font + ('italic',))

        # syntax highlighting
        for tag, opts in syntax_highlighting.items():
            props = tag_props.copy()
            props.update(opts)
            self.tag_configure(tag, **props)

        self.tag_raise('sel')

    def clear_highlight(self, event=None):
        self.tag_remove('matching_brackets', '1.0', 'end')
        self.tag_remove('unmatched_bracket', '1.0', 'end')

    def find_matching_par(self, event=None):
        """Highlight matching brackets."""
        char = self.get('insert-1c')
        if char in ['(', '{', '[']:
            return self.find_closing_par(char)
        elif char in [')', '}', ']']:
            return self.find_opening_par(char)
        else:
            return False

    def find_closing_par(self, char):
        """Highlight the closing bracket of CHAR if it is on the same line."""
        close_char = self.autoclose[char]
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

    def find_opening_par(self, char):
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


