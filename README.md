# Workscope-Dev

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/workscope-dev)](https://pypi.org/project/workscope-dev/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-green)](https://claude.ai/code)

**An orchestration framework for AI-assisted coding with Claude Code.**

Structure your work. Enforce your rules. Ship with confidence.

→ Learn more at [workscope.dev](https://workscope.dev)

---

## Why WSD?

AI coding tools are powerful, but using them effectively requires more than good prompts. Without structure, you get "vibe coding"—generated code that works until it doesn't, built on foundations no one fully understands. WSD brings discipline to AI-assisted development by organizing work into bounded units, loading relevant context deliberately, and verifying results through specialized review processes.

WSD doesn't replace your judgment. It gives you a framework for applying it consistently: breaking large projects into AI-appropriate workscopes, enforcing your project's rules automatically, and maintaining traceability across sessions.

## Key Features

### Bounded Workscopes

Every unit of work is formally defined, sized for a single AI session, and tracked from assignment to completion. A workscope goes through a structured lifecycle:

1. **Assignment** — Work is selected from your project's checkboxlists using a deterministic algorithm
2. **Context Loading** — Relevant documentation and code files are identified and loaded
3. **Execution** — The AI performs the assigned tasks with full context
4. **Quality Review** — Specialized agents verify rule compliance, spec alignment, test coverage, and code health—with authority to reject work that doesn't meet standards
5. **Completion** — Work is accepted, checkboxlists are updated, and an audit trail is preserved

Each workscope gets a unique ID, an immutable record, and a work journal documenting the session.

### Living Task Management

Your work items don't hide in a project management server—they live right in your project as checkboxlists scattered across your documentation. This means:

- **Instantly editable** — Change priorities by editing a markdown file
- **Version controlled** — Task history lives in git alongside your code
- **Dynamically scheduled** — The Task-Master agent constructs your schedule on the fly, following cross-document references to find the next appropriate work
- **Parallel-aware** — Multiple workscopes can run concurrently without conflicts

Five checkbox states (`[ ]` `[%]` `[*]` `[x]` `[-]`) enable hierarchical tracking across documents, from high-level phases down to individual implementation tasks.

### Structured Documentation

WSD provides a documentation architecture that AI agents understand. Instead of hoping the AI finds the right context, the system deliberately surfaces relevant files:

- **Feature specifications** organized by feature in `docs/features/`
- **Tickets** for discrete issues in `docs/tickets/`
- **Working memory** in `docs/workbench/` for active context
- **Core documents** like your PRD and Action Plan in `docs/core/`
- **Rules and standards** that agents are trained to follow in `docs/read-only/`

Agents know where to look. Specifications stay in sync with implementation. Context flows to where it's needed.

## Quick Start

**Install WSD:**

```bash
pipx install workscope-dev
```

**Integrate into your project:**

```bash
wsd install path/to/your/project
```

This adds WSD's workflow system to your project, including slash commands for Claude Code, documentation structure, and development tools.

**Start your first session** by running `/wsd:init` in Claude Code. See the [User Guide](dev/wsd/User-Guide.md) for the complete workflow.

### Alternative: Install from Source

```bash
git clone https://github.com/rcgray/workscope-dev.git
cd workscope-dev
./wsd.py install path/to/your/project
```

## Supported Projects

WSD works with multiple project types and detects your stack automatically:

- **Python** — pytest, mypy, ruff, bandit integration
- **TypeScript** — ESLint, Prettier, TypeDoc integration
- **JavaScript** — ESLint, Prettier, JSDoc integration
- **Polyglot** — Mixed Python + Node.js projects supported
- **Codeless** — Documentation, research, and planning projects

## Requirements

- **Python 3.10+** — Required for WSD tools
- **Claude Code** — The AI assistant WSD orchestrates
- **Git** — Recommended for rollback safety

For TypeScript/JavaScript projects, Node.js 18+ is also required.

## Documentation

After installation, guides are available in `dev/wsd/`:

| Guide | Description |
|-------|-------------|
| [User Guide](dev/wsd/User-Guide.md) | Daily usage, workflow lifecycle, commands |
| [Integration Guide](dev/wsd/Integration-Guide.md) | Installation, customization, collision handling |
| [Task Runner Guide](dev/wsd/Task-Runner-Guide.md) | Development tools, health checks, unified commands |
| [Update Guide](dev/wsd/Update-Guide.md) | Updating WSD while preserving customizations |

Platform-specific setup:
- [Python Project Guide](dev/wsd/Python-Project-Guide.md)
- [Node Project Guide](dev/wsd/Node-Project-Guide.md)
- [Codeless Project Guide](dev/wsd/Codeless-Project-Guide.md)

## License

MIT
