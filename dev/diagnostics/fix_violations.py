#!/usr/bin/env python
"""Fix Rule 3.4 violation and linting issues."""

from pathlib import Path

# Read test file
test_file = Path("tests/test_collect_trials.py")
content = test_file.read_text()

# Fix 1: Rule 3.4 violation - Remove "Phase 6" reference
content = content.replace(
    "# Integration Tests - Phase 6",
    "# End-to-End Integration Tests"
)

# Fix 2: Move import re to top of file
# First, remove the inline import
content = content.replace("            import re\n\n            ", "            ")

# Now find the imports section and add re
import_section_end = content.find("from src.collect_trials import (")
if import_section_end > 0:
    # Find the line before "from src.collect_trials"
    lines_before = content[:import_section_end].split('\n')
    # Insert "import re" before the from import
    insert_pos = content[:import_section_end].rfind('\n') + 1
    content = content[:insert_pos] + "import re\n" + content[insert_pos:]

# Fix 3 & 4: Extract magic numbers to constants
# Add constants near the top of the test section
fixtures_marker = "# ============================================================================="
first_marker_pos = content.find(fixtures_marker)
second_marker_pos = content.find(fixtures_marker, first_marker_pos + 1)

# Insert constants after the second marker (before fixtures)
constants_section = """

# Test constants for integration tests
EXPECTED_FILE_COUNT_FLAT = 4  # export + main session + 2 agent files
EXPECTED_TRIAL_COUNT_PARTIAL_FAILURE = 3  # Three trials with mixed outcomes
"""

content = content[:second_marker_pos + len(fixtures_marker) + 1] + constants_section + content[second_marker_pos + len(fixtures_marker) + 1:]

# Replace magic numbers with constants
content = content.replace(
    "assert len(result.files_copied) == 4  # export + main + 2 agents",
    "assert len(result.files_copied) == EXPECTED_FILE_COUNT_FLAT"
)

content = content.replace(
    "assert len(results) == 3",
    "assert len(results) == EXPECTED_TRIAL_COUNT_PARTIAL_FAILURE"
)

# Write back
test_file.write_text(content)

print("Fixed all violations")
print("1. Removed 'Phase 6' reference (Rule 3.4)")
print("2. Moved import re to top of file")
print("3. Extracted magic numbers to named constants")
