#!/usr/bin/env python
"""Append execution report to Work Journal."""

from pathlib import Path

# Read execution report
report = Path("dev/diagnostics/journal_update_execution.md").read_text()

# Read current journal
journal = Path("dev/journal/archive/Journal-Workscope-20260119-084630.md")
content = journal.read_text()

# Append report
updated = content + "\n\n" + report

# Write back
journal.write_text(updated)

print("Updated Work Journal with execution report")
