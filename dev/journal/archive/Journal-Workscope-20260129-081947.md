# Work Journal - 2026-01-29 08:19
## Workscope ID: Workscope-20260129-081947

## Initialization

- Workscope ID generated: `20260129-081947`
- Work Journal created at `dev/journal/archive/Journal-Workscope-20260129-081947.md`
- Custom workscope mode (`--custom`) — awaiting User assignment

## Onboarding (Project-Bootstrapper)

### Files Read During Initialization

**WSD Platform System Files:**
1. `docs/read-only/Agent-System.md`
2. `docs/read-only/Agent-Rules.md`
3. `docs/core/Design-Decisions.md`
4. `docs/read-only/Documentation-System.md`
5. `docs/read-only/Checkboxlist-System.md`
6. `docs/read-only/Workscope-System.md`
7. `docs/core/PRD.md`

**Standards (Mandatory per Project-Bootstrapper):**
8. `docs/read-only/standards/Coding-Standards.md`
9. `docs/read-only/standards/Python-Standards.md`
10. `docs/read-only/standards/Process-Integrity-Standards.md`
11. `docs/read-only/standards/Specification-Maintenance-Standards.md`

**Project Context (Mandatory per Project-Bootstrapper):**
12. `docs/core/Action-Plan.md`
13. `docs/core/Investigation-Journal.md`
14. `docs/core/Timeline.md`
15. `docs/core/Research-Questions.md`

### Key Rules and Standards Acknowledged

- **Rule 5.1**: No backward compatibility — this project has not shipped
- **Rule 3.4**: No meta-process references in product artifacts
- **Rule 3.11**: Use `dev/diagnostics/` for temporary files; copy to `docs/workbench/` for read-only file edits
- **Rule 4.4**: Never use `cat >> file << EOF` — use Edit/Write tools for file operations
- **Rule 4.2**: Read entire files unless directed otherwise
- **Rule 2.2**: No git commands that modify repository state (strict whitelist)
- **Rule 2.1**: Do not edit files in `docs/read-only/`, `docs/references/`, or `dev/wsd/`
- **Specification-Maintenance-Standards**: Update specs when changing code
- **Python-Standards**: Use type hints, Google-style docstrings, `uv` for dependencies, `ruff` for linting, `mypy` for type checking
- **Process-Integrity-Standards**: Automation tools must match underlying tool results
- **Source of Truth Priority**: Documentation > Test > Code

### Project Understanding

This is the "Phantom Reads Investigation" project investigating Claude Code Issue #17407. Key aspects:

- **The Bug**: Claude Code's native Read tool can silently fail, causing the agent to believe it read file contents when it received phantom read markers instead
- **Two Eras**: Era 1 (≤2.0.59) uses `[Old tool result content cleared]`; Era 2 (≥2.0.60) uses `<persisted-output>` markers
- **Current Theory**: The "Danger Zone" model — phantom reads on the 200K model require both X ≥ ~73K (pre-operation context) AND Y ≥ ~50K (agent-initiated reads)
- **Confirmed Mitigations**: MCP Filesystem bypass (100% success), hoisting via `@` notation, 1M context model (out of scope)
- **Current Phase**: Phase 4 (Analysis Tools) — tasks 4.5 and 4.6 remain open
- **Methodology**: Experiment-Methodology-04 with separated setup/analysis commands

### Conditional Reading (deferred until workscope assigned)

- If tests are involved: `docs/read-only/standards/Python-Test-Environment-Isolation-Standards.md`
- If environment/config work: `docs/read-only/standards/Environment-and-Config-Variable-Standards.md`, `docs/read-only/standards/Python-Testing-Configuration-Variables-Standards.md`
- If data structures: `docs/read-only/standards/Data-Structure-Documentation-Standards.md`
