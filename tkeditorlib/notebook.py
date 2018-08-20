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
        self.tab_nb = tab_nb

    @property
    def tab_nb(self):
        return self.label.tab_nb

    @tab_nb.setter
    def tab_nb(self, tab_nb):
        self.label.tab_nb = tab_nb

    def state(self, *args):
        res = ttk.Frame.state(self, *args)
        self.label.state(*args)
        if args and 'selected' in self.state():
            self.configure(width=self.label.winfo_reqwidth() + 12,
                           height=self.label.winfo_reqheight() + 8)
            self.label.place(bordermode='inside', x=0, y=0, relheight=1.1)
        else:
            self.label.place(bordermode='inside', x=0, y=0, relwidth=1, relheight=1)
            self.configure(width=self.label.winfo_reqwidth() + 12,
                           height=self.label.winfo_reqheight() + 8)
        return res

    def bind(self, sequence=None, func=None, add=None):
        return self.label.bind(sequence, func, add)

    def unbind(self, sequence, funcid=None):
        self.label.unbind(sequence, funcid)

    def tab_configure(self, *args, **kwargs):
        return self.label.configure(*args, **kwargs)


class MyNotebook(ttk.Frame):

    _initialized = False

    def __init__(self, master=None, **kwargs):
        ttk.Frame.__init__(self, master, class_='MyNotebook', padding=(0, 0, 0, 1),
                           relief='raised', **kwargs)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

        self._visible_tabs = []
        self._hidden_tabs = []
        self._tab_labels = {}
        self._tabs = {}
        self._tab_options = {}
        self._indexes = {}
        self._nb_tab = 0
        self._current_tab = None
        self._dragged_tab = None

        # --- init style
        if not MyNotebook._initialized:
            self._setup_style()
            MyNotebook._initialized = True

        # --- widgets
        # to display current tab content
        self._body = ttk.Frame(self, padding=2)
        self._body.rowconfigure(0, weight=1)
        self._body.columnconfigure(0, weight=1)
        self._body.grid_propagate(False)
        # tab labels
        self._canvas = tk.Canvas(self)  # to scroll through tab labels
        self._tab_frame = ttk.Frame(self._canvas)  # to display tab labels
        self._sep = ttk.Separator(self, orient='horizontal')
        self._canvas.create_window(0, 1, anchor='nw', window=self._sep, width=1,
                                   tags='sep', height=1)
        self._canvas.create_window(0, 0, anchor='nw', window=self._tab_frame, tags='window')
        self._canvas.configure(height=self._tab_frame.winfo_reqheight())
        # dragging dummy
        self._dummy_frame = ttk.Frame(self._tab_frame)
        self._dummy_sep = ttk.Separator(self._tab_frame, orient='horizontal')
        self._dummy_sep.place(in_=self._dummy_frame, x=0, relwidth=1, height=1,
                              y=0, anchor='sw', bordermode='outside')
        # tab navigation
        self._btn_left = ttk.Button(self, style='MyNotebook.Left.Button',
                                    command=self.show_prev)
        self._btn_right = ttk.Button(self, style='MyNotebook.Right.Button',
                                     command=self.show_next)

        # --- grid
        self._btn_left.grid(row=0, column=0, sticky='ns', pady=(0, 1))
        self._canvas.grid(row=0, column=1, sticky='ew')
        self._btn_right.grid(row=0, column=2, sticky='ns', pady=(0, 1))
        self._body.grid(row=1, columnspan=3, sticky='ewns', padx=1, pady=1)

        # --- bindings
        self._tab_frame.bind('<Configure>', self._on_configure)
        self._canvas.bind('<Configure>', self._on_configure)
        self.bind_all('<ButtonRelease-1>', self._on_click)
        self.bind('<<ThemeChanged>>', self._setup_style)

    def _on_press(self, event):
        self.show(event.widget.tab_nb)
        tab = event.widget.tab_nb
        widget = self._tab_labels[tab]
        x = widget.winfo_x()
        y = widget.winfo_y()
        self._dummy_frame.configure(width=widget.winfo_reqwidth(),
                                    height=widget.winfo_reqheight())
        self._dummy_frame.grid(**widget.grid_info())
        self.update_idletasks()
        self._dummy_sep.place(in_=self._dummy_frame, y=self._dummy_frame.winfo_height())
        widget.grid_remove()
        widget.place(x=x, y=y)
        widget.lift()
        self._dragged_tab = widget
        self._dx = - event.x_root
        self._y = event.y_root
        self._distance_to_dragged_border = widget.winfo_rootx() - event.x_root
        widget.bind_all('<Motion>', self._on_drag)

    def _on_drag(self, event):
        self._dragged_tab.place(x=self._dragged_tab.winfo_x() + event.x_root + self._dx)
        x_border = event.x_root + self._distance_to_dragged_border
        if event.x_root > - self._dx:
            # move towards right
            w = self._dragged_tab.winfo_width()
            tab_below = self._tab_frame.winfo_containing(x_border + w + 2, self._y)
        else:
            tab_below = self._tab_frame.winfo_containing(x_border - 2, self._y)
        if tab_below and tab_below.master in self._tab_labels.values():
            tab_below = tab_below.master
        elif tab_below not in self._tab_labels:
            tab_below = None
        if tab_below and abs(x_border - tab_below.winfo_rootx()) < tab_below.winfo_width() / 2:
            # swap
            self._swap(tab_below)

        self._dx = - event.x_root

    def _swap(self, tab):
        g1, g2 = self._dummy_frame.grid_info(), tab.grid_info()
        self._dummy_frame.grid(**g2)
        tab.grid(**g1)
        i1 = self._visible_tabs.index(self._dragged_tab.tab_nb)
        i2 = self._visible_tabs.index(tab.tab_nb)
        self._visible_tabs[i1] = tab.tab_nb
        self._visible_tabs[i2] = self._dragged_tab.tab_nb
        self.see(self._dragged_tab.tab_nb)

    def _on_click(self, event):
        if self._dragged_tab:
            self._dragged_tab.unbind_all('<Motion>')
            self._dragged_tab.grid(**self._dummy_frame.grid_info())
            self._dragged_tab = None
            self._dummy_frame.grid_forget()

    def add(self, widget, **kwargs):
        name = str(widget)
        if name in self._indexes:
            ind = self._indexes[name]
            self.tab(ind, **kwargs)
            self.show(ind)
        else:
            sticky = kwargs.pop('sticky', 'ewns')
            padding = kwargs.pop('padding', 0)
            self._tabs[self._nb_tab] = widget
            ind = self._nb_tab
            self._indexes[name] = ind
            self._tab_labels[ind] = Tab(self._tab_frame,
                                        tab_nb=self._nb_tab, **kwargs)
            self._tab_labels[ind].bind('<ButtonRelease-1>', self._on_click)
            self._tab_labels[ind].bind('<ButtonPress-1>', self._on_press)
            self._body.configure(height=max(self._body.winfo_height(), widget.winfo_reqheight()),
                                 width=max(self._body.winfo_width(), widget.winfo_reqwidth()))

            self._tab_options[ind] = dict(text='', image='', compound='none')
            self._tab_options[ind].update(kwargs)
            self._tab_options[ind].update(dict(padding=padding, sticky=sticky))
            self.show(self._nb_tab, new=True, update=True)

            self._nb_tab += 1

    def index(self, tab_id):
        if isinstance(tab_id, int):
            return self._visible_tabs.index(tab_id)
        else:
            return self._indexes[str(tab_id)]

    def show_next(self):
        if self._current_tab is not None:
            index = self._visible_tabs.index(self._current_tab)
            index += 1
            if index < len(self._visible_tabs):
                self.show(self._visible_tabs[index])

    def show_prev(self):
        if self._current_tab is not None:
            index = self._visible_tabs.index(self._current_tab)
            index -= 1
            if index >= 0:
                self.show(self._visible_tabs[index])

    def show(self, tab, new=False, update=False):
        # hide current tab body
        if self._current_tab is not None:
            self._tabs[self._current_tab].grid_remove()
            self._tab_labels[self._current_tab].state(['!selected'])

        if tab in self._hidden_tabs:
            self._tab_labels[tab].grid()
            self._visible_tabs.insert(self._tab_labels[tab].grid_info()['column'], tab)
            self._hidden_tabs.remove(tab)

        # update current tab
        self._current_tab = tab
        self._tab_labels[tab].state(['selected'])

        if new:
            # add new tab
            c, r = self._tab_frame.grid_size()
            self._tab_labels[tab].grid(row=0, column=c)
            self._visible_tabs.append(tab)
        self.update_idletasks()

        # ensure tab visibility
        self.see(tab)
        # display body
        if update:
            sticky = self._tab_options[tab]['sticky']
            pad = self._tab_options[tab]['padding']
            self._tabs[tab].grid(in_=self._body, sticky=sticky, padx=pad, pady=pad)
        else:
            self._tabs[tab].grid(in_=self._body)
        self.update_idletasks()

    def see(self, tab):
        """Make tab label visible."""
        if tab is None:
            return
        elif not isinstance(tab, int):
            tab = self.index(tab)
        w = self._tab_frame.winfo_reqwidth()
        x1 = self._tab_labels[tab].winfo_x() / w
        x2 = x1 + self._tab_labels[tab].winfo_reqwidth() / w
        xc1, xc2 = self._canvas.xview()
        if x1 < xc1:
            self._canvas.xview_moveto(x1)
        elif x2 > xc2:
            self._canvas.xview_moveto(xc1 + x2 - xc2)
        i = self._visible_tabs.index(tab)
        if i == 0:
            self._btn_left.state(['disabled'])
            if len(self._visible_tabs) > 1:
                self._btn_right.state(['!disabled'])
        elif i == len(self._visible_tabs) - 1:
            self._btn_right.state(['disabled'])
            self._btn_left.state(['!disabled'])
        else:
            self._btn_right.state(['!disabled'])
            self._btn_left.state(['!disabled'])

    def hide(self, tab):
        if not isinstance(tab, int):
            tab = self.index(tab)
        if tab in self._visible_tabs:
            self._visible_tabs.remove(tab)
            self._hidden_tabs.append(tab)
            self._tab_labels[tab].grid_remove()
            if self._current_tab == tab:
                if self._visible_tabs:
                    self.show(self._visible_tabs[0])
                else:
                    self._current_tab = None
                self._tabs[tab].grid_remove()

    def forget(self, tab):
        if not isinstance(tab, int):
            tab = self.index(tab)
        if tab in self._hidden_tabs:
            self._hidden_tabs.remove(tab)
        elif tab in self._visible_tabs:
            self._visible_tabs.remove(tab)
            self._tab_labels[tab].grid_forget()
            if self._current_tab == tab:
                if self._visible_tabs:
                    tab2 = self._visible_tabs[0]
                    self.show(tab2)
                else:
                    self._current_tab = None
                self._tabs[tab].grid_forget()
        del self._tab_labels[tab]
        del self._indexes[str(self._tabs[tab])]
        del self._tabs[tab]

    def select(self, tab=None):
        if tab is None:
            return str(self._tabs[self._current_tab])
        elif str(tab) in self._indexes:
            self.show(self._indexes[str(tab)])
        elif tab in self._tabs:
            self.show(tab)
        else:
            raise ValueError('No such tab in the notebook: %s' % tab)

    def tab(self, tab, option=None, **kw):
        if str(tab) in self._indexes:
            tab = self._indexes[str(tab)]
        elif tab not in self._tabs:
            raise ValueError('No such tab in the notebook: %s' % tab)
        if option:
            return self._tab_options[tab][option]
        else:
            self._tab_options[tab].update(kw)
            sticky = kw.pop('padding', None)
            padding = kw.pop('sticky', None)
            self._tab_labels[tab].tab_configure(**kw)
            if sticky is not None or padding is not None and self._current_tab == tab:
                self.show(tab, update=True)

    def _on_configure(self, event=None):
        self.update_idletasks()
        h = self._tab_frame.winfo_reqheight()
        self._canvas.configure(height=h)
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))
        self._canvas.coords('sep', 0, h - 1)
        self._canvas.itemconfigure('sep', width=self._canvas.winfo_width())
        self._sep.lower(self._tab_frame)
        self.see(self._current_tab)
        if self._tab_frame.winfo_reqwidth() < self._canvas.winfo_width():
            self._btn_left.grid_remove()
            self._btn_right.grid_remove()
        else:
            self._btn_left.grid()
            self._btn_right.grid()

    def _setup_style(self, vent=None):
        style = ttk.Style(self)
        style.layout('MyNotebook', style.layout('TFrame'))
        style.layout('MyNotebook.Tab', style.layout('TFrame'))
        style.layout('MyNotebook.Tab.Label', style.layout('TLabel'))
        style.layout('MyNotebook.Left.Button',
                     [('Button.padding',
                       {'sticky': 'nswe',
                        'children': [('Button.leftarrow', {'sticky': 'nswe'})]})])
        style.layout('MyNotebook.Right.Button',
                     [('Button.padding',
                       {'sticky': 'nswe',
                        'children': [('Button.rightarrow', {'sticky': 'nswe'})]})])

        style.configure('MyNotebook', relief='raised', borderwidth=1, padding=1)
        style.configure('MyNotebook.Tab', relief='raised', borderwidth=1,
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
    colors = ['red', 'blue', 'cyan', 'white', 'yellow', 'green', 'brown', 'orange']
    n = MyNotebook(root)
    n.grid()
    for i, c in enumerate(colors):
        f = tk.Frame(root, bg=c, width=200, height=200)
        n.add(f, text='frame %i %s' % (i, c))
