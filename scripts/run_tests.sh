#!/bin/bash
set -e

# Activate virtual environment
source venv/bin/activate

# Run tests
python tests/test_all_apis.py
