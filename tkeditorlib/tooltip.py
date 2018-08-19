import tkinter as tk
from tkinter import ttk


class Tooltip(tk.Toplevel):
    """Tooltip to display when the mouse stays long enough on an item."""
    def __init__(self, parent, **kwargs):
        """
        Create Tooltip.

        Options:
            * parent: parent window
            * title
            * background: background color
            * foreground: foreground color
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
        self.attributes('-alpha', kwargs.get('alpha', 1))
        self.overrideredirect(True)
        self.configure(padx=kwargs.get('borderwidth', 1))
        self.configure(pady=kwargs.get('borderwidth', 1))
        self.configure(bg=kwargs.get('bordercolor', 'black'))

        self.style = ttk.Style(self)
        frame = ttk.Frame(self, padding=4, style='tooltip.TFrame')
        frame.pack()
        bg = kwargs.get('background', 'black')
        fg = kwargs.get('foreground', 'white')
        self.style.configure('tooltip.TLabel', background=bg)
        self.style.configure('tooltip.TFrame', background=bg)
        self.style.configure('tooltip.TLabel', foreground=fg)
        self.style.configure('title.tooltip.TLabel', foreground='#FF4D00')

        self.im = kwargs.get('image', None)
        title = kwargs.get('title', None)
        if title is not None:
            self.title = ttk.Label(frame, text=title, style='title.tooltip.TLabel',
                                   font='TkDefaultFont 9 bold')
            self.title.pack(fill='x')
            ttk.Separator(frame, orient='horizontal').pack(fill='x')
        self.label = ttk.Label(frame, text=kwargs.get('text', ''), image=self.im,
                               style='tooltip.TLabel',
                               compound=kwargs.get('compound', 'left'))
        self.label.pack(fill='x')

    def __setitem__(self, key, value):
        self.configure(**{key: value})

    def configure(self, **kwargs):
        if 'text' in kwargs:
            self.label.configure(text=kwargs.pop('text'))
        if 'title' in kwargs:
            self.title.configure(text=kwargs.pop('title'))
        if 'image' in kwargs:
            self.label.configure(image=kwargs.pop('image'))
        if 'background' in kwargs:
            self.style.configure('tooltip.TLabel', background=kwargs['background'])
            self.style.configure('tooltip.TFrame', background=kwargs['background'])
        if 'foreground' in kwargs:
            fg = kwargs.pop('foreground')
            self.style.configure('tooltip.TLabel', foreground=fg)
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
        self.delay = delay
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
        if event.widget.winfo_containing(x, y) != self.tooltip:
            self.tooltip.withdraw()

    def display_tooltip(self, tag):
        self.tooltip['text'] = self.tooltip_text[tag]
        self.tooltip.deiconify()
        x, y, w, h = self.text.bbox(self.text.tag_ranges(tag)[-1])
        self.tooltip.geometry('+%i+%i' % (x + w + self.text.winfo_rootx(),
                                          y + h + self.text.winfo_rooty()))

    def reset(self):
        for tag, (id1, id2) in self.tooltip_bind_ids.items():
            self.text.tag_unbind(tag, '<Enter>', id1)
            self.text.tag_unbind(tag, '<Leave>', id2)
        self.tooltip_text.clear()
        self.tooltip_bind_ids.clear()
