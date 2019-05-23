#! /usr/bin/python3
# -*- coding:Utf-8 -*-

import os

from setuptools import setup

APP_NAME = "tkeditor"


with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

with open("tkeditorlib/__init__.py") as file:
    exec(file.read())

images = [os.path.join("tkeditorlib/images/", img) for img in os.listdir("tkeditorlib/images/")]
ssl = [os.path.join("tkeditorlib/ssl/", img) for img in os.listdir("tkeditorlib/ssl/")]
html = [os.path.join("tkeditorlib/html/", img) for img in os.listdir("tkeditorlib/html/")]

data_files = [("/usr/share/applications", ["{}.desktop".format(APP_NAME)]),
              ("/usr/share/{}/images/".format(APP_NAME), images),
              ("/usr/share/{}/ssl/".format(APP_NAME), ssl),
              ("/usr/share/{}/html/".format(APP_NAME), html),
              ("/usr/share/doc/{}/".format(APP_NAME), ["README.rst"]),
              ("/usr/share/man/man1", ["{}.1.gz".format(APP_NAME)]),
              ("/usr/share/pixmaps", ["{}.svg".format(APP_NAME)])]

# for loc in os.listdir('tkeditorlib/locale'):
    # data_files.append(("/usr/share/locale/{}/LC_MESSAGES/".format(loc),
                       # ["tkeditorlib/locale/{}/LC_MESSAGES/{}.mo".format(loc, APP_NAME)]))

setup(name="tkeditor",
      version=__version__,
      description="Python IDE",
      author="Juliette Monsel",
      author_email="j_4321@protonmail.com",
      url="https://gitlab.com/j_4321/TkEditor/",
      license="GNU General Public License v3",
      packages=['tkeditorlib'],
      data_files=data_files,
      long_description=long_description,
      scripts=["tkeditor"],
      install_requires=["jedi", "pygments", "pyflakes", "pycodestyle",
                        "tkfilebrowser", "ewmh", "python-xlib",
                        "Pillow", "docutils"])
