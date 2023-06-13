# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2020 Juliette Monsel <j_4321 at protonmail dot com>

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

Jupyter kernel selection dialog
"""
from tkinter import Toplevel
from tkinter.ttk import Button, Label, Entry

from tkfilebrowser import askopenfilename

from pytkeditorlib.utils.constants import JUPYTER
if JUPYTER:
    from pytkeditorlib.utils.constants import jupyter_runtime_dir


class SelectKernel(Toplevel):
    """Kernel selection Toplevel."""
    def __init__(self, master):
        """Create the Toplevel to select an existing Jupyter kernel."""
        Toplevel.__init__(self, master, class_=master.winfo_class(), padx=10, pady=10)
        self.resizable(True, False)
        self.title("Select existing kernel")
        self.columnconfigure(0, minsize=22)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.selected_kernel = ''

        Label(self,
              text="Select the .json connection file or enter the existing kernel's id:").grid(columnspan=4,
                                                                                               sticky='w',
                                                                                               pady=4)
        self.entry = Entry(self, width=10)
        self.entry.grid(row=1, columnspan=3, sticky='ew', pady=4)
        self.entry.bind('<Return>', lambda e: self.validate())
        Button(self, text='...', width=2, padding=0,
               command=self.select_file).grid(row=1, column=3, sticky='sn', pady=4)

        Button(self, text='Ok', command=self.validate).grid(row=2, column=1,
                                                            padx=4, pady=4,
                                                            sticky='e')
        Button(self, text='Cancel', command=self.destroy).grid(row=2, column=2,
                                                               padx=4, pady=4,
                                                               sticky='w')
        self.transient(master)
        self.entry.focus_set()
        self.update_idletasks()
        self.grab_set()

    def validate(self):
        """Validate selection."""
        self.selected_kernel = self.entry.get()
        self.destroy()

    def select_file(self):
        """Choose file with filebrowser."""
        filename = askopenfilename(self, "Select connection file",
                                   initialdir=jupyter_runtime_dir(),
                                   defaultextension='.json',
                                   filetypes=[('JSON', '*.json'), ('All files', '*')])
        if filename:
            self.entry.delete(0, 'end')
            self.entry.insert(0, filename)
