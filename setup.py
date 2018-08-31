#! /usr/bin/python3
# -*- coding:Utf-8 -*-

from setuptools import setup

files = ["images/*", "ssl/*"]

setup(name="tkeditor",
      version="1.0.0",
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
      requires=["os", "sys", "tkinter", "screeninfo", "pygments", "pyflakes", "pycodestyle", "tkfilebrowser"])
