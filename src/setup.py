#!/usr/bin/env python

from distutils.core import setup

setup(name='svd_parser',
      version='0.1',
      description='Kvasir hardware description file generator for CMSIS SVD files',
      author='Jackie Kay',
      author_email='jacquelinekay1@gmail.com',
      url='https://github.com/kvasir-io/HardwareDescriptionFileGenerator',
      install_requires=['bs4', 'empy'],
      packages=['svd_parser'],
     )
