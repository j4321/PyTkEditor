## PyTkEditor log - 2021-06-28 11:32:27.110795 ##

"ansi_color_fg = {39: 'foreground default'}\nansi_color_bg = {49: 'background default'}\n"
'ansi_color_bg'
#[Out] Traceback (most recent call last):
#        File "<console>", line 1, in <module>
#      NameError: name 'ansi_color_bg' is not defined
"\nansi_color_fg = {39: 'foreground default'}\nansi_color_bg = {49: 'background default'}\n"
'ansi_color_bg'
#[Out] Traceback (most recent call last):
#        File "<console>", line 1, in <module>
#      NameError: name 'ansi_color_bg' is not defined
"a = 1\nansi_color_fg = {39: 'foreground default'}\nansi_color_bg = {49: 'background default'}"
'ansi_color_bg'
#[Out] {49: 'background default'}


"_console.logstart('')"
## PyTkEditor log - 2021-06-28 11:37:12.864609 ##

_console.logstart('-o')
#[Out] <code object <module> at 0x7fc640914710, file "<console>", line 1>
import tkinter as tk
import re
root = tk.Tk()
text = tk.Text(root)
ansi_colors_dark = ['black', 'red', 'green', 'yellow', 'royal blue', 'magenta',
                    'cyan', 'light gray']
ansi_colors_light = ['dark gray', 'tomato', 'light green', 'light goldenrod', 'light blue',
                     'pink', 'light cyan', 'white']
ansi_font_format = {
    1: 'bold',
    3: 'italic',
    4: 'underline',
    9: 'overstrike',
}
ansi_font_reset = {
    21: 'bold',
    23: 'italic',
    24: 'underline',
    29: 'overstrike'
}
#[Out] <code object <module> at 0x7fc646ca60e0, file "<console>", line 1>
ansi_color_a = 1
ansi_color_b = 2
ansi_color_c = 3
#[Out] <code object <module> at 0x7fc64107d500, file "<console>", line 1>
ansi_color_fg = {39: 'foreground default'}
ansi_color_bg = {49: 'background default'}
#[Out] <code object <module> at 0x7fc641075710, file "<console>", line 1>
#[Out] <code object <module> at 0x7fc641075710, file "<console>", line 1>
## PyTkEditor log - 2021-06-28 11:54:16.590116 ##

"_console.logstart('-o')"


_console.logstart('-o')
#[Out] _console.logstart('-o')
'ansi_color_a = 1'
'ansi_color_b = 2'
'ansi_color_c = 3'
''
ansi_color_a = 1
ansi_color_b = 2
ansi_color_c = 3
#[Out] _cwd = _getcwd()
#[Out] ansi_color_a = 1
#[Out] ansi_color_b = 2
#[Out] ansi_color_c = 3
"ansi_color_fg = {39: 'foreground default'}"
"ansi_color_bg = {49: 'background default'}"
''
ansi_color_fg = {39: 'foreground default'}
ansi_color_bg = {49: 'background default'}
#[Out] _cwd = _getcwd()
#[Out] ansi_color_fg = {39: 'foreground default'}
#[Out] ansi_color_bg = {49: 'background default'}
'ansi_color_bg'
ansi_color_bg
#[Out] _cwd = _getcwd()
#[Out] ansi_color_bg
#[Out] {49: 'background default'}
'ansi_color_fg'
ansi_color_fg
#[Out] _cwd = _getcwd()
#[Out] ansi_color_fg
#[Out] {39: 'foreground default'}
'import tkinter as tk'
'import re'
'root = tk.Tk()'
'text = tk.Text(root)'
"ansi_colors_dark = ['black', 'red', 'green', 'yellow', 'royal blue', 'magenta',\n                    'cyan', 'light gray']"
"ansi_colors_light = ['dark gray', 'tomato', 'light green', 'light goldenrod', 'light blue',\n                     'pink', 'light cyan', 'white']"
"ansi_font_format = {\n    1: 'bold',\n    3: 'italic',\n    4: 'underline',\n    9: 'overstrike',"
'}'
"ansi_font_reset = {\n    21: 'bold',\n    23: 'italic',\n    24: 'underline',\n    29: 'overstrike'"
'}'
'ansi_color_a = 1'
'ansi_color_b = 2'
'ansi_color_c = 3'
"ansi_color_fg = {39: 'foreground default'}"
"ansi_color_bg = {49: 'background default'}"
"for i, (col_dark, col_light) in enumerate(zip(ansi_colors_dark, ansi_colors_light)):\n    ansi_color_fg[30 + i] = 'foreground ' + col_dark\n    ansi_color_fg[90 + i] = 'foreground ' + col_light\n    ansi_color_bg[40 + i] = 'background ' + col_dark\n    ansi_color_bg[100 + i] = 'background ' + col_light\n    text.tag_configure('underline foreground ' + col_dark, underlinefg=col_dark, underline=True)\n    text.tag_configure('overstrike foreground ' + col_dark, overstrikefg=col_dark, overstrike=True)\n    text.tag_configure('foreground ' + col_dark, foreground=col_dark)\n    text.tag_configure('background ' + col_dark, background=col_dark)\n    text.tag_configure('underline foreground ' + col_light, underlinefg=col_light, underline=True)\n    text.tag_configure('overstrike foreground ' + col_light, overstrikefg=col_light, overstrike=True)\n    text.tag_configure('foreground ' + col_light, foreground=col_light)\n    text.tag_configure('background ' + col_light, background=col_light)"
''
import tkinter as tk
import re
root = tk.Tk()
text = tk.Text(root)
ansi_colors_dark = ['black', 'red', 'green', 'yellow', 'royal blue', 'magenta',
                    'cyan', 'light gray']
