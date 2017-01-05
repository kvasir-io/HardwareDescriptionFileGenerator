#!/usr/bin/env python

from distutils.core import setup

setup(name='svd_generator',
      version='0.1',
      description='Kvasir hardware description file generator for CMSIS SVD files',
      author='Jackie Kayj',
      author_email='jacquelinekay1@gmail.com',
      url='https://github.com/kvasir-io/HardwareDescriptionFileGenerator',
      install_requires=['bs4', 'em']
      packages=['svd_parser'],
     )
