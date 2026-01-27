# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project uses **Workscope-Dev (WSD)**, an orchestration framework for AI-assisted coding. Work is organized into bounded **workscopes** that follow a structured lifecycle: init → prepare → execute → close.

## Research Context

This repository documents and investigates the **Phantom Reads bug** in Claude Code ([Issue #17407](https://github.com/anthropics/claude-code/issues/17407)). The bug causes Claude to believe it has successfully read file contents when it has not.

Key research artifacts:
- `docs/theories/Consolidated-Theory.md` - Unified theoretical framework (X + Y threshold model)
- `docs/core/Investigation-Journal.md` - Detailed discovery narrative
- `docs/experiments/` - Experiment methodologies and results

### Source Code

- `src/cc_version.py` - Claude Code version management for testing
- `src/collect_trials.py` - Trial data collection utilities

## File Reading Instructions

This project uses the Filesystem MCP server for reliable file reading. The native `Read` tool is disabled.

**To read files, use these MCP tools instead:**
- `mcp__filesystem__read_text_file` - Read a single file
- `mcp__filesystem__read_multiple_files` - Read multiple files at once
- `mcp__filesystem__list_directory` - List directory contents
- `mcp__filesystem__search_files` - Search for files by pattern

**Example usage:**
Instead of: `Read` tool with `file_path` parameter
Use: `mcp__filesystem__read_text_file` with `path` parameter

This workaround prevents the Phantom Reads bug (Issue #17407).

## Essential Commands

### WSD Workflow (in Claude Code)
```
/wsd:init                    # Start a workscope session
/wsd:prepare                 # Load context for assigned work
/wsd:execute                 # Execute work + QA checks
/wsd:close                   # Finalize completed workscope
/wsd:abort                   # Cancel workscope at any point
```

### Environment Setup
```bash
uv sync                      # Install dependencies
uv run pytest               # Run tests in virtual environment
```

### Task Runner (in terminal)
```bash
./wsd.py health              # Run comprehensive health checks
./wsd.py test                # Run full test suite
pytest tests/test_cc_version.py -v                    # Run single test file
pytest tests/test_cc_version.py::test_func_name -v   # Run single test
./wsd.py lint                # Check code style
./wsd.py lint:fix            # Auto-fix lint issues
./wsd.py format              # Format code
./wsd.py type                # Run type checker
./wsd.py validate            # Run lint + type + format:check
./wsd.py docs:update         # Update project documentation
```

## Architecture

### Directory Structure
- `docs/core/` - PRD, Action-Plan, Design-Decisions (project source of truth)
- `docs/features/` - Feature specifications
- `docs/tickets/open/` and `docs/tickets/closed/` - Issue tracking
- `docs/workbench/` - Working memory for active context
- `docs/read-only/` - System rules and standards (DO NOT EDIT)
- `docs/references/` - Templates and archives (DO NOT EDIT)
- `dev/wsd/` - WSD guides and documentation
- `dev/workscopes/archive/` - Immutable workscope records
- `dev/journal/archive/` - Work journals
- `dev/diagnostics/` - Temporary agent artifacts
- `scripts/` - WSD tooling scripts

### Key System Documents
- `docs/read-only/Agent-Rules.md` - Strict behavioral rules for all agents
- `docs/read-only/Checkboxlist-System.md` - Task tracking with checkbox states
- `docs/read-only/Workscope-System.md` - Workscope file format
- `docs/core/Design-Decisions.md` - Project-specific design philosophies

### Utility Scripts
- `scripts/health_check.py` - Health check implementation
- `scripts/update_docs.py` - Documentation update tooling
- `scripts/archive_claude_sessions.py` - Session archival

## Critical Rules

### Forbidden Actions
- Do NOT edit files in `docs/read-only/`, `docs/references/`, or `dev/wsd/`
- Do NOT run git commands that modify state (only read-only git commands allowed)
- Do NOT edit `.env` files (edit `.env.example` instead)

### Code Quality
- Fail immediately at point of failure; no workarounds for internal logic errors
- Trust documented guarantees; avoid redundant defensive fallbacks
- Update specifications when changing code (specs are source of truth)
- Use 4 spaces for indentation
- All code files must have descriptive comment blocks
- No meta-process references in product artifacts (no phase numbers, task IDs in code)

### Checkbox States
- `[ ]` - Unaddressed (available)
- `[%]` - Incomplete/unverified
- `[*]` - Assigned to active workscope
- `[x]` - Completed
- `[-]` - Intentionally skipped (requires User authorization)

## Special Agents

QA agents have **veto power** during `/wsd:execute`:
- **Documentation-Steward** - Verifies code matches specifications
- **Rule-Enforcer** - Verifies compliance with Agent-Rules.md
- **Test-Guardian** - Verifies test coverage and no regressions
- **Health-Inspector** - Runs health checks (lint, type, security, format)

Context agents assist during `/wsd:prepare`:
- **Context-Librarian** - Finds relevant documentation
- **Codebase-Surveyor** - Identifies relevant source files
- **Project-Bootstrapper** - Educates on project rules

## Source of Truth Priority

When conflicts exist: Documentation (Specification) > Test > Code

Discrepancies must be escalated to the User, not silently resolved.