ansi_colors_light = ['dark gray', 'tomato', 'light green', 'light goldenrod', 'light blue',
                     'pink', 'light cyan', 'white']
ansi_font_format = {
    1: 'bold',
    3: 'italic',
    4: 'underline',
    9: 'overstrike',
}
ansi_font_reset = {
    21: 'bold',
    23: 'italic',
    24: 'underline',
    29: 'overstrike'
}
ansi_color_a = 1
ansi_color_b = 2
ansi_color_c = 3
ansi_color_fg = {39: 'foreground default'}
ansi_color_bg = {49: 'background default'}
for i, (col_dark, col_light) in enumerate(zip(ansi_colors_dark, ansi_colors_light)):
    ansi_color_fg[30 + i] = 'foreground ' + col_dark
    ansi_color_fg[90 + i] = 'foreground ' + col_light
    ansi_color_bg[40 + i] = 'background ' + col_dark
    ansi_color_bg[100 + i] = 'background ' + col_light
    text.tag_configure('underline foreground ' + col_dark, underlinefg=col_dark, underline=True)
    text.tag_configure('overstrike foreground ' + col_dark, overstrikefg=col_dark, overstrike=True)
    text.tag_configure('foreground ' + col_dark, foreground=col_dark)
    text.tag_configure('background ' + col_dark, background=col_dark)
    text.tag_configure('underline foreground ' + col_light, underlinefg=col_light, underline=True)
    text.tag_configure('overstrike foreground ' + col_light, overstrikefg=col_light, overstrike=True)
    text.tag_configure('foreground ' + col_light, foreground=col_light)
    text.tag_configure('background ' + col_light, background=col_light)
