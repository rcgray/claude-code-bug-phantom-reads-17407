#!/usr/bin/env python
"""Final Work Journal update."""

from pathlib import Path

# Read QA update
qa_update = Path("dev/diagnostics/journal_qa_update.md").read_text()

# Read current journal
journal = Path("dev/journal/archive/Journal-Workscope-20260119-084630.md")
content = journal.read_text()

# Append QA results
updated = content + "\n\n" + qa_update

# Write back
journal.write_text(updated)

print("Updated Work Journal with QA results")
