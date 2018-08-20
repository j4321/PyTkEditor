#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 20:25:11 2018

@author: juliette
"""
from tkeditorlib.notebook import Notebook
from tkeditorlib.editor import Editor


class EditorNotebook(Notebook):
    def __init__(self, master):
        Notebook.__init__(self, master)

    def undo(self):
        if self._current_tab is not None:
            self._tabs[self._current_tab].undo()

    def redo(self):
        if self._current_tab is not None:
            self._tabs[self._current_tab].redo()