#[Out] _cwd = _getcwd()
#[Out] import tkinter as tk
#[Out] import re
#[Out] root = tk.Tk()
#[Out] text = tk.Text(root)
#[Out] ansi_colors_dark = ['black', 'red', 'green', 'yellow', 'royal blue', 'magenta',
#                          'cyan', 'light gray']
#[Out] ansi_colors_light = ['dark gray', 'tomato', 'light green', 'light goldenrod', 'light blue',
#                           'pink', 'light cyan', 'white']
#[Out] ansi_font_format = {
#          1: 'bold',
#          3: 'italic',
#          4: 'underline',
#          9: 'overstrike',
#[Out] ansi_font_format = {
#          1: 'bold',
#          3: 'italic',
#          4: 'underline',
#          9: 'overstrike',
#      }
#[Out] ansi_font_reset = {
#          21: 'bold',
#          23: 'italic',
#          24: 'underline',
#          29: 'overstrike'
#[Out] ansi_font_reset = {
#          21: 'bold',
#          23: 'italic',
#          24: 'underline',
#          29: 'overstrike'
#      }
#[Out] ansi_color_a = 1
#[Out] ansi_color_b = 2
#[Out] ansi_color_c = 3
#[Out] ansi_color_fg = {39: 'foreground default'}
#[Out] ansi_color_bg = {49: 'background default'}
#[Out] for i, (col_dark, col_light) in enumerate(zip(ansi_colors_dark, ansi_colors_light)):
#          ansi_color_fg[30 + i] = 'foreground ' + col_dark
#          ansi_color_fg[90 + i] = 'foreground ' + col_light
#          ansi_color_bg[40 + i] = 'background ' + col_dark
#          ansi_color_bg[100 + i] = 'background ' + col_light
#          text.tag_configure('underline foreground ' + col_dark, underlinefg=col_dark, underline=True)
#          text.tag_configure('overstrike foreground ' + col_dark, overstrikefg=col_dark, overstrike=True)
#          text.tag_configure('foreground ' + col_dark, foreground=col_dark)
#          text.tag_configure('background ' + col_dark, background=col_dark)
#          text.tag_configure('underline foreground ' + col_light, underlinefg=col_light, underline=True)
#          text.tag_configure('overstrike foreground ' + col_light, overstrikefg=col_light, overstrike=True)
#          text.tag_configure('foreground ' + col_light, foreground=col_light)
#          text.tag_configure('background ' + col_light, background=col_light)
#[Out] for i, (col_dark, col_light) in enumerate(zip(ansi_colors_dark, ansi_colors_light)):
#          ansi_color_fg[30 + i] = 'foreground ' + col_dark
#          ansi_color_fg[90 + i] = 'foreground ' + col_light
#          ansi_color_bg[40 + i] = 'background ' + col_dark
#          ansi_color_bg[100 + i] = 'background ' + col_light
#          text.tag_configure('underline foreground ' + col_dark, underlinefg=col_dark, underline=True)
#          text.tag_configure('overstrike foreground ' + col_dark, overstrikefg=col_dark, overstrike=True)
#          text.tag_configure('foreground ' + col_dark, foreground=col_dark)
#          text.tag_configure('background ' + col_dark, background=col_dark)
#          text.tag_configure('underline foreground ' + col_light, underlinefg=col_light, underline=True)
#          text.tag_configure('overstrike foreground ' + col_light, overstrikefg=col_light, overstrike=True)
#          text.tag_configure('foreground ' + col_light, foreground=col_light)
#          text.tag_configure('background ' + col_light, background=col_light)
''
"for i, (col_dark, col_light) in enumerate(zip(ansi_colors_dark, ansi_colors_light)):\n    ansi_color_fg[30 + i] = 'foreground ' + col_dark\n    ansi_color_fg[90 + i] = 'foreground ' + col_light\n    ansi_color_bg[40 + i] = 'background ' + col_dark\n    ansi_color_bg[100 + i] = 'background ' + col_light\n    text.tag_configure('underline foreground ' + col_dark, underlinefg=col_dark, underline=True)\n    text.tag_configure('overstrike foreground ' + col_dark, overstrikefg=col_dark, overstrike=True)\n    text.tag_configure('foreground ' + col_dark, foreground=col_dark)\n    text.tag_configure('background ' + col_dark, background=col_dark)\n    text.tag_configure('underline foreground ' + col_light, underlinefg=col_light, underline=True)\n    text.tag_configure('overstrike foreground ' + col_light, overstrikefg=col_light, overstrike=True)\n    text.tag_configure('foreground ' + col_light, foreground=col_light)\n    text.tag_configure('background ' + col_light, background=col_light)"
'ansi_regexp = re.compile(r"\\x1b\\[((\\d+;)*\\d+)m")'
'def insert_ansi(txt, index="insert"):\n    first_line, first_char = map(int, str(text.index(index)).split("."))\n    # find all ansi codes in txt\n    res = []\n    lines = txt.splitlines()\n    if not lines:\n        return\n    def get_ansi(line_txt, line_nb, index_offset):\n        delta = index_offset  # difference between the character position in the original line and in the text widget\n                              # (initial offset due to insertion position if fisrt line + extra offset due to deletion of ansi codes)\n        for match in ansi_regexp.finditer(line_txt):\n            codes = [int(c) for c in match.groups()[0].split(\';\')]\n            start, end = match.span()\n            res.append(((line_nb, start - delta), codes))\n            delta += end - start\n    get_ansi(lines[0], first_line, -first_char)  # take into account offset due to insertion position\n    for line_nb, line in enumerate(lines, first_line + 1):\n        get_ansi(line, line_nb, 0)\n    stripped_txt = ansi_regexp.sub(\'\', txt)\n    tag_ranges = {}\n    opened_tags = []\n    for pos, codes in res:\n        for code in codes:\n            if code == 0:  # reset all\n                for tag in opened_tags:\n                    tag_ranges[tag].append(\'%i.%i\' % pos)\n                opened_tags.clear()\n            elif code in ansi_font_reset:\n                tag = ansi_font_reset[code]\n                if tag in opened_tags:\n                    tag_ranges[tag].append(\'%i.%i\' % pos)\n                    opened_tags.remove(tag)\n            elif code in ansi_font_format:\n                tag = ansi_font_format[code]\n                if tag not in tag_ranges:\n                    tag_ranges[tag] = []\n                tag_ranges[tag].append(\'%i.%i\' % pos)\n                opened_tags.append(tag)\n            elif code in ansi_color_fg:\n                tag = ansi_color_fg[code]\n                for t in tuple(opened_tags):\n                    if t.startswith(\'foreground\'):\n                        opened_tags.remove(t)\n                        tag_ranges[t].append(\'%i.%i\' % pos)\n                if tag not in tag_ranges:\n                    tag_ranges[tag] = []\n                tag_ranges[tag].append(\'%i.%i\' % pos)\n                opened_tags.append(tag)\n            elif code in ansi_color_bg:\n                tag = ansi_color_bg[code]\n                for t in tuple(opened_tags):\n                    if t.startswith(\'background\'):\n                        opened_tags.remove(t)\n                        tag_ranges[t].append(\'%i.%i\' % pos)\n                if tag not in tag_ranges:\n                    tag_ranges[tag] = []\n                tag_ranges[tag].append(\'%i.%i\' % pos)\n                opened_tags.append(tag)\n    for tag in opened_tags:\n        tag_ranges[tag].append(\'end\')\n    return tag_ranges, stripped_txt'
''
for i, (col_dark, col_light) in enumerate(zip(ansi_colors_dark, ansi_colors_light)):
    ansi_color_fg[30 + i] = 'foreground ' + col_dark
    ansi_color_fg[90 + i] = 'foreground ' + col_light
    ansi_color_bg[40 + i] = 'background ' + col_dark
    ansi_color_bg[100 + i] = 'background ' + col_light
    text.tag_configure('underline foreground ' + col_dark, underlinefg=col_dark, underline=True)
    text.tag_configure('overstrike foreground ' + col_dark, overstrikefg=col_dark, overstrike=True)
    text.tag_configure('foreground ' + col_dark, foreground=col_dark)
    text.tag_configure('background ' + col_dark, background=col_dark)
    text.tag_configure('underline foreground ' + col_light, underlinefg=col_light, underline=True)
    text.tag_configure('overstrike foreground ' + col_light, overstrikefg=col_light, overstrike=True)
    text.tag_configure('foreground ' + col_light, foreground=col_light)
    text.tag_configure('background ' + col_light, background=col_light)
