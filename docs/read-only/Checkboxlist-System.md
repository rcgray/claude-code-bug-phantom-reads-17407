# Checkboxlist System Overview

This document defines the checkboxlist system that serves as the fundamental task management and coordination mechanism for this project. Every agent (both User Agents and Special Agents) must understand this system to contribute effectively and maintain project workflow integrity.

## System Overview & Philosophy

The core principle of our checkboxlist system is that **all non-trivial work is organized into hierarchical, numbered, checkbox-tracked task lists that serve as living project plans**. This system ensures that complex projects remain organized, trackable, and actionable while providing a deterministic way to identify the next appropriate work to be performed.

Checkboxlists are the fundamental building blocks of our development process. They transform abstract objectives into concrete, ordered sequences of actionable tasks that can be systematically executed and tracked.

## Checkboxlist Definition

A **checkboxlist** is an ordered list of items organized into a potentially infinitely nested hierarchy of logical groups, where each individual item is:

1. **Numbered** according to its location in the hierarchy
2. **Indented** appropriately to show its hierarchical level
3. **Marked with a checkbox** indicating its current status
4. **Formatted** with markdown for readability

Example anatomy of a checkboxlist:

```markdown
## Phase 0: Blocking Tasks
- [x] Audit on some aspect of the codebase (see docs/workbench/file.md), which is now complete
- [ ] Refactor of Phase 1 getters and setters (see docs/workbench/refactor-plan.md)

## Phase 1: Some high-level task group
- [ ] **1.1** - Initial implementation
  - [ ] **1.1.1** - Setup basic structure
  - [ ] **1.1.2** - Implement core functionality
- [ ] **1.2** - Testing and validation

## Phase 2: Another high-level task group
- [ ] **2.1** - Complex feature implementation
  - [x] **2.1.1** - Design phase completed
  - [-] **2.1.2** - Initially planned approach (decided to skip after design review)
  - [*] **2.1.3** - Currently being implemented by another workscope
  - [ ] **2.1.4** - Next step after 2.1.3 completes
- [ ] **2.2** - Documentation and deployment
```

**Important Note**: Comments on individual tasks should be used with care and should generally annotate exceptions or caveats to normal completion or reasons for skipping. The comment above "(decided to skip after design review)" is appropriate, but "Completed on 03-25-2024" is not. Phase titles should almost never have comments. Finally, comments that merely report progress (e.g., "4 Complete, 1 Remaining") are **FORBIDDEN**. This violates the Source of Truth principle, where the checkboxlist itself conveys the completion status of a phase and does not benefit from a summary comment that will quickly become outdated.

## Checkbox States

Each checkbox represents one of five possible states, which can be understood along two important dimensions:

### The Five States:
- **`[ ]`** - **Unaddressed**: Task not yet started or attempted
- **`[%]`** - **Incomplete/Unverified**: Task has existing work that is INCOMPLETE or UNVERIFIED - treat IDENTICALLY to `[ ]` for ALL selection purposes. The User Agent has full implementation responsibility. (Requires explicit User authorization to create)
- **`[*]`** - **Assigned to Active Workscope**: Currently designated for an active workscope (used for parallel workflow coordination)
- **`[x]`** - **Completed**: Task has been finished successfully
- **`[-]`** - **Intentionally Skipped**: Task deliberately abandoned and left for posterity (requires explicit User authorization)

### Two-Dimensional Classification:

| State | Work Remains? | Available for Workscope Selection? |
| ----- | ------------- | ---------------------------------- |
| `[ ]` | Yes           | Yes                                |
| `[%]` | Yes           | Yes (validation needed)            |
| `[*]` | Yes           | No (assigned elsewhere)            |
| `[x]` | No            | No (completed)                     |
| `[-]` | No            | No (skipped)                       |

**For Task Master Workscope Selection**: `[ ]` and `[%]` are **available**; `[*]`, `[x]`, and `[-]` are **unavailable**
**For Project Status Assessment**: `[ ]`, `[%]`, and `[*]` indicate **work remains**; `[x]` and `[-]` indicate **work completed**
**For Checkboxlist Completeness**: A checkboxlist is **complete** when ALL tasks are in terminal states (`[x]` or `[-]`). No `[ ]`, `[%]`, or `[*]` tasks remain.

## Hierarchical Structure & Numbering

### Phase Organization
Checkboxlists are organized into **Phases** representing high-level groupings of related work:

- **Phase 0**: Special blocking phase for urgent issues discovered during execution that must be resolved before any other work
- **Phase 1, 2, 3...**: Regular phases containing the main body of work, executed sequentially

⚠️ **PHASE 0 TRAP**: Phase 0 DOES NOT refer to work that is "foundational" or "fundamental." Rather, it is a special, reserved phase for blocking tasks that arise during implementation of the regular phases of the list. When READING a checkboxlist, consider Phase 0 items to be BLOCKING the regular phases, when creating a new checkboxlist, it should NEVER begin with Phase 0. New checkboxlists should begin with Phase 1.

