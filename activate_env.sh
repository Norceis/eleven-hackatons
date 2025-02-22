#!/bin/bash

if [ ! -e env/bin/activate ]; then
  python3.10 -m venv env/ || return # exit on error
  source env/bin/activate
  echo "Activated virtual env"
  python -m pip install --upgrade pip wheel setuptools
  python -m pip install -e .[all]
else
  source env/bin/activate
  python -m pip install -e .[all]
  echo "Activated virtual env"
fi
