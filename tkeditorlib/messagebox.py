#! /usr/bin/python3
# -*- coding:Utf-8 -*-
"""
TkEditor - Python IDE
Copyright 2018 Juliette Monsel <j_4321@protonmail.com>

TkEditor is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

TkEditor is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Custom tkinter messageboxes
"""


from webbrowser import open as url_open
import tkinter as tk
from tkinter import ttk
from .autoscrollbar import AutoHideScrollbar as Scrollbar
from .constants import ICONS, REPORT_URL, CONFIG


def _(txt):
    return txt


class OneButtonBox(tk.Toplevel):
    def __init__(self, parent=None, title="", message="", button=_("Ok"), image=None):
        """
        Create a message box with one button.

        Arguments:
            parent: parent of the toplevel window
            title: message box title
            message: message box text (that can be selected)
            button: message displayed on the button
            image: image displayed at the left of the message, either a PhotoImage or a string
        """
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.resizable(False, False)
        self.title(title)
        self.result = ""
        self.button = button
        if isinstance(image, str):
            data = ICONS.get(image)
            if data:
                self.img = tk.PhotoImage(master=self, data=data)
            else:
                self.img = tk.PhotoImage(master=self, file=image)
            image = self.img
        frame = ttk.Frame(self)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        l = len(message)
        w = max(1, min(l, 50))
        h = 0
        for line in message.splitlines():
            h += 1 + len(line) // w
        if h < 3:
            w = min(l, 35)
            h = 0
            for line in message.splitlines():
                h += 1 + len(line) // w
        theme_name = '{} Theme'.format(CONFIG.get('General', 'theme').capitalize())
        fg = CONFIG.get(theme_name, 'fg')
        display = tk.Text(frame, font="TkDefaultFont 10 bold", fg=fg,
                          height=h, width=w, wrap="word")
        display.configure(inactiveselectbackground=display.cget("selectbackground"))
        display.insert("1.0", message)
        display.configure(state="disabled")
        display.grid(row=0, column=1, pady=(10, 4), padx=4, sticky="ewns")
        display.update_idletasks()
        if display.bbox('end-1c') is None:
            display.configure(height=h + 1)
        display.bind("<Button-1>", lambda event: display.focus_set())
        if image:
            ttk.Label(frame, image=image).grid(row=0, column=0, padx=4, pady=(10, 4))
        b = ttk.Button(self, text=button, command=self.validate)
        frame.pack()
        b.pack(padx=10, pady=10)
        self.grab_set()
        b.focus_set()

    def validate(self):
        self.result = self.button
        self.destroy()

    def get_result(self):
        return self.result


