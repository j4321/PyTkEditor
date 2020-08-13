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


Tooltips
"""
import tkinter as tk
from tkinter import ttk

from pytkeditorlib.utils.constants import get_screen


class Tooltip(tk.Toplevel):
    """Tooltip to display when the mouse stays long enough on an item."""
    def __init__(self, parent, **kwargs):
        """
        Create Tooltip.

        Options:
            * parent: parent window
            * title
            * titlestyle
            * borderwidth
            * bordercolor
            * image: PhotoImage/BitmapImage to display in the tooltip
            * text: text (str) to display in the tooltip
            * compound: relative orientation of the graphic relative to the text
            * alpha: opacity of the tooltip (0 for transparent, 1 for opaque),
                     the text is affected too, so 0 would mean an invisible tooltip
        """
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.attributes('-type', 'tooltip')
        self.attributes('-alpha', kwargs.get('alpha', 0.85))
        self.overrideredirect(True)
        self.configure(padx=kwargs.get('borderwidth', 1))
        self.configure(pady=kwargs.get('borderwidth', 1))
        self.configure(bg=kwargs.get('bordercolor', 'black'))

        self.style = ttk.Style(self)
        frame = ttk.Frame(self, padding=4, style='tooltip.TFrame')
        frame.pack()

        self.image = kwargs.get('image', None)
        title = kwargs.get('title', '')
        titlestyle = kwargs.get('titlestyle', 'title.tooltip.TLabel')
        self.title = ttk.Label(frame, text=title, style=titlestyle)
        if title:
            self.title.pack(fill='x', side='top')
            ttk.Separator(frame, orient='horizontal').pack(fill='x', side='top')
        self.label = ttk.Label(frame, text=kwargs.get('text', ''), image=self.image,
                               style='tooltip.TLabel',
                               compound=kwargs.get('compound', 'left'))
        self.label.pack(fill='x', side='bottom')

    def __getitem__(self, key):
        return self.cget(key)

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def deiconify(self):
        """Only deiconify tooltip if it constains text."""
        if self['text']:
            tk.Toplevel.deiconify(self)

    def cget(self, key):
        if key == 'text':
            return self.label.cget('text')
        if key == 'title':
            return self.title.cget('text')
        if key == 'image':
            return self.label.cget('image')
        if key == 'alpha':
            return self.attributes('-alpha')
        return tk.Toplevel.cget(self, key)

    def configure(self, cnf=None, **kw):
        kwargs = {}
        if cnf:
            kwargs.update(cnf)
        kwargs.update(kw)
        if 'text' in kwargs:
            self.label.configure(text=kwargs.pop('text'))
        if 'title' in kwargs:
            self.title.configure(text=kwargs.pop('title'))
        if 'image' in kwargs:
            self.label.configure(image=kwargs.pop('image'))
        if 'alpha' in kwargs:
            self.attributes('-alpha', kwargs.pop('alpha'))
        tk.Toplevel.configure(self, **kwargs)


class TooltipBaseWrapper:
    """Base class for tooltip wrapper."""
    def __init__(self, master, delay=1000, **kwargs):
        """
        Create a Tooltip wrapper with parent master.

        Options:

            * delay: hover delay before displaying the tooltip (ms)
            * all keyword arguments of a Tooltip

        """
        self.master = master
        self.tooltips = {}  # {object name: tooltip text, ...}
        # keep track of binding ids to cleanly remove them
        self.bind_enter_ids = {}  # {object name: bind id, ...}
        self.bind_leave_ids = {}  # {object name: bind id, ...}

        # time delay before displaying the tooltip
        self._delay = int(delay)
        self._timer_id = None

        self.tooltip = Tooltip(master, **kwargs)
        self.tooltip.withdraw()

        self._current = None

        self.tooltip.bind('<Leave>', self._on_leave_tooltip)
        self.tooltip.bind('<Destroy>', self.quit)  # cleanly remove all bindings and scheduled callbacks

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def __getitem__(self, key):
        return self.cget(key)

    def cget(self, key):
        if key == 'delay':
            return self._delay
        return self.tooltip.cget(key)

    def configure(self, **kwargs):
        try:
            self._delay = int(kwargs.pop('delay', self._delay))
        except ValueError:
            raise ValueError('expected integer for the delay option.')
        self.tooltip.configure(**kwargs)

    def _bind(self, object_id, sequence, function):
        """
        Bind to object at event sequence a call to function function.

        Return identifier
        """
        return ''

    def _unbind(self, object_id, sequence, funcid):
        """Unbind for object for event sequence and delete the associated funcid."""

    @staticmethod
    def _obj_to_id(obj):
        """Return id corresponding to object."""
        return obj

    def _tooltip_pos(self):
        """Return tooltip position."""
        x = self.master.winfo_pointerx() + 14
        y = self.master.winfo_pointery() + 14

        h = self.tooltip.winfo_reqheight()
        w = self.tooltip.winfo_reqwidth()

        screen = get_screen(*self.tooltip.winfo_pointerxy())

        if y + h > screen[3]:
            y -= h
        if x + w > screen[2]:
            x -= w

        return x, y

    def add_tooltip(self, obj, text):
        """Add new object to wrapper."""
        object_id = self._obj_to_id(obj)
        self.tooltips[object_id] = text
        self.bind_enter_ids[object_id] = self._bind(object_id, '<Enter>',
                                                    lambda e: self._on_enter(e, object_id))
        self.bind_leave_ids[object_id] = self._bind(object_id, '<Leave>',
                                                    self._on_leave)

    def remove_tooltip(self, object_id):
        """Remove object from wrapper."""
        try:
            del self.tooltips[object_id]
            self._unbind(object_id, '<Enter>', self.bind_enter_ids[object_id])
            self._unbind(object_id, '<Leave>', self.bind_leave_ids[object_id])
            del self.bind_enter_ids[object_id]
            del self.bind_leave_ids[object_id]
            if self._current == object_id:
                self._current = None
        except KeyError:
            pass

    def set_tooltip_text(self, object_id, text):
        """Change tooltip text for given object."""
        self.tooltips[object_id] = text

    def remove_all(self):
        """Remove all tooltips."""
        for object_id in self.tooltips:
            self._unbind(object_id, '<Enter>', self.bind_enter_ids[object_id])
            self._unbind(object_id, '<Leave>', self.bind_leave_ids[object_id])
        self.tooltips.clear()
        self.bind_enter_ids.clear()
        self.bind_leave_ids.clear()

    def _on_enter(self, event, object_id):
        """Change current object and launch timer to display tooltip."""
        if not self.tooltip.winfo_ismapped():
            self._timer_id = self.master.after(self._delay, self.display_tooltip)
            self._current = object_id

    def _on_leave(self, event):
        """Hide tooltip if visible or cancel tooltip display."""
        if self.tooltip.winfo_ismapped():
            x, y = event.widget.winfo_pointerxy()
            try:
                if event.widget.winfo_containing(x, y) != self.tooltip:
                    self.tooltip.withdraw()
            except KeyError:
                self.tooltip.withdraw()
        else:
            try:
                self.master.after_cancel(self._timer_id)
            except ValueError:
                pass
        self._current = None

    def _on_leave_tooltip(self, event):
        """Hide tooltip."""
        x, y = event.widget.winfo_pointerxy()
        try:
            if event.widget.winfo_containing(x, y) != self.tooltip:
                self.tooltip.withdraw()
        except KeyError:
            self.tooltip.withdraw()

    def display_tooltip(self):
        """Display tooltip with text corresponding to current widget."""
        if self._current is not None:
            self.tooltip['text'] = self.tooltips[self._current]
            self.tooltip.update_idletasks()
            self.tooltip.geometry('+%i+%i' % (self._tooltip_pos()))
            self.tooltip.deiconify()

    def quit(self, event=None):
        """Remove all bindings and cancel timer."""
        try:
            self.master.after_cancel(self._timer_id)
        except ValueError:
            pass
        self.remove_all()


class TooltipWrapper(TooltipBaseWrapper):
    """Wrapper for tooltips displayed when the mouse hovers over widgets."""

    def _bind(self, object_id, sequence, function):
        """
        Bind to object at event sequence a call to function function.

        Return identifier
        """
        widget = self.master.nametowidget(object_id)
        return widget.bind(sequence, function)

    def _unbind(self, object_id, sequence, funcid):
        """Unbind for object for event sequence."""
        widget = self.master.nametowidget(object_id)
        widget.unbind(sequence, funcid)

    @staticmethod
    def _obj_to_id(obj):
        """Return id corresponding to object."""
        return str(obj)

    def _tooltip_pos(self):
        """Return tooltip position."""
        widget = self.master.nametowidget(self._current)
        x = widget.winfo_pointerx() + 14
        y = widget.winfo_rooty() + widget.winfo_height() + 2

        h = self.tooltip.winfo_reqheight()
        w = self.tooltip.winfo_reqwidth()

        screen = get_screen(*self.tooltip.winfo_pointerxy())

        if y + h > screen[3]:
            y = widget.winfo_rooty() - h
        if x + w > screen[2]:
            x = widget.winfo_pointerx() - w
        return x, y


class TooltipTextWrapper(TooltipBaseWrapper):
    """Tooltip wrapper for a Text widget."""

    def _bind(self, object_id, sequence, function):
        """
        Bind to object at event sequence a call to function function.

        Return identifier
        """
        return self.master.tag_bind(object_id, sequence, function)

    def _unbind(self, object_id, sequence, funcid):
        """Unbind for object for event sequence."""
        self.master.tag_unbind(object_id, sequence, funcid)

    def _tooltip_pos(self):
        """Return tooltip position."""
        x_b, y_b, w, h = self.master.bbox(self.master.tag_ranges(self._current)[-1])
        x_r = self.master.winfo_rootx()
        y_r = self.master.winfo_rooty()
        h_t = self.tooltip.winfo_reqheight()
        screen = get_screen(x_r, y_r)
        y = y_r + y_b + h
        x = x_r + x_b + w
        if y + h_t > screen[3]:
            y = y_r + y_b - h_t
        return x, y


class TooltipNotebookWrapper(TooltipBaseWrapper):
    """Tooltip wrapper for a Notebook widget."""

    def _bind(self, object_id, sequence, function):
        """
        Bind to object at event sequence a call to function function.

        Return identifier
        """
        return self.master.tab_bind(object_id, sequence, function, bind_all=False)

    def _unbind(self, object_id, sequence, funcid):
        """Unbind for object for event sequence and delete the associated funcid."""
        self.master.tab_unbind(object_id, sequence, funcid)
