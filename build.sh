#!/usr/bin/env bash

rm -rf *.egg-info build dist

set -e

python3 setup.py bdist_wheel sdist

while getopts 'iuc' flag; do
  case "${flag}" in
    i) python3 -m pip install . ;;
    u) twine upload dist/* ;;
    c) rm -rf *.egg-info build dist ;;
    *) echo 'Unexpected flag.'
       exit 1 ;;
  esac
done
