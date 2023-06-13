# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright 2018-2020 Juliette Monsel <j_4321 at protonmail dot com>

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

Dialogs
"""
from pytkeditorlib.utils.constants import JUPYTER
from .about import About
from .colorpicker import ColorPicker
from .complistbox import CompListbox
from .config import Config
from .help_dialog import HelpDialog
from .kernel_dialog import SelectKernel
from .messagebox import showerror, showinfo, askokcancel, askyesno, askyesnocancel, askoptions
from .print import PrintDialog
from .search import SearchDialog
from .tooltip import TooltipNotebookWrapper, TooltipTextWrapper, Tooltip, TooltipWrapper

