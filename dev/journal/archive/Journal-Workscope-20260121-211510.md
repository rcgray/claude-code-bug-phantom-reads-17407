# Work Journal - 2026-01-21 21:15
## Workscope ID: Workscope-20260121-211510

---

## Initialization Phase

### Project Context
This is the "Phantom Reads Investigation" project - a git repository for publishing on GitHub that documents and reproduces Claude Code Issue #17407 ("Phantom Reads"). The bug causes Claude Code to believe it has successfully read file contents when it has not.

### Initialization Method
Initialized via `/wsd:init --custom` - will receive custom workscope from User.

---

## Project-Bootstrapper Onboarding Report

### Files Read for Onboarding

**System Documentation (read during /wsd:boot):**
1. `docs/read-only/Agent-System.md` - Special Agent workflow system
2. `docs/read-only/Agent-Rules.md` - Strict behavioral rules (133 numbered rules)
3. `docs/read-only/Documentation-System.md` - Document placement and lifecycle
4. `docs/read-only/Checkboxlist-System.md` - Task tracking with checkbox states
5. `docs/read-only/Workscope-System.md` - Work assignment and tracking
6. `docs/core/Design-Decisions.md` - Project-specific design philosophies

**Standards Files (read during /wsd:onboard):**
7. `docs/read-only/standards/Coding-Standards.md` - Universal coding guidelines
8. `docs/read-only/standards/Python-Standards.md` - Python-specific standards
9. `docs/read-only/standards/TypeScript-Standards.md` - TypeScript standards

**Project Context:**
10. `docs/core/PRD.md` - Project Requirements Document

### Critical Rules to Remember

**MOST COMMONLY VIOLATED:**

1. **Rule 5.1 - NO BACKWARD COMPATIBILITY**: This app has not shipped. Never include migration-based solutions, backward compatibility concerns, or legacy support.

2. **Rule 3.4 - NO META-PROCESS REFERENCES IN PRODUCT ARTIFACTS**: Code/tests must never contain phase numbers, task references, ticket references, or timeline references.

3. **Rule 3.11 - WRITE-BLOCKED FILES**: If blocked from editing a file in `docs/read-only/` or `.claude/`, copy to `docs/workbench/` with exact same filename, edit cleanly.

4. **Rule 4.4 - FORBIDDEN SHELL PATTERNS**: NEVER use `cat >>`, `echo >>`, `<< EOF`, `> file`, `>> file`. Use Read/Edit/Write tools instead.

5. **Rule 4.2 - READ ENTIRE FILES**: When given a file to read, read the ENTIRE file unless otherwise directed.

6. **Rule 3.5 - SPEC SYNC**: When changing code, specification documents MUST be updated in the same workscope.

7. **Rule 3.12 - VERIFY PROOF OF WORK**: Never accept Special Agent reports without proper evidence (test summaries, health check tables, etc.).

8. **Rules 3.15, 3.16 - REPORT ALL DISCOVERIES**: Report all issues to User. "Not my workscope" determines what to fix, not what to report.

### Python Standards Summary
- ALL functions/methods MUST have explicit return type annotations
- Type parameters MUST be lowercase (`list[int]` not `List[int]`)
- NEVER import `List`, `Dict`, `Tuple` from typing
- Use Google-style docstrings with Args:, Returns:, Raises:
- Use `Path.open()` over `open()`
- Shebangs: `#!/usr/bin/env python` (NOT python3)
- 4 spaces for indentation

### Forbidden Actions
- Do NOT edit: `docs/read-only/`, `docs/references/`, `docs/reports/`, `dev/template/`, `.env`
- Do NOT run state-modifying git commands (only read-only git allowed)
- Do NOT create temp files in project root (use `dev/diagnostics/`)

### QA Agents with Veto Power
- Documentation-Steward: Verifies code matches specifications
- Rule-Enforcer: Verifies compliance with Agent-Rules.md
- Test-Guardian: Verifies test coverage and no regressions
- Health-Inspector: Runs health checks

---

## Awaiting Custom Workscope

Initialization and onboarding complete. Awaiting custom workscope assignment from User.

