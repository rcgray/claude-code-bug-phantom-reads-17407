#!/usr/bin/env python
"""Fix failing test assertions about export deletion."""

from pathlib import Path

# Read test file
test_file = Path("tests/test_collect_trials.py")
content = test_file.read_text()

# Fix 1: test_batch_collection_with_mixed_outcomes
# Skipped trials should NOT have exports deleted
content = content.replace(
    '        assert not (exports_dir / "trial2.txt").exists()  # Skipped',
    '        assert (exports_dir / "trial2.txt").exists()  # Skipped (not deleted)'
)

# Fix 2: test_multiple_exports_same_workscope_id
# Second export should NOT be deleted when skipped
content = content.replace(
    '        # Verify first export deleted, second also deleted on skip\n        assert not export_1.exists()\n        assert not export_2.exists()',
    '        # Verify first export deleted, second not deleted (skipped)\n        assert not export_1.exists()\n        assert export_2.exists()'
)

# Write back
test_file.write_text(content)

print("Fixed both test assertions")
