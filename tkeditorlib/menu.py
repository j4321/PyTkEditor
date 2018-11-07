#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 14:55:51 2018

@author: juliette
"""

from tkinter import Menu


class LongMenu(Menu):
    def __init__(self, master=None, max_height=20, **kwargs):
        Menu.__init__(self, master, **kwargs)
        self.max_height = max_height

    def add(self, itemType, cnf={}, **kw):
        end = self.index('end')
        if end is None:
            end = 1
        else:
            end += 2  # end is the index of the last item starting from 0 so the
                      # nb of items after the addition is end + 2
        if not end % self.max_height:
            kw['columnbreak'] = True
        Menu.add(self, itemType, cnf, **kw)
            
