# Work Journal - 2026-01-26 10:23
## Workscope ID: Workscope-20260126-102324

## Initialization

- **Mode**: Custom (`--custom` flag)
- **Workscope Assignment**: Pending from User

## Project Bootstrapper Onboarding

Received comprehensive onboarding from the Project-Bootstrapper agent.

### Critical Violations to Avoid

1. **Rule 5.1: NO BACKWARD COMPATIBILITY** - This app has not shipped yet. No migration-based solutions, legacy support, or comments acknowledging old designs.
2. **Rule 3.4: NO META-COMMENTARY IN PRODUCT ARTIFACTS** - No phase numbers, task references, ticket references in source code, tests, scripts, or configs.
3. **Rule 3.11: Blocked Write Access** - Copy blocked files to `docs/workbench/` with exact same filename, edit cleanly.

### Special Agent Proof of Work Requirements

- **Test-Guardian**: Must include test summary output (e.g., "140 passed in 0.23s")
- **Health-Inspector**: Must include full health check summary table
- **Task-Master**: Must provide workscope file path
- **Context-Librarian/Codebase-Surveyor**: Must provide actual file paths

### Files Read During Onboarding

**Foundation documents (read during /wsd:init):**
- `docs/core/PRD.md`
- `docs/read-only/Agent-System.md`
- `docs/read-only/Agent-Rules.md`
- `docs/core/Design-Decisions.md`
- `docs/read-only/Documentation-System.md`
- `docs/read-only/Checkboxlist-System.md`
- `docs/read-only/Workscope-System.md`

**Mandatory standards files (read during /wsd:onboard):**
- `docs/read-only/standards/Coding-Standards.md`
- `docs/read-only/standards/Python-Standards.md`
- `docs/read-only/standards/Process-Integrity-Standards.md`
- `docs/read-only/standards/Specification-Maintenance-Standards.md`

### Key Standards Learned

**Coding Standards:**
- Fail at point of failure immediately - no workarounds
- Handle external uncertainties gracefully, be strict about internal logic
- Use 4 spaces for indentation
- All code files should begin with comment blocks explaining purpose
- No meta-process references in product artifacts

**Python Standards:**
- Use `uv` for dependency management
- Use `ruff` for linting/formatting, `mypy` for type checking, `pytest` for testing
- ALL functions must have explicit return type annotations
- Type parameters must be lowercase (`list[int]` not `List[int]`)
- Google-style docstrings with Args, Returns, Raises sections

**Process Integrity Standards:**
- Automation Fidelity: tools must produce equivalent results to underlying tools
- No silent suppression of errors or warnings
- All exceptions require explicit user approval

**Specification Maintenance Standards:**
- Specifications are authoritative sources of truth
- When code changes, specifications must change in the same workscope
- Drift verification required before completion

## Awaiting Custom Workscope

Halting and waiting for User to provide custom workscope assignment.

