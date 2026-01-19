#!/usr/bin/env python
"""Append integration tests to test file."""

from pathlib import Path

# Read the remaining test methods
remaining = Path("dev/diagnostics/integration_tests_remaining.py").read_text()

# Read current test file
test_file = Path("tests/test_collect_trials.py")
current_content = test_file.read_text()

# Append the remaining content
updated_content = current_content + remaining

# Write back
test_file.write_text(updated_content)

print("Successfully appended remaining test methods")
