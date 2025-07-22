# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

# Add the project root and src directory to Python path
project_root = os.path.abspath('../..')  # Go up two levels to project root
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

project = 'pm'
copyright = '2025, bo'
author = 'bo'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

# -- Autodoc configuration ---------------------------------------------------
# Include special methods like __init__, __lt__, etc.
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'special-members': '__init__,__lt__,__le__,__gt__,__ge__,__eq__,__ne__',  # Include these special methods
}

# Function to include specific methods (opposite of skip)
def skip_member(app, what, name, obj, skip, options):
    # Don't skip __init__ and comparison methods - we want to document them
    if name in ['__init__', '__lt__', '__le__', '__gt__', '__ge__', '__eq__', '__ne__']:
        return False  # False means "don't skip" = "include"
    return skip

def setup(app):
    app.connect('autodoc-skip-member', skip_member)


templates_path = ['_templates']
exclude_patterns = []

language = 'it'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
