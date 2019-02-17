# -*- coding: utf-8 -*-
import os

from setuptools import setup

VERSION = '0.1.1'

setup(
    name='treebank_toolkit',
    packages=["treebank_toolkit"],
    version=VERSION,
    description='Treebank toolkit processes a Conll/conllu treebank into treebank with static oracle transitions derived according a given transition system',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    long_description_content_type="text/markdown",
    author=u'Clementine',
    author_email='iclementine@outlook.com',
    url='https://github.com/iclementine/treebank_boolkit/',
    install_requires=['conllu'],
    keywords=['transition', 'conllu', 'conll', 'conll-u', 'parser', 'nlp'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
)
