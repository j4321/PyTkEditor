#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import jedi
from jedi import settings
from pygments import lex
from pygments.lexers import Python3Lexer
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import re
from tkeditorlib.autoscrollbar import AutoHideScrollbar
from tkeditorlib.constants import IM_WARN, IM_ERR, SYNTAX_HIGHLIGHTING, IM_CLOSE
from tkeditorlib.complistbox import CompListbox
from tkeditorlib.tooltip import TooltipTextWrapper
from tkeditorlib.filebar import FileBar


settings.case_insensitive_completion = False


class Editor(ttk.Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master, class_='Editor')

        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self._im_close = tk.PhotoImage(master=self, file=IM_CLOSE)

        self._syntax_icons = {'warning': tk.PhotoImage(master=self, file=IM_WARN),
                              'error': tk.PhotoImage(master=self, file=IM_ERR)}

        self._paste = False
        self._autoclose = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        self._search_count = tk.IntVar(self)

        self._comp = CompListbox(self)
        self._comp.set_callback(self._comp_sel)

        style = ttk.Style(self)
        bg = style.lookup('TFrame', 'background', default='light grey')
        select_fg = style.lookup('TEntry', 'selectforeground', ['focus'])
        select_bg = style.lookup('TEntry', 'selectbackground', ['focus'])

        self.text = tk.Text(self, fg="black", bg="white", undo=True,
                            autoseparators=True,
                            relief='flat', borderwidth=0,
                            highlightthickness=0, wrap='none',
                            selectbackground=select_bg,
                            inactiveselectbackground=select_bg,
                            selectforeground=select_fg,
                            insertbackground='black', font="DejaVu\ Sans\ Mono 10")
        self.sep = tk.Frame(self.text, bg='gray60')
        self.sep.place(y=0, relheight=1, x=632, width=1)

        self.line_nb = tk.Text(self, width=1, cursor='arrow',
                               bg=bg, selectbackground=bg,
                               fg='gray40', selectforeground='gray40',
                               highlightthickness=0, relief='flat',
                               font="DejaVu\ Sans\ Mono 10")
        self.line_nb.insert('1.0', '1')
        self.line_nb.tag_configure('right', justify='right')
        self.line_nb.tag_add('right', '1.0', 'end')
        self.line_nb.configure(state='disabled')

        self.syntax_checks = tk.Text(self, width=2, cursor='arrow',
                                     state='disabled',
                                     bg=bg, selectbackground=bg,
                                     fg='gray40', selectforeground='gray40',
                                     highlightthickness=0, relief='flat',
                                     font="DejaVu\ Sans\ Mono 10")
        self.textwrapper = TooltipTextWrapper(self.syntax_checks, background='light yellow',
                                              foreground='black', title='Syntax')

        sx = AutoHideScrollbar(self, orient='horizontal', command=self.text.xview)
        sy = AutoHideScrollbar(self, orient='vertical', command=self.yview)
        self.filebar = FileBar(self, self, width=10, bg=bg)
        self.text.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        self.line_nb.configure(yscrollcommand=sy.set)
        self.syntax_checks.configure(yscrollcommand=sy.set)

        # --- search and replace
        self.frame_search = ttk.Frame(self, padding=2)
        self.frame_search.columnconfigure(1, weight=1)
        self.entry_search = ttk.Entry(self.frame_search)
        self.entry_search.bind('<Return>', self.search)
        self.entry_search.bind('<Control-r>', self.replace)
        self.entry_replace = ttk.Entry(self.frame_search)
        self.entry_replace.bind('<Control-f>', self.find)
        search_buttons = ttk.Frame(self.frame_search)
