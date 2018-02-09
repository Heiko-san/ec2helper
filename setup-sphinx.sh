#!/bin/bash

sphinx-quickstart -q --ext-autodoc --ext-intersphinx --ext-viewcode -a "Heiko Finzel" -p ec2helper -v "0.1" -r "0.1a1" docs
sed -i 's!# import os!import os\nimport sys\nsys.path.insert(0, os.path.abspath("../"))!' docs/conf.py
sphinx-apidoc -o docs ec2helper
