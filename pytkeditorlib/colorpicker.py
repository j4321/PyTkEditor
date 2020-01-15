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

from tkcolorpicker import colorpicker


class ColorPicker(colorpicker.ColorPicker):
    """Color picker dialog."""

    def __init__(self, parent=None, color=(255, 0, 0), alpha=False,
                 title="Color Chooser"):
        colorpicker.ColorPicker.__init__(self, parent, color, alpha, title)

        # --- validation
        button_frame = self.grid_slaves(4, 0)[0]
        ttk.Button(button_frame, text="Insert",
                   command=self.insert).pack(side="right", padx=10)
        self.grab_release()

    def insert(self):
        rgb, hsv, hexa = self.square.get()
        if self.alpha_channel:
            hexa = self.hexa.get()
            rgb += (self.alpha.get(),)
        self.color = rgb, hsv, hexa
        self.event_generate("<<ColorSelected>>")

    def ok(self):
        self.insert()
        self.destroy()
