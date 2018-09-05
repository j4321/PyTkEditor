#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
Combobox with autocompletion
"""

from tkinter import TclError
from tkinter.ttk import Combobox


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
            self['values'] = l
            if l:
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
