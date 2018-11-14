import tkinter as tk
from tkinter import ttk
from tkeditorlib.constants import get_screen


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

        self.im = kwargs.get('image', None)
        title = kwargs.get('title', '')
        titlestyle = kwargs.get('titlestyle', 'title.tooltip.TLabel')
        self.title = ttk.Label(frame, text=title, style=titlestyle)
        if title:
            self.title.pack(fill='x', side='top')
            ttk.Separator(frame, orient='horizontal').pack(fill='x', side='top')
        self.label = ttk.Label(frame, text=kwargs.get('text', ''), image=self.im,
                               style='tooltip.TLabel',
                               compound=kwargs.get('compound', 'left'))
        self.label.pack(fill='x', side='bottom')

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def configure(self, **kwargs):
        if 'text' in kwargs:
            self.label.configure(text=kwargs.pop('text'))
        if 'title' in kwargs:
            self.title.configure(text=kwargs.pop('title'))
        if 'image' in kwargs:
            self.label.configure(image=kwargs.pop('image'))
        if 'alpha' in kwargs:
            self.attributes('-alpha', kwargs.pop('alpha'))
        tk.Toplevel.configure(self, **kwargs)


class TooltipTextWrapper:
    """Tooltip wrapper for a Treeview."""
    def __init__(self, text, delay=1000, **kwargs):
        """
        Create a Tooltip wrapper for the Treeview tree.

        This wrapper enables the creation of tooltips for tree's items with all
        the bindings to make them appear/disappear.

        Options:
            * text: wrapped Text
            * delay: hover delay before displaying the tooltip (ms)
            * all keyword arguments of a Tooltip
        """
        self.text = text
        self.delay = int(delay)
        self._timer_id = ''
        self.tooltip_text = {}
        self.tooltip_bind_ids = {}
        self.tooltip = Tooltip(text, **kwargs)
        self.tooltip.withdraw()

        self.tooltip.bind('<Leave>', self._on_leave_tooltip)

    def add_tooltip(self, tag, text):
        self.tooltip_text[tag] = text
        id1 = self.text.tag_bind(tag, '<Enter>', lambda e: self._on_enter(e, tag))
        id2 = self.text.tag_bind(tag, '<Leave>', lambda e: self._on_leave(e, tag))
        self.tooltip_bind_ids[tag] = (id1, id2)

    def _on_enter(self, event, tag):
        if not self.tooltip.winfo_ismapped():
            self._timer_id = event.widget.after(self.delay, self.display_tooltip, tag)

    def _on_leave(self, event, tag):
        if self.tooltip.winfo_ismapped():
            x, y = event.widget.winfo_pointerxy()
            try:
                if event.widget.winfo_containing(x, y) != self.tooltip:
                    self.tooltip.withdraw()
            except KeyError:
                self.tooltip.withdraw()
        else:
            try:
                event.widget.after_cancel(self._timer_id)
            except ValueError:
                pass

    def _on_leave_tooltip(self, event):
        x, y = event.widget.winfo_pointerxy()
        try:
            if event.widget.winfo_containing(x, y) != self.tooltip:
                self.tooltip.withdraw()
        except KeyError:
            self.tooltip.withdraw()

    def display_tooltip(self, tag):
        self.tooltip['text'] = self.tooltip_text[tag]
        self.tooltip.update_idletasks()
        xb, yb, w, h = self.text.bbox(self.text.tag_ranges(tag)[-1])
        xr = self.text.winfo_rootx()
        yr = self.text.winfo_rooty()
        ht = self.tooltip.winfo_reqheight()
        screen = get_screen(xr, yr)
        y = yr + yb + h
        x = xr + xb + w
        if y + ht > screen[3]:
            y = yr + yb - ht

        self.tooltip.geometry('+%i+%i' % (x, y))
        self.tooltip.deiconify()

    def reset(self):
        for tag, (id1, id2) in self.tooltip_bind_ids.items():
            self.text.tag_unbind(tag, '<Enter>', id1)
            self.text.tag_unbind(tag, '<Leave>', id2)
        self.tooltip_text.clear()
        self.tooltip_bind_ids.clear()


