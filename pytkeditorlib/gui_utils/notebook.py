#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2019 Juliette Monsel <j_4321 at protonmail dot com>

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


Notebook with draggable / scrollable tabs
"""
from tkinter import ttk
import tkinter as tk


class Tab(ttk.Frame):
    """Notebook tab."""
    def __init__(self, master=None, tab_nb=0, **kwargs):
        ttk.Frame.__init__(self, master, class_='Notebook.Tab',
                           style='Notebook.Tab', padding=1)
        self._state = kwargs.pop('state', 'normal')
        self.tab_nb = tab_nb
        self._closebutton = kwargs.pop('closebutton', True)
        self._closecommand = kwargs.pop('closecommand', None)
        self.frame = ttk.Frame(self, style='Notebook.Tab.Frame')
        self.label = ttk.Label(self.frame, style='Notebook.Tab.Label', **kwargs,
                               anchor='center', takefocus=False)
        self.closebtn = ttk.Button(self.frame, style='Notebook.Tab.Close',
                                   command=self.closecommand, padding=0,
                                   class_='Notebook.Tab.Close',
                                   takefocus=False)
        self.label.pack(side='left', padx=(2, 0))
        if self._closebutton:
            self.closebtn.pack(side='right', padx=(0, 2), pady=(1, 0))
        self.update_idletasks()
        self.configure(width=self.frame.winfo_reqwidth() + 2,
                       height=self.frame.winfo_reqheight() + 2)
        self.frame.place(bordermode='inside', anchor='nw', x=0, y=0,
                         relwidth=1, relheight=1)
        self.label.bind('<Configure>', self._resize)
        if self._state == 'disabled':
            self.state(['disabled'])
        elif self._state != 'normal':
            raise ValueError("state option should be 'normal' or 'disabled'")

        self.bind('<ButtonRelease-2>', self._b2_press)

    def _b2_press(self, event):
        if self.identify(event.x, event.y):
            self.closecommand()

    def _resize(self, event):
        self.configure(width=self.frame.winfo_reqwidth() + 2,
                       height=self.frame.winfo_reqheight() + 2)

    def closecommand(self):
        """Close button command."""
        self._closecommand(self.tab_nb)

    def state(self, *args):
        res = ttk.Frame.state(self, *args)
        self.label.state(*args)
        self.frame.state(*args)
        self.closebtn.state(*args)
        if args and 'selected' in self.state():
            self.configure(width=self.frame.winfo_reqwidth() + 2,
                           height=self.frame.winfo_reqheight() + 2)
            self.frame.place_configure(relheight=1.1)
        else:
            self.frame.place_configure(relheight=1)
            self.configure(width=self.frame.winfo_reqwidth() + 2,
                           height=self.frame.winfo_reqheight() + 2)
        return res

    def bind(self, sequence=None, func=None, add=None, bind_all=True):
        """
        Bind to this widget at event SEQUENCE a call to function FUNC.

        An additional boolean parameter ADD specifies whether FUNC will
        be called additionally to the other bound function or whether
        it will replace the previous function.

        If BIND_ALL is true, bind both the Frame and the Label of the tab,
        otherwise, bind only to the Frame.
        """
        funcid = self.frame.bind(sequence, func, add)
        if bind_all:
            funcid2 = self.label.bind(sequence, func, add)
        else:
            funcid2 = None
        return funcid, funcid2 

    def unbind(self, sequence, funcids=(None, None)):
        self.label.unbind(sequence, funcids[1])
        self.frame.unbind(sequence, funcids[0])

    def tab_configure(self, **kwargs):
        """Configure tab."""
        if 'closecommand' in kwargs:
            self._closecommand = kwargs.pop('closecommand')
        if 'closebutton' in kwargs:
            self._closebutton = kwargs.pop('closebutton')
            if self._closebutton:
                self.closebtn.pack(side='right', padx=(0, 6))
            else:
                self.closebtn.pack_forget()
            self.update_idletasks()
            self.configure(width=self.frame.winfo_reqwidth() + 2,
                           height=self.frame.winfo_reqheight() + 2)
        if 'state' in kwargs:
            state = kwargs.pop('state')
            if state == 'normal':
                self.state(['!disabled'])
            elif state == 'disabled':
                self.state(['disabled'])
            else:
                raise ValueError("state option should be 'normal' or 'disabled'")
            self._state = state
        if not kwargs:
            return
        self.label.configure(**kwargs)

    def tab_cget(self, option):
        """Get tab option."""
        if option == 'closecommand':
            return self._closecommand
        if option == 'closebutton':
            return self._closebutton
        if option == 'state':
            return self._state
        return self.label.cget(option)


class Notebook(ttk.Frame):
    """
    Notebook widget.

    Unlike the ttk.Notebook, the tab width is constant and determine by the tab
    label. When there are too many tabs to fit in the widget, buttons appear on
    the left and the right of the Notebook to navigate through the tabs.

    The tab have an optional close button and the notebook has an optional tab
    menu. Tabs can be optionnaly dragged.
    """

    _initialized = False

    def __init__(self, master=None, **kwargs):
        """
        Create a Notebook widget with parent master.

        STANDARD OPIONS

            class, cursor, style, takefocus

        WIDGET-SPECIFIC OPTIONS

            closebutton: boolean (default True)
                whether to display a close button on the tabs

            closecommand: function or None (default Notebook.forget)
                command executed when the close button of a tab is pressed,
                the tab index is passed in argument.

            tabdrag: boolean (default True)
                whether to enable dragging of tab labels

            tabmenu: boolean (default True)
                whether to display a menu showing the tab labels in alphabetical order

        TAB OPTIONS

            state, sticky, padding, text, image, compound

        TAB IDENTIFIERS (tab_id)

            The tab_id argument found in several methods may take any of
            the following forms:

                * An integer between zero and the number of tabs
                * The name of a child window
                * The string "current", which identifies the
                  currently-selected tab
                * The string "end", which returns the number of tabs (only
                  valid for method index)

        """
        self._closebutton = bool(kwargs.pop('closebutton', True))
        self._closecommand = kwargs.pop('closecommand', self.forget)
        self._tabdrag = bool(kwargs.pop('tabdrag', True))
        self._tabmenu = bool(kwargs.pop('tabmenu', True))

        ttk.Frame.__init__(self, master, class_='Notebook', padding=(0, 0, 0, 1),
                           **kwargs)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self._tab_var = tk.IntVar(self, -1)

        self._visible_tabs = []
        self._active_tabs = []  # not disabled
        self._hidden_tabs = []
        self._tab_labels = {}
        self._tab_menu_entries = {}
        self._tabs = {}
        self._tab_options = {}
        self._indexes = {}
        self._nb_tab = 0
        self.current_tab = -1
        self._dragged_tab = None
        self._dx = 0
        self._y = 0
        self._distance_to_dragged_border = 0

        style = ttk.Style(self)
        bg = style.lookup('TFrame', 'background')

        # --- widgets
        # to display current tab content
        self._body = ttk.Frame(self, padding=1, style='Notebook',
                               relief='flat')
        self._body.rowconfigure(0, weight=1)
        self._body.columnconfigure(0, weight=1)
        self._body.grid_propagate(False)
        # tab labels
        # canvas to scroll through tab labels
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0,
                                 borderwidth=0, takefocus=False)
        self._tab_frame2 = ttk.Frame(self, height=26, style='Notebook',
                                     relief='flat')
        # self._tab_frame2 is a trick to be able to drag a tab on the full
        # canvas width even if self._tab_frame is smaller.
        self._tab_frame = ttk.Frame(self._tab_frame2, style='Notebook',
                                    relief='flat', height=26)  # to display tab labels
        self._sep = ttk.Separator(self._tab_frame2, orient='horizontal')
        self._sep.place(bordermode='outside', anchor='sw', x=0, rely=1,
                        relwidth=1, height=1)
        self._tab_frame.pack(side='left')

        self._canvas.create_window(0, 0, anchor='nw', window=self._tab_frame2,
                                   tags='window')
        self._canvas.configure(height=self._tab_frame.winfo_reqheight())
        # empty frame to show the spot formerly occupied by the tab
        self._dummy_frame = ttk.Frame(self._tab_frame, style='Notebook', relief='flat')
        self._dummy_sep = ttk.Separator(self._tab_frame, orient='horizontal')
        self._dummy_sep.place(in_=self._dummy_frame, x=0, relwidth=1, height=1,
                              y=0, anchor='sw', bordermode='outside')
        # tab navigation
        self._tab_menu = tk.Menu(self, tearoff=False, relief='sunken',
                                 bg=style.lookup('TEntry', 'fieldbackground',
                                                 default='white'),
                                 activebackground=style.lookup('TEntry',
                                                               'selectbackground',
                                                               ['focus'], 'gray70'),
                                 activeforeground=style.lookup('TEntry',
                                                               'selectforeground',
                                                               ['focus'], 'gray70'))
        self._tab_list = ttk.Menubutton(self, width=1, menu=self._tab_menu,
                                        style='Notebook.TMenubutton',
                                        padding=0)
        self._tab_list.state(['disabled'])
        self._btn_left = ttk.Button(self, style='Left.Notebook.TButton',
                                    command=self.select_prev, takefocus=False)
        self._btn_right = ttk.Button(self, style='Right.Notebook.TButton',
                                     command=self.select_next, takefocus=False)

        # --- grid
        self._tab_list.grid(row=0, column=0, sticky='ns', pady=(0, 1))
        if not self._tabmenu:
            self._tab_list.grid_remove()
        self._btn_left.grid(row=0, column=1, sticky='ns', pady=(0, 1))
        self._canvas.grid(row=0, column=2, sticky='ew')
        self._btn_right.grid(row=0, column=3, sticky='ns', pady=(0, 1))
        self._body.grid(row=1, columnspan=4, sticky='ewns', padx=1, pady=1)

        ttk.Frame(self, height=1,
                  style='separator.TFrame').place(x=1, anchor='nw',
                                                  rely=1, height=1,
                                                  relwidth=1)

        self._border_left = ttk.Frame(self, width=1, style='separator.TFrame')
        self._border_right = ttk.Frame(self, width=1, style='separator.TFrame')
        self._border_left.place(bordermode='outside', in_=self._body, x=-1, y=-2,
                                width=1, height=self._body.winfo_reqheight() + 2, relheight=1)
        self._border_right.place(bordermode='outside', in_=self._body, relx=1, y=-2,
                                 width=1, height=self._body.winfo_reqheight() + 2, relheight=1)

        # --- bindings
        self._tab_frame.bind('<Configure>', self._on_configure)
        self._canvas.bind('<Configure>', self._on_configure)
        self.bind_all('<ButtonRelease-1>', self._on_click)

        self.config = self.configure

    def __getitem__(self, key):
        return self.cget(key)

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def _on_configure(self, event=None):
        self.update_idletasks()
        # ensure that canvas has the same height as the tabs
        h = self._tab_frame.winfo_reqheight()
        self._canvas.configure(height=h)
        # ensure that _tab_frame2 fills the canvas if _tab_frame is smaller
        self._canvas.itemconfigure('window',
                                   width=max(self._canvas.winfo_width(),
                                             self._tab_frame.winfo_reqwidth()))
        # update canvas scrollregion
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))
        # ensure visibility of current tab
        self.see(self.current_tab)
        # check wheter next/prev buttons needs to be displayed
        if self._tab_frame.winfo_reqwidth() < self._canvas.winfo_width():
            self._btn_left.grid_remove()
            self._btn_right.grid_remove()
        elif len(self._visible_tabs) > 1:
            self._btn_left.grid()
            self._btn_right.grid()

    def _on_press(self, event, tab):
        # show clicked tab content
        self._show(tab)

        if not self._tabdrag or self.tab(tab, 'state') == 'disabled':
            return

        # prepare dragging
        widget = self._tab_labels[tab]
        x = widget.winfo_x()
        y = widget.winfo_y()
        # replace tab by blank space (dummy)
        self._dummy_frame.configure(width=widget.winfo_reqwidth(),
                                    height=widget.winfo_reqheight())
        self._dummy_frame.grid(**widget.grid_info())
        self.update_idletasks()
        self._dummy_sep.place_configure(in_=self._dummy_frame, y=self._dummy_frame.winfo_height())
        widget.grid_remove()
        # place tab above the rest to drag it
        widget.place(bordermode='outside', x=x, y=y)
        widget.lift()
        self._dragged_tab = widget
        self._dx = - event.x_root  # - current mouse x position on screen
        self._y = event.y_root   # current y mouse position on screen
        self._distance_to_dragged_border = widget.winfo_rootx() - event.x_root
        widget.bind_all('<Motion>', self._on_drag)
        widget.bind_all('<Escape>', self._on_click)
        widget.bind_all('<ButtonRelease-1>', self._on_click)

    def _on_drag(self, event):
        self._dragged_tab.place_configure(x=self._dragged_tab.winfo_x() + event.x_root + self._dx)
        x_border = event.x_root + self._distance_to_dragged_border
        # get tab below dragged_tab
        if event.x_root > - self._dx:
            # move towards right
            w = self._dragged_tab.winfo_width()
            tab_below = self._tab_frame.winfo_containing(x_border + w + 2, self._y)
        else:
            # move towards left
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
        """Swap dragged_tab with tab."""
        g1, g2 = self._dummy_frame.grid_info(), tab.grid_info()
        self._dummy_frame.grid(**g2)
        tab.grid(**g1)
        i1 = self._visible_tabs.index(self._dragged_tab.tab_nb)
        i2 = self._visible_tabs.index(tab.tab_nb)
        self._visible_tabs[i1] = tab.tab_nb
        self._visible_tabs[i2] = self._dragged_tab.tab_nb
        self.see(self._dragged_tab.tab_nb)

    def _on_click(self, event):
        """Stop dragging."""
        if self._dragged_tab:
            self._dragged_tab.unbind_all('<Motion>')
            self._dragged_tab.unbind_all('<Escape>')
            self._dragged_tab.unbind_all('<ButtonRelease-1>')
            self._dragged_tab.grid(**self._dummy_frame.grid_info())
            self._dragged_tab = None
            self._dummy_frame.grid_forget()

    def _menu_insert(self, tab, text):
        menu = []
        for t in self._tabs:
            menu.append((self.tab(t, 'text'), t))
        menu.sort()
        ind = menu.index((text, tab))
        self._tab_menu.insert_radiobutton(ind, label=text,
                                          variable=self._tab_var, value=tab,
                                          command=lambda t=tab: self._show(t))
        for i, (label, key) in enumerate(menu):
            self._tab_menu_entries[key] = i

    def _resize(self):
        """Resize the notebook so that all widgets can be displayed fully."""
        w, h = 0, 0
        for tab in self._visible_tabs:
            widget = self._tabs[tab]
            w = max(w, widget.winfo_reqwidth())
            h = max(h, widget.winfo_reqheight())
        w = max(w, self._tab_frame.winfo_reqwidth())
        self._canvas.configure(width=w)
        self._body.configure(width=w, height=h)
        self._on_configure()

    def _show(self, tab_id, new=False, update=False):
        if self.tab(tab_id, 'state') == 'disabled':
            if tab_id in self._active_tabs:
                self._active_tabs.remove(tab_id)
            return
        # hide current tab body
        if self._current_tab >= 0:
            self._tabs[self.current_tab].grid_remove()
            self._tab_labels[self.current_tab].state(['!selected'])

        # restore tab if hidden
        if tab_id in self._hidden_tabs:
            self._tab_labels[tab_id].grid(in_=self._tab_frame)
            self._visible_tabs.insert(self._tab_labels[tab_id].grid_info()['column'], tab_id)
            self._active_tabs = [t for t in self._visible_tabs
                                 if self._tab_options[t]['state'] == 'normal']
            self._hidden_tabs.remove(tab_id)

        # update current tab
        self.current_tab = tab_id
        self._tab_var.set(tab_id)
        self._tab_labels[tab_id].state(['selected'])

        if new:
            # add new tab
            c = self._tab_frame.grid_size()[0]
            self._tab_labels[tab_id].grid(in_=self._tab_frame, row=0, column=c, sticky='s')
            self._visible_tabs.append(tab_id)

        self.update_idletasks()
        self._on_configure()
        # ensure tab visibility
        self.see(tab_id)
        # display body
        if update:
            sticky = self._tab_options[tab_id]['sticky']
            pad = self._tab_options[tab_id]['padding']
            self._tabs[tab_id].grid(in_=self._body, sticky=sticky, padx=pad, pady=pad)
        else:
            self._tabs[tab_id].grid(in_=self._body)
        self.update_idletasks()
        self.event_generate('<<NotebookTabChanged>>')

    def _popup_menu(self, event, tab):
        pass # to be overriden in subclass

    @property
    def current_tab(self):
        return self._current_tab

    @current_tab.setter
    def current_tab(self, tab_nb):
        self._current_tab = tab_nb
        self._tab_var.set(tab_nb)

    def cget(self, key):
        if key == 'closebutton':
            return self._closebutton
        if key == 'closecommand':
            return self._closecommand
        if key == 'tabmenu':
            return self._tabmenu
        if key == 'tabdrag':
            return self._tabdrag
        return ttk.Frame.cget(self, key)

    def configure(self, cnf=None, **kw):
        if cnf:
            kwargs = cnf.copy()
            kwargs.update(kw)
        else:
            kwargs = kw.copy()
        tab_kw = {}
        if 'closebutton' in kwargs:
            self._closebutton = bool(kwargs.pop('closebutton'))
            tab_kw['closebutton'] = self._closebutton
        if 'closecommand' in kwargs:
            self._closecommand = kwargs.pop('closecommand')
            tab_kw['closecommand'] = self._closecommand
        if 'tabdrag' in kwargs:
            self._tabdrag = bool(kwargs.pop('tabdrag'))
        if 'tabmenu' in kwargs:
            self._tabmenu = bool(kwargs.pop('tabmenu'))
            if self._tabmenu:
                self._tab_list.grid()
            else:
                self._tab_list.grid_remove()
            self.update_idletasks()
            self._on_configure()
        if tab_kw:
            for tab, label in self._tab_labels.items():
                label.tab_configure(**tab_kw)
            self.update_idletasks()
        ttk.Frame.configure(self, **kwargs)

    def keys(self):
        keys = ttk.Frame.keys(self)
        return keys + ['closebutton', 'closecommand', 'tabmenu']

    def busy(self, busy, tab=False):
        """Toggle busy cursor."""
        if busy:
            self.configure(cursor='watch')
            if tab:
                if self.current_tab >= 0:
                    self._tabs[self.current_tab].busy(True)
        else:
            self.configure(cursor='')
            if self.current_tab >= 0:
                self._tabs[self.current_tab].busy(False)

    def add(self, widget, **kwargs):
        """
        Add widget (or redisplay it if it was hidden) in the notebook and return
        the tab index.

        * text: tab label
        * image: tab image
        * compound: how the tab label and image are organized
        * sticky: for the widget inside the notebook
        * padding: padding (int) around the widget in the notebook
        * state: state ('normal' or 'disabled') of the tab
        """
        # Todo: underline
        name = str(widget)
        if name in self._indexes:
            ind = self._indexes[name]
            self.tab(ind, **kwargs)
            self._show(ind)
            self.update_idletasks()
        else:
            sticky = kwargs.pop('sticky', 'ewns')
            padding = kwargs.pop('padding', 0)
            self._tabs[self._nb_tab] = widget
            ind = self._nb_tab
            self._indexes[name] = ind
            self._tab_labels[ind] = Tab(self._tab_frame2, tab_nb=ind,
                                        closecommand=self._closecommand,
                                        closebutton=self._closebutton,
                                        **kwargs)
            self._tab_labels[ind].bind('<ButtonRelease-1>', self._on_click)
            self._tab_labels[ind].bind('<ButtonRelease-3>', lambda e: self._popup_menu(e, ind))
            self._tab_labels[ind].bind('<ButtonPress-1>', lambda e: self._on_press(e, ind))
            self._body.configure(height=max(self._body.winfo_height(), widget.winfo_reqheight()),
                                 width=max(self._body.winfo_width(), widget.winfo_reqwidth()))

            self._tab_options[ind] = dict(text='', image='', compound='none', state='normal')
            self._tab_options[ind].update(kwargs)
            self._tab_options[ind].update(dict(padding=padding, sticky=sticky))
            self._tab_menu_entries[ind] = self._tab_menu.index('end')
            self._tab_list.state(['!disabled'])
            self._active_tabs.append(ind)
            self._show(self._nb_tab, new=True, update=True)

            self._nb_tab += 1
            self._menu_insert(ind, kwargs.get('text', ''))
        return ind

    def insert(self, where, widget, **kwargs):
        """
        Insert WIDEGT at the position given by WHERE in the notebook.

        For keyword options, see add method.
        """
        # existing = str(widget) in self._indexes
        index = self.add(widget, **kwargs)
        if where == 'end':
            where = len(self._visible_tabs)
        print(self._visible_tabs)
        self._visible_tabs.remove(index)
        self._visible_tabs.insert(where, index)
        print(self._visible_tabs)
        for i in range(where, len(self._visible_tabs)):
            ind = self._visible_tabs[i]
            self._tab_labels[ind].grid_configure(column=i)
        self.update_idletasks()
        self._on_configure()

    def enable_traversal(self):
        self.bind('<Control-Tab>', lambda e: self.select_next(True))
        self.bind('<Shift-Control-ISO_Left_Tab>', lambda e: self.select_prev(True))

    def index(self, tab_id):
        """Return the tab index of TAB_ID."""
        if tab_id == tk.END:
            return len(self._tabs)
        if tab_id == tk.CURRENT:
            return self.current_tab
        if tab_id in self._tabs:
            return tab_id
        try:
            return self._indexes[str(tab_id)]
        except KeyError:
            raise ValueError('No such tab in the Notebook: %s' % tab_id)

    def select_next(self, rotate=False):
        """Go to next tab."""
        if self.current_tab >= 0:
            index = self._visible_tabs.index(self.current_tab)
            index += 1
            if index < len(self._visible_tabs):
                self._show(self._visible_tabs[index])
            elif rotate:
                self._show(self._visible_tabs[0])

    def select_prev(self, rotate=False):
        """Go to prev tab."""
        if self.current_tab >= 0:
            index = self._visible_tabs.index(self.current_tab)
            index -= 1
            if index >= 0:
                self._show(self._visible_tabs[index])
            elif rotate:
                self._show(self._visible_tabs[-1])

    def see(self, tab_id):
        """Make label of tab TAB_ID visible."""
        if tab_id < 0:
            return
        tab = self.index(tab_id)
        w = self._tab_frame.winfo_reqwidth()
        label = self._tab_labels[tab]
        x1 = label.winfo_x() / w
        x2 = x1 + label.winfo_reqwidth() / w
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

    def hide(self, tab_id):
        """Hide tab TAB_ID."""
        tab = self.index(tab_id)
        if tab in self._visible_tabs:
            self._visible_tabs.remove(tab)
            index = self._active_tabs.index(tab)
            if tab in self._active_tabs:
                self._active_tabs.remove(tab)
            self._hidden_tabs.append(tab)
            self._tab_labels[tab].grid_remove()
            if self.current_tab == tab:
                if self._active_tabs:
                    self._show(self._active_tabs[max(index - 1, 0)])
                else:
                    self.current_tab = -1
                self._tabs[tab].grid_remove()
            self.update_idletasks()
            self._on_configure()
            self._resize()

    def forget(self, tab_id):
        """Remove tab TAB_ID from notebook."""
        tab = self.index(tab_id)
        if tab in self._hidden_tabs:
            self._hidden_tabs.remove(tab)
        elif tab in self._visible_tabs:
            index = self._active_tabs.index(tab)
            if tab in self._active_tabs:
                self._active_tabs.remove(tab)
            self._visible_tabs.remove(tab)
            self._tab_labels[tab].grid_forget()
            if self.current_tab == tab:
                if self._active_tabs:
                    self._show(self._active_tabs[max(index - 1, 0)])
                else:
                    self.current_tab = -1
                    if not self._visible_tabs and not self._hidden_tabs:
                        self._tab_list.state(['disabled'])
                self._tabs[tab].grid_forget()
        del self._tab_labels[tab]
        del self._indexes[str(self._tabs[tab])]
        del self._tabs[tab]
        self.update_idletasks()
        self._on_configure()
        i = self._tab_menu_entries[tab]
        for t, ind in self._tab_menu_entries.items():
            if ind > i:
                self._tab_menu_entries[t] -= 1
        self._tab_menu.delete(self._tab_menu_entries[tab])
        del self._tab_menu_entries[tab]
        self._resize()

    def select(self, tab_id=None):
        """Select tab TAB_ID. If TAB_ID is None, return currently selected tab."""
        if tab_id is None:
            return self.current_tab
        self._show(self.index(tab_id))

    def tab(self, tab_id, option=None, **kw):
        """
        Query or modify TAB_ID options.

        The widget corresponding to tab_id can be obtained by passing the option
        'widget' but cannot be modified.
        """
        tab = self.index(tab_id)
        if option == 'widget':
            return self._tabs[tab]
        if option:
            return self._tab_options[tab][option]

        self._tab_options[tab].update(kw)
        sticky = kw.pop('padding', None)
        padding = kw.pop('sticky', None)
        self._tab_labels[tab].tab_configure(**kw)
        if sticky is not None or padding is not None and self.current_tab == tab:
            self._show(tab, update=True)
        if 'text' in kw:
            self._tab_menu.delete(self._tab_menu_entries[tab])
            self._menu_insert(tab, kw['text'])
        if 'state' in kw:
            self._tab_menu.entryconfigure(self._tab_menu_entries[tab],
                                          state=kw['state'])
            if kw['state'] == 'disabled':
                if tab in self._active_tabs:
                    self._active_tabs.remove(tab)
                if tab == self.current_tab:
                    tabs = self._visible_tabs.copy()
                    if tab in tabs:
                        tabs.remove(tab)
                    if tabs:
                        self._show(tabs[0])
                    else:
                        self._tabs[tab].grid_remove()
                        self.current_tab = -1
            else:
                self._active_tabs = [t for t in self._visible_tabs
                                     if self._tab_options[t]['state'] == 'normal']
                if self.current_tab == -1:
                    self._show(tab)

    def tabs(self):
        """Return the tuple of visible tab ids in the order of display."""
        return tuple(self._visible_tabs)

    def tab_bind(self, tab, sequence=None, func=None, add=None, bind_all=True):
        """
        Bind to the TAB label at event SEQUENCE a call to function FUNC.

        An additional boolean parameter ADD specifies whether FUNC will be
        called additionally to the other bound function or whether it will
        replace the previous function. See bind for the return value.

        If BIND_ALL is true, bind both the Frame and the Label of the tab,
        otherwise, bind only to the Frame.
        """
        self._tab_labels[tab].bind(sequence, func, add, bind_all)

    def tab_unbind(self, tab, sequence, funcids=(None, None)):
        """Unbind for the TAB label for event SEQUENCE."""
        self._tab_labels[tab].unbind(sequence, funcids)

