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


Combobox with autocompletion
"""
from tkinter import TclError, Listbox
from tkinter.ttk import Combobox, Frame, Entry

from .autoscrollbar import AutoHideScrollbar


class AutoCompleteCombobox(Combobox):
    def __init__(self, master=None, allow_other_values=False,
                 additional_validation=None, **kwargs):
        """
        Create a AutoCompleteCombobox, i.e. a Combobox with autocompletion.

        Keyword arguments:
         - the same arguments as a Comboxbox but the validatecommand is not taken into account
         - allow_other_values (boolean): whether the user is allowed to enter values not in the list
         - additional_validation (function): if 'allow_other_values' is True and
             the inserted text is not in the list, apply 'additional_validation' to
             what will be the content of the entry after the change.
             Therefore 'additional_validation' must be a function taking as argument
             a string (the text in the entry if the change is allowed) and returning
             a boolean depending on whether the change should be allowed.
        """
        Combobox.__init__(self, master, **kwargs)
        self._allow_other_values = allow_other_values
        if additional_validation is None:
            self._additional_validation = lambda txt: True
        else:
            self._additional_validation = additional_validation
        self._validate = self.register(self.validate)
        self.configure(validate='key',
                       validatecommand=(self._validate, "%d", "%S", "%i", "%s", "%P"))
        # navigate on keypress in the dropdown
        self.tk.eval("""
proc ComboListKeyPressed {w key} {
        if {[string length $key] > 1 && [string tolower $key] != $key} {
                return
        }

        set cb [winfo parent [winfo toplevel $w]]
        set text [string map [list {[} {\[} {]} {\]}] $key]
        if {[string equal $text ""]} {
                return
        }

        set values [$cb cget -values]
        set x [lsearch -glob -nocase $values $text*]
        if {$x < 0} {
                return
        }

        set current [$w curselection]
        if {$current == $x && [string match -nocase $text* [lindex $values [expr {$x+1}]]]} {
                incr x
        }

        $w selection clear 0 end
        $w selection set $x
        $w activate $x
        $w see $x
}