### Numbering Convention
Items are numbered hierarchically using this pattern:

```markdown
## Phase 1: Description
- [ ] **1.1** - First major task in Phase 1
  - [ ] **1.1.1** - First subtask
  - [ ] **1.1.2** - Second subtask
    - [ ] **1.1.2.1** - Detailed sub-subtask
    - [ ] **1.1.2.2** - Another detailed sub-subtask
  - [ ] **1.1.3** - Third subtask
- [ ] **1.2** - Second major task in Phase 1
```

### Markdown Formatting Requirements
- Use appropriate header levels for Phases (`##`, `###`, `####` based on document depth)
- Bold the hierarchical numbers: `**1.1.**`, `**2.1.3.**`
- Use proper indentation (2 spaces per level)
- Include descriptive task names after the numbers

### Content Separation Rules

**Core principle: A checkboxlist must be a cohesive, uninterrupted list of tasks.**

Once a checkboxlist begins (starting with the first Phase header), it must contain ONLY phase headers and task items until it ends. No explanatory text, analysis, or other content can be inserted between tasks or between phase headers and their tasks.

- **Checkboxlists contain ONLY** numbered tasks with checkbox states and brief task descriptions
- **Phase headers** must be immediately followed by their tasks - no text in between
- **Analysis, rationale, and context** belong in document sections OUTSIDE the checkboxlist
- **Supporting information** goes in dedicated sections using standard markdown headers (`##`, `###`, `####`)

**Correct Checkboxlist Structure:**
```markdown
## Action Plan

### Phase 0: Audit (BLOCKING)
- [ ] **0.1** - Verify configuration files
  - [ ] **0.1.1** - Check template files
  - [ ] **0.1.2** - Check example files

### Phase 1: Implementation
- [ ] **1.1** - Update source code
- [ ] **1.2** - Update tests
```

**Common Violation - Embedded Content:**
```markdown
### Phase 0: Audit (BLOCKING)

**Severity**: HIGH           ← VIOLATION - text between header and tasks
**Discovery Date**: 2025-10-24  ← VIOLATION - text between header and tasks

- [ ] **0.1** - Verify files

**Focus Areas**:             ← VIOLATION - text between tasks
- Template files
- Example files

- [ ] **0.2** - Check references
```

Any text that appears between a phase header and its first task, or between tasks themselves, breaks the checkboxlist cohesiveness and violates the structure.

## Phase 0: Blocking Tasks

**Phase 0 is fundamentally different from all other phases**:

1. **Absolute Priority**: Any incomplete Phase 0 item blocks ALL other work in the checkboxlist
2. **Sequential Processing**: Phase 0 items must be addressed in order (top-most incomplete item first)
3. **Discovery Pattern**: Phase 0 items typically emerge during execution of regular phases when blocking issues are discovered
4. **Escalation Function**: Serves as the primary mechanism for handling urgent, blocking work that must be resolved immediately

**Critical Rule**: If ANY item in Phase 0 is available for selection (`[ ]` or `[%]`), no work from Phases 1+ can be selected for workscopes. Items marked `[*]` (assigned to other workscopes) do not block progression.

## Parent-Child State Relationships

Parent task states are automatically determined by their children's states using this priority logic:

1. **If ANY child is `[ ]` or `[%]`** → Parent becomes `[ ]` (available work exists below)
2. **If ANY child is `[*]` (and no `[ ]`/`[%]`)** → Parent becomes `[ ]` (work in progress, branch not complete)
3. **If ALL children are `[x]` or `[-]`** → Parent becomes `[x]` (branch completed)
4. **If ALL children are `[-]`** → Parent becomes `[-]` (entire branch skipped)

**Important:** Parents are never `[*]` or `[%]`. Only leaf tasks can be assigned to workscopes or marked for validation.

### Parent-Child State Algorithm

**CRITICAL: These conditions must be evaluated IN ORDER. Stop at the FIRST condition that matches.**

```pseudocode
function determineParentState(children):
    if ANY child has state [ ] or [%]:
        return [ ]  # Available work exists - parent shows available

    else if ANY child has state [*]:
        return [ ]  # Work in progress - parent still shows available (not complete)

    else if ANY child has state [x]:
        return [x]  # All terminal states, at least one completed

    else if ALL children have state [-]:
        return [-]  # Only possible if every single child is skipped
```

### Navigation Signals

This design creates natural navigation signals for Task Master workscope selection:

- **`[ ]`** on a parent means "available work exists below - continue deeper"
- **`[x]`** on a parent means "branch complete - skip to next branch"
- **`[-]`** on a parent means "branch skipped - skip to next branch"

