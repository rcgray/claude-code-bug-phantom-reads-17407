# Work Journal - 2026-01-26 11:29
## Workscope ID: Workscope-20260126-112928

## Initialization

- **Mode**: Custom workscope (`--custom` flag)
- **Status**: Awaiting workscope assignment from User

## Project-Bootstrapper Onboarding

The Project-Bootstrapper provided comprehensive onboarding education.

### Mandatory Files Read

1. `docs/read-only/Agent-System.md` - Agent collaboration system and workflow standards
2. `docs/read-only/Agent-Rules.md` - Strict rules all agents must follow
3. `docs/core/Design-Decisions.md` - Project-specific design philosophies
4. `docs/read-only/Documentation-System.md` - Documentation organization standards
5. `docs/read-only/Checkboxlist-System.md` - Task management and coordination
6. `docs/read-only/Workscope-System.md` - Work assignment and tracking
7. `docs/core/PRD.md` - Project overview (Phantom Reads Investigation)
8. `docs/read-only/standards/Coding-Standards.md` - General coding guidelines
9. `docs/read-only/standards/Python-Standards.md` - Python-specific standards

### Key Rules to Remember

**Rule 5.1 (Critical)**: This app has NOT shipped. No backward compatibility, migration notes, or legacy support. Act as if new designs have always existed.

**Rule 3.4**: No meta-process references in product artifacts (source code, test files, scripts). Phase numbers and task references are FORBIDDEN in code files.

**Rule 3.11**: If write access to read-only directories fails, copy to `docs/workbench/` with exact same filename and edit there.

**Rule 3.12**: Demand proper proof of work from Special Agents (test output summaries, health check tables, actual file paths).

**Rule 4.2**: Read ENTIRE files unless otherwise directed.

**Rule 4.4**: Forbidden - Do NOT use `cat >> file << EOF` or similar shell patterns to write files.

### Project Context

- **Project**: Claude Code Phantom Reads Investigation (Issue #17407)
- **Purpose**: Reproduce and investigate phantom reads bug in Claude Code
- **Language**: Python (primary)
- **Framework**: Workscope-Dev (WSD)

### `[%]` Task Handling

- Treat `[%]` exactly like `[ ]` - full implementation responsibility
- Find the "delta" between current state and specification, then implement it
- Never assume existing work is correct or complete

## Next Steps

Halting to await custom workscope assignment from User.

