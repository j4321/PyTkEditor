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


class MyNotebook(ttk.Frame):

    _initialized = False

    def __init__(self, master=None, **kwargs):
        ttk.Frame.__init__(self, master, class_='MyNotebook', padding=(0, 0, 0, 1),
                           relief='raised', **kwargs)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)
        self.visible_tabs = []
        self.hidden_tabs = {'right': [], 'left': []}
        self.tab_labels = {}
        self.tabs = {}
        self._nb_tab = 0
        self.current_tab = None
        self._dragged_tab = None

        # --- init style
        if not MyNotebook._initialized:
            self._setup_style()
            MyNotebook._initialized = True

        # --- widgets
        # to display current tab content
        self.body = ttk.Frame(self, padding=2)
        self.body.rowconfigure(0, weight=1)
        self.body.columnconfigure(0, weight=1)
        self.body.grid_propagate(False)
        # tab labels
        self.canvas = tk.Canvas(self)  # to scroll through tab labels
        self.tab_frame = ttk.Frame(self.canvas)  # to display tab labels
        self.sep = ttk.Separator(self, orient='horizontal')
        self.canvas.create_window(0, 1, anchor='nw', window=self.sep, width=1,
                                  tags='sep', height=1)
        self.canvas.create_window(0, 0, anchor='nw', window=self.tab_frame, tags='window')
        self.canvas.configure(height=self.tab_frame.winfo_reqheight())
        # dragging dummy
        self._dummy_frame = ttk.Frame(self.tab_frame)
        self._dummy_sep = ttk.Separator(self.tab_frame, orient='horizontal')
        self._dummy_sep.place(in_=self._dummy_frame, x=0, relwidth=1, height=1,
                              y=0, anchor='sw', bordermode='outside')
        # tab navigation
        self.__btn_left = ttk.Button(self, style='MyNotebook.Left.Button',
                                     command=self.show_prev)
        self.__btn_right = ttk.Button(self, style='MyNotebook.Right.Button',
                                      command=self.show_next)

        # --- grid
        self.__btn_left.grid(row=0, column=0, sticky='ns', pady=(0, 1))
        self.canvas.grid(row=0, column=1, sticky='ew')
        self.__btn_right.grid(row=0, column=2, sticky='ns', pady=(0, 1))
        self.body.grid(row=1, columnspan=3, sticky='ewns', padx=1, pady=1)

        # --- bindings
        self.tab_frame.bind('<Configure>', self._on_configure)
        self.canvas.bind('<Configure>', self._on_configure)
        self.bind_all('<ButtonRelease-1>', self._on_click)

    def _on_press(self, event):
        self.show(event.widget.tab_nb)
        tab = event.widget.tab_nb
        widget = self.tab_labels[tab]
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
            tab_below = self.tab_frame.winfo_containing(x_border + w + 2, self._y)
        else:
            tab_below = self.tab_frame.winfo_containing(x_border - 2, self._y)
        if tab_below and tab_below.master in self.tab_labels.values():
            tab_below = tab_below.master
        elif tab_below not in self.tab_labels:
            tab_below = None
        if tab_below and abs(x_border - tab_below.winfo_rootx()) < tab_below.winfo_width() / 2:
            # swap
            self._swap(tab_below)

        self._dx = - event.x_root

    def _swap(self, tab):
        g1, g2 = self._dummy_frame.grid_info(), tab.grid_info()
        self._dummy_frame.grid(**g2)
        tab.grid(**g1)
        i1 = self.visible_tabs.index(self._dragged_tab.tab_nb)
        i2 = self.visible_tabs.index(tab.tab_nb)
        self.visible_tabs[i1] = tab.tab_nb
        self.visible_tabs[i2] = self._dragged_tab.tab_nb
        self.see(self._dragged_tab.tab_nb)

    def _on_click(self, event):
        if self._dragged_tab:
            self._dragged_tab.unbind_all('<Motion>')
            self._dragged_tab.grid(**self._dummy_frame.grid_info())
            self._dragged_tab = None
            self._dummy_frame.grid_forget()

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
        self.tab_labels[self._nb_tab].bind('<ButtonPress-1>', self._on_press)
        self.body.configure(height=max(self.body.winfo_height(), widget.winfo_reqheight()),
                            width=max(self.body.winfo_width(), widget.winfo_reqwidth()))

        self.show(self._nb_tab, new=True, sticky=sticky, padx=padding, pady=padding)

        self._nb_tab += 1

    def show_next(self):
        if self.current_tab is not None:
            index = self.visible_tabs.index(self.current_tab)
            index += 1
            if index < len(self.visible_tabs):
                self.show(self.visible_tabs[index])

    def show_prev(self):
        if self.current_tab is not None:
            index = self.visible_tabs.index(self.current_tab)
            index -= 1
            if index >= 0:
                self.show(self.visible_tabs[index])

    def show(self, tab, new=False, **kw):
        # hide current tab body
        if self.current_tab is not None:
            self.tabs[self.current_tab].grid_remove()
            self.tab_labels[self.current_tab].state(['!selected'])

        # update current tab
        self.current_tab = tab
        self.tab_labels[tab].state(['selected'])

        if new:
            # add new tab
            c, r = self.tab_frame.grid_size()
            self.tab_labels[tab].grid(row=0, column=c)
            self.visible_tabs.append(tab)
        self.update_idletasks()

        # ensure tab visibility
        self.see(tab)
        # display body
        self.tabs[tab].grid(in_=self.body, **kw)

    def see(self, tab):
        """Make tab label visible."""
        if tab is None:
            return
        w = self.tab_frame.winfo_reqwidth()
        x1 = self.tab_labels[tab].winfo_x() / w
        x2 = x1 + self.tab_labels[tab].winfo_reqwidth() / w
        xc1, xc2 = self.canvas.xview()
        if x1 < xc1:
            self.canvas.xview_moveto(x1)
        elif x2 > xc2:
            self.canvas.xview_moveto(xc1 + x2 - xc2)
        i = self.visible_tabs.index(tab)
        if i == 0:
            self.__btn_left.state(['disabled'])
            if len(self.visible_tabs) > 1:
                self.__btn_right.state(['!disabled'])
        elif i == len(self.visible_tabs) - 1:
            self.__btn_right.state(['disabled'])
            self.__btn_left.state(['!disabled'])
        else:
            self.__btn_right.state(['!disabled'])
            self.__btn_left.state(['!disabled'])

