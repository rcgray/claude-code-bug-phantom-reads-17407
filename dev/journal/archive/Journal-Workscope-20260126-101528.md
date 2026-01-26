# Work Journal - 2026-01-26 10:15
## Workscope ID: Workscope-20260126-101528

## Initialization

Initialized with `/wsd:init --custom` flag. Will receive custom workscope from User after onboarding.

**Project**: Phantom Reads Investigation (Claude Code Issue #17407)

## Onboarding (Project-Bootstrapper)

### Files Read During Onboarding

**System Files (read during /wsd:boot):**
1. `docs/read-only/Agent-System.md` - Agent collaboration and workflow standards
2. `docs/read-only/Agent-Rules.md` - Strict rules all agents must follow
3. `docs/core/Design-Decisions.md` - Project-specific design philosophies
4. `docs/read-only/Documentation-System.md` - Documentation organization
5. `docs/read-only/Checkboxlist-System.md` - Task tracking system
6. `docs/read-only/Workscope-System.md` - Work assignment mechanism

**Additional Files (read during /wsd:onboard):**
7. `docs/read-only/standards/Coding-Standards.md` - General coding principles
8. `docs/read-only/standards/Python-Standards.md` - Python-specific standards

**Project Context (read during /wsd:init):**
9. `docs/core/PRD.md` - Project overview and requirements

### Key Rules Acknowledged

**Critical Violations to Avoid:**
- **Rule 5.1**: No backward compatibility concerns - app has not shipped
- **Rule 3.4**: No meta-process references in product artifacts (no phase numbers, task IDs in code)
- **Rule 3.11**: If write access blocked, copy file to `docs/workbench/` and edit there

**Important Behaviors:**
- **Rule 3.5**: Update specifications when changing code
- **Rule 3.12**: Verify Special Agent proof of work before accepting
- **Rule 3.15/3.16**: Report ALL discoveries to User (even if not in workscope)
- **Rule 3.20**: Distinguish INTRODUCED vs IFF vs PRE-EXISTING failures
- **Rule 4.2**: Read entire files unless directed otherwise
- **Rule 4.9**: Report all QA discoveries in USER ACTION ITEMS

**Coding Standards:**
- Fail at point of failure immediately
- Trust documented guarantees (don't add redundant fallbacks)
- Use Sources of Truth, avoid duplicate state tracking
- 4 spaces for indentation
- All code files need descriptive comment blocks

**Python Standards:**
- Use `uv` for dependency management
- Type hints mandatory on all functions (including return types)
- Lowercase generic types (`list[int]` not `List[int]`)
- Google-style docstrings with Args, Returns, Raises sections
- Use `ruff` for linting/formatting, `mypy` for type checking, `pytest` for tests

## Workscope Assignment

**Status**: Awaiting custom workscope from User

---

