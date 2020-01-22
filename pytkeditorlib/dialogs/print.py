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

Print dialog
"""
import tkinter as tk
from tkinter import ttk
import os
from tempfile import mkstemp

from tkfilebrowser import asksaveasfilename
import cups

from pytkeditorlib.dialogs import askyesno

PAPER_SIZES = ['A4', 'Letter', 'A0', 'A1', 'A2', 'A3', 'A5', 'A6', 'A7',
               'A8', 'A9', 'A10', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
               'B8', 'B9', 'B10', 'Legal', 'Executive', 'Tabloid', 'Statement',
               'Halfletter', 'Folio', 'Flsa', 'Flse', 'Note', 'C0', 'C1', 'C2',
               'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'Juniorlegal',
               'Memo', 'Governmentletter', 'Governmentlegal', 'Ledger']


class PrintDialog(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master, class_=master.winfo_class(), padx=10)
        self.title("Print")

        try:
            self.conn = cups.Connection()
        except RuntimeError:
            self.printers = {}
        else:
            self.printers = self.conn.getPrinters()

        # --- Printer
        frame_printer = ttk.Labelframe(self, text='Printer:')
        printers = list(self.printers) + ['Print to file (PDF)']
        self.printer = ttk.Combobox(frame_printer, exportselection=False, values=printers, state="readonly")
        self._location = ttk.Label(frame_printer)
        self._type = ttk.Label(frame_printer)
        output = ttk.Frame(frame_printer)
        self.output = ttk.Entry(output)
        self.output.insert(0, os.path.join(os.path.expanduser('~'), 'output.pdf'))
        self._browse_btn = ttk.Button(output, text='...', padding=0, width=2,
                                      command=self._browse)
        self._browse_btn.pack(side='right')
        self.output.pack(side='left', fill='x')

        ttk.Label(frame_printer, text='Name:').grid(row=0, column=0,
                                                    sticky='e', padx=4, pady=4)
        self.printer.grid(row=0, column=1, sticky='w', padx=4, pady=4)
        ttk.Label(frame_printer, text='Location:').grid(row=1, column=0,
                                                        sticky='e', padx=4, pady=4)
        self._location.grid(row=1, column=1, sticky='w', padx=4, pady=4)
        ttk.Label(frame_printer, text='Type:').grid(row=2, column=0,
                                                    sticky='e', padx=4, pady=4)
        self._type.grid(row=2, column=1, sticky='w', padx=4, pady=4)
        ttk.Label(frame_printer, text='Output file:').grid(row=3, column=0,
                                                           sticky='e', padx=4, pady=4)
        output.grid(row=3, column=1, sticky='w', padx=4, pady=4)

        if self.printers:
            self.printer.set(tuple(self.printers.keys())[0])
            self.output.state(('disabled',))
            self._browse_btn.state(('disabled',))
        else:
            self.printer.set('Print to file (PDF)')
        self.select_printer()

        # --- Options
        frame_options = ttk.Labelframe(self, text='Options:')
        ttk.Label(frame_options, text='Paper size:').grid(row=0, column=0, sticky='e',
                                                          padx=4, pady=4)
        ttk.Label(frame_options, text='Layout:').grid(row=1, column=0, sticky='e',
                                                      padx=4, pady=4)
        ttk.Label(frame_options, text='Margins:').grid(row=2, column=0, sticky='ne',
                                                       padx=4, pady=4)

        # --- --- margins
        frame_margins = ttk.Frame(frame_options)
        self.margins = {}

        r = 0
        c = 0
        for side in ["top", "left", "bottom", "right"]:
            sp = ttk.Spinbox(frame_margins, format="%.1f", from_=0, to=10, width=4, justify="right")
            self.margins[side] = sp
            sp.set("1.0")
            ttk.Label(frame_margins, text=side).grid(row=r, column=c, sticky="e",
                                                     padx=(8, 4), pady=4)
            sp.grid(row=r, column=c + 1)
            ttk.Label(frame_margins, text="cm").grid(row=r, column=c + 2, sticky="w",
                                                     padx=(4, 8), pady=4)
            c += 3
            if c == 6:
                c = 0
                r += 1

        self.display_linenos = tk.BooleanVar(self, True)
        self.display_title = tk.BooleanVar(self, True)
        self.paper_size = ttk.Combobox(frame_options, exportselection=False, state="readonly", values=PAPER_SIZES)
        self.paper_size.set(PAPER_SIZES[0])
        self.layout = ttk.Combobox(frame_options, exportselection=False, state="readonly", values=['Portrait', 'Landscape'])
        self.layout.set('Portrait')

        self.paper_size.grid(row=0, column=1, sticky='w', padx=4, pady=4)
        self.layout.grid(row=1, column=1, sticky='w', padx=4, pady=4)
        frame_margins.grid(row=2, column=1, sticky='w', padx=4, pady=4)
        ttk.Checkbutton(frame_options, variable=self.display_linenos,
                        text='Display line numbers').grid(row=3, columnspan=2, sticky='w',
                                                          padx=4, pady=4)
        ttk.Checkbutton(frame_options, variable=self.display_title,
                        text='Display filename as title').grid(row=4, columnspan=2, sticky='w',
                                                               padx=4, pady=4)
        # -- validation
        frame_btns = ttk.Frame(self)
        ttk.Button(frame_btns, text='Cancel', command=self.destroy).pack(side='left', padx=4, pady=4)
        ttk.Button(frame_btns, text='Print', command=self.print).pack(side='left', padx=4, pady=4)

        frame_printer.pack(side='top', fill='x', pady=4)
        frame_options.pack(side='top', fill='x', pady=4)
        frame_btns.pack(side='top', anchor='center')
        self.printer.bind("<<ComboboxSelected>>", self.select_printer)
        self.layout.bind("<<ComboboxSelected>>", self._clear_sel)
        self.paper_size.bind("<<ComboboxSelected>>", self._clear_sel)
        self.grab_set()

    def _browse(self):
        initialdir, initialfile = os.path.split(self.output.get())
        filename = asksaveasfilename(self, initialfile=initialfile,
                                     initialdir=initialdir,
                                     defaultext='.pdf',
                                     filetypes=[('PDF', '*.pdf'),
                                                ('All files', '*')])
        if filename:
            self.output.delete(0, 'end')
            self.output.insert(0, filename)

    @staticmethod
    def _clear_sel(event=None):
        event.widget.selection_clear()

    def select_printer(self, event=None):
        self.printer.selection_clear()
        printer = self.printer.get()
        if printer == 'Print to file (PDF)':
            self.output.state(('!disabled',))
            self._browse_btn.state(('!disabled',))
        else:
            self.output.state(('disabled',))
            self._browse_btn.state(('disabled',))
        props = self.printers.get(printer, {})
        self._location.configure(text=props.get('printer-location', ''))
        self._type.configure(text=props.get('printer-type', ''))

    def print(self):
        print_options = {}
        printer = self.printer.get()
        print_options['title'] = self.display_title.get()
        print_options['linenos'] = self.display_linenos.get()
        print_options['page-size'] = self.paper_size.get().lower()
        print_options['orientation'] = self.layout.get().lower()
        for side, sp in self.margins.items():
            try:
                margin = float(sp.get())
            except ValueError:
                margin = 1
            print_options[f"margin-{side}"] = f"{margin}cm"
        if printer == 'Print to file (PDF)':
            filename = self.output.get()
            if os.path.exists(filename):
                ans = askyesno("Warning",
                               f"The file {filename} already exists. Do you want to replace it?",
                               icon="warning", parent=self)
                if not ans:
                    return
            if filename:
                self.master.export_to_pdf(filename, **print_options)
        else:
            filename = mkstemp(suffix=".pdf")
            self.master.export_to_pdf(filename, **print_options)
            self.conn.printFile(printer, filename)
            os.remove(filename)
        self.destroy()
