#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 09:57:50 2018

@author: juliette
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkeditorlib.constants import CONFIG
from tkeditorlib.autocomplete import AutoCompleteCombobox


class Config(tk.Toplevel):
    def __init__(self, master):
         tk.Toplevel.__init__(self, master)
         self.transient(master)
         self.grab_set()
         self.configure(padx=4, pady=4)
         self.title('TkEditor - Config')

         ttk.Label(self, text='General').grid(row=0)