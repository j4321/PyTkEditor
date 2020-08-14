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
import logging

from pygments import lex
from pygments.lexers.python import Python3Lexer
from tkcolorpicker.functions import rgb_to_hsv, hexa_to_rgb
import jedi

from pytkeditorlib.utils.constants import CONFIG, load_style, get_screen
from pytkeditorlib.dialogs.tooltip import Tooltip
from pytkeditorlib.dialogs.complistbox import CompListbox


class RichText(Text):
    """Rich text widget with bracket matching and syntax highlighting."""

    def __init__(self, master, wtype, **kw):
        """
        Create RichText widget.

        Arguments:

            master: widget's master
            wtype: widget type, namely "Editor" or "Console"
            kw: Text keyword arguments
        """
        Text.__init__(self, master, **kw)
        self.wtype = wtype

        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

        self.syntax_highlighting_tags = []
        self.lexer = Python3Lexer()   # lexer for syntax highlighting

        self.autoclose = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}

        self.bind("<FocusOut>", self._on_focus_out)
        # remove unwanted Text bindings
        self.bind("<Control-w>", lambda e: "break")
        self.bind("<Control-h>", lambda e: "break")
        self.bind("<Control-b>", lambda e: "break")
        self.bind("<Control-f>", lambda e: "break")
        self.bind("<Control-t>", lambda e: "break")

        self.update_style()

    def _on_focus_out(self, event):
        self.clear_highlight()

    def _proxy(self, *args):
        """Proxy between tkinter widget and tcl interpreter."""
        cmd = (self._orig,) + args
        insert_moved = (args[0] in ("insert", "delete") or args[0:3] == ("mark", "set", "insert"))
        if insert_moved:
            self.clear_highlight()

        try:
            result = self.tk.call(cmd)
        except TclError:
            logging.exception('TclError')
            return

        if insert_moved:
            self.event_generate("<<CursorChange>>", when="tail")
            self.find_matching_par()

        return result

    def _parse(self, text, start):
        """Apply syntax highlighting to text at index start"""
        data = text
        while data and data[0] == '\n':
            start = self.index('%s+1c' % start)
            data = data[1:]
        self.mark_set('range_start', start)
        for t in self.syntax_highlighting_tags:
            self.tag_remove(t, start, "range_start +%ic" % len(data))
        for token, content in lex(data, self.lexer):
            self.mark_set("range_end", "range_start + %ic" % len(content))
            for t in token.split():
                self.tag_add(str(t), "range_start", "range_end")
            if str(token) == 'Token.Comment.Cell':
                col = int(self.index("range_end").split(".")[1])
                if col < 79:
                    self.insert("range_end", " " * (79 - col), "Token.Comment.Cell")
            self.mark_set("range_start", "range_end")

    def _load_style(self):
        """Load new widget style."""
        font = (CONFIG.get("General", "fontfamily"),
                CONFIG.getint("General", "fontsize"))
        bg, highlight_bg, syntax_highlighting = load_style(CONFIG.get(self.wtype, 'style'))
        fg = syntax_highlighting.get('Token.Name', {}).get('foreground', 'black')

        self.syntax_highlighting_tags = list(syntax_highlighting.keys())
        syntax_highlighting['Token.Generic.Prompt'].setdefault('foreground', fg)

        # --- syntax highlighting
        syntax_highlighting['prompt'] = syntax_highlighting['Token.Generic.Prompt']
        syntax_highlighting['output'] = {'foreground': fg}
        syntax_highlighting['highlight_find'] = {'background': highlight_bg}
        syntax_highlighting['Token.Comment.Cell'] = syntax_highlighting['Token.Comment'].copy()
        syntax_highlighting['Token.Comment.Cell']['underline'] = True

        # bracket matching:  fg;bg;font formatting
        mb = CONFIG.get(self.wtype, 'matching_brackets', fallback='#00B100;;bold').split(';')
        syntax_highlighting['matching_brackets'] = {'foreground': mb[0],
                                                    'background': mb[1],
                                                    'font': font + tuple(mb[2:])}
        umb = CONFIG.get(self.wtype, 'unmatched_bracket', fallback='#FF0000;;bold').split(';')
        syntax_highlighting['unmatched_bracket'] = {'foreground': umb[0],
                                                    'background': umb[1],
                                                    'font': font + tuple(umb[2:])}
        return fg, bg, highlight_bg, font, syntax_highlighting

    def _update_style(self, fg, bg, selectfg, selectbg, font, syntax_highlighting):
        """Update widget style."""
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

    def update_style(self):
        """Load and update widget style."""
        fg, bg, highlight_bg, font, syntax_highlighting = self._load_style()
        if rgb_to_hsv(*hexa_to_rgb(highlight_bg))[2] > 50:
            selectfg = 'black'
        else:
            selectfg = 'white'
        self._update_style(fg, bg, selectfg, highlight_bg, font, syntax_highlighting)

    def clear_highlight(self, event=None):
        """Clear matching brackets highlighting."""
        self.tag_remove('matching_brackets', '1.0', 'end')
        self.tag_remove('unmatched_bracket', '1.0', 'end')

    def find_matching_par(self, event=None):
        """Highlight matching brackets."""
        char = self.get('insert-1c')
        if char in ['(', '{', '[']:
            return self.find_closing_par(char)
        if char in [')', '}', ']']:
            return self.find_opening_par(char)
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