ansi_regexp = re.compile(r"\x1b\[((\d+;)*\d+)m")
def insert_ansi(txt, index="insert"):
    first_line, first_char = map(int, str(text.index(index)).split("."))
    # find all ansi codes in txt
    res = []
    lines = txt.splitlines()
    if not lines:
        return
    def get_ansi(line_txt, line_nb, index_offset):
        delta = index_offset  # difference between the character position in the original line and in the text widget
                              # (initial offset due to insertion position if fisrt line + extra offset due to deletion of ansi codes)
        for match in ansi_regexp.finditer(line_txt):
            codes = [int(c) for c in match.groups()[0].split(';')]
            start, end = match.span()
            res.append(((line_nb, start - delta), codes))
            delta += end - start
    get_ansi(lines[0], first_line, -first_char)  # take into account offset due to insertion position
    for line_nb, line in enumerate(lines, first_line + 1):
        get_ansi(line, line_nb, 0)
    stripped_txt = ansi_regexp.sub('', txt)
    tag_ranges = {}
    opened_tags = []
    for pos, codes in res:
        for code in codes:
            if code == 0:  # reset all
                for tag in opened_tags:
                    tag_ranges[tag].append('%i.%i' % pos)
                opened_tags.clear()
            elif code in ansi_font_reset:
                tag = ansi_font_reset[code]
                if tag in opened_tags:
                    tag_ranges[tag].append('%i.%i' % pos)
                    opened_tags.remove(tag)
            elif code in ansi_font_format:
                tag = ansi_font_format[code]
                if tag not in tag_ranges:
                    tag_ranges[tag] = []
                tag_ranges[tag].append('%i.%i' % pos)
                opened_tags.append(tag)
            elif code in ansi_color_fg:
                tag = ansi_color_fg[code]
                for t in tuple(opened_tags):
                    if t.startswith('foreground'):
                        opened_tags.remove(t)
                        tag_ranges[t].append('%i.%i' % pos)
                if tag not in tag_ranges:
                    tag_ranges[tag] = []
                tag_ranges[tag].append('%i.%i' % pos)
                opened_tags.append(tag)
            elif code in ansi_color_bg:
                tag = ansi_color_bg[code]
                for t in tuple(opened_tags):
                    if t.startswith('background'):
                        opened_tags.remove(t)
                        tag_ranges[t].append('%i.%i' % pos)
                if tag not in tag_ranges:
                    tag_ranges[tag] = []
                tag_ranges[tag].append('%i.%i' % pos)
                opened_tags.append(tag)
    for tag in opened_tags:
        tag_ranges[tag].append('end')
    return tag_ranges, stripped_txt
