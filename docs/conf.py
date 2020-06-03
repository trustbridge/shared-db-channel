# -*- coding: utf-8 -*-
import sys
import os

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinxcontrib.plantuml',
    'sphinxcontrib.spelling'
]

spelling_lang='en_US'
spelling_word_list_filename='wordlist.txt'

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'TrustBridge Shared DB Channel'
copyright = u"2020, Commonwealth of Australia"
version = '0.0.1'
release = version
exclude_patterns = ['_build', '.venv']
pygments_style = 'sphinx'
html_theme = 'alabaster'
html_static_path = ['_static']
