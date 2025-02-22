#!/bin/bash

if [ ! -e env/bin/activate ]; then
  python3.12 -m venv env/ || return # exit on error
  source env/bin/activate
  echo "Activated virtual env"
  python -m pip install --upgrade pip wheel setuptools
  python -m pip install -e .[all]
  python -m pip install -r requirements.txt
else
  source env/bin/activate
  python -m pip install -e .[all]
python -m pip install -r requirements.txt
  echo "Activated virtual env"
fi
