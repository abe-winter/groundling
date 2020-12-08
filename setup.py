#!/usr/bin/env python3

import os
from distutils.core import setup
from setuptools import find_packages
from sth.version import __version__

setup(
  name='sth',
  version= __version__,
  description="swiss army knife for (my) small starlette projects",
  author="Abe Winter",
  author_email="awinter.public+sth@gmail.com",
  url="https://github.com/abe-winter/sth",
  packages=find_packages(include=['sth', 'sth.*']),
  keywords=['starlette', 'swiss-army', 'auth', 'orm'],
  install_requires=[
    'asyncpg==0.21.0',
    'httpx==0.16.1',
    'starlette==0.14.1',
    'scrypt==0.8.16',
    'aiofiles==0.6.0',
    'python-multipart==0.0.5',
    'itsdangerous==1.1.0',
    'ujson==4.0.1',
  ],
  python_requires='>=3.6', # for format strings
  long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
  long_description_content_type='text/markdown',
)
