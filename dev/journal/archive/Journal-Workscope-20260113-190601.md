# Work Journal - 2026-01-13 19:06
## Workscope ID: Workscope-20260113-190601

## Initialization

- **Session Type**: Custom workscope (`/wsd:init --custom`)
- **Project**: Phantom Reads Investigation (Claude Code Issue #17407)
- **Purpose**: Awaiting custom workscope assignment from User

## Project-Bootstrapper Onboarding Report

### Mandatory Files to Read (Phase 1 & 2 - REQUIRED):

1. `docs/read-only/Agent-Rules.md` - CRITICAL: Inviolable rules
2. `docs/read-only/Agent-System.md` - Agent roles and responsibilities
3. `docs/read-only/Workscope-System.md` - Workscope file format
4. `docs/read-only/Checkboxlist-System.md` - Checkbox states and system
5. `docs/read-only/Documentation-System.md` - Documentation organization
6. `docs/core/Design-Decisions.md` - Project-specific design philosophies

### Standards Files (Phase 3 - Based on Workscope):

**General Standards:**
- `docs/read-only/standards/Coding-Standards.md`
- `docs/read-only/standards/Process-Integrity-Standards.md`
- `docs/read-only/standards/Specification-Maintenance-Standards.md`

**Python Standards (if applicable):**
- `docs/read-only/standards/Python-Standards.md`
- `docs/read-only/standards/Python-Test-Environment-Isolation-Standards.md`
- `docs/read-only/standards/Python-Testing-Configuration-Variables-Standards.md`

**TypeScript Standards (if applicable):**
- `docs/read-only/standards/TypeScript-Standards.md`
- `docs/read-only/standards/TypeScript-Test-Environment-Isolation-Standards.md`
- `docs/read-only/standards/TypeScript-Testing-Configuration-Variables-Standards.md`

**Domain-Specific Standards:**
- `docs/read-only/standards/Data-Structure-Documentation-Standards.md`
- `docs/read-only/standards/Environment-and-Config-Variable-Standards.md`

### Critical Project Files:
- `docs/core/PRD.md` - Complete project requirements
- `README.md` - User-facing documentation
- `docs/core/Action-Plan.md` - Implementation checkboxlist

### Key Rules to Remember:

1. **Rule 5.1**: NO backward compatibility - this is the most violated rule
2. **Rule 3.4**: NO meta-commentary in shipping products (no phase numbers, task IDs in code)
3. **Rule 3.11**: Write access issues - copy to docs/workbench/ if blocked
4. **Rule 4.4**: FORBIDDEN shell patterns: `cat >>`, `echo >>`, `<< EOF`

### QA Agents with Veto Power:
- Documentation-Steward
- Rule-Enforcer
- Test-Guardian
- Health-Inspector

### Source of Truth Priority:
Documentation (Specification) > Test > Code

### Forbidden Actions:
- Do NOT edit: `docs/read-only/`, `docs/references/`, `dev/wsd/`
- Do NOT run git commands that modify state
- Do NOT edit `.env` files
- Do NOT add backward compatibility

## Status

Onboarding complete. Awaiting custom workscope assignment from User.
