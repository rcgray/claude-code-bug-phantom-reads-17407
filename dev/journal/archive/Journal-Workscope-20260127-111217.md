# Work Journal - 2026-01-27 11:12
## Workscope ID: Workscope-20260127-111217

## Initialization

- **Timestamp**: 2026-01-27 11:12:17
- **Initialization Mode**: Custom (`--custom` flag)
- **Project**: Phantom Reads Investigation (Claude Code Issue #17407)

## Project-Bootstrapper Onboarding

Consulted Project-Bootstrapper agent for onboarding guidance.

### Files to Read (Mandatory)

**Critical Rule Files (READ EVERY WORD):**
1. `docs/read-only/Agent-Rules.md` - 132 numbered rules governing ALL agent behavior
2. `docs/read-only/Checkboxlist-System.md` - Task organization and checkbox states
3. `docs/read-only/Workscope-System.md` - Work assignment structure
4. `docs/read-only/standards/Coding-Standards.md` - Universal coding principles
5. `docs/read-only/standards/Python-Standards.md` - Python-specific requirements
6. `docs/core/Design-Decisions.md` - Project-specific design philosophies

**Essential Context Files:**
7. `docs/core/PRD.md` - Project goals and terminology

### Key Rules Highlighted

**Most Frequently Violated Rules:**
- **Rule 5.1**: NO backward compatibility - app has not shipped
- **Rule 3.4**: NO meta-commentary in product artifacts (source code, tests, scripts)
- **Rule 3.11**: Use `dev/diagnostics/` for temp files, escalate write access issues

**Forbidden Actions:**
- Editing `docs/read-only/`, `docs/references/`, `docs/reports/`, `.env` files
- Non-read-only git commands (only status, diff, log, show, grep, blame allowed)

**Project-Specific:**
- Use MCP Filesystem tools (`mcp__filesystem__read_text_file`) instead of native Read tool to avoid Phantom Reads bug
- Read entire files unless directed otherwise (Rule 4.2)
- Retry failed reads at least once before escalating (Rule 4.5)

**Python Requirements:**
- ALL functions must have return type annotations
- Use lowercase type parameters (`list[int]` not `List[int]`)
- Google-style docstrings with Args:, Returns:, Raises:
- Use `uv` for dependency management

**Source of Truth Priority:** Documentation > Test > Code

### QA Agents with Veto Power
- Documentation-Steward
- Rule-Enforcer
- Test-Guardian
- Health-Inspector

## Status

**Onboarding Complete.** Awaiting custom workscope from User.
