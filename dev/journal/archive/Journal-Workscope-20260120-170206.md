# Work Journal - 2026-01-20 17:02
## Workscope ID: Workscope-20260120-170206

## Initialization Phase

**Session Type:** Custom Workscope (--custom flag)

### WSD Platform Documentation Read (via /wsd:boot)

- `docs/read-only/Agent-System.md` - Agent collaboration system, responsibilities, workflows
- `docs/read-only/Agent-Rules.md` - Strict rules for all agents
- `docs/core/Design-Decisions.md` - Project-specific design philosophies
- `docs/read-only/Documentation-System.md` - Documentation organization standards
- `docs/read-only/Checkboxlist-System.md` - Task management and coordination
- `docs/read-only/Workscope-System.md` - Work assignment and tracking

### Project Introduction Read

- `docs/core/PRD.md` - Phantom Reads Investigation project overview

### Project-Bootstrapper Onboarding Report

**Key Project Context:**
- This is a Python-based research project investigating Claude Code Issue #17407 ("Phantom Reads")
- The bug causes Claude Code to believe it has read file contents when it has not
- Two eras of behavior: Era 1 (≤2.0.59) uses `[Old tool result content cleared]`, Era 2 (≥2.0.60) uses `<persisted-output>` markers
- Reset Timing Theory: Mid-session context resets (50-90%) predict phantom reads with 100% accuracy
- MCP Filesystem bypass workaround provides 100% success rate

**Critical Rules to Remember:**
1. Rule 5.1 - NO backward compatibility (project not released yet)
2. Rule 3.4 - NO meta-commentary in product artifacts (no "Phase 2" or task references in code)
3. Rule 4.4 - `cat >> file << EOF` is FORBIDDEN - use Read/Edit/Write tools

**Project Tools:**
- `uv` for dependency management (NOT pip/poetry/rye)
- `ruff` for linting and formatting
- `mypy` for type checking
- `pytest` for testing
- `./wsd.py` as task runner

**Read-Only Directories (DO NOT EDIT):**
- `docs/read-only/`
- `docs/references/`
- `dev/wsd/`

### Additional Standards Files Read

1. `docs/read-only/standards/Python-Standards.md` - Python development best practices
   - Use lowercase type hints (list, dict, not List, Dict)
   - ALL functions need explicit return type annotations
   - Use Path.open() instead of open()
   - Dataclasses require complete field documentation

2. `docs/read-only/standards/Data-Structure-Documentation-Standards.md` - Dataclass documentation requirements
   - Every dataclass must have Attributes section
   - Every field must be documented with clear descriptions
   - Boolean fields must explain True/False meanings
   - Optional fields must explain what None represents

3. `docs/read-only/standards/Specification-Maintenance-Standards.md` - Keeping specs synchronized
   - Specification documents are authoritative sources of truth
   - Code changes require specification updates in same workscope
   - Three forms of drift: Missing, Dead, Inconsistent documentation

4. `docs/read-only/standards/Process-Integrity-Standards.md` - Tool automation standards
   - Automation must produce equivalent results to direct tool execution
   - No silent error suppression

### Onboarding Confirmation

I have read and understood:
- [x] Python-Standards.md
- [x] Data-Structure-Documentation-Standards.md
- [x] Specification-Maintenance-Standards.md
- [x] Process-Integrity-Standards.md
- [x] This project investigates Claude Code itself (meta-awareness required)
- [x] Use `uv` for dependency management
- [x] Use `./wsd.py` for running tasks
- [x] The three most violated rules (5.1, 3.4, 4.4)
- [x] Which directories are read-only
- [x] Specifications must be updated with code changes
- [x] All dataclasses need Attributes sections
- [x] Use lowercase type hints (list, dict, not List, Dict)
- [x] This will be published on GitHub
- [x] QA agents have veto power

---

## Awaiting Custom Workscope Assignment

Session initialized with `--custom` flag. Awaiting work assignment from User.

