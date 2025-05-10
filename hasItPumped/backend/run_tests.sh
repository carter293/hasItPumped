#!/bin/bash

# Run tests with the correct Python path
PYTHONPATH=$(pwd) pytest -v "$@"