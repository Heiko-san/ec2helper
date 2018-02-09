#!/bin/bash

sphinx-quickstart -q --ext-autodoc --ext-intersphinx --ext-viewcode -a "Heiko Finzel" -p ec2helper -v "0.1" -r "0.1a1" docs
# look for our code in docs/../
sed -i 's!# import os!import os\nimport sys\nsys.path.insert(0, os.path.abspath("../"))!' docs/conf.py
# allow sphinx to use virtualenv
sed -i 's/^SPHINXBUILD.*$/SPHINXBUILD   = python -m sphinx/' docs/Makefile
sphinx-apidoc -o docs ec2helper
