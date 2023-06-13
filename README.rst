PyTkEditor
==========
Copyright 2018-2020 Juliette Monsel <j_4321 at protonmail dot com>

Python3 IDE written with Tkinter for Linux.

**Main features:**

    - Multi-tab code editor with line numbers

    - Widgets (can be hidden):

        + Rich text python console
        + Console history
        + Help widget to graphically display the help about objects from the console or the editor
        + File browser with filter on file extensions
        + Code structure (classes, functions, TODOs, cells, comments ``# ---``)

    - Autocompletion on tab in editor and console

    - Syntax highlighting (all pygments styles are supported) in editor, console and history

    - Search and replace (in single tab or whole session)

    - Run code in external terminal, embedded console or Jupyter QtConsole

    - Optional syntax and style (PEP8) checking

    - Color picker

    - Partially customizable layout (vertical or horizontal splitting with resizable panes)

    - Print file or export in HTML (preserving syntax highlighting)



**Disclaimer:** This is a project I made for fun and this IDE is not meant
to perform well or to be really stable. The console especially will
never reach the level of the IPython qtconsole. I add new features when
I have new ideas.

Quickstart
----------

**Requirement:** Linux

**Dependencies:**

    - openssl
    - Python 3 with Tkinter
    - `setuptools <https://pypi.org/project/setuptools/>`_ (install dependency)
    - `docutils <https://pypi.org/project/docutils/>`_
    - `ewmh <https://pypi.org/project/ewmh/>`_
    - `jedi <https://pypi.org/project/jedi/>`_
    - `pdfkit <https://pypi.org/project/pdfkit/>`_
    - `Pillow <https://pypi.org/project/Pillow/>`_
    - `pycodestyle <https://pypi.org/project/pycodestyle/>`_
    - `pycups <https://pypi.org/project/pycups/>`_
    - `pyflakes <https://pypi.org/project/pyflakes/>`_
    - `pygments <https://pypi.org/project/pygments/>`_
    - `tkfilebrowser <https://pypi.org/project/tkfilebrowser/>`_
    - `tkcolorpicker <https://pypi.org/project/tkcolorpicker/>`_
    - `python-xlib <https://pypi.org/project/python-xlib/>`_
    - `qtconsole <https://pypi.org/project/qtconsole/>`_ (optional: Execute in Jupyter QtConsole)

**Install:**

::

    $ sudo python3 setup.py install

though it will not be managed by your package manager.

You can also directly launch it without installing.

**Launch:**

If PyTkEditor is installed:

::

    $ pytkeditor [ files ]

or from the main menu *Development > PyTkEditor*.

Without installing:

::

    $ python3 pytkeditor [ files ]


Troubleshooting
---------------

If you encounter bugs or if you have suggestions, please open an issue
on `Github <https://github.com/j4321/PyTkEditor/issues>`_.