class TooltipNotebookWrapper:
    """
    Tooltip wrapper widget handle tooltip display when the mouse hovers over
    widgets.
    """
    def __init__(self, notebook, **kwargs):
        """
        Construct a Tooltip wrapper with parent master.

        Keyword Options
        ---------------

        Tooltip options,

        delay: time (ms) the mouse has to stay still over the widget before
        the Tooltip is displayed.

        """
        self.tooltips = {}  # {widget name: tooltip text, ...}
        # keep track of binding ids to cleanly remove them
        self.bind_enter_ids = {}  # {widget name: bind id, ...}
        self.bind_leave_ids = {}  # {widget name: bind id, ...}

        # time delay before displaying the tooltip
        self._delay = 1000
        self._timer_id = None

        self.notebook = notebook

        self.tooltip = Tooltip(notebook)
        self.tooltip.withdraw()
        # widget currently under the mouse if among wrapped widgets:
        self.current_tab = None

        self.configure(**kwargs)

        self.config = self.configure

        self.tooltip.bind('<Leave>', self._on_leave_tooltip)

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def __getitem__(self, key):
        return self.cget(key)

    def cget(self, key):
        if key == 'delay':
            return self._delay
        else:
            return self.tooltip.cget(key)

    def configure(self, **kwargs):
        try:
            self._delay = int(kwargs.pop('delay', self._delay))
        except ValueError:
            raise ValueError('expected integer for the delay option.')
        self.tooltip.configure(**kwargs)

    def add_tooltip(self, tab, text):
        """Add new widget to wrapper."""
        self.tooltips[tab] = text
        self.bind_enter_ids[tab] = ttk.Frame.bind(self.notebook._tab_labels[tab], '<Enter>', lambda e: self._on_enter(e, tab))
        self.bind_leave_ids[tab] = ttk.Frame.bind(self.notebook._tab_labels[tab], '<Leave>', lambda e: self._on_leave(e, tab))

    def set_tooltip_text(self, tab, text):
        """Change tooltip text for given widget."""
        self.tooltips[tab] = text

    def remove_all(self):
        """Remove all tooltips."""
        for tab in self.tooltips:
            ttk.Frame.unbind(self.notebook._tab_labels[tab], '<Enter>', self.bind_enter_ids[tab])
            ttk.Frame.unbind(self.notebook._tab_labels[tab], '<Leave>', self.bind_leave_ids[tab])
        self.tooltips.clear()
        self.bind_enter_ids.clear()
        self.bind_leave_ids.clear()

    def remove_tooltip(self, tab):
        """Remove widget from wrapper."""
        try:
            del self.tooltips[tab]
            ttk.Frame.unbind(self.notebook._tab_labels[tab], '<Enter>', self.bind_enter_ids[tab])
            ttk.Frame.unbind(self.notebook._tab_labels[tab], '<Leave>', self.bind_leave_ids[tab])
            del self.bind_enter_ids[tab]
            del self.bind_leave_ids[tab]
        except KeyError:
            pass

    def _on_enter(self, event, tab):
        """Change current widget and launch timer to display tooltip."""
        if not self.tooltip.winfo_ismapped():
            self._timer_id = self.notebook.after(self._delay, self.display_tooltip)
            self.current_tab = tab

    def _on_leave(self, event, tab):
        """Hide tooltip if visible or cancel tooltip display."""
        if self.tooltip.winfo_ismapped():
            x, y = self.notebook.winfo_pointerxy()
            if not self.notebook.winfo_containing(x, y) == self.tooltip:
                self.tooltip.withdraw()
        else:
            try:
                self.notebook.after_cancel(self._timer_id)
            except ValueError:
                pass
        self.current_tab = None

    def _on_leave_tooltip(self, event):
        """Hide tooltip."""
        if self.current_tab is None:
            return
        x, y = event.widget.winfo_pointerxy()
        if not event.widget.winfo_containing(x, y) in self.notebook._tab_labels[self.current_tab].children.values():
            self.tooltip.withdraw()

    def display_tooltip(self):
        """Display tooltip with text corresponding to current widget."""
        if self.current_tab is None:
            return
        disabled = "disabled" in self.notebook.state()

        if not disabled:
            self.tooltip['text'] = self.tooltips[self.current_tab]
            self.tooltip.deiconify()
            x = self.notebook.winfo_pointerx() + 14
            y = self.notebook.winfo_pointery() + 14
            self.tooltip.geometry('+%i+%i' % (x, y))