#    def hide(self, tab, side):
#        self.visible_tabs.remove(tab)
#        self.tab_labels[tab].grid_remove()
#        self.hidden_tabs[side].append(tab)
#        self._arrow_btns[side].state(['!disabled'])
#        if self.current_tab == tab:
#            if self.visible_tabs:
#                tab = self.visible_tabs[0]
#                self.show(tab)
#            else:
#                self.current_tab = None
#                self.tabs[tab].grid_remove()

    def _on_configure(self, event=None):
        self.update_idletasks()
        h = self.tab_frame.winfo_reqheight()
        self.canvas.configure(height=h)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.canvas.coords('sep', 0, h - 1)
        self.canvas.itemconfigure('sep', width=self.canvas.winfo_width())
        self.sep.lower(self.tab_frame)
        self.see(self.current_tab)
        if self.tab_frame.winfo_reqwidth() < self.canvas.winfo_width():
            self.__btn_left.grid_remove()
            self.__btn_right.grid_remove()
        else:
            self.__btn_left.grid()
            self.__btn_right.grid()

    def _setup_style(self):
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
    colors = ['red', 'blue', 'cyan', 'white', 'yellow', 'green', 'brown', 'orange']
    n = MyNotebook(root)
#    n = ttk.Notebook(root)
    n.grid()
#    n.grid(sticky='ewsn')
    for i, c in enumerate(colors):
        f = tk.Frame(root, bg=c, width=200, height=200)
        n.add(f, text='frame %i %s' % (i, c))
