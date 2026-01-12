# Workscope-Dev User Guide

**Version:** 1.0.0
**Audience:** Developers using WSD for AI-assisted development

## Introduction

This guide covers the day-to-day use of Workscope-Dev (WSD) after installation and setup. It explains the workscope lifecycle, available commands, and how to work effectively with the agent system.

For installation, see `Integration-Guide.md`. For platform-specific configuration, see the relevant project guide (`Python-Project-Guide.md`, `Node-Project-Guide.md`, or `Codeless-Project-Guide.md`).

## The Workscope Lifecycle

WSD organizes AI-assisted development into discrete units of work called **workscopes**. Each workscope represents a well-defined set of tasks suitable for a single AI session. The lifecycle follows a structured sequence that ensures quality, traceability, and effective handoffs.

### Lifecycle Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        WORKSCOPE LIFECYCLE                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │  /wsd:init   │───▶│ /wsd:prepare │───▶│ /wsd:execute │    │
│  │              │    │              │    │              │    │
│  │ Initialize   │    │ Onboard with │    │ Execute work │    │
│  │ session      │    │ context      │    │ + QA checks  │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│         │                                       │            │
│         │                                       ▼            │
│         │                              ┌──────────────┐      │
│         │                              │ /wsd:close   │      │
│         │                              │      or      │      │
│         ▼                              │ /wsd:abort   │      │
│  ┌──────────────┐                      │              │      │
│  │ /wsd:abort   │◀─────────────────────│ Finalize or  │      │
│  │              │  (cancel anytime)    │ cancel       │      │
│  │ Cancel work  │                      └──────────────┘      │
│  └──────────────┘                                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Phase 1: Initialization (`/wsd:init`)

The initialization phase prepares a fresh AI session (User Agent) for work.

**What happens:**
1. The User Agent reads critical WSD system documentation to understand components and workflow
2. A unique Workscope ID is generated from the current timestamp (format: `YYYYMMDD-HHMMSS`)
3. A Work Journal is created at `dev/journal/archive/Journal-Workscope-{ID}.md`
4. The Task-Master agent analyzes project documentation and assigns a workscope using a depth-first search algorithm
5. An immutable workscope file is created at `dev/workscopes/archive/Workscope-{ID}.md`

**Usage:**
```
/wsd:init                              # Standard initialization
/wsd:init --custom                     # Skip Task-Master, receive custom assignment from User
/wsd:init Do task 3.5 next             # Provide directive to Task-Master
```

**Completion:** The User Agent reports their Workscope ID and awaits further instruction.

### Phase 2: Preparation (`/wsd:prepare`)

The preparation phase onboards the User Agent with context relevant to their assigned workscope.

**What happens:**
1. Context-Librarian identifies documentation files relevant to the workscope tasks
2. Codebase-Surveyor identifies source code files relevant to the workscope tasks
3. Project-Bootstrapper educates the User Agent on project rules and behavioral expectations

**Why this matters:** Proper context loading dramatically improves AI accuracy and reduces hallucination. The User Agent enters execution with full awareness of relevant specifications, code patterns, and project conventions.

**Usage:**
```
/wsd:prepare
```

**Completion:** The User Agent confirms readiness to execute.

### Phase 3: Execution (`/wsd:execute`)

The execution phase is where the actual work happens, followed by comprehensive quality assurance.

**What happens:**
1. The User Agent performs the tasks assigned in their workscope
2. Work is continuously documented in the Work Journal
3. Upon completion, several Special Agents review the work in a QA gauntlet:
   - **Documentation-Steward**: Verifies code and specifications are aligned
   - **Rule-Enforcer**: Verifies compliance with Agent-Rules.md and standards
   - **Test-Guardian**: Verifies test coverage and no regressions
   - **Health-Inspector**: Examines code quality, formatting, security, and health checks

**Important:** Special Agents have **veto power**. They can reject submissions that don't meet standards, requiring the User Agent to revise their work.

Preferably, the User Agent will deal with the Special Agents directly, taking burden off the User for enforcing rules or ensuring specification alginment, but in a stalemate the User Agent will otherwise escalate the Special Agent rejection to the User. The User can choose to override the Special Agents' concerns, but **this is often where bugs, improper implementations, or higher level design inconsistencies are discovered.**

**Usage:**
```
/wsd:execute
```

**Completion:** All QA checks pass and the User Agent reports completion with any notes for the User.

### Phase 4: Termination (`/wsd:close` or `/wsd:abort`)

The termination phase finalizes or cancels the workscope.

#### Successful Completion (`/wsd:close`)

