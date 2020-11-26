# -*- coding: utf-8 -*-

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinxcontrib.plantuml',
    'sphinxcontrib.spelling',
    'sphinxcontrib.redoc',
]

spelling_lang = 'en_US'
spelling_word_list_filename = 'wordlist.txt'

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

redoc_uri = 'https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js'
redoc = [
    {
        'name': 'Shared DB Channel API',
        'page': 'api',
        'spec': 'swagger.yaml',
        'embed': True,
        'opts': {
            'required-props-first': True,
            'hide-hostname': True,
            'suppress-warnings': True,
        },
    },
]
