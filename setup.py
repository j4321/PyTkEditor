#! /usr/bin/python3
# -*- coding:Utf-8 -*-

from setuptools import setup

with open("tkeditorlib/__init__.py") as file:
    exec(file.read())

files = ["images/*", "ssl/*", "html/*"]

setup(name="tkeditor",
      version=__version__,
      description="Python IDE",
      author="Juliette Monsel",
      author_email="j_4321@protonmail.fr",
      license="GNU General Public License v3",
      packages=['tkeditorlib'],
      package_data={'tkeditorlib': files},
      data_files=[("/usr/share/pixmaps", ["tkeditor.svg"]),
                  ("/usr/share/applications", ["tkeditor.desktop"])],
      scripts=["tkeditor"],
      long_description="""Python IDE in Tkinter.""",
      install_requires=["jedi", "pygments", "pyflakes", "pycodestyle",
                        "tkfilebrowser", "ewmh", "python-xlib",
                        "Pillow", "docutils"])
