# -*- coding: utf-8 -*-
"""
PyTkEditor - Python IDE
Copyright © Spyder Project Contributors
Copyright (c) 2017, Project Jupyter Contributors
Copyright 2020 Juliette Monsel <j_4321 at protonmail dot com>

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

    
Originally distributed under the MIT license:

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

QString compatibility.
"""

import sys


PY2 = sys.version[0] == '2'


def qstring_length(text):
    """
    Tries to compute what the length of an utf16-encoded QString would be.
    """
    if PY2:
        # I don't know what this is encoded in, so there is nothing I can do.
        return len(text)
    utf16_text = text.encode('utf16')
    length = len(utf16_text) // 2
    # Remove Byte order mark.
    # TODO: All unicode Non-characters should be removed
    if utf16_text[:2] in [b'\xff\xfe', b'\xff\xff', b'\xfe\xff']:
        length -= 1
    return length
