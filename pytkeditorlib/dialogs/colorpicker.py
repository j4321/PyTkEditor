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

Colorpicker dialog
"""
from tkinter import ttk
import re

from tkcolorpicker import colorpicker


class ColorPicker(colorpicker.ColorPicker):
    """Color picker dialog."""

    def __init__(self, parent=None, color=None, alpha=False,
                 title="Color Chooser"):
        self._prefix = True
        try:
            match = re.match(r"^(#?)[0-9A-Fa-f]{6}$", color)
            if not match.groups()[0]:
                color = '#' + color
                self._prefix = False
        except (TypeError, AttributeError):
            color = '#FF0000'
            self._prefix = True
        colorpicker.ColorPicker.__init__(self, parent, color, alpha, title)

        # --- validation
        button_frame = self.grid_slaves(4, 0)[0]
        b_ok, b_close = button_frame.pack_slaves()
        b_close.configure(text='Close')
        b_ok.pack_forget()
        b_ok.pack(side="right", padx=10)
        ttk.Button(button_frame, text="Insert",
                   command=self.insert).pack(side="right", padx=10)
        self.grab_release()
        self.bind_all('<2>', lambda e: print(e.widget))

    def insert(self):
        rgb, hsv, hexa = self.square.get()
        if self.alpha_channel:
            hexa = self.hexa.get()
            rgb += (self.alpha.get(),)
        self.color = rgb, hsv, hexa
        self.event_generate("<<ColorSelected>>")

    def get_color(self):
        if self._prefix:
            # return HTML format with leading #
            return self.color[2]
        else:
            # return HTML format without leading #
            return self.color[2][1:]

    def ok(self):
        self.insert()
        self.destroy()
