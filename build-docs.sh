#!/bin/bash

source venv/bin/activate
cd docs
time make html
deactivate
