#! /usr/bin/python3
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


Splash
"""
from tkinter import Tk, PhotoImage, TclError, Frame
from tkinter import ttk
import os

from constants import IMAGES, ANIM_LOADING, CONFIG, get_screen, PIDFILE


class Splash(Tk):
    def __init__(self, **kw):
        Tk.__init__(self, **kw)
        try:
            self.attributes('-type', 'splash')
        except TclError:
            self.overrideredirect(True)
        x1, y1, x2, y2 = get_screen(*self.winfo_pointerxy())
        x = (x1 + x2)//2
        y = (y1 + y2)//2
        self.geometry(f'+{x - 233}+{y - 144}')
        self.configure(padx=4, pady=4)

        self._im = PhotoImage(file=IMAGES['icon'], master=self)
        self._loading = [PhotoImage(f'img_anim_{i}', file=img, master=self)
                         for i, img in enumerate(ANIM_LOADING)]
        self._nb_img = len(ANIM_LOADING)
        # style
        style = ttk.Style()
        theme_name = CONFIG.get('General', 'theme').capitalize()
        theme2 = 'Light' if theme_name == 'Dark' else 'Dark'
        bg = CONFIG.get(f'{theme_name} Theme', 'bg')
        fg = CONFIG.get(f'{theme_name} Theme', 'fg')
        self.configure(bg=CONFIG.get(f'{theme2} Theme', 'bg'))
        style.configure('TLabel', background=bg, foreground=fg)
        style.configure('TProgressbar', background=bg, foreground=fg)
        frame = Frame(self, padx=150, pady=10, bg=bg)
        frame.pack(fill='both')

        ttk.Label(frame, text="PyTkEditor", image=self._im, compound='bottom',
                  font="TkDefaultFont 20").pack(pady=8, padx=8)
        self.loading = ttk.Label(frame, text='Loading', image='img_anim_0',
                                 compound='bottom')
        self.loading.pack(pady=8, padx=8)
        self._loading_id = self.after(1, self.anim)
        self._anim_index = 0
        self.bind('<Destroy>', self.on_destroy)
        self.update_idletasks()

    def on_destroy(self, event):
        try:
            self.after_cancel(self._loading_id)
        except ValueError:
            pass

    def anim(self):
        """Display animation."""
        self._anim_index += 1
        self._anim_index %= self._nb_img
        try:  # check whether main app has been killed
            with open(PIDFILE) as fich:
                pid = fich.read().strip()
            assert os.path.exists("/proc/%s" % pid)
        except (FileNotFoundError, AssertionError):
            self.destroy()
            return
        self.loading.configure(image=f'img_anim_{self._anim_index}')
        self._loading_id = self.after(100, self.anim)


if __name__ == '__main__':
    s = Splash()
    s.mainloop()