**What happens:**
1. Context-Librarian reviews workbench documents for potential archival
2. Task-Master updates checkboxlists to mark completed tasks with `[x]`
3. The workscope is formally closed

**Usage:**
```
/wsd:close
```

#### Cancellation (`/wsd:abort`)

**What happens:**
1. Checkboxlists are restored to their original state (assigned `[*]` items become unaddressed `[ ]`)
2. The workscope is marked as aborted
3. Any work performed is left in place (use git to revert if needed)
4. Note: this can be called at any point in the workscope cycle, not just at the end.

**Usage:**
```
/wsd:abort
```

### Post-Workscope Activities

After a workscope completes, the User typically:
1. Reviews the Work Journal and any Special Agent notes
2. Stages or commits work in git
3. Runs `./wsd.py docs:update` to update project reports
4. Tests new functionality manually if desired
5. Updates plans, rules, or documentation as needed
6. Runs `/clear` to create a fresh User Agent
7. Returns to Phase 1 for another workscope cycle

## Slash Commands Reference

WSD provides custom slash commands that drive the workflow. Commands are organized by category.

### Workscope Lifecycle Commands

| Command        | Description                                            |
| -------------- | ------------------------------------------------------ |
| `/wsd:init`    | Initialize a new workscope session                     |
| `/wsd:prepare` | Onboard User Agent with context for assigned workscope |
| `/wsd:execute` | Execute the workscope and run QA checks                |
| `/wsd:close`   | Accept and finalize completed workscope                |
| `/wsd:abort`   | Cancel workscope and restore checkboxlists             |
| `/wsd:onboard` | Standalone onboarding (used by `/wsd:init --custom`)   |

### Platform Setup Commands

| Command      | Description                                                |
| ------------ | ---------------------------------------------------------- |
| `/wsd:setup` | Configure platform-specific tooling after WSD installation |

### Documentation Commands

| Command           | Description                                                   |
| ----------------- | ------------------------------------------------------------- |
| `/open-ticket`    | Create a new ticket with checkboxlist in `docs/tickets/open/` |
| `/add-dd`         | Add a new design decision to `docs/core/Design-Decisions.md`  |
| `/create-feature` | Create a new feature specification in `docs/features/`        |
| `/commit-msg`     | Generate a commit message for staged changes                  |

### Development Commands

| Command     | Description                                             |
| ----------- | ------------------------------------------------------- |
| `/fix-loop` | Run iterative fix loop for failing tests or lint errors |

## Special Agents Reference

Special Agents are domain experts that provide specialized capabilities during the workscope lifecycle. They are invoked by User Agents or commands as needed.

### Task Assignment

| Agent           | Role                                                                                                                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Task-Master** | Manages workscope assignment using depth-first search on checkboxlists. Creates immutable workscope files. Updates checkbox states on close. Moves tickets from open to closed folder locations. |

### Context Engineering

| Agent                    | Role                                                                                                                   |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| **Context-Librarian**    | Discovers documentation relevant to tasks. Manages workbench document archival. Maintains institutional memory.        |
| **Codebase-Surveyor**    | Identifies source code files relevant to tasks. Provides file paths for User Agent to read.                            |
| **Project-Bootstrapper** | Educates User Agents on project rules and conventions. Improves compliance by setting expectations before work begins. |

### Quality Assurance

| Agent                     | Role                                                                                                     |
| ------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Documentation-Steward** | Ensures code implementations match specifications. Flags specification drift. Has veto power.            |
| **Rule-Enforcer**         | Verifies compliance with Agent-Rules.md and coding standards. Has veto power.                            |
| **Test-Guardian**         | Runs test suite, verifies coverage, prevents regressions. Reports test results as Proof of Work.         |
| **Health-Inspector**      | Runs comprehensive health checks (lint, type, security, format). Reports health status as Proof of Work. |

### Specialized Tasks

| Agent                 | Role                                                         |
| --------------------- | ------------------------------------------------------------ |
| **Feature-Writer**    | Creates feature specification documents following templates. |
| **Demo-Presenter**    | Creates executable demonstrations for stakeholders.          |
| **Process-Inspector** | Audits development tools and processes for accuracy.         |

## Key Artifacts

WSD creates and manages several important artifacts during the workscope lifecycle.

### Workscope Files

**Location:** `dev/workscopes/archive/Workscope-YYYYMMDD-HHMMSS.md`

Immutable records of assigned work. Created by Task-Master during `/wsd:init`. Never modified after creation. Contains:
- Workscope ID and navigation path
- Phase inventory of the terminal checkboxlist
- Assigned task numbers and descriptions (Selected Tasks)
- Phase 0 status and context documents

