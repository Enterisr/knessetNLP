#!/usr/bin/env python3
"""
Script to run translation evaluation from the root directory.
This avoids import issues by keeping everything at the same level.
"""

from evaluators.evaluate_translation import main

if __name__ == "__main__":
    main()
