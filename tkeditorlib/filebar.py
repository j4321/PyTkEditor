#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 14:55:51 2018

@author: juliette
"""

from tkinter import Canvas


class FileBar(Canvas):
    def __init__(self, master, widget, **kwargs):
        Canvas.__init__(self, master, **kwargs)

        self.widget = widget
        self.colors = {'warning': 'orange', 'error': 'red'}
        self.update_idletasks()
        self.highlight = self.create_rectangle(0, 0, 0, 0, width=0,
                                               fill=self.option_get('fill', '*Canvas'))

        self.bind('<1>', self.on_click)
        self.bind('<Map>', self.update_highlight)

    def update_highlight(self, event=None):
        height = self.winfo_height()
        deb, fin = self.widget.yview()
        self.coords(self.highlight, 0, int(deb * height), self.winfo_width(),
                    int(fin * height))

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
            self.coords(self.highlight, 0, int(deb * height), self.winfo_width(),
                        int((deb + h) * height))
            self.widget.yview('moveto', deb)

    def add_mark(self, line, category):
        end = int(self.widget.get_end().split('.')[0])
        y = int((line / end) * self.winfo_height())
        self.create_rectangle(1, y - 1, self.winfo_width(), y + 1,
                              fill=self.colors[category], width=0, tag='mark')

    def clear(self):
        self.delete('mark')