class RichEditor(RichText):
    """Rich text editor widget with bracket autoclosing and hints."""

    def __init__(self, master, wtype, **kw):
        RichText.__init__(self, master, wtype, **kw)

        # tooltip for argument hints
        self._tooltip = Tooltip(self, title='Arguments',
                                titlestyle='args.title.tooltip.TLabel')
        self._tooltip.withdraw()
        self._tooltip.bind('<FocusOut>', lambda e: self._tooltip.withdraw())
        # autocompletion dialog
        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)

        self.bind("<ButtonPress>", self._on_btn_press)
        self.bind("<apostrophe>", self.auto_close_string)
        self.bind("<quotedbl>", self.auto_close_string)
        self.bind('<parenleft>', self._on_left_par)
        self.bind("<bracketleft>", self.auto_close)
        self.bind("<braceleft>", self.auto_close)
        self.bind("<parenright>", self.close_brackets)
        self.bind("<bracketright>", self.close_brackets)
        self.bind("<braceright>", self.close_brackets)
        self.bind("<Escape>", self._on_escape)
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<KeyRelease-Left>", self._on_key_release_left_right)
        self.bind("<KeyRelease-Right>", self._on_key_release_left_right)
        self.bind("<Down>", self.on_down)
        self.bind("<Up>", self.on_up)
        self.bind("<Control-i>", self.inspect)

    def _on_key_release(self, event):
        pass  # to be overriden in subclass

    def _on_key_release_left_right(self, event):
        self._comp.withdraw()

    def _on_escape(self, event):
        self._comp.withdraw()
        self._tooltip.withdraw()

    def _on_focus_out(self, event):
        self._comp.withdraw()
        self._tooltip.withdraw()
        self.clear_highlight()

    def _on_btn_press(self, event):
        self.clear_highlight()
        self._comp.withdraw()
        self._tooltip.withdraw()
        self.edit_separator()

    def _on_left_par(self, event):
        self._args_hint()
        self.auto_close(event)
        self._tooltip.deiconify()
        return "break"

    def _comp_sel(self):
        """Select completion."""
        txt = self._comp.get()
        self._comp.withdraw()
        self.insert('insert', txt)

    def _comp_generate(self):
        """Generate autocompletion list."""
        return []  # to be overriden in subclass

    def _comp_display(self):
        """Display autocompletion."""
        self._comp.withdraw()
        comp = self._comp_generate()
        if len(comp) == 1:
            self.insert('insert', comp[0].complete)
        elif len(comp) > 1:
            self._comp.update_completion(comp)
            xb, yb, w, h = self.bbox('insert')
            xr = self.winfo_rootx()
            yr = self.winfo_rooty()
            hcomp = self._comp.winfo_reqheight()
            screen = get_screen(xr, yr)
            y = yr + yb + h
            x = xr + xb
            if y + hcomp > screen[3]:
                y = yr + yb - hcomp
            self._comp.geometry('+%i+%i' % (x, y))
            self._comp.deiconify()

    def _jedi_script(self):
        """Return jedi script and row, column number."""
        row, col = map(int, self.index('insert').split('.'))
        return jedi.Script(self.get('1.0', 'end')), row, col

    def _args_hint(self, event=None):
        self._tooltip.configure(text='')
        index = self.index('insert')
        try:
            script, row, col = self._jedi_script()
            res = script.infer(row, col)
        except Exception:
            logging.exception('Jedi Error')   # jedi raised an exception
            return
        self.mark_set('insert', index)
        if res:
            try:
                args = res[-1].docstring().splitlines()[0]
            except Exception:
                logging.exception('Jedi Error') # usually caused by an exception raised in Jedi
                return
            if args in ['', 'NoneType()']:
                return
            self._tooltip.configure(text=args)
            xb, yb, w, h = self.bbox('insert')
            xr = self.winfo_rootx()
            yr = self.winfo_rooty()
            ht = self._tooltip.winfo_reqheight()
            screen = get_screen(xr, yr)
            y = yr + yb + h
            x = xr + xb
            if y + ht > screen[3]:
                y = yr + yb - ht

            self._tooltip.geometry('+%i+%i' % (x, y))
            self._tooltip.deiconify()

    def inspect(self, event=None):
        if self.tag_ranges('sel'):
            obj = self.get('sel.first linestart', 'sel.first wordend').split()[-1]
        else:
            obj = self.get('insert wordstart', 'insert wordend')
        if obj[0].isalpha():
            self.inspect_obj = obj, self.wtype
            self.event_generate('<<Inspect>>')
        return "break"

    def on_down(self, event):
        """Down arrow."""
        if self._comp.winfo_ismapped():
            self._comp.sel_next()
            return "break"

    def on_up(self, event):
        """Up arrow."""
        if self._comp.winfo_ismapped():
            self._comp.sel_prev()
            return "break"

    def close_brackets(self, event):
        """Close brackets."""
        if self.get('insert') == event.char:
            self.mark_set('insert', 'insert+1c')
        else:
            self.insert('insert', event.char, 'Token.Punctuation')
        self.find_opening_par(event.char)
        return 'break'

    def auto_close(self, event):
        """Autoclose brackets."""
        sel = self.tag_ranges('sel')
        if sel:
            text = self.get('sel.first', 'sel.last')
            index = self.index('sel.first')
            self.insert('sel.first', event.char)
            self.insert('sel.last', self.autoclose[event.char])
            self.mark_set('insert', 'sel.last+1c')
            self.tag_remove('sel', 'sel.first', 'sel.last')
            self._parse(event.char + text + self.autoclose[event.char], index)
        else:
            self.insert('insert', event.char, ['Token.Punctuation', 'matching_brackets'])
            if not self.find_matching_par():
                self.tag_remove('unmatched_bracket', 'insert-1c')
                self.insert('insert', self.autoclose[event.char],
                            ['Token.Punctuation', 'matching_brackets'])
                self.mark_set('insert', 'insert-1c')
        self.edit_separator()
        return 'break'

    def auto_close_string(self, event):
        """Autoclose quotes."""
        sel = self.tag_ranges('sel')
        if sel:
            text = self.get('sel.first', 'sel.last')
            if len(text.splitlines()) > 1:
                char = event.char * 3
            else:
                char = event.char
            self.insert('sel.first', char)
            self.insert('sel.last', char)
            self.mark_set('insert', 'sel.last+%ic' % (len(char)))
            self.tag_remove('sel', 'sel.first', 'sel.last')
        elif self.get('insert') == event.char:
            self.mark_set('insert', 'insert+1c')
        else:
            self.insert('insert', event.char * 2)
            self.mark_set('insert', 'insert-1c')
        self.edit_separator()
        return 'break'



