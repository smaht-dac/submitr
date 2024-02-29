# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------

project = 'smaht-submitr'
copyright = '2020-2024 President and Fellows of Harvard College'
author = 'Harvard Medical School / DBMI / SMaHT DAC Team'
master_doc = 'index'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_tabs.tabs'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_show_sourcelink = False
html_context = {
  "display_github": False, # Intends to remove the "Edit on GitHub" link
  "github_user": "", # Optional: Specify GitHub username here
  "github_repo": "", # Optional: Specify repository name here
  "github_version": "", # Optional: Specify branch name here
  "conf_py_path": "", # Optional: Specify path to conf.py file here
}
html_theme_options = {
  "sticky_navigation": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = ['styles.css', "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"]

# https://sphinx-tabs.readthedocs.io/en/latest/
sphinx_tabs_disable_tab_closing = True

# Special config to:
# - support bold highlighted text (:boldcode:)
# - support opening a link an a different/new tab (:toplink:)
from docutils import nodes, utils
from sphinx.util.nodes import make_refnode, split_explicit_title

def setup(app):
    app.add_role('boldcode', boldcode_role)
    app.add_role('toplink', toplink_role)

def boldcode_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    node = nodes.literal(rawtext, text, classes=['boldcode'])
    return [node], []

def toplink_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    has_title, title, target = split_explicit_title(text)
    node = nodes.reference(rawtext, utils.unescape(title if has_title else target), refuri=target, **options)
    node['target'] = '_blank'
    return [node], []
