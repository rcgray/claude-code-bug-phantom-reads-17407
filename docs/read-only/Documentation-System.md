# Documentation System Overview

This document defines the documentation organization system and standards for AI assistants working on this project. Every agent must understand this system to contribute effectively and avoid documentation chaos.

## System Overview & Philosophy

The core principle of our documentation system is that **different document types have different life cycles and audiences**. This system solves the critical problem of AI assistants creating documentation in random locations, cluttering the workspace, or placing important context where future agents cannot find it.

Our documentation is organized around **document permanence** and **audience scope**:

- **Temporary**: Created for immediate use, can be deleted at any time
- **Active**: Relevant to current work, actively searched and referenced
- **Permanent**: Long-term reference material that remains indefinitely

The system channels documents into appropriate locations based on their intended lifespan, preventing both temporary clutter in permanent locations and important context from being lost in temporary directories.

## Directory Reference & Purposes

### Core Directory Structure

```
├── dev/                 # Development artifacts
│   ├── diagnostics/     # Temporary working directory for scripts, analysis
│   ├── journal/         # Agent work session journals
│   │   └── archive/     # Previous work session journals
│   └── workscopes/      # Agent workscope records
│       └── archive/     # Workscope file archives
├── docs/                # Documentation hierarchy
│   ├── archive/         # Retired documents no longer relevant
│   ├── core/            # Foundational project specifications
│   ├── diagrams/        # Architecture visuals and diagrams
│   ├── features/[name]/ # Individual feature documentation
│   ├── public/          # User-facing documentation (to publish)
│   ├── read-only/       # Rules and standards (not editable by agents)
│   │   └── standards/   # Standards and best practices
│   ├── references/      # Reference material and templates
│   │   └── templates/   # Document templates
│   ├── reports/         # Tool-generated project insights
│   ├── tickets/         # Issue tracking
│   │   ├── open/        # Active tickets
│   │   └── closed/      # Completed tickets
│   └── workbench/       # Active working memory for current tasks
```

### Directory Decision Matrix

| Directory               | Purpose                                                | Audience                          | Lifecycle              | Ownership                      |
| ----------------------- | ------------------------------------------------------ | --------------------------------- | ---------------------- | ------------------------------ |
| `dev/diagnostics/`      | Temporary scripts, one-off analysis, throwaway content | Agent creating it                 | Can be deleted anytime | Individual agents              |
| `dev/journal/`          | Work session documentation                             | User monitoring, future reference | Archived after session | Individual agents              |
| `docs/core/`            | Foundational specs (PRD, Action Plan, etc.)            | All agents, long-term             | Permanent              | Explicitly directed            |
| `docs/features/[name]/` | Individual feature documentation                       | Feature-specific agents           | Permanent (branches)   | Task-master, context-librarian |
| `docs/public/`          | User-facing documentation to publish with project      | End-users of the project          | Permanent              | Explicitly directed            |
| `docs/reports/`         | Tool-generated project insights (read-only for agents) | All agents (as context source)    | Refreshed by tools     | N/A (tool-generated)           |
| `docs/workbench/`       | Context for active work items                          | Future agents, context-librarian  | Active until archived  | Context-librarian              |
| `docs/archive/`         | Retired but preserved documents                        | Rarely accessed                   | Long-term storage      | Context-librarian              |

## Document Lifecycle & Decision Trees

### When to Use Each Directory

#### Use `dev/diagnostics/` When:
- Creating temporary analysis scripts
- One-time debugging tools
- Throwaway documentation that won't be needed by future agents
- Quick tests or experiments
- **Content can be deleted immediately after your session**

#### Use `docs/workbench/` When:
- Creating unsolicited but helpful documentation
- Writing analysis that future agents might need
- Documenting refactor plans, audit results, test breakdowns
- Creating context for multi-session tasks
- **Content needs to persist beyond your session but isn't permanent**

#### Use `docs/core/` or `docs/references/` When:
- **Explicitly instructed** to create permanent documentation
- Writing foundational specifications
- Creating long-term reference material
- **Never do this without explicit direction**

#### Use `docs/features/[name]/` When:
- **Only when directed** by task-master or context-librarian
- Working on feature-specific documentation
- Each feature is a permanent "branch" of documentation

### The Critical Decision: Diagnostics vs. Workbench

The key distinction is **audience and persistence**:

- **`dev/diagnostics/`**: "I need this for my current work, nobody else needs it"
- **`docs/workbench/`**: "Future agents working on this task will need this context"