class ShowError(tk.Toplevel):
    def __init__(self, parent=None, title="", message="", traceback="",
                 report_msg=False, button=_("Ok"), image="error"):
        """
        Create an error messagebox.
        Arguments:
            parent: parent of the toplevel window
            title: message box title
            message: message box text (that can be selected)
            button: message displayed on the button
            traceback: error traceback to display below the error message
            report_msg: if True display a suggestion to report error
            image: image displayed at the left of the message, either a PhotoImage or a string
        """
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.resizable(False, False)
        self.title(title)
        self.result = ""
        self.button = button

        # --- style
        theme_name = '{} Theme'.format(CONFIG.get('General', 'theme').capitalize())
        fg = CONFIG.get(theme_name, 'fg')
        fieldbg = CONFIG.get(theme_name, 'fieldbg')

        if not parent:
            style = ttk.Style(self)
            style.theme_use('clam')
            style.configure("url.TLabel", foreground="blue")
            style.configure("txt.TFrame", background='white')

        if isinstance(image, str):
            data = ICONS.get(image)
            if data:
                self.img = tk.PhotoImage(master=self, data=data)
            else:
                self.img = tk.PhotoImage(master=self, file=image)
            image = self.img
        frame = ttk.Frame(self)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        l = len(message)
        l2 = len(traceback)
        w = max(1, min(max(l, l2), 50))
        if not l2 and l // w < 3:
            w = 35
        h = 0
        for line in message.splitlines():
            h += 1 + len(line) // w
        h2 = 0
        for line in traceback.splitlines():
            h2 += 1 + len(line) // w

        display = tk.Text(frame, font="TkDefaultFont 10 bold", fg=fg,
                          height=h, width=w, wrap="word")
        display.configure(inactiveselectbackground=display.cget("selectbackground"))
        display.insert("1.0", message)
        display.configure(state="disabled")
        display.grid(row=0, column=1, pady=(10, 4), padx=4, sticky="ewns")
        display.bind("<Button-1>", lambda event: display.focus_set())
        display.update_idletasks()
        if display.bbox('end-1c') is None:
            display.configure(height=h + 1)
        if image:
            ttk.Label(frame, image=image).grid(row=0, column=0, padx=4, pady=(10, 4))
        frame.pack(fill='x')

        if traceback:
            frame2 = ttk.Frame(self)
            frame2.columnconfigure(0, weight=1)
            frame2.rowconfigure(0, weight=1)
            txt_frame = ttk.Frame(frame2, style='txt.TFrame', relief='sunken', borderwidth=1)
            error_msg = tk.Text(txt_frame, width=w, wrap='word', font="TkDefaultFont 10",
                                bg=fieldbg, fg=fg, height=8)
            error_msg.bind("<Button-1>", lambda event: error_msg.focus_set())
            error_msg.insert('1.0', traceback)
            error_msg.configure(state="disabled")
            scrolly = Scrollbar(frame2, orient='vertical',
                                command=error_msg.yview)
            scrolly.grid(row=0, column=1, sticky='ns')
            scrollx = Scrollbar(frame2, orient='horizontal',
                                command=error_msg.xview)
            scrollx.grid(row=1, column=0, sticky='ew')
            error_msg.configure(yscrollcommand=scrolly.set,
                                xscrollcommand=scrollx.set)
            error_msg.pack(side='left', fill='both', expand=True)
            txt_frame.grid(row=0, column=0, sticky='ewsn')
            frame2.pack(fill='both', padx=4, pady=(4, 4))
        if report_msg:
            report_frame = ttk.Frame(self)
            ttk.Label(report_frame, text=_("Please report this bug on ")).pack(side="left")
            url = ttk.Label(report_frame, style="url.TLabel", cursor="hand1",
                            font="TkDefaultFont 10 underline",
                            text=REPORT_URL)
            url.pack(side="left")
            url.bind("<Button-1>", lambda e: url_open(REPORT_URL))
            report_frame.pack(fill="x", padx=4, pady=(4, 0))
        b = ttk.Button(self, text=button, command=self.validate)
        b.pack(padx=10, pady=(4, 10))
        self.update_idletasks()
        self.set_hight(display, h)
        self.grab_set()
        b.focus_set()

    def set_hight(self, display, h):
        bbox = display.bbox('end - 1c')
        if bbox is None:
            self.after(10, self.set_hight, display, h)
        elif display.winfo_height() - bbox[1] - bbox[3] > 10:
            display.configure(height=h - 1)

    def validate(self):
        self.result = self.button
        self.destroy()

    def get_result(self):
        return self.result


class TwoButtonBox(tk.Toplevel):
    """Messagebox with two buttons."""

    def __init__(self, parent, title="", message="", button1=_("Yes"),
                 button2=_("No"), image=None):
        """
        Create a messagebox with two buttons.

        Arguments:
            parent: parent of the toplevel window
            title: message box title
            message: message box text
            button1/2: message displayed on the first/second button
            image: image displayed at the left of the message
        """

        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.resizable(False, False)
        self.title(title)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.result = ""
        self.button1 = button1
        self.button2 = button2

        if isinstance(image, str):
            data = ICONS.get(image)
            if data:
                self.img = tk.PhotoImage(master=self, data=data)
            else:
                self.img = tk.PhotoImage(master=self, file=image)
            image = self.img
        frame = ttk.Frame(self)
        frame.grid(row=0, columnspan=2, sticky="ewsn")
        if image:
            ttk.Label(frame, image=image).pack(side="left", padx=(10, 4), pady=(10, 4))
        ttk.Label(frame, text=message, font="TkDefaultFont 10 bold",
                  wraplength=335).pack(side="left", padx=(4, 10), pady=(10, 4))

        b1 = ttk.Button(self, text=button1, command=self.command1)
        b1.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        ttk.Button(self, text=button2,
                   command=self.command2).grid(row=1, column=1, padx=10, pady=10,
                                               sticky="w")
        self.grab_set()
        b1.focus_set()

    def command1(self):
        self.result = self.button1
        self.destroy()

    def command2(self):
        self.result = self.button2
        self.destroy()

    def get_result(self):
        return self.result


