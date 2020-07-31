PyTkEditor
==========
Copyright 2018-2020 Juliette Monsel

Python3 IDE written with Tkinter for Linux.

.. note::

    This is a project I made for fun and this IDE is not meant to perform well
    or to be really stable. The console especially will never reach the level
    of the IPython qtconsole. I add new features when I have new ideas.

.. contents:: Table of Contents


Main features
-------------

    - Multi-tab code editor with line numbers

    - Widgets (can be hidden):

        + Rich text python console
        + Console history
        + Help widget to graphically display the help about objects from the console or the editor
        + File browser with filter on file extensions
        + Code analysis widget (available only if pylint is installed)
        + Code structure (classes, functions, TODOs, cells, comments ``# ---``)

    - Autocompletion on Tab key :kbd:`⇥` in editor and console

    - Syntax highlighting (all pygments styles are supported) in editor, console and history

    - Search and replace (in single tab or whole session)

    - Run code in external terminal, embedded console or Jupyter QtConsole (if installed)

    - Optional syntax and style (PEP8) checking

    - Color picker

    - Partially customizable layout (vertical or horizontal splitting with resizable panes)

    - Print file or export in HTML (preserving syntax highlighting)


Keyboard shortcuts
------------------

Global
~~~~~~

.. container:: twocol

    .. container:: leftside

        :kbd:`Ctrl` :kbd:`X`

        :kbd:`Ctrl` :kbd:`C`

        :kbd:`Ctrl` :kbd:`V`

        :kbd:`Ctrl` :kbd:`N`

        :kbd:`Ctrl` :kbd:`O`

        :kbd:`Ctrl` :kbd:`P`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`E`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`A`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`P`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`I`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`H`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`F`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`G`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`R`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`S`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`T`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`W`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`Q`

        :kbd:`F11`

        :kbd:`Alt`

    .. container:: rightside

        Cut

        Copy

        Paste

        New file

        Open file

        Open file switcher

        Switch to Editor

        Switch to Code analysis

        Switch to Console

        Switch to History

        Switch to Help

        Switch to File browser

        Switch to Code structure (Go to entry)

        Find and replace in whole session

        Save all files

        Open last closed file

        Close all files

        Quit

        Toggle fullscreen

        Show menubar if hidden

Editor
~~~~~~

.. container:: twocol

    .. container:: leftside

        :kbd:`⇥`

        :kbd:`Shift` :kbd:`⇥`

        :kbd:`Ctrl` :kbd:`Z`

        :kbd:`Ctrl` :kbd:`Y`

        :kbd:`Ctrl` :kbd:`A`

        :kbd:`Ctrl` :kbd:`E`

        :kbd:`Ctrl` :kbd:`D`

        :kbd:`Ctrl` :kbd:`K`

        :kbd:`Ctrl` :kbd:`I`

        :kbd:`Ctrl` :kbd:`F`

        :kbd:`Ctrl` :kbd:`R`

        :kbd:`Ctrl` :kbd:`L`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`P`

        :kbd:`Ctrl` :kbd:`S`

        :kbd:`Ctrl` :kbd:`Alt` :kbd:`S`

        :kbd:`Ctrl` :kbd:`U`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`U`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`C`

        :kbd:`Ctrl` :kbd:`⇥`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`⇥`

        :kbd:`Ctrl` :kbd:`↓`

        :kbd:`Ctrl` :kbd:`↑`

        :kbd:`Ctrl` :kbd:`⏎`

        :kbd:`Shift` :kbd:`⏎`

        :kbd:`F5`

        :kbd:`F9`

        :kbd:`F10`

    .. container:: rightside

        Autocomplete current word or indent line / selection

        Unindent line / selection

        Undo

        Redo

        Select all

        Toggle comment

        Duplicate line(s)

        Delete line(s)

        Inspect current object

        Find

        Replace

        Go to line

        Print

        Save

        Save as

        Upper case

        Lower case

        Open color picker

        Go to next file

        Go to previous file

        Go to next cell

        Go to previous cell

        Run current cell

        Run current cell and move to next

        Run file

        Run selection in Console

        Run selection in Jupyter QtConsole

Console
~~~~~~~

.. container:: twocol

    .. container:: leftside

        :kbd:`⇥`

        :kbd:`Shift` :kbd:`⇥`

        :kbd:`Ctrl` :kbd:`Z`

        :kbd:`Ctrl` :kbd:`Y`

        :kbd:`Ctrl` :kbd:`Shift` :kbd:`C`

        :kbd:`Ctrl` :kbd:`A`

        :kbd:`Ctrl` :kbd:`E`

        :kbd:`Ctrl` :kbd:`D`

        :kbd:`Ctrl` :kbd:`K`

        :kbd:`Ctrl` :kbd:`I`

        :kbd:`Ctrl` :kbd:`/`

        :kbd:`Ctrl` :kbd:`\\`

        :kbd:`Ctrl` :kbd:`⏎`

        :kbd:`Shift` :kbd:`⏎`

        :kbd:`Shift` :kbd:`Esc`

        :kbd:`Ctrl` :kbd:`L`

        :kbd:`Ctrl` :kbd:`.`

    .. container:: rightside

        Autocomplete current word or indent line / selection

        Unindent line / selection

        Undo

        Redo

        Copy raw text

        Go to the start of the line

        Go to the end of the line

        Delete the character on the right of the insertion cursor

        Delete the end of line

        Inspect current object

        Select all

        Clear selection

        Insert newline

        Execute code

        Clear line

        Clear console

        Restart console


Troubleshooting
---------------

If you encounter bugs or if you have suggestions, please open an issue
on `Github <https://github.com/j4321/PyTkEditor/issues>`_.


