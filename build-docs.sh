#!/bin/bash

source venv/bin/activate
# force rebuild of all pages
rm -rf docs/_build
cd docs
time make html
deactivate
