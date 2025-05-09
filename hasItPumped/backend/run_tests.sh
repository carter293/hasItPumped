#!/bin/bash

# Set PYTHONPATH to include the src directory
export PYTHONPATH=$(pwd)/src:$PYTHONPATH

# Run pytest with verbose output
python -m pytest -v