When in doubt, err on the side of `docs/workbench/` for _context_ (not scripts or tools) that might be useful to future agents.

## Agent Collaboration with Documentation

### Document Discovery & Handoffs

**For User Agents Seeking Context:**
- **Always** rely on the context-librarian Special Agent to surface relevant documents
- **Never** search directories yourself - this wastes time and context window
- The context-librarian is specialized and optimized for this task

**For User Agents Creating Context:**
1. Place documents in `docs/workbench/` to ensure future visibility
2. Use descriptive naming (5-7 words, kebab-case)
3. The context-librarian will naturally discover well-named, properly placed documents

### Multi-Session Document Collaboration

- **Edit documents in place** - don't create multiple versions
- `docs/workbench/` documents are meant to evolve as tasks progress
- Version control is handled by git, not by creating duplicate files
- Keep workbench uncluttered for context-librarian effectiveness

**Note:** For complete information about User Agent and Special Agent responsibilities, workflows, and collaboration patterns, see `docs/read-only/Agent-System.md`.

## Quality Standards & Best Practices

### Markdown Writing Style

- **Prefer paragraph-style writing** with lists where applicable
- Use clear section headings for scannable structure
- Include code samples for architecture examples, but avoid full implementations
- Keep specs focused on requirements, not implementation details

### Document Metadata

- **Content-focused** documents are preferred
- Timestamps are welcome (one-time, don't require updates)
- **Avoid** status fields that require ongoing maintenance
- **Never include** time estimates (AI development timeframes are completely different)
- **Don't mark** priorities or urgency (handled outside documentation)
- Dependencies and blockers are helpful to note

### Naming Conventions

- **5-7 words** describing the document's purpose
- **kebab-case** formatting
- **Descriptive** enough for context-librarian to understand relevance
- Examples: `phase-5-cli-cleanup-review.md`, `provider-enum-elimination-strategy.md`

### Cross-Referencing Patterns

- `docs/workbench/` documents **reference** `docs/core/` documents frequently
- `docs/core/` documents generally **don't reference** workbench (except Action-Plan.md)
- Think of `docs/core/` as the "foundation" and `docs/workbench/` as "working memory"
- Use relative paths for internal references

### Checkboxlist Document Standards
- **Analysis sections** precede implementation checklists using standard markdown headers (`####`, `#####`)
- **Checkboxlists focus on actionable tasks** with minimal embedded context
- **Context and rationale** belong in dedicated analysis sections, not within task descriptions
- **Phase descriptions** should be concise and action-oriented
- **Separate content from structure** - keep analysis separate from checkbox hierarchies for Task Master navigation

## Anti-Patterns & Common Mistakes

### Critical Violations

**Never Create New Directories:**
- **NEVER** create `docs/reviews/` or any undefined directories
- Other agents and the context-librarian Special Agent don't know to look in undefined locations
- Inventing directories makes your documents invisible and useless

**Never Mix Document Types:**
- Don't put temporary clutter in `docs/workbench/` (use `dev/diagnostics/`)
- Don't put multi-session context in `dev/diagnostics/` (use `docs/workbench/`)
- Don't create permanent documentation without explicit instruction

**Never Create Version Proliferation:**
- Don't create multiple versions of the same document for "version control"
- Edit existing `docs/workbench/` documents in place
- Git handles version control, not filename variations

### Content Quality Mistakes

**In Specifications:**
- Don't include full implementations (that's what code files are for)
- Don't add time estimates (irrelevant in AI-powered development)
- Don't mark priorities or urgency (handled by humans outside documentation)
- Focus on requirements and architecture, not implementation details

**In All Documents:**
- Don't create documents that require ongoing status updates. The exception to this are feature overviews or tickets that contain action plans (numbered tasks with checkboxes for the task-master agent to manage).
- Don't duplicate information that's already captured elsewhere
- Don't write for yourself if other User Agents will need the context

## Decision Framework Summary

When creating any document, ask yourself:

1. **Who needs this?** (Just me → `dev/diagnostics/`, Future User Agents → `docs/workbench/`, Everyone long-term → permanent location)
2. **How long will it be relevant?** (This session only → diagnostics, Current work → workbench, Indefinitely → permanent)
3. **Was I explicitly told where to put it?** (If yes, follow instructions exactly)
4. **Am I inventing a new directory?** (If yes, stop - use `docs/workbench/` instead)

Following this system ensures your documentation contributes to project success rather than creating organizational chaos. The context-librarian and other Special Agents can only help effectively when documents are placed predictably in the correct locations.
