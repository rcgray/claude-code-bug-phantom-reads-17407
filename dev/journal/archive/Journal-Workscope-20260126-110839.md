# Work Journal - 2026-01-26 11:08
## Workscope ID: Workscope-20260126-110839

---

## Initialization Phase

- **Workscope Type**: Custom (via `--custom` flag)
- **Status**: Awaiting custom workscope from User

### Project Context
This is the "Phantom Reads Investigation" project - a GitHub repository for reproducing Claude Code Issue #17407. The project investigates the "Phantom Reads" bug where file read operations fail silently, leaving Claude believing it read file contents when it didn't.

---

## Project-Bootstrapper Onboarding Report

### Mandatory Files Read

#### System Rules & Workflow
1. `docs/read-only/Agent-Rules.md` ✓
2. `docs/read-only/Agent-System.md` ✓
3. `docs/read-only/Documentation-System.md` ✓
4. `docs/read-only/Checkboxlist-System.md` ✓
5. `docs/read-only/Workscope-System.md` ✓

#### Coding Standards
6. `docs/read-only/standards/Coding-Standards.md` ✓
7. `docs/read-only/standards/Python-Standards.md` ✓

#### Project Context
8. `docs/core/PRD.md` ✓
9. `docs/core/Design-Decisions.md` ✓

### Critical Rules to Follow

**Three Most Violated Rules:**

1. **Rule 5.1 - Backward Compatibility Prohibition**: This app has NOT shipped. No migration scripts, no "legacy support", no "old" vs "new" code paths.

2. **Rule 3.4 - No Meta-Process References in Product Artifacts**: Source code, tests, and scripts must NOT contain phase numbers, task references, or ticket references.

3. **Rule 3.11 - Write Access to Read-Only Directories**: If write access denied, copy file to `docs/workbench/` with exact same filename and edit there.

### Python Standards Summary

- **Type annotations required** on all functions (`-> None`, `-> str`, etc.)
- **Lowercase type parameters** (`list[int]` NOT `List[int]`)
- **Never import** `List`, `Dict`, `Tuple` from typing
- **Use `Path.open()`** over `open()`
- **Google-style docstrings** with `Args:`, `Returns:`, `Raises:`
- **Document all test parameters** including pytest fixtures
- **Use `uv`** for package management
- **Use `ruff`** for linting/formatting
- **Use `mypy`** for type checking

### QA Proof of Work Requirements

- **Test-Guardian**: Must show test summary line (e.g., `====== X passed in Y.YYs ======`)
- **Health-Inspector**: Must show complete HEALTH CHECK SUMMARY table
- **Context-Librarian/Codebase-Surveyor**: Must provide actual file paths, not summaries

---

## Current Status

**HALTED**: Awaiting custom workscope assignment from User.

