#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 14:55:51 2018

@author: juliette
"""

from tkinter import Canvas, Frame
from PIL import Image, ImageTk


def active_color(color, factor=3):
    """Return a lighter shade of color (RGB triplet with value max 255) in HTML format."""
    r, g, b = color
    r *= 255 / 65535
    g *= 255 / 65535
    b *= 255 / 65535
    r += (255 - r) / factor
    g += (255 - g) / factor
    b += (255 - b) / factor
    return ("#%2.2x%2.2x%2.2x" % (round(r), round(g), round(b))).upper()
        

class FileBar(Canvas):
    def __init__(self, master, widget, **kwargs):
        Canvas.__init__(self, master, **kwargs)
        
        self._marks = {'warning': [], 'error': [], 'sep': []}

        self.widget = widget
        self.colors = {'warning': 'orange', 'error': 'red', 'sep': 'blue'}
        self.active_colors = {'warning': '#FFC355', 'error': '#FF5555', 'sep': '#5555FF'}
        self.update_idletasks()
        self._highlight_img = Image.new('RGBA', (1, 1), "#ffffff88")
        self._highlight_photoimg = ImageTk.PhotoImage(self._highlight_img, master=self)
        self.highlight = self.create_image(0, 0, anchor='nw', image=self._highlight_photoimg)
        # self.highlight = self.create_rectangle(0, 0, 0, 0, width=0,
                                               # fill=self.option_get('fill', '*Canvas'))
        self.bind('<1>', self.on_click)
        self.bind('<Map>', self.update_positions)

    def update_style(self, comment_fg):
        col = self.winfo_rgb(self.option_get('fill', '*Canvas'))
        self._highlight_img = Image.new('RGBA', self._highlight_img.size,
                                        active_color(col, 2) + '95')
        self._highlight_photoimg = ImageTk.PhotoImage(self._highlight_img, master=self)
        self.itemconfigure(self.highlight, image=self._highlight_photoimg)
        self.configure(bg=self.option_get('background', '*Canvas'))
        self.colors['sep'] = comment_fg
        self.active_colors['sep'] = active_color(self.winfo_rgb(comment_fg))

    def update_positions(self, event=None):
        height = self.winfo_height()
        deb, fin = self.widget.yview()
        size = (self.winfo_width(), int((fin - deb) * height))
        self._highlight_img = self._highlight_img.resize(size)
        self._highlight_photoimg = ImageTk.PhotoImage(self._highlight_img, master=self)
        self.itemconfigure(self.highlight, image=self._highlight_photoimg)
        self.coords(self.highlight, 0, int(deb * height))
        # self.coords(self.highlight, 0, int(deb * height), self.winfo_width(),
                    # int(fin * height))
        for l in self._marks.values():
            for iid, rely in l:
                y = int(rely * self.winfo_height())
                self.coords(iid, 1, y - 1, self.winfo_width(), y + 1)
        self.tag_raise(self.highlight)
                
    def on_click(self, event):
        try:
            frac = event.y / event.widget.winfo_height()
        except TypeError:
            pass
        else:
            deb, fin = self.widget.yview()
            h = (fin - deb)
            height = self.winfo_height()
            deb = max(0, frac - h / 2)
            # self.coords(self.highlight, 0, int(deb * height), self.winfo_width(),
                        # int((deb + h) * height))
            self.coords(self.highlight, 0, int(deb * height))
            self.widget.yview('moveto', deb)

    def add_mark(self, line, category):
        end = int(self.widget.get_end().split('.')[0])
        rely = line / end
        y = int(rely * self.winfo_height())
        iid = self.create_rectangle(1, y - 1, self.winfo_width(), y + 1,
                                    fill=self.colors[category], width=0,
                                    tag=category)
        self._marks[category].append((iid, rely))
        self.tag_raise(self.highlight)

    def clear_syntax_issues(self):
        self.delete('warning')
        self._marks['warning'].clear()
        self.delete('error')
        self._marks['error'].clear()

    def clear_cells(self):
        self.delete('sep')
        self._marks['sep'].clear()