set popdown [ttk::combobox::PopdownWindow %s]
bind $popdown.f.l <KeyPress> [list ComboListKeyPressed %%W %%K]
""" % (self))

    def validate(self, action, modif, pos, prev_txt, new_txt):
        """Complete the text in the entry with values from the combobox."""
        try:
            sel = self.selection_get()
            txt = prev_txt.replace(sel, '')
        except TclError:
            txt = prev_txt
        if action == "0":
            txt = txt[:int(pos)] + txt[int(pos) + 1:]
            return True
        else:
            values = self.cget('values')
            txt = txt[:int(pos)] + modif + txt[int(pos):]
            l = [i for i in values if i[:len(txt)] == txt]
            if l:
                i = values.index(l[0])
                self.current(i)
                index = self.index("insert")
                self.delete(0, "end")
                self.insert(0, l[0].replace("\ ", " "))
                self.selection_range(index + 1, "end")
                self.icursor(index + 1)
                return True
            else:
                return self._allow_other_values and (self._additional_validation(new_txt))

    def __getitem__(self, key):
        return self.cget(key)

    def keys(self):
        keys = Combobox.keys(self)
        keys.append('allow_other_values')
        return keys

    def cget(self, key):
        if key == 'allow_other_values':
            return self._allow_other_values
        else:
            return Combobox.cget(self, key)

    def config(self, dic={}, **kwargs):
        self.configure(dic={}, **kwargs)

    def configure(self, dic={}, **kwargs):
        dic2 = {}
        dic2.update(dic)
        dic2.update(kwargs)
        self._allow_other_values = dic2.pop('allow_other_values', self._allow_other_values)
        Combobox.config(self, dic2)


class AutoCompleteCombobox2(AutoCompleteCombobox):
    def __init__(self, master=None, allow_other_values=False,
                 additional_validation=None, completevalues=[],
                 **kwargs):
        """
        Create a AutoCompleteCombobox, i.e. a Combobox with autocompletion whose
        listbox only contains the items matching the content of the entry.

        Keyword arguments:
         - the same arguments as a Comboxbox but the validatecommand is not taken into account
         - allow_other_values (boolean): whether the user is allowed to enter values not in the list
         - additional_validation (function): if 'allow_other_values' is True and
             the inserted text is not in the list, apply 'additional_validation' to
             what will be the content of the entry after the change.
             Therefore 'additional_validation' must be a function taking as argument
             a string (the text in the entry if the change is allowed) and returning
             a boolean depending on whether the change should be allowed.
        """
        kwargs.setdefault('values', completevalues)
        AutoCompleteCombobox.__init__(self, master,
                                      allow_other_values=allow_other_values,
                                      additional_validation=additional_validation,
                                      **kwargs)
        self.complete_values = completevalues

    def validate(self, action, modif, pos, prev_txt, new_txt):
        """Complete the text in the entry with values from the combobox."""
        try:
            sel = self.selection_get()
            txt = prev_txt.replace(sel, '')
        except TclError:
            txt = prev_txt
        if action == "0":
            txt = txt[:int(pos)] + txt[int(pos) + 1:]
            values = self.complete_values
            l = [i for i in values if i[:len(txt)] == txt]
            self['values'] = l
            return True
        else:
            values = self.cget('values')
            txt = txt[:int(pos)] + modif + txt[int(pos):]
            l = [i for i in values if i[:len(txt)] == txt]
            if l:
                self['values'] = l
                self.current(0)
                index = self.index("insert")
                self.delete(0, "end")
                self.insert(0, l[0].replace("\ ", " "))
                self.selection_range(index + 1, "end")
                self.icursor(index + 1)
                return True
            else:
                return self._allow_other_values and (self._additional_validation(new_txt))

    def set_completion_list(self, completevalues):
        self.complete_values = completevalues
        self['values'] = completevalues


class AutoCompleteEntryListbox(Frame):
    def __init__(self, master=None, completevalues=[], allow_other_values=False,
                 **kwargs):
        """
        Create a Entry + Listbox with autocompletion.

        Keyword arguments:
         - allow_other_values (boolean): whether the user is allowed to enter values not in the list
        """
        exportselection = kwargs.pop('exportselection', False)
        width = kwargs.pop('width', None)
        justify = kwargs.pop('justify', None)
        font = kwargs.pop('font', None)
        Frame.__init__(self, master, padding=4, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._allow_other_values = allow_other_values
        self._completevalues = completevalues
        self._validate = self.register(self.validate)
        self.entry = Entry(self, width=width, justify=justify, font=font,
                           validate='key', exportselection=exportselection,
                           validatecommand=(self._validate, "%d", "%S", "%i", "%s", "%P"))
        f = Frame(self, style='border.TFrame', padding=1)
        self.listbox = Listbox(f, width=width, justify=justify, font=font,
                               exportselection=exportselection, selectmode="browse",
                               highlightthickness=0, relief='flat')
        self.listbox.pack(fill='both', expand=True)
        scroll = AutoHideScrollbar(self, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.entry.grid(sticky='ew')
        f.grid(sticky='nsew')
        scroll.grid(row=1, column=1, sticky='ns')
        for c in self._completevalues:
            self.listbox.insert('end', c)

        self.listbox.bind('<<ListboxSelect>>', self.update_entry)
        self.listbox.bind("<KeyPress>", self.keypress)
        self.entry.bind("<Tab>", self.tab)
        self.entry.bind("<Down>", self.down)
        self.entry.bind("<Up>", self.up)
        self.entry.focus_set()

    def tab(self, event):
        """Move at the end of selected text on tab press."""
        self.entry = event.widget
        self.entry.selection_clear()
        self.entry.icursor("end")
        return "break"

    def keypress(self, event):
        """Select the first item which name begin by the key pressed."""
        key = event.char.lower()
        l = [i for i in self._completevalues if i[0].lower() == key]
        if l:
            i = self._completevalues.index(l[0])
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(i)
            self.listbox.see(i)
            self.update_entry()

    def up(self, event):
        """Navigate in the listbox with up key."""
        try:
            i = self.listbox.curselection()[0]
            self.listbox.selection_clear(0, "end")
            if i <= 0:
                i = len(self._completevalues)
            self.listbox.see(i - 1)
            self.listbox.select_set(i - 1)
        except (TclError, IndexError):
            self.listbox.selection_clear(0, "end")
            i = len(self._completevalues)
            self.listbox.see(i - 1)
            self.listbox.select_set(i - 1)
        self.listbox.event_generate('<<ListboxSelect>>')

    def down(self, event):
        """Navigate in the listbox with down key."""
        try:
            i = self.listbox.curselection()[0]
            self.listbox.selection_clear(0, "end")
            if i >= len(self._completevalues):
                i = -1
            self.listbox.see(i + 1)
            self.listbox.select_set(i + 1)
        except (TclError, IndexError):
            self.listbox.selection_clear(0, "end")
            self.listbox.see(0)
            self.listbox.select_set(0)
        self.listbox.event_generate('<<ListboxSelect>>')

    def validate(self, action, modif, pos, prev_txt, new_txt):
        """Complete the text in the entry with values."""
        try:
            sel = self.entry.selection_get()
            txt = prev_txt.replace(sel, '')
        except TclError:
            txt = prev_txt
        if action == "0":
            txt = txt[:int(pos)] + txt[int(pos) + 1:]
            return True
        else:
            txt = txt[:int(pos)] + modif + txt[int(pos):]
            l = [i for i in self._completevalues if i[:len(txt)] == txt]
            if l:
                i = self._completevalues.index(l[0])
                self.listbox.selection_clear(0, "end")
                self.listbox.selection_set(i)
                self.listbox.see(i)
                index = self.entry.index("insert")
                self.entry.delete(0, "end")
                self.entry.insert(0, l[0].replace("\ ", " "))
                self.entry.selection_range(index + 1, "end")
                self.entry.icursor(index + 1)
                return True
            else:
                return self._allow_other_values

    def __getitem__(self, key):
        return self.cget(key)

    def update_entry(self, event=None):
        """Update entry when an item is selected in the listbox."""
        try:
            sel = self.listbox.get(self.listbox.curselection()[0])
        except (TclError, IndexError):
            return
        self.entry.delete(0, "end")
        self.entry.insert(0, sel)
        self.entry.selection_clear()
        self.entry.icursor("end")
        self.event_generate('<<ItemSelect>>')

    def keys(self):
        keys = Combobox.keys(self)
        keys.append('allow_other_values')
        return keys

    def get(self):
        return self.entry.get()

    def cget(self, key):
        if key == 'allow_other_values':
            return self._allow_other_values
        elif key == 'completevalues':
            return self._completevalues
        else:
            return self.cget(self, key)

    def config(self, dic={}, **kwargs):
        self.configure(dic={}, **kwargs)

    def configure(self, dic={}, **kwargs):
        dic2 = {}
        dic2.update(dic)
        dic2.update(kwargs)
        self._allow_other_values = dic2.pop('allow_other_values', self._allow_other_values)
        self._completevalues = dic2.pop('completevalues', self._completevalues)
        self.config(self, dic2)