For the complete workscope file format specification, see `docs/read-only/Workscope-System.md`.

### Work Journals

**Location:** `dev/journal/archive/Journal-Workscope-YYYYMMDD-HHMMSS.md`

Living records of session activity. Created during `/wsd:init`. Continuously updated by User Agent. Contains:
- Session timeline
- Decisions made
- Special Agent reports
- Issues encountered

### Checkboxlists

**Primary Location:** `docs/core/Action-Plan.md`
**Additional Locations:** Feature specs, tickets, and other documentation

Hierarchical task lists using five checkbox states:
- `[ ]` - Unaddressed (available for selection)
- `[%]` - Incomplete/unverified (requires fresh review, treated like `[ ]`)
- `[*]` - Assigned to active workscope
- `[x]` - Completed
- `[-]` - Intentionally skipped (requires User authorization)

### Workbench Documents

**Location:** `docs/workbench/`

Temporary working memory for the current focus. Documents here are:
- Created during active work
- Reviewed for archival during `/wsd:close`
- Promoted to permanent locations (`docs/features/`, `docs/read-only/`, etc.) or archived

### AI Diagnostics

**Location:** `dev/diagnostics/`

A digital "scratch pad" for agent work. A place for temporary files to go and be forgotten.
- Some LLM models insist on creating reports on every task that the User did not request and is not interested in.
- Some tasks require the creation of a temporary script for a one-off operation.
- Occasionally, an agent will generate an artifact (document or script) that might be useful in the future or to re-run during a longer investigation, and they can be found here.
- The Diagnostics folder is for the agents, by the agents, and outside the User's concern.

## Common Workflows

### Starting a New Session

```bash
# In Claude Code
/wsd:init                    # Initialize and get workscope assignment
# Review the assigned workscope
/wsd:prepare                 # Load context for the work
/wsd:execute                 # Do the work and pass QA
# Address any concerns raised by User Agent
/wsd:close                   # Finalize the workscope
/clear                       # Start fresh for next session
```

### Custom Work Assignment

```bash
/wsd:init --custom           # Initialize without Task-Master assignment
# Benefits:
#   - User Agent is briefed on all essential system context
#   - Workscope-ID is generated and Work Journal is started
#   - User Agent is onboarded with Project-Bootstrapper to understand rules and conventions

# User provides custom instructions directly in interactive chat
```

### Handling QA Failures

If a Special Agent rejects work during `/wsd:execute`:
1. Review the agent's feedback in the Work Journal
2. Make requested corrections
3. The User Agent will re-engage the agent for approval (request "resume the conversation with...")
4. If issues persist, escalate to User for guidance

### Aborting Mid-Session

```bash
/wsd:abort                   # Cancel at any point
# Checkboxlists restored to pre-session state
# Use git to revert any unwanted file changes
```

## Task Runner Commands

The WSD Task Runner (`./wsd.py`) provides unified commands for development tasks. Full documentation is in `Task-Runner-Guide.md`, but commonly used commands include:

```bash
./wsd.py health              # Run comprehensive health checks
./wsd.py test                # Run test suite
./wsd.py lint                # Check code style
./wsd.py lint:fix            # Auto-fix lint issues
./wsd.py format              # Format code
./wsd.py docs:update         # Update project documentation reports
```

## Best Practices

### For Effective Sessions

1. **One workscope at a time**: Complete or abort before starting another
2. **Trust the QA gauntlet**: Special Agents catch issues you might miss
3. **Use journals**: Work Journals are your audit trail and handoff notes
4. **Commit frequently**: Git is your safety net for any mistakes

Note: **Parallel workscopes are supported**: the Task-Master agent coordinates "reserved" tasks using `[*]`

### For Project Organization

1. **Keep Action Plan updated**: It drives the entire workscope assignment system
2. **Use tickets for discoveries**: Found a bug? `/open-ticket` captures it for later
3. **Interject new work**: Using `Phase 0` in any checkboxlist. Any unaddressed item in Phase 0 is **blocking** and must be prioritized for selection by the Task-Master over any other task in a checkboxlist.
4. **Archive workbench regularly**: Promote or archive documents to prevent clutter, though the Context-Librarian also cleans up.
5. **Document design decisions**: `/add-dd` preserves design philosophies specific to a project that will be read by all future agents.

### For Teams

1. **Standardize on lifecycle**: All team members follow init → prepare → execute → close
2. **Review Work Journals**: They capture what each session accomplished
3. **Share via workbench**: Cross-session coordination happens through workbench documents

---

*This guide covers WSD usage. For installation, see `Integration-Guide.md`. For updates, see `Update-Guide.md`. For platform configuration, see the project guides.*
