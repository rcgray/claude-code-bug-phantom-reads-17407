# Work Journal - 2026-01-26 11:08
## Workscope ID: Workscope-20260126-110844

---

## Initialization Phase

**Status**: In Progress (--custom flag)

### Documents Read
- `docs/core/PRD.md` - Project overview (Phantom Reads Investigation)
- `docs/read-only/Agent-System.md` - Agent collaboration model
- `docs/read-only/Agent-Rules.md` - Strict behavioral rules
- `docs/core/Design-Decisions.md` - Project design philosophies
- `docs/read-only/Documentation-System.md` - Documentation organization
- `docs/read-only/Checkboxlist-System.md` - Task management system
- `docs/read-only/Workscope-System.md` - Workscope file format and lifecycle

### Project Understanding
This is the "Phantom Reads Investigation" project - a Git repository for reproducing Claude Code Issue #17407. The bug causes Claude Code to believe it has read file contents when it hasn't. Key findings:
- Reset Timing Theory: Mid-session resets (50-90%) predict phantom reads with 100% accuracy
- Two eras: Era 1 (≤2.0.59) uses `[Old tool result content cleared]`, Era 2 (≥2.0.60) uses `<persisted-output>`
- MCP Filesystem bypass provides 100% success rate workaround

---

## Project-Bootstrapper Onboarding

**Consulted**: Project-Bootstrapper agent

### Mandatory Files to Read
The Project-Bootstrapper has commanded I read these files:

**Already Read:**
- [x] `docs/read-only/Agent-Rules.md` - Inviolable laws
- [x] `docs/core/PRD.md` - Project context
- [x] `docs/core/Design-Decisions.md` - Project-specific philosophies

**Standards Files Read:**
- [x] `docs/read-only/standards/Coding-Standards.md` - General coding standards

**Technology-Specific (read if applicable to workscope):**
- `docs/read-only/standards/Python-Standards.md`
- `docs/read-only/standards/Python-Test-Environment-Isolation-Standards.md`
- `docs/read-only/standards/TypeScript-Standards.md`
- `docs/read-only/standards/TypeScript-Test-Environment-Isolation-Standards.md`

### Critical Rules Highlighted

**MOST VIOLATED RULES TO AVOID:**

1. **Rule 5.1 - No Backward Compatibility**: This app has not shipped. NO migration scripts, legacy support, or backward compatibility code.

2. **Rule 3.4 - No Meta-Process References in Product Artifacts**: No phase numbers, task IDs, or dev process references in source code, tests, or scripts. These ARE allowed in Feature specs, tickets, and Action Plans.

3. **Rule 3.11 - Read-Only Directory Workaround**: If I need to edit a file in `docs/read-only/`, copy it to `docs/workbench/` with the same filename and edit there.

### Additional Critical Rules

- **Rule 4.1**: Diagnostic files go in `dev/diagnostics/`, not project root
- **Rule 4.2**: Read ENTIRE files when asked
- **Rule 3.5**: Update specs when changing code (specs are source of truth)
- **Rule 3.12**: Verify Special Agent proof of work before accepting
- **Rules 3.15, 3.16, 4.9**: Report ALL discoveries to User (I am User's eyes and ears)

### Project-Specific Terms Confirmed
- Session Agent: Agent in example sessions (not me)
- Trial: Single experimental run in `dev/misc/[collection]/`
- Era 1/Era 2: Different phantom read mechanisms
- Karpathy script: Agent-interpretable instructions

---

## Status: Awaiting Custom Workscope

Initialization complete with `--custom` flag. Awaiting workscope assignment from User.