Since parents are never `[*]`, seeing `[ ]` on a parent with `[*]` children correctly signals "this branch has work in progress but isn't complete yet" - the `[*]` tasks might fail and revert to `[ ]`.

### Cross-Document Parent-Child Relationships

**Hierarchy Spans Documents:**
Parent-child relationships exist across document boundaries through references:
- Task with "(see docs/filename)" = PARENT of linked document's checkboxlist
- Parent-child priority logic applies regardless of document separation
- State propagation must occur bidirectionally between linked documents

**Priority Logic Across Documents:**
When a parent task references a linked document:
1. Evaluate ALL children in the linked document
2. Apply standard priority logic: "If ANY child is `[ ]` or `[%]` → Parent becomes `[ ]`"
3. Update parent task state in the referring document
4. Continue propagation up any additional parent levels

**Example:**
```
docs/core/Action-Plan.md:
  - [ ] **13.10.9** - Implement caching (see docs/features/caching/Caching-Overview.md)

docs/features/caching/Caching-Overview.md:
  - [x] **3.1** - Design cache structure
  - [x] **3.2** - Implement cache invalidation
  - [ ] **3.3** - Add cache metrics  ← Forces parent 13.10.9 to be [ ]
```

## Single Checkboxlist Rule

Each document (ticket, spec, workbench file) must contain at most ONE authoritative checkboxlist. Multiple checkboxlists in a single document create ambiguity about which tasks are assigned, how progress is tracked, and which represents actual work to be done. When you encounter a document with multiple distinct Phase-based checkboxlists (e.g., both "## Implementation Plan" and "## Action Plan" with different tasks), immediately escalate to the User with the document path and line numbers where each begins. Never assume which checkboxlist is authoritative.

## Workscope Selection Process

The Task Master is responsible for systematically identifying the next appropriate workscope using a deterministic process that:

1. **Prioritizes Phase 0**: Always handles blocking tasks first
2. **Follows Cross-References**: Navigates linked checkboxlists to find the deepest incomplete work
3. **Ensures Appropriate Scope**: Selects work suitable for one User Agent session
4. **Coordinates Parallel Work**: Uses `[*]` state to prevent conflicts between concurrent workscopes
5. **Creates Workscope Files**: Documents selections in formal workscope files with unique IDs

The detailed algorithm, sizing guidelines, and comprehensive examples for workscope selection are documented in the Workscope System (`docs/read-only/Workscope-System.md`).

## Navigation vs. Actionable Tasks

Checkboxlists contain two fundamentally different types of tasks that must be recognized and handled differently:

### Navigation Pointer Tasks (References)

**Pattern:** Task text contains "(see docs/...)" or similar reference

**Purpose:** Guide navigation to deeper checkboxlists where actual work resides

**Selection:** Never select these directly for workscopes; always follow the link

**Examples:**
- "[ ] - Implement authentication (see docs/features/auth/Auth-Overview.md)"
- "[ ] - Fix cache bug (see docs/tickets/open/cache-bug.md)"
- "[ ] - Refactor module (see docs/workbench/refactor-plan.md)"

### Actionable Leaf Tasks

**Pattern:** Specific, concrete action with clear completion criteria

**Purpose:** Define actual work to be performed

**Selection:** These are appropriate for workscope assignment

**Examples:**
- "[ ] **1.1** - Change get_cache() to use ConfigManager.get_effective_config()"
- "[ ] **2.3** - Update test assertions to expect 1000MB default"
- "[ ] **3.4** - Add docstring to explain zero value behavior"

**Critical Rule:** The Task Master must recognize navigation pointers and follow them to find leaf tasks. Assigning a navigation pointer violates the hierarchical checkboxlist system.

## Document Locations & Types

### Special Checkboxlists:
- **`docs/core/Action-Plan.md`**: The root checkboxlist for the entire project
- **`docs/references/Action-Plan-Archive.md`**: Archived completed phases for historical reference

### Feature-Specific Checkboxlists:
- **`docs/features/[feature-name]/[Feature-Name]-Overview.md`**: Contains Feature Implementation Plan (FIP) at the end

### Ticket Checkboxlists:
- **`docs/tickets/open/[ticket-name].md`**: Active tickets with their resolution checkboxlists
- **`docs/tickets/closed/[ticket-name].md`**: Completed tickets (moved by Task Master)

### Workbench Checkboxlists:
- **`docs/workbench/[descriptive-name].md`**: Investigation, audit, or smaller task checkboxlists

### Connectivity Rule:
Checkboxlists only become "active" when connected to the root Action Plan through a chain of references. Orphaned checkboxlists remain dormant until linked into the project plan.

## Task Management Operations

### Adding New Work:
1. **Insertion Point**: Specify where new task should be inserted (e.g., "new 2.4")
2. **Renumbering**: Push existing tasks down as needed to maintain sequential numbering
3. **Scope Consideration**: Ensure new tasks fit logically within their phase grouping