class AskYesNoCancel(tk.Toplevel):
    """Messagebox with two buttons."""

    def __init__(self, parent, title="", message="", image=None,
                 button1=_("Yes"), button2=_("No"), button3=_("Cancel")):
        """
        Create a messagebox with three buttons.

        Arguments:
            parent: parent of the toplevel window
            title: message box title
            message: message box text
            button1/2: message displayed on the first/second button
            image: image displayed at the left of the message
        """

        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.resizable(False, False)
        self.title(title)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.result = None

        if isinstance(image, str):
            data = ICONS.get(image)
            if data:
                self.img = tk.PhotoImage(master=self, data=data)
            else:
                self.img = tk.PhotoImage(master=self, file=image)
            image = self.img
        frame = ttk.Frame(self)
        frame.grid(row=0, columnspan=3, sticky="ewsn")
        if image:
            ttk.Label(frame, image=image).pack(side="left", padx=(10, 4), pady=(10, 4))
        ttk.Label(frame, text=message, font="TkDefaultFont 10 bold",
                  wraplength=335).pack(side="left", padx=(4, 10), pady=(10, 4))

        b1 = ttk.Button(self, text=button1, command=self.command1)
        b1.grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(self, text=button2, command=self.command2).grid(row=1, column=1,
                                                                   padx=10, pady=10)
        ttk.Button(self, text=button3, command=self.destroy).grid(row=1, column=2,
                                                                  padx=10, pady=10)
        self.grab_set()
        b1.focus_set()

    def command1(self):
        self.result = True
        self.destroy()

    def command2(self):
        self.result = False
        self.destroy()

    def get_result(self):
        return self.result


def showmessage(title="", message="", parent=None, button=_("Ok"), image=None):
    """
    Display a dialog with a single button.

    Return the text of the button ("Ok" by default)

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
        button: text displayed on the button
        image: image to display on the left of the message, either a PhotoImage
               or a string ('information', 'error', 'question', 'warning' or
               image path)
    """
    box = OneButtonBox(parent, title, message, button, image)
    box.wait_window(box)
    return box.get_result()


def showerror(title="", message="", traceback="", report_msg=False, parent=None):
    """
    Display an error dialog.

    Return "Ok"

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        traceback: error traceback to display below the error message
        report_msg: if True display a suggestion to report error
        parent: parent window
    """
    box = ShowError(parent, title, message, traceback, report_msg)
    box.wait_window(box)
    return box.get_result()


def showinfo(title="", message="", parent=None):
    """
    Display an information dialog with a single button.

    Return "Ok".

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
    """
    return showmessage(title, message, parent, image="information")


def askokcancel(title="", message="", parent=None, icon="question"):
    """
    Display a dialog with buttons "Ok" and "Cancel".

    Return True if "Ok" is selected, False otherwise.

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
        icon: icon to display on the left of the message, either a PhotoImage
              or a string ('information', 'error', 'question', 'warning' or
               mage path)
    """
    box = TwoButtonBox(parent, title, message, _("Ok"), _("Cancel"), icon)
    box.wait_window(box)
    return box.get_result() == _("Ok")


def askyesno(title="", message="", parent=None, icon="question"):
    """
    Display a dialog with buttons "Ok" and "Cancel".

    Return True if "Ok" is selected, False otherwise.

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
        icon: icon to display on the left of the message, either a PhotoImage
              or a string ('information', 'error', 'question', 'warning' or
               mage path)
    """
    box = TwoButtonBox(parent, title, message, _("Yes"), _("No"), icon)
    box.wait_window(box)
    return box.get_result() == _("Yes")


def askyesnocancel(title="", message="", parent=None, icon="question"):
    """
    Display a dialog with buttons "Yes","No" and "Cancel".

    Return True if "Ok" is selected, False if "No" is selected, None otherwise.

    Arguments:
        title: dialog title
        message: message displayed in the dialog
        parent: parent window
        icon: icon to display on the left of the message, either a PhotoImage
              or a string ('information', 'error', 'question', 'warning' or
               mage path)
    """
    box = AskYesNoCancel(parent, title, message, image=icon)
    box.wait_window(box)
    return box.get_result()