#        ttk.Button(search_buttons, text='▲', padding=0, width=2,
#                   command=lambda: self.search(backwards=True)).pack(side='left', padx=2, pady=4)
#        ttk.Button(search_buttons, text='▼', padding=0, width=2,
#                   command=lambda: self.search(forwards=True)).pack(side='left', padx=2, pady=4)
        ttk.Button(search_buttons, style='Up.TButton', padding=0,
                   command=lambda: self.search(backwards=True)).pack(side='left', padx=2, pady=4)
        ttk.Button(search_buttons, style='Down.TButton', padding=0,
                   command=lambda: self.search(forwards=True)).pack(side='left', padx=2, pady=4)
        self.case_sensitive = ttk.Checkbutton(search_buttons, text='aA')
        self.case_sensitive.state(['selected', '!alternate'])
        self.case_sensitive.pack(side='left', padx=2, pady=4)
        self.regexp = ttk.Checkbutton(search_buttons, text='regexp')
        self.regexp.state(['!selected', '!alternate'])
        self.regexp.pack(side='left', padx=2, pady=4)
        self.full_word = ttk.Checkbutton(search_buttons, text='[-]')
        self.full_word.state(['!selected', '!alternate'])
        self.full_word.pack(side='left', padx=2, pady=4)
        self.replace_buttons = ttk.Frame(self.frame_search)
        ttk.Button(self.replace_buttons, text='Replace', padding=0,
                   command=self.replace_sel).pack(side='left', padx=2, pady=4)
        ttk.Button(self.replace_buttons, text='Replace and Find', padding=0,
                   command=self.replace_find).pack(side='left', padx=2, pady=4)
        ttk.Button(self.replace_buttons, text='Replace All', padding=0,
                   command=self.replace_all).pack(side='left', padx=2, pady=4)

        frame_find = ttk.Frame(self.frame_search)
        ttk.Button(frame_find, padding=0,
                   command=lambda: self.frame_search.grid_remove(),
                   image=self._im_close, style='close.TButton').pack(side='left')
        ttk.Label(frame_find, text='Find:').pack(side='right')
        # ------- placement
        frame_find.grid(row=0, column=0, padx=2, pady=4, sticky='ew')
        self.label_replace = ttk.Label(self.frame_search, text='Replace by:')
        self.label_replace.grid(row=1, column=0, sticky='e', pady=4, padx=4)
        self.entry_search.grid(row=0, column=1, sticky='ew', pady=4, padx=2)
        self.entry_replace.grid(row=1, column=1, sticky='ew', pady=4, padx=2)
        search_buttons.grid(row=0, column=2, sticky='w')
        self.replace_buttons.grid(row=1, column=2, sticky='w')

        # --- grid
        self.text.grid(row=0, column=2, sticky='ewns')
        self.line_nb.grid(row=0, column=1, sticky='ns')
        self.syntax_checks.grid(row=0, column=0, sticky='ns')
        sx.grid(row=1, column=2, sticky='ew')
        sy.grid(row=0, column=4, sticky='ns')
        self.filebar.grid(row=0, column=3, sticky='ns')
        ttk.Separator(self, orient='horizontal').grid(row=2, column=0, columnspan=5, sticky='ew')
        self.frame_search.grid(row=3, column=0, columnspan=5, sticky='ew')
        self.frame_search.grid_remove()

        #  --- syntax highlighting
        for tag, opts in SYNTAX_HIGHLIGHTING.items():
            self.text.tag_configure(tag, selectforeground=select_fg, **opts)

        # --- bindings
        self.text.bind("<KeyRelease>", self.on_key)
        self.text.bind("<ButtonPress>", self._on_press)
        self.text.bind("<Down>", self.on_down)
        self.text.bind("<Up>", self.on_up)
        self.text.bind("<<Paste>>", self.on_paste)
        self.text.bind("<apostrophe>", self.auto_close_string)
        self.text.bind("<quotedbl>", self.auto_close_string)
        self.text.bind("<parenleft>", self.auto_close)
        self.text.bind("<bracketleft>", self.auto_close)
        self.text.bind("<braceleft>", self.auto_close)
        self.text.bind("<parenright>", self.close_brackets)
        self.text.bind("<bracketright>", self.close_brackets)
        self.text.bind("<braceright>", self.close_brackets)
        self.text.bind("<Control-z>", self.undo)
        self.text.bind("<Control-y>", self.redo)
        self.text.bind("<Control-d>", self.duplicate_lines)
        self.text.bind("<Control-k>", self.delete_lines)
        self.text.bind("<Control-a>", self.select_all)
        self.text.bind("<Return>", self.on_return)
        self.text.bind("<BackSpace>", self.on_backspace)
        self.text.bind("<Tab>", self.on_tab)
        self.text.bind("<ISO_Left_Tab>", self.unindent)
        self.text.bind('<Control-f>', self.find)
        self.text.bind('<Control-r>', self.replace)
        self.text.bind('<Control-l>', self.goto_line)
        self.text.bind('<Control-e>', self.toggle_comment)
        self.text.bind('<Configure>', self.filebar.update_highlight)
        self.text.bind('<4>', self._on_b4)
        self.line_nb.bind('<4>', self._on_b4)
        self.text.bind('<5>', self._on_b5)
        self.line_nb.bind('<5>', self._on_b5)
        self.bind('<FocusOut>', lambda e: self._comp.withdraw())

        self.text.focus_set()
        self.text.edit_modified(0)

    def _on_press(self, event):
        if self._comp.winfo_ismapped():
            self._comp.withdraw()

    def _on_b4(self, event):
        self.yview('scroll', -3, 'units')
        return "break"

    def _on_b5(self, event):
        self.yview('scroll', 3, 'units')
        return "break"

    def undo(self, event=None):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass
        finally:
            self.update_nb_line()
            self.parse_all()
        return "break"

    def redo(self, event=None):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass
        finally:
            self.update_nb_line()
            self.parse_all()
        return "break"

    def parse(self, text, start):
        data = text
        while data and '\n' == data[0]:
            start = self.text.index('%s+1c' % start)
            data = data[1:]
        self.text.mark_set('range_start', start)
        for t in SYNTAX_HIGHLIGHTING:
            self.text.tag_remove(t, start, "range_start +%ic" % len(data))
        for token, content in lex(data, Python3Lexer()):
            self.text.mark_set("range_end", "range_start + %ic" % len(content))
            for t in token.split():
                self.text.tag_add(str(t), "range_start", "range_end")
            self.text.mark_set("range_start", "range_end")

    def parse_all(self):
        self.parse(self.text.get('1.0', 'end'), '1.0')

    def on_down(self, event):
        if self._comp.winfo_ismapped():
            self._comp.sel_next()
            return "break"
        else:
            self.parse(self.text.get('insert linestart', 'insert lineend'), 'insert linestart')

    def on_up(self, event):
        if self._comp.winfo_ismapped():
            self._comp.sel_prev()
            return "break"
        else:
            self.parse(self.text.get('insert linestart', 'insert lineend'), 'insert linestart')

    def on_key(self, event):
        key = event.keysym
        if key in ('Return',) + tuple(self._autoclose):
            return
        elif self._comp.winfo_ismapped():
            if event.char.isalnum():
                self._comp_display()
            elif key not in ['Tab', 'Down', 'Up']:
                self._comp.withdraw()
        elif (event.char in [' ', ':', ',', ';', '(', '[', '{', ')', ']', '}'] or
              key in ['BackSpace', 'Left', 'Right']):
            self.parse(self.text.get("insert linestart", "insert lineend"),
                       "insert linestart")
        elif key == 'x':
            self.update_nb_line()

    def select_all(self, event):
        self.text.tag_add('sel', '1.0', 'end')
        return "break"

    def auto_close(self, event):
        sel = self.text.tag_ranges('sel')
        if sel:
            text = self.text.get('sel.first', 'sel.last')
            index = self.text.insert('sel.first')
            self.text.insert('sel.first', event.char)
            self.text.insert('sel.last', self._autoclose[event.char])
            self.text.mark_set('insert', 'sel.last+1c')
            self.text.tag_remove('sel', 'sel.first', 'sel.last')
            self.parse(event.char + text + self._autoclose[event.char], index)
        else:
            self.text.insert('insert', event.char + self._autoclose[event.char], 'Token.Punctuation')
            self.text.mark_set('insert', 'insert-1c')
        return 'break'

    def auto_close_string(self, event):
        sel = self.text.tag_ranges('sel')
        if sel:
            text = self.text.get('sel.first', 'sel.last')
            if len(text.splitlines()) > 1:
                char = event.char * 3
            else:
                char = event.char
            self.text.insert('sel.first', char)
            self.text.insert('sel.last', char)
            self.text.mark_set('insert', 'sel.last+%ic' % (len(char)))
            self.text.tag_remove('sel', 'sel.first', 'sel.last')
        elif self.text.get('insert') == event.char:
            self.text.mark_set('insert', 'insert+1c')
        else:
            self.text.insert('insert', event.char * 2)
            self.text.mark_set('insert', 'insert-1c')
        self.parse_all()
        return 'break'

    def close_brackets(self, event):
        if self.text.get('insert') == event.char:
            self.text.mark_set('insert', 'insert+1c')
        else:
            self.text.insert('insert', event.char, 'Token.Punctuation')
        return 'break'

    def on_paste(self, event):
        self._paste = True
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete(*sel)
        txt = self.clipboard_get()
        self.text.insert("insert", txt)
        self.update_nb_line()
        self.parse_all()
        self.see('insert')
        return "break"

    def toggle_comment(self, event):
        sel = self.text.tag_ranges('sel')
        if sel:
            lines = self.text.get('sel.first linestart', 'sel.last lineend').splitlines()
            index = self.text.index('sel.first linestart')
            self.text.delete('sel.first linestart', 'sel.last lineend')
        else:
            lines = self.text.get('insert linestart', 'insert lineend').splitlines()
            index = self.text.index('insert linestart')
            self.text.delete('insert linestart', 'insert lineend')

        for i, line in enumerate(lines):
            res = re.match(r'^( )*# ', line)
            if res:
                lines[i] = res.group()[:-2] + line[len(res.group()):]
            elif not re.match(r'^( )*$', line):
                lines[i] = re.match(r'( )*', line).group() + '# ' + line.lstrip(' ')
        txt = '\n'.join(lines)
        self.text.insert(index, txt)
        self.parse(txt, index)

    def duplicate_lines(self, event):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            index = 'sel.last'
            line = self.text.get('sel.first linestart', 'sel.last lineend')
        else:
            index = 'insert'
            line = self.text.get('insert linestart', 'insert lineend')
        start = self.text.index('%s lineend +1c' % index)
        self.text.insert('%s lineend' % index, '\n%s' % line)
        self.parse(line, start)
        self.update_nb_line()
        return "break"

    def delete_lines(self, event):
        self.text.edit_separator()
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete('sel.first linestart', 'sel.last lineend +1c')
        else:
            self.text.delete('insert linestart', 'insert lineend +1c')
        self.update_nb_line()
        return "break"

    def _get_indent(self):
        line_nb, col = [int(i) for i in str(self.text.index('insert')).split('.')]
        if line_nb == 1:
            return '    '
        line_nb -= 1
        prev_line = self.text.get('%i.0' % line_nb, '%i.end' % line_nb)
        line = self.text.get('insert linestart', 'insert lineend')
        res = re.match(r'( )*', line)
        if res.span()[-1] < col:
            return '    '
        indent_prev = len(re.match(r'( )*', prev_line).group())
        indent = len(res.group())
        if indent < indent_prev:
            return ' ' * (indent_prev - indent)
        else:
            return '    '

    def on_tab(self, event):
        if self._comp.winfo_ismapped():
            self._comp_sel()
            return "break"

        sel = self.text.tag_ranges('sel')
        if sel:
            start = str(self.text.index('sel.first'))
            end = str(self.text.index('sel.last'))
            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0]) + 1
            for line in range(start_line, end_line):
                self.text.insert('%i.0' % line, '    ')
        else:
            txt = self.text.get('insert-1c')
            if not txt.isalnum() and txt != '.':
                self.text.insert('insert', self._get_indent())
            else:
                self._comp_display()
        return "break"

    def _comp_display(self):
        index = self.text.index('insert wordend')
        if index[-2:] != '.0':
