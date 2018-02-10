#!/bin/bash

if [ -d docs ]; then
    exit 1
fi

sphinx-quickstart -q --ext-autodoc --ext-intersphinx --ext-viewcode -a "Heiko Finzel" -p ec2helper -v "0.1" -r "0.1a1" docs

### docs/Makefile ###
# allow sphinx to use virtualenv
sed -i 's/^SPHINXBUILD.*$/SPHINXBUILD   = python -m sphinx/' docs/Makefile

### docs/conf.py ###
# look for our code in docs/../
sed -i 's!# import os!import os\nimport sys\nsys.path.insert(0, os.path.abspath("../"))!' docs/conf.py
# use the readthedocs theme
sed -i 's/^html_theme\s*=.*$/html_theme = "sphinx_rtd_theme"/' docs/conf.py
# some autodoc defaults
echo "autodoc_default_flags = ['members', 'undoc-members', 'show-inheritance']" >> docs/conf.py
