#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 16:02:58 2018

@author: juliette
"""
from tkinter import ttk
import tkinter as tk


class Tab(ttk.Frame):
    def __init__(self, master=None, tab_nb=0, **kwargs):
        ttk.Frame.__init__(self, master, class_='MyNotebook.Tab',
                           style='MyNotebook.Tab', padding=1)
        self.label = ttk.Label(self, style='MyNotebook.Tab.Label', **kwargs,
                               anchor='center', padding=1)
        self.update_idletasks()
        self.configure(width=self.label.winfo_reqwidth() + 12,
                       height=self.label.winfo_reqheight() + 8)
        self.label.place(bordermode='inside', x=0, y=0, relwidth=1, relheight=1)
        self.label.tab_nb = tab_nb

    def state(self, *args):
        res = ttk.Frame.state(self, *args)
        self.label.state(*args)
        if args and 'selected' in self.state():
            self.label.configure(padding=(1, 0, 1, 2))
            self.configure(width=self.label.winfo_reqwidth() + 12,
                           height=self.label.winfo_reqheight() + 8)
            self.label.place(bordermode='inside', x=0, y=0, relheight=1.1)
        else:
            self.label.configure(padding=1)
            self.label.place(bordermode='inside', x=0, y=0, relwidth=1, relheight=1)
            self.configure(width=self.label.winfo_reqwidth() + 12,
                           height=self.label.winfo_reqheight() + 8)
        return res

    def bind(self, sequence=None, func=None, add=None):
        return self.label.bind(sequence, func, add)


class MyNotebook(ttk.Frame):

    _initialized = False

    def __init__(self, master=None, **kwargs):
        ttk.Frame.__init__(self, master, class_='MyNotebook', padding=(1, 0, 1, 1),
                           relief='raised', **kwargs)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)
        self.visible_tabs = []
        self.hidden_tabs = {'right': [], 'left': []}
        self.tab_labels = {}
        self.tabs = {}
        self._nb_tab = 0
        self.body = ttk.Frame(self, padding=2)
        self.tab_frame = ttk.Frame(self)
        self.sep = ttk.Separator(self.tab_frame, orien='horizontal')
        self.body.rowconfigure(0, weight=1)
        self.body.columnconfigure(0, weight=1)
        self.body.grid_propagate(False)

        self.current_tab = None

        if not MyNotebook._initialized:
            self._setup_style()
            MyNotebook._initialized = True

        self._arrow_btns = {}
        self._arrow_btns['left'] = ttk.Button(self, style='MyNotebook.Left.Button',
                                              command=self.show_prev)
        self._arrow_btns['left'].grid(row=0, column=0, sticky='ns')
        self.tab_frame.grid(row=0, column=1, sticky='ew')
        self._arrow_btns['right'] = ttk.Button(self, style='MyNotebook.Right.Button',
                                               command=self.show_next)
        self._arrow_btns['right'].grid(row=0, column=2, sticky='ns')
        self.body.grid(row=1, columnspan=3, sticky='ewns')
        self._prev_width = 0

        self.tab_frame.bind('<Configure>', self.on_configure)

    def _on_click(self, event):
        self.show(event.widget.tab_nb)

    def add(self, widget, **kwargs):
        text = kwargs.get('text', '')
        image = kwargs.get('image', '')
        compound = kwargs.get('compound', 'none')
        sticky = kwargs.get('sticky', 'ewns')
        padding = kwargs.get('padding', 0)

        self.tabs[self._nb_tab] = widget
        self.tab_labels[self._nb_tab] = Tab(self.tab_frame,
                                            tab_nb=self._nb_tab,
                                            text=text, image=image,
                                            compound=compound)
        self.tab_labels[self._nb_tab].bind('<ButtonRelease-1>', self._on_click)
        self.body.configure(height=max(self.body.winfo_height(), widget.winfo_reqheight()),
                            width=max(self.body.winfo_width(), widget.winfo_reqwidth()))

        self.show(self._nb_tab, new=True, sticky=sticky, padx=padding, pady=padding)

        self._nb_tab += 1

    def show_next(self):
        if self.current_tab is not None:
            index = self.visible_tabs.index(self.current_tab)
            index += 1
            if index >= len(self.visible_tabs):
                if self.hidden_tabs['right']:
                    self.show(self.hidden_tabs['right'][-1])
                    self.on_configure(side='left')
                    self._arrow_btns['left'].state(['!disabled'])
                else:
                    self._arrow_btns['right'].state(['disabled'])
            else:
                self.show(self.visible_tabs[index])
                self._arrow_btns['left'].state(['!disabled'])

    def show_prev(self):
        if self.current_tab is not None:
            index = self.visible_tabs.index(self.current_tab)
            index -= 1
            if index < 0:
                if self.hidden_tabs['left']:
                    self.show(self.hidden_tabs['left'][-1])
                    self.on_configure(side='right')
                    self._arrow_btns['right'].state(['!disabled'])
                else:
                    self._arrow_btns['left'].state(['disabled'])
            else:
                self.show(self.visible_tabs[index])
                self._arrow_btns['right'].state(['!disabled'])

    def show(self, tab, new=False, **kw):
        if self.current_tab is not None:
            self.tabs[self.current_tab].grid_remove()
            self.tab_labels[self.current_tab].state(['!selected'])
        self.current_tab = tab
        if tab not in self.visible_tabs:
            if new:
                c, r = self.tab_frame.grid_size()
                self.tab_labels[tab].grid(row=0, column=c)
                self.visible_tabs.append(tab)
            else:
                self.tab_labels[tab].grid()
                c = self.tab_labels[tab].grid_info()['column']
                if tab in self.hidden_tabs['left']:
                    self.hidden_tabs['left'].remove(tab)
                    self.visible_tabs.insert(0, tab)
                    if not self.hidden_tabs['left']:
                        self._arrow_btns['left'].state(['disabled'])
                elif tab in self.hidden_tabs['right']:
                    self.hidden_tabs['right'].remove(tab)
                    self.visible_tabs.append(tab)
                    if not self.hidden_tabs['right']:
                        self._arrow_btns['right'].state(['disabled'])
        self.tabs[tab].grid(in_=self.body, **kw)
        self.tab_labels[tab].state(['selected'])

    def hide(self, tab, side):
        self.visible_tabs.remove(tab)
        self.tab_labels[tab].grid_remove()
        self.hidden_tabs[side].append(tab)
        self._arrow_btns[side].state(['!disabled'])
        if self.current_tab == tab:
            if self.visible_tabs:
                tab = self.visible_tabs[0]
                self.show(tab)
            else:
                self.current_tab = None
                self.tabs[tab].grid_remove()

    def on_configure(self, event=None, side='right'):
        self.update_idletasks()
        width = self.tab_frame.winfo_width()
        rw = self.tab_frame.winfo_reqwidth()
        if self._prev_width >= width:
            if len(self.visible_tabs) > 1 and rw > width:
                i = 0 if side == 'left' else -1
                self.hide(self.visible_tabs[i], side)
        else:
            if self.hidden_tabs['right']:
                tab = self.hidden_tabs['right'][-1]
                if rw + self.tab_labels[tab].winfo_reqwidth() < width:
                    self.show(tab)
            elif self.hidden_tabs['left']:
                tab = self.hidden_tabs['left'][-1]
                if rw + self.tab_labels[tab].winfo_reqwidth() < width:
                    self.show(tab)
        if len(self.visible_tabs) == len(self.tabs):
            self._arrow_btns['left'].grid_remove()
            self._arrow_btns['right'].grid_remove()
        elif len(self.visible_tabs) == len(self.tabs) - 1:
            self._arrow_btns['left'].grid()
            self._arrow_btns['right'].grid()
            self._arrow_btns['left'].state(['disabled'])
        self._prev_width = width
        self.sep.place(x=0, relwidth=1, y=self.tab_frame.winfo_reqheight() - 1)

    def _setup_style(self):
        style = ttk.Style(self)
        style.layout('MyNotebook', style.layout('TFrame'))
        style.layout('MyNotebook.Tab', style.layout('TFrame'))
        style.layout('MyNotebook.Tab.Label', style.layout('TLabel'))
        style.layout('MyNotebook.Left.Button',
                     [('Button.leftarrow', {'sticky': 'nswe'})])
        style.layout('MyNotebook.Right.Button',
                     [('Button.rightarrow', {'sticky': 'nswe'})])

        style.configure('MyNotebook', relief='raised', borderwidth=1, padding=1)
        style.configure('MyNotebook.Tab', relief='sunken', borderwidth=1,
                        background=style.lookup('TNotebook.Tab', 'background'))
        style.configure('MyNotebook.Tab.Label', relief='flat', borderwidth=0,
                        padding=4,
                        background=style.lookup('TNotebook.Tab', 'background'))

        style.map('MyNotebook.Tab.Label',
                  **{'lightcolor': [('selected', '#eeebe7')],
                     'background': [('selected', '#dcdad5')]})
        style.map('MyNotebook.Tab',
                  **{'lightcolor': [('selected', '#eeebe7')],
                     'background': [('selected', '#dcdad5')]})

        style.map('MyNotebook.Left.Button', arrowcolor=[('disabled', 'gray50')])
        style.map('MyNotebook.Right.Button', arrowcolor=[('disabled', 'gray50')])


if __name__ == '__main__':
    root = tk.Tk()
    s = ttk.Style(root)
    s.theme_use('clam')
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    n = MyNotebook(root)
#    n = ttk.Notebook(root)
    n.grid(sticky='ew')
#    n.grid(sticky='ewsn')
    f1 = tk.Frame(root, bg='yellow', width=200, height=200)
    n.add(f1, text='frame 0')
    f2 = tk.Frame(root, bg='red', width=200, height=200)
    n.add(f2, text='frame 1')
    f3 = tk.Frame(root, bg='cyan', width=200, height=200)
    n.add(f3, text='frame 2')
    f4 = tk.Frame(root, width=200, height=200)
    ttk.Label(f4, text='Test').pack()
    n.add(f4, text='frame 3')