#[Out] _cwd = _getcwd()
#[Out] for i, (col_dark, col_light) in enumerate(zip(ansi_colors_dark, ansi_colors_light)):
#          ansi_color_fg[30 + i] = 'foreground ' + col_dark
#          ansi_color_fg[90 + i] = 'foreground ' + col_light
#          ansi_color_bg[40 + i] = 'background ' + col_dark
#          ansi_color_bg[100 + i] = 'background ' + col_light
#          text.tag_configure('underline foreground ' + col_dark, underlinefg=col_dark, underline=True)
#          text.tag_configure('overstrike foreground ' + col_dark, overstrikefg=col_dark, overstrike=True)
#          text.tag_configure('foreground ' + col_dark, foreground=col_dark)
#          text.tag_configure('background ' + col_dark, background=col_dark)
#          text.tag_configure('underline foreground ' + col_light, underlinefg=col_light, underline=True)
#          text.tag_configure('overstrike foreground ' + col_light, overstrikefg=col_light, overstrike=True)
#          text.tag_configure('foreground ' + col_light, foreground=col_light)
#          text.tag_configure('background ' + col_light, background=col_light)
#[Out] def insert_ansi(txt, index="insert"):
#          first_line, first_char = map(int, str(text.index(index)).split("."))
#          # find all ansi codes in txt
#          res = []
#          lines = txt.splitlines()
#          if not lines:
#              return
#          def get_ansi(line_txt, line_nb, index_offset):
#              delta = index_offset  # difference between the character position in the original line and in the text widget
#                                    # (initial offset due to insertion position if fisrt line + extra offset due to deletion of ansi codes)
#              for match in ansi_regexp.finditer(line_txt):
#                  codes = [int(c) for c in match.groups()[0].split(';')]
#                  start, end = match.span()
#                  res.append(((line_nb, start - delta), codes))
#                  delta += end - start
#          get_ansi(lines[0], first_line, -first_char)  # take into account offset due to insertion position
#          for line_nb, line in enumerate(lines, first_line + 1):
#              get_ansi(line, line_nb, 0)
#          stripped_txt = ansi_regexp.sub('', txt)
#          tag_ranges = {}
#          opened_tags = []
#          for pos, codes in res:
#              for code in codes:
#                  if code == 0:  # reset all
#                      for tag in opened_tags:
#                          tag_ranges[tag].append('%i.%i' % pos)
#                      opened_tags.clear()
#                  elif code in ansi_font_reset:
#                      tag = ansi_font_reset[code]
#                      if tag in opened_tags:
#                          tag_ranges[tag].append('%i.%i' % pos)
#                          opened_tags.remove(tag)
#                  elif code in ansi_font_format:
#                      tag = ansi_font_format[code]
#                      if tag not in tag_ranges:
#                          tag_ranges[tag] = []
#                      tag_ranges[tag].append('%i.%i' % pos)
#                      opened_tags.append(tag)
#                  elif code in ansi_color_fg:
#                      tag = ansi_color_fg[code]
#                      for t in tuple(opened_tags):
#                          if t.startswith('foreground'):
#                              opened_tags.remove(t)
#                              tag_ranges[t].append('%i.%i' % pos)
#                      if tag not in tag_ranges:
#                          tag_ranges[tag] = []
#                      tag_ranges[tag].append('%i.%i' % pos)
#                      opened_tags.append(tag)
#                  elif code in ansi_color_bg:
#                      tag = ansi_color_bg[code]
#                      for t in tuple(opened_tags):
#                          if t.startswith('background'):
#                              opened_tags.remove(t)
#                              tag_ranges[t].append('%i.%i' % pos)
#                      if tag not in tag_ranges:
#                          tag_ranges[tag] = []
#                      tag_ranges[tag].append('%i.%i' % pos)
#                      opened_tags.append(tag)
#          for tag in opened_tags:
#              tag_ranges[tag].append('end')
#          return tag_ranges, stripped_txt
#[Out] def insert_ansi(txt, index="insert"):
#          first_line, first_char = map(int, str(text.index(index)).split("."))
#          # find all ansi codes in txt
#          res = []
#          lines = txt.splitlines()
#          if not lines:
#              return
#          def get_ansi(line_txt, line_nb, index_offset):
#              delta = index_offset  # difference between the character position in the original line and in the text widget
#                                    # (initial offset due to insertion position if fisrt line + extra offset due to deletion of ansi codes)
#              for match in ansi_regexp.finditer(line_txt):
#                  codes = [int(c) for c in match.groups()[0].split(';')]
#                  start, end = match.span()
#                  res.append(((line_nb, start - delta), codes))
#                  delta += end - start
#          get_ansi(lines[0], first_line, -first_char)  # take into account offset due to insertion position
#          for line_nb, line in enumerate(lines, first_line + 1):
#              get_ansi(line, line_nb, 0)
#          stripped_txt = ansi_regexp.sub('', txt)
#          tag_ranges = {}
#          opened_tags = []
#          for pos, codes in res:
#              for code in codes:
#                  if code == 0:  # reset all
#                      for tag in opened_tags:
#                          tag_ranges[tag].append('%i.%i' % pos)
#                      opened_tags.clear()
#                  elif code in ansi_font_reset:
#                      tag = ansi_font_reset[code]
#                      if tag in opened_tags:
#                          tag_ranges[tag].append('%i.%i' % pos)
#                          opened_tags.remove(tag)
#                  elif code in ansi_font_format:
#                      tag = ansi_font_format[code]
#                      if tag not in tag_ranges:
#                          tag_ranges[tag] = []
#                      tag_ranges[tag].append('%i.%i' % pos)
#                      opened_tags.append(tag)
#                  elif code in ansi_color_fg:
#                      tag = ansi_color_fg[code]
#                      for t in tuple(opened_tags):
#                          if t.startswith('foreground'):
#                              opened_tags.remove(t)
#                              tag_ranges[t].append('%i.%i' % pos)
#                      if tag not in tag_ranges:
#                          tag_ranges[tag] = []
#                      tag_ranges[tag].append('%i.%i' % pos)
#                      opened_tags.append(tag)
#                  elif code in ansi_color_bg:
#                      tag = ansi_color_bg[code]
#                      for t in tuple(opened_tags):
#                          if t.startswith('background'):
#                              opened_tags.remove(t)
#                              tag_ranges[t].append('%i.%i' % pos)
#                      if tag not in tag_ranges:
#                          tag_ranges[tag] = []
#                      tag_ranges[tag].append('%i.%i' % pos)
#                      opened_tags.append(tag)
#          for tag in opened_tags:
#              tag_ranges[tag].append('end')
#          return tag_ranges, stripped_txt
'print(2)'
'print("a")'
''
print(2)
print("a")
#[Out] _cwd = _getcwd()
#[Out] print(2)
#[Out] 2
#[Out] print("a")
#[Out] a
''