### Updating Task Status:
1. **Completion Tracking**: Update checkboxes based on actual work completion
2. **Parent Propagation**: Parent states automatically reflect child completion status
3. **State Transitions**: Tasks can move between any states as work progresses or requirements change

### Workscope Management:
1. **Assignment**: Mark selected tasks as `[*]` when creating workscope
2. **Completion Processing**: Update ONLY the specific `[*]` tasks that were assigned to the completed workscope to appropriate final states (`[x]`, `[ ]`) based on User Agent results. Never modify `[*]` items belonging to other active workscopes.
3. **Parallel Coordination**: Multiple Task Masters treat `[*]` as unavailable for new workscope selection but only manage their own assigned `[*]` items

### Cross-Document Hierarchy Responsibilities
**Task Master MUST:**
- Recognize parent-child relationships across document boundaries
- Apply parent-child priority logic spanning multiple documents
- Propagate state changes bidirectionally through navigation paths
- Maintain consistency across the entire connected hierarchy

**During Any Checkboxlist Update:**
1. **Local Changes**: Update the immediate tasks
2. **Cross-Document Propagation**: Follow navigation path back to parent documents
3. **Priority Logic Application**: Update parent states based on children across documents
4. **Root Validation**: Ensure consistency reaches back to Action Plan

## Authority & Responsibilities

### Task Master Special Agent:
- **Primary Authority**: Responsible for maintaining all checkboxlists
- **Workscope Assignment**: Uses depth-first search to identify and assign appropriate work
- **Status Management**: Updates checkbox states and manages task progression
- **Consistency Maintenance**: Repairs checkboxlist inconsistencies and ensures parent-child state alignment
- **Ticket Management**: Moves completed tickets from `open/` to `closed/` directories

### User Agents:
- **Execution Focus**: Execute assigned workscopes without directly modifying checkboxlists
- **Status Reporting**: Report completion status to Task Master for checkboxlist updates
- **Escalation**: Alert User to checkboxlist issues discovered during work

### All Other Agents:
- **Read-Only Access**: Understand checkboxlists for context but do not modify them
- **User Direction Only**: Only edit checkboxlists under explicit User instruction

### User Authority:
- **Skip Authorization**: ONLY the User can mark tasks as skipped `[-]` or direct agents to do so
- **Validation Authorization**: ONLY the User can mark tasks as needing validation `[%]` (typically by converting `[x]` to `[%]`)
- **State Transitions**: Can override any checkbox state transitions
- **Structural Changes**: Authorizes major checkboxlist reorganization or archival

## Critical Rules & Violations

### Forbidden Actions:
- **Autonomous Skipping**: No agent may mark items as `[-]` without explicit User authorization
- **Autonomous Validation Marking**: No agent may mark items as `[%]` without explicit User authorization
- **Unauthorized Editing**: Non-Task Master agents must not edit checkboxlists except under User direction
- **Phase 0 Bypass**: Never select regular phase work when Phase 0 contains available items (`[ ]` or `[%]`)

### Required Actions:
- **State Consistency**: Task Master must maintain parent-child state relationships
- **Status Tracking**: All workscope assignments and completions must update checkbox states
- **Link Validation**: Broken checkboxlist references must be escalated to User immediately

### Error Recovery:
- **Inconsistent States**: Task Master should repair automatically when safe, escalate when uncertain
- **Missing References**: Escalate to User or consult Context Librarian for resolution
- **Conflicting Information**: Always escalate to User for clarification

## Integration with Other Systems

### Agent System Integration:
- Checkboxlists define workscopes that drive the User Agent → Special Agent workflow
- Task Master serves as the authoritative source for "what work should happen next"
- All agents must understand checkboxlist context to function effectively within project workflows

### Documentation System Integration:
- Checkboxlists appear at the END of documents covering their respective topics
- Workbench documents containing checkboxlists follow standard documentation lifecycle
- Context Librarian helps locate relevant checkboxlists when references break

### Version Control Integration:
- Checkboxlist updates correspond to workscope completions and git commits
- Completed workscopes represent logical units of progress suitable for version control
- Historical checkboxlist states preserved through git history

## Success Principles

Effective checkboxlist management requires:

1. **Systematic Approach**: Always follow the depth-first search algorithm for workscope selection
2. **State Integrity**: Maintain accurate parent-child state relationships at all times
3. **Clear Authority**: Respect the Task Master's role while escalating appropriately to User
4. **Living Documents**: Treat checkboxlists as evolving plans that adapt to project realities
5. **Deterministic Process**: Use consistent rules that produce predictable, repeatable results

This checkboxlist system ensures that complex multi-phase projects remain organized, trackable, and efficiently executable while providing clear coordination mechanisms for our elite team of User and Special Agents.
