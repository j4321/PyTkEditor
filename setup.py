#! /usr/bin/python3
# -*- coding:Utf-8 -*-

import os

from setuptools import setup

APP_NAME = "pytkeditor"


with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

with open("pytkeditorlib/utils/version.py") as file:
    exec(file.read())

images = [os.path.join("pytkeditorlib/images/", img) for img in os.listdir("pytkeditorlib/images/")]
ssl = [os.path.join("pytkeditorlib/ssl/", img) for img in os.listdir("pytkeditorlib/ssl/")]
html = [os.path.join("pytkeditorlib/html/", img) for img in os.listdir("pytkeditorlib/html/")]

data_files = [("/usr/share/applications", ["{}.desktop".format(APP_NAME)]),
              ("/usr/share/{}/images/".format(APP_NAME), images),
              ("/usr/share/{}/ssl/".format(APP_NAME), ssl),
              ("/usr/share/{}/html/".format(APP_NAME), html),
              ("/usr/share/doc/{}/".format(APP_NAME), ["README.rst"]),
              ("/usr/share/man/man1", ["{}.1.gz".format(APP_NAME)]),
              ("/usr/share/pixmaps", ["{}.svg".format(APP_NAME)])]

# for loc in os.listdir('pytkeditorlib/locale'):
    # data_files.append(("/usr/share/locale/{}/LC_MESSAGES/".format(loc),
                       # ["pytkeditorlib/locale/{}/LC_MESSAGES/{}.mo".format(loc, APP_NAME)]))

setup(name="pytkeditor",
      version=__version__,
      description="Python IDE",
      author="Juliette Monsel",
      author_email="j_4321@protonmail.com",
      url="https://gitlab.com/j_4321/PyTkEditor/",
      license="GNU General Public License v3",
      packages=['pytkeditorlib',
                'pytkeditorlib.code_editor',
                'pytkeditorlib.dialogs',
                'pytkeditorlib.gui_utils',
                'pytkeditorlib.utils',
                'pytkeditorlib.custom_qtconsole',
                'pytkeditorlib.widgets'],
      data_files=data_files,
      long_description=long_description,
      scripts=["pytkeditor"],
      install_requires=["jedi", "pygments", "pyflakes", "pycodestyle",
                        "tkfilebrowser", "ewmh", "python-xlib", "tkcolorpicker",
                        "Pillow", "docutils", "pdfkit", "pycups"],
      extras_require={'Execute in Jupyter QtConsole': ["qtconsole"]})