#            self.text.mark_set('insert', 'insert wordend')
            line = self.text.get('insert wordstart', 'insert wordend')
            print(line)
            i = len(line) - 1
            while i > -1 and line[i] in self._autoclose.values():
                i -= 1
            print(self.text.get('insert wordstart','insert wordstart +%ic' % (i + 1)))
            self.text.mark_set('insert', 'insert wordstart +%ic' % (i + 1))
        row, col = str(self.text.index('insert')).split('.')
        script = jedi.Script(self.text.get('1.0', 'end'), int(row), int(col), 'completion.py')
        comp = script.completions()
        self._comp.withdraw()
        if len(comp) == 1:
            self.text.insert('insert', comp[0].complete)
        elif len(comp) > 1:
            self._comp.update(comp)
            x, y, w, h = self.text.bbox('insert')
            xr = self.text.winfo_rootx()
            yr = self.text.winfo_rooty()
            self._comp.geometry('+%i+%i' % (xr + x, yr + y + h))
            self._comp.deiconify()

    def _comp_sel(self):
        txt = self._comp.get()
        self._comp.withdraw()
        self.text.insert('insert', txt)

    def on_return(self, event):
        if self._comp.winfo_ismapped():
            self._comp_sel()
            return "break"

        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete('sel.first', 'sel.last')
        index = self.text.index('insert linestart')
        t = self.text.get("insert linestart", "insert")
        self.parse(t, index)
        indent = re.match(r'( )*', t).group()
        colon = re.search(r':( )*$', t)
        if colon:
            if len(colon.group()) > 1:
                self.text.delete('insert-%ic' % (len(colon.group()) - 1), 'insert')
            indent = indent + '    '

        self.text.insert('insert', '\n' + indent)
        self.update_nb_line()
        # update whole syntax highlighting
        self.parse_all()
        self.see('insert')
        return "break"

    def update_nb_line(self):
        row = int(str(self.text.index('end')).split('.')[0]) - 1
        row_old = int(str(self.line_nb.index('end')).split('.')[0]) - 1
        self.line_nb.configure(state='normal')
        self.syntax_checks.configure(state='normal')
        if row_old < row:
            self.syntax_checks.insert('end', '\n')
            self.line_nb.insert('end',
                                '\n' + '\n'.join([str(i) for i in range(row_old + 1, row + 1)]),
                                'right')

        elif row_old > row:
            self.line_nb.delete('%i.0' % (row + 1), 'end')
            self.syntax_checks.delete('%i.0' % (row + 1), 'end')
        self.line_nb.configure(width=len(str(row)), state='disabled')
        self.syntax_checks.configure(state='disabled')
        self.filebar.update_highlight()

    def on_backspace(self, event):
        txt = event.widget
        sel = self.text.tag_ranges('sel')
        if sel:
            self.text.delete('sel.first', 'sel.last')
        else:
            linestart = txt.get('insert linestart', 'insert')
            if re.search(r'    $', linestart):
                txt.delete('insert-4c', 'insert')
            elif txt.get('insert-1c', 'insert+1c') in [c1 + c2 for c1, c2 in self._autoclose.items()]:
                txt.delete('insert-1c', 'insert+1c')
            else:
                txt.delete('insert-1c')
        self.update_nb_line()
        return "break"

    def unindent(self, event):
        txt = event.widget
        sel = txt.tag_ranges('sel')
        if sel:
            start = str(txt.index('sel.first'))
            end = str(txt.index('sel.last'))
        else:
            start = str(txt.index('insert'))
            end = str(txt.index('insert'))
        start_line = int(start.split('.')[0])
        end_line = int(end.split('.')[0]) + 1
        for line in range(start_line, end_line):
            if txt.get('%i.0' % line, '%i.4' % line) == '    ':
                txt.delete('%i.0' % line, '%i.4' % line)
        return "break"

    def yview(self, *args):
        self.line_nb.yview(*args)
        self.syntax_checks.yview(*args)
        res = self.text.yview(*args)
        if args:
            self.filebar.update_highlight()
        return res

    def find(self, event=None):
        self.label_replace.grid_remove()
        self.entry_replace.grid_remove()
        self.replace_buttons.grid_remove()
        self.frame_search.grid()
        self.entry_search.focus_set()
        sel = self.text.tag_ranges('sel')
        if sel:
            self.entry_search.delete(0, 'end')
            self.entry_search.insert(0, self.text.get('sel.first', 'sel.last'))
        self.entry_search.selection_range(0, 'end')
        return "break"

    def replace(self, event=None):
        self.entry_replace.grid()
        self.label_replace.grid()
        self.replace_buttons.grid()
        self.frame_search.grid()
        self.entry_search.focus_set()
        sel = self.text.tag_ranges('sel')
        if sel:
            self.entry_search.delete(0, 'end')
            self.entry_search.insert(0, self.text.get('sel.first', 'sel.last'))
        self.entry_search.selection_range(0, 'end')
        return "break"

    def replace_sel(self, notify_no_match=True):
        pattern = self.entry_search.get()
        new_text = self.entry_replace.get()
        sel = self.text.tag_ranges('sel')
        if not sel:
            self.search(notify_no_match=notify_no_match)
            return False
        else:
            sel_text = self.text.get('sel.first', 'sel.last')
            regexp = 'selected' in self.regexp.state()
            if ((regexp and re.search('^' + pattern + '$', sel_text)) or
               (not regexp and pattern == sel_text)):
                    self.text.replace('sel.first', 'sel.last', new_text)
                    return True
            else:
                self.search(notify_no_match=notify_no_match)
                return False

    def replace_find(self):
        if self.replace_sel():
            self.search()

    def replace_all(self):
        res = True
        self.text.mark_set('insert', '1.0')
        # replace all occurences in text
        while res:
            self.search(notify_no_match=False, stopindex='end')
            res = self.replace_sel(notify_no_match=False)

    def search(self, event=None, backwards=False, forwards=True,
               notify_no_match=True, **kw):
        pattern = self.entry_search.get()
        full_word = 'selected' in self.full_word.state()
        options = {'regexp': 'selected' in self.regexp.state(),
                   'nocase': 'selected' not in self.case_sensitive.state(),
                   'count': self._search_count}
        options.update(kw)
        if backwards:
            options['backwards'] = True
        else:  # forwards
            options['forwards'] = True

        res = self.text.search(pattern, 'insert', **options)

        if res and full_word:
            index = 'start'
            end_word = self.text.index(res + ' wordend')
            end_res = self.text.index(res + '+%ic' % self._search_count.get())

            while index and index != res and end_word != end_res:
                index = self.text.search(pattern, end_res, **options)
                end_word = self.text.index(index + ' wordend')
                end_res = self.text.index(index + '+%ic' % self._search_count.get())

            if index != 'start':
                res = index

        self.text.tag_remove('sel', '1.0', 'end')
        if res:
            self.text.tag_add('sel', res, '%s+%ic' % (res, self._search_count.get()))
            if forwards:
                self.text.mark_set('insert', '%s+%ic' % (res, self._search_count.get()))
            else:
                self.text.mark_set('insert', '%s-1c' % (res))
            self.see(res)
        else:
            if notify_no_match:
                messagebox.showinfo("Search complete", "No match found")

    def goto_line(self, event):

        def goto(event):
            try:
                line = int(e.get())
                self.see('%i.0' % line)
                self.text.mark_set('insert', '%i.0' % line)
            except ValueError:
                pass
            finally:
                top.destroy()

        top = tk.Toplevel(self)
        top.transient(self)
        top.grab_set()
        top.title('Go to')

        ttk.Label(top, text='Line: ').pack(side='left', padx=4, pady=4)
        e = ttk.Entry(top, width=5)
        e.pack(side='left', padx=4, pady=4)
        e.focus_set()
        e.bind('<Return>', goto)

    def goto_item(self, start, end):
        self.see(start)
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_add('sel', start, end)

    def get(self, strip=True):
        txt = self.text.get('1.0', 'end')
        if strip:
            index = self.text.index('insert')
            print(index)
            txt = txt.splitlines()
            for i, line in enumerate(txt):
                txt[i] = line[:re.search(r'( )*$', line).span()[0]]
            txt = '\n'.join(txt)
            self.text.delete('1.0', 'end')
            self.text.insert('1.0', txt)
            self.parse_all()
            self.text.mark_set('insert', index)
            self.see('insert')
        return txt

    def get_end(self):
        return str(self.text.index('end'))

    def delete(self, index1, index2=None):
        self.text.delete(index1, index2=index2)
        self.update_nb_line()
        self.parse_all()

    def insert(self, index, text):
        self.text.insert(index, text)
        self.update_nb_line()
        self.parse_all()

    def see(self, index):
        self.text.see(index)
        self.line_nb.see(index)
        self.syntax_checks.see(index)

    def show_syntax_issues(self, results):
        self.syntax_checks.configure(state='normal')
        self.syntax_checks.delete('1.0', 'end')
        self.textwrapper.reset()
        self.filebar.clear()
        end = int(str(self.text.index('end')).split('.')[0]) - 1
        self.syntax_checks.insert('end', '\n' * end)
        for line, (category, msg) in results.items():
            self.syntax_checks.image_create('%i.0' % line,
                                            image=self._syntax_icons[category])
            self.syntax_checks.tag_add(str(line), '%i.0' % line)
            self.filebar.add_mark(line, category)
            self.textwrapper.add_tooltip(str(line), msg)
        self.syntax_checks.configure(state='disabled')

