#!/bin/bash

# Setting kaggle API key
export KAGGLE_USERNAME=$1
export KAGGLE_KEY=$2

cd project
pip install -r requirements.txt
python3 unit_tests.py