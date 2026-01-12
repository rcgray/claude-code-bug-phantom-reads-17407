# Workscope System Overview

This document defines the workscope system that serves as the fundamental work assignment and tracking mechanism for this project. Every agent (both User Agents and Special Agents) must understand this system to effectively coordinate work execution and maintain project momentum.

## System Overview & Philosophy

The core principle of our workscope system is that **every unit of work assigned to a User Agent is formally defined, immutably documented, and uniquely identified**. This system ensures that complex work assignments remain consistent throughout their lifecycle, from initial selection through final completion.

A workscope represents the atomic unit of work in our development process - it's what a single User Agent can reasonably accomplish in one session while maintaining quality and thoroughness. The workscope system transforms the abstract concept of "work to be done" into concrete, traceable, and manageable assignments.

## Workscope Definition

A **workscope** is a formally documented work assignment that:

1. **Identifies specific tasks** from checkboxlists that form a coherent unit of work
2. **Maintains immutability** through file-based documentation that cannot change during execution
3. **Provides unique identification** via timestamp-based filenames
4. **Tracks navigation path** showing how the tasks were discovered
5. **Records context** including Phase 0 status and any User directive

### Workscope File Format

Every workscope is documented in a file at `dev/workscopes/archive/Workscope-YYYYMMDD-HHMMSS.md`. This is the **authoritative specification** for workscope file contents—all other documents should reference this section rather than defining their own format.

**Important Note:** Workscope files are produced by the Task-Master agent (an LLM) and consumed by other agents. The format described here is a guide for interpretation, not a rigid schema. Minor variations in formatting, section headers, or additional context are acceptable as long as the core information is present and interpretable.

**Required Sections:**

```markdown
# Workscope-YYYYMMDD-HHMMSS

## Workscope ID
YYYYMMDD-HHMMSS

## Navigation Path
1. `docs/core/Action-Plan.md` (Phase 0, item 0.22)
2. `docs/tickets/open/some-ticket.md`

## Phase Inventory (Terminal Checkboxlist)

**Document:** `docs/tickets/open/some-ticket.md`

```
PHASE INVENTORY FOR some-ticket.md:
Phase 0: CLEAR
Phase 1: CLEAR
Phase 2: 2.1 - First available task description
Phase 3: 3.1 - Another task description

FIRST AVAILABLE PHASE: Phase 2
FIRST AVAILABLE ITEM: 2.1 - First available task description
```

## Selected Tasks

**Phase 2: Phase Description**

- [ ] **2.1** - First task description
  - [ ] **2.1.1** - Subtask one
  - [ ] **2.1.2** - Subtask two
- [ ] **2.2** - Second task description

**Total Leaf Tasks**: 4

## Phase 0 Status (Root Action Plan)

**Status**: BLOCKING

Phase 0 has available items:
- 0.22 - Description of blocking item
- 0.23 - Another blocking item

(or simply "CLEAR" if no Phase 0 items remain)

## Context Documents

**Primary Context:**
- docs/core/Action-Plan.md
- docs/tickets/open/some-ticket.md

**Related Documentation:**
- docs/core/Design-Decisions.md

**Implementation Files:**
- source/some-file.py

## Directive

None provided.
(or the workscope directive text from User)
```

**Section Details:**

| Section | Description |
|---------|-------------|
| **Workscope ID** | Timestamp-based identifier (`YYYYMMDD-HHMMSS`). May be prefixed with `Workscope-` in some contexts. |
| **Navigation Path** | List of documents traversed from Action-Plan.md to the terminal checkboxlist. Format varies (numbered list, arrows, etc.) but shows the navigation chain. |
| **Phase Inventory** | Phase-by-phase status of the terminal checkboxlist showing first available item in each phase or "CLEAR". Typically includes the terminal document name. |
| **Selected Tasks** | Checkbox items with their states BEFORE marking as `[*]`, showing the exact work assigned. May include phase headers and task counts. |
| **Phase 0 Status** | Whether Action-Plan.md Phase 0 is BLOCKING (with details) or CLEAR. May include listing of specific Phase 0 items. |
| **Context Documents** | Documents relevant to the workscope. Often categorized (Primary, Related, Implementation, Tests). |
| **Directive** | Workscope directive from User (if provided) or "None provided." May appear as "Workscope Directive" in some files. |

The Task-Master may include additional sections (e.g., "Work Description", "Scope Summary") providing helpful context. These are informational and do not change the workscope assignment.

## ⚠️ Critical Violation: The Parent Reference Trap

**The most common workscope selection error** is assigning a parent reference task instead of following links to find actual work.

**Violation Pattern:**
A checkboxlist task contains "(see docs/...)" — this is a **navigation pointer**, not actionable work.

**Examples:**
- "[ ] - Fix cache bug (see docs/tickets/open/cache-bug.md)"
- "[ ] - Implement feature (see docs/workbench/feature-plan.md)"

**Correct Process:**
1. Recognize "(see...)" as a signal to navigate deeper
2. Follow link to the referenced document
3. Find checkboxlist in that document
4. Select specific leaf tasks from that checkboxlist
5. Mark those leaf tasks as `[*]` in the linked document

**Wrong:** Selecting "Fix cache bug (see ticket.md)" from Action-Plan.md
**Right:** Navigating to ticket.md and selecting "1.1 Update function signature"

This violation defeats the hierarchical system - parent references are navigation, leaf tasks are work.

## Workscope Selection Algorithm

The Task Master implements a systematic depth-first search algorithm to identify the most appropriate work for assignment. This algorithm ensures deterministic, consistent workscope selection across all project checkboxlists.

### Core Navigation Rules

**State Classifications:**
- **Available States**: `[ ]` (unaddressed) and `[%]` (needs fresh review) - can be selected for workscopes
- **Unavailable States**: `[*]` (assigned elsewhere), `[x]` (completed), `[-]` (skipped) - cannot be selected
- **Phase 0 Priority**: Always examine Phase 0 before any regular phases (absolute blocking priority)
- **Link Following**: When an item references another checkboxlist document, navigate there and continue the algorithm

**Cross-Document Parent-Child Relationships:**

When following links to other documents, recognize that:
- The referencing task serves as PARENT to the entire linked checkboxlist
- Parent-child priority logic applies across document boundaries
- State changes must propagate bidirectionally between linked documents
- Navigation path tracks this hierarchical relationship for state propagation

### Selection Algorithm Steps

1. **Initialize Focus**: Start with the root checkboxlist document (usually Action-Plan.md)

2. **Phase Priority Check**:
   - First check if Phase 0 section exists
   - If Phase 0 has available items (`[ ]` or `[%]`), MUST select from Phase 0
   - If Phase 0 is clear or all items are unavailable, proceed to regular phases

3. **Item Evaluation**: For each item in the current section:
   - Skip unavailable items (`[*]`, `[x]`, `[-]`)
   - For available items (`[ ]` or `[%]`), proceed to navigation decision

4. **Navigation Decision** for available items:
   - **If item links to another document**: Follow link, set as new focus, return to step 2
   - **If item has available sub-items**: Continue deeper into hierarchy
   - **If item is a leaf node**: Consider for workscope selection

5. **Scope Assessment**: Determine if current item(s) form an appropriate workscope:
   - **Single task of appropriate size**: Select it
   - **Task too large**: Select subset of its sub-items
   - **Task too small**: Consider grouping with sibling tasks
   - **Coherence check**: Ensure selected tasks form a logical unit

6. **Workscope Creation**:
   - Create workscope file in `dev/workscopes/archive/` with actual checkbox states
   - After file creation, mark selected items as `[*]` in their checkboxlists
   - Return workscope filename to User Agent

### Workscope Sizing Guidelines

**Phase 0 Items (Items Directly in Phase 0 Sections)**:
- **ALWAYS assigned as single items** - never group multiple Phase 0 items from the same checkboxlist together
- **CLARIFICATION**: This constraint applies ONLY to items directly within a Phase 0 section, NOT to work discovered by following links from Phase 0 items
- When a Phase 0 item links to another document (e.g., "Fix bug (see ticket.md)"):
  - The Phase 0 single-item constraint does NOT apply within the linked document
  - Apply normal workscope sizing guidelines to tasks found in the linked document
  - Can select multiple related tasks from the linked checkboxlist as a coherent workscope
- Phase 0 items are intentionally divided by the User into discrete units of work
- The constraint prevents combining "Fix bug A" and "Fix bug B" from Phase 0, NOT limiting the size of work found within bug A's ticket
- Experience shows grouped Phase 0 items (from the same Phase 0 section) lead to failed workscopes

**Example of Correct Application:**
- Phase 0 has: "[ ] Fix cache bug (see ticket.md)" and "[ ] Fix auth bug (see auth-ticket.md)"
- CANNOT combine both Phase 0 items into one workscope
- CAN follow link to ticket.md and select multiple tasks (4.1, 4.2, 4.3, 4.4, 4.5) from within that ticket
- The Phase 0 constraint is about not mixing different Phase 0 items, not about limiting work size within a single Phase 0 item's scope

**Regular Phase Items**:
- **Ideal Size**: 2-5 hours of focused work
- **Coherence**: Tasks should be related and buildable upon each other
- **Dependencies**: Include all tasks needed to reach a testable state
- **Completeness**: Prefer complete features over partial implementations

**Cross-Document Tasks**:
- Follow references to find the actual actionable work
- Maintain navigation path for traceability
- Consider the full depth of work when sizing

## Workscope Selection Examples

### Example 1: Simple Direct Selection
```
Situation: Action Plan Phase 0 clear, working through Phase 3
Current Position: Phase 3, item 3.4 is available with no sub-items

Navigation Path: Action-Plan.md
Selected Tasks: 3.4 "Implement dashboard monitoring widgets"
Phase 0 Status: CLEAR
Decision: Single appropriately-sized task
```

### Example 2: Hierarchical Breakdown
```
Situation: Large task with multiple sub-items
Current Position: Phase 5, item 5.3 has 7 sub-items

Navigation Path: Action-Plan.md
Assessment: 5.3 too large as a whole, but 5.3.1-5.3.3 form logical unit
Selected Tasks (showing actual states):
- [ ] **5.3.1** - Implement data validation rules
- [ ] **5.3.2** - Create validation error messages
- [ ] **5.3.3** - Add client-side validation feedback
Phase 0 Status: CLEAR
Decision: Coherent sub-group of related tasks
Note: After workscope file creation, these will be marked [*] in Action-Plan.md
```

### Example 3: Cross-Document Navigation
```
Situation: Action Plan references feature FIP
Current Position: Phase 4 links to User-Management-Overview.md

Navigation Path: Action-Plan.md → User-Management-Overview.md
FIP Status: Phase 2 partially complete, items 2.4-2.6 available
Selected Tasks:
- [ ] **2.4** - Add password reset flow
- [ ] **2.5** - Implement email notifications
Phase 0 Status: CLEAR
Decision: Related features from FIP
```

### Example 4: Phase 0 Blocking with Directive Override
```
Situation: Phase 0 has two items, User directive to do second one first
Current Position: Phase 0 has [%] **0.1** - "Auth errors on Chrome", [ ] **0.2** - "Logging system error"

User Directive: "Logging system error bug in Phase 0"
Navigation Path: Action-Plan.md
Selected Task (following directive):
- [ ] **0.2** - Logging system error
Phase 0 Status: BLOCKING with 2 items remaining
Decision: Override normal order per User directive
Note: Auth errors task skipped despite being first, per directive
```

### Example 5: Multi-Level Navigation Chain
```
Situation: Complex navigation through multiple documents
Starting Point: Action Plan Phase 8

Navigation Path:
  Action-Plan.md →
  Callback-Server-Overview.md →
  callback-performance-audit.md

Final Position: Audit doc has 5 items, items 4-5 available
Selected Tasks:
- [ ] **4** - Benchmark current performance
- [ ] **5** - Document optimization opportunities
Phase 0 Status: CLEAR
Decision: Deepest available work found through chain
```

### Example 6: Task Needing Fresh Review (`[%]` State)
```
Situation: Task may have existing work but needs fresh implementation review
Current Position: Phase 3, item 3.4 marked [%]

Navigation Path: Action-Plan.md
Selected Task (showing actual state):
- [%] **3.4** - Implement caching layer (work may exist - verify and complete)
Phase 0 Status: CLEAR
Decision: Treat as [ ] - User Agent has full implementation responsibility

Note: User Agent works through task as if implementing from scratch, comparing
against what exists at each step. Find the "delta" between current state and
specification, then implement it. Do not assume existing work is complete or correct.
```

### Example 7: Workscope Directive Application
```
Situation: User provides directive "just grab the first three items of 3.15"
Current Position: Phase 3, item 3.15 has 10 sub-items

Navigation Path: Action-Plan.md
User Directive: "just grab the first three items"
Selected Tasks (following directive):
- [ ] **3.15.1** - Setup environment
- [ ] **3.15.2** - Configure services
- [ ] **3.15.3** - Initial deployment
Phase 0 Status: CLEAR
Decision: Limited scope per User directive
Note: Items 3.15.4-3.15.10 intentionally excluded per directive
```

### Example 8: Parallel Workscope Coordination
```
Situation: Multiple workscopes active
Current Position: Phase 3, items 3.1-3.3 marked [*], item 3.5 available

Existing Assignments: 3.1-3.3 assigned to Workscope-20240912-091500
Selected Tasks: [ ] **3.5** - Add monitoring dashboards
Phase 0 Status: CLEAR
Decision: Skip [*] items, select next available
```

### Example 9: Phase 0 Item Leading to Multiple Tasks
```
Situation: Phase 0 item in Action Plan links to a ticket with multiple phases
Current Position: Phase 0 item "Implement cache design (see ticket.md)"

Navigation Path: Action-Plan.md → docs/tickets/open/implement-cache-design.md
Ticket Status: Phases 1-3 complete, Phase 4 has 5 documentation tasks
Selected Tasks (from within the ticket):
- [ ] **4.1** - Update Config-Spec.md
- [ ] **4.2** - Update .env.example
- [ ] **4.3** - Add sizing guidance
- [ ] **4.4** - Search and update old references
- [ ] **4.5** - Update README
Phase 0 Status: BLOCKING (this Phase 0 item from Action Plan)
Decision: All 5 documentation tasks form coherent workscope

Note: Even though this originates from a Phase 0 item, the Phase 0 single-item
rule doesn't apply to tasks WITHIN the linked document. We can group related
tasks from the ticket as normal.
```

### Example 10: Fresh Review After Spec Update (`[%]` State)
```
Situation: Spec was updated after initial implementation - tasks need fresh review
Current Position: Phase 2, items marked [%] after spec changes

Navigation Path: Action-Plan.md → Feature-Overview.md
Selected Tasks (showing actual states):
- [%] **2.1** - Implement core parser (work may exist - verify and complete)
- [%] **2.2** - Add error handling (work may exist - verify and complete)
- [%] **2.3** - Create unit tests (work may exist - verify and complete)
Phase 0 Status: CLEAR
Decision: Treat as [ ] - User Agent has full implementation responsibility

Note: User Agent works through each task as if implementing from scratch,
comparing against existing code at each step. Find the "delta" between current
implementation and current specification, then implement it. The User Agent is
responsible for the complete, correct implementation - not just reviewing or
reporting findings. If 100% of work exists and is correct, confirm it; if gaps
exist, fill them.
```

## Workscope Lifecycle

### 1. Initial Creation (Task-Master)
- Performs depth-first search to identify appropriate work
- Creates workscope file with unique timestamp ID showing actual task states
- Populates Context Documents section with documents discovered during selection
- After file creation, marks selected tasks as `[*]` in checkboxlists
- Returns workscope filename to User Agent
- Workscope file is now permanently immutable

### 2. Context Enhancement (Context-Librarian)
- Reads workscope file to understand the assignment
- Reviews Context Documents that were included in the workscope file by the Task-Master
- Identifies additional relevant documents from broader project knowledge of workbench, references, tickets, and other documentation
- Provides complete file list directly to User Agent via response
- Workscope file remains immutable throughout this process

### 3. Assignment (User Agent)
- Receives workscope filename from Task Master
- Receives file list from Context-Librarian
- Reads workscope file and all Context-Librarian provided documents
- References workscope ID when communicating with Special Agents
- Maintains workscope ID throughout entire session

### 4. Execution (User Agent + Special Agents)
- User Agent executes tasks defined in workscope (for `[%]` tasks, treat as `[ ]` with possible existing work)
- Special Agents read workscope file directly for complete context
- Workscope file remains immutable (never modified after creation)
- All agents reference same authoritative workscope definition

### 5. Completion (Task-Master)
- Receives completion report referencing workscope ID
- Updates `[*]` items to final states (`[x]` or `[ ]`)
- Only modifies items listed in the specific workscope file
- Workscope file remains as permanent record

### 6. Cross-Document State Propagation (Task-Master)
- After updating workscope tasks to final states:
  1. **Navigate Back Through Navigation Path**: Return to each parent document in reverse order
  2. **Apply Parent-Child Logic**: Update parent task states based on children in linked documents
  3. **Propagate to Root**: Continue until reaching the root Action Plan document
  4. **Validate Consistency**: Ensure no parent-child violations exist across document boundaries

Example Navigation Path Propagation:

- Update tasks in: cache-management-system-spec.md
- Propagate back to: Action-Plan.md (update 13.10.9 based on cache spec children)
- Validate: Full hierarchy consistency from root to leave

### 7. Archival Review (Context-Librarian)
- Uses workscope definition and provided file lists to understand which documents were essential
- Maintains clean workbench based on workscope usage patterns

### 8. User Action Identification (User Agent)
- Reviews all artifacts created during workscope execution
- Identifies items requiring User decisions:
  - Files in `docs/workbench/` that may need promotion to permanent locations
  - Configuration changes that need User approval
  - Standards or references that need permanent homes
  - System settings that require adjustment
- Explicitly communicates these in final report to User
- Distinguishes between "work complete" and "pending User action"

### 9. Long-term Preservation (Automatic)
- Workscope files accumulate in `dev/workscopes/archive/`
- Provide audit trail of all work performed
- Enable process analysis and improvement
- Can be referenced for debugging or investigations

## Parallel Workscope Management

When multiple User Agents work simultaneously:

### Assignment Isolation
- Each Task Master creates separate workscope files
- Workscope IDs ensure no confusion between assignments
- `[*]` markers indicate items unavailable for selection

### Completion Isolation
- Task Master only updates items in its assigned workscope file
- Never modifies `[*]` items from other workscopes
- Workscope ID in completion report ensures correct updates

### Collision Avoidance
- DFS algorithm treats all `[*]` items as unavailable
- Continues searching for unassigned work
- Escalates if no available work remains

## Authority & Responsibilities

### Task Master Authority
- **Initial Creation**: Creates workscope files with context documents
- **Selection**: Implements DFS algorithm for work selection
- **Assignment**: Marks items as `[*]` after file creation
- **Completion**: Updates only items from its created workscopes

### Context-Librarian Authority
- **Context Discovery**: Identifies comprehensive documentation for workscopes
- **Direct Communication**: Provides file lists directly to User Agents
- **Archival Intelligence**: Uses workscope history to inform archival decisions

### User Agent Responsibilities
- **Reference**: Use workscope ID consistently throughout session
- **Execution**: Complete tasks as defined in workscope file
- **Reporting**: Include workscope ID in completion reports

### Special Agent Access
- **Read Access**: Can read workscope files for context
- **No Modification**: Cannot change workscope definitions
- **Reference**: Should cite workscope ID in their assessments

### User Authority
- **Directives**: Provides workscope directives that Task-Master must follow
  - May specify which items to select or skip
  - May limit scope (e.g., "just the first three sub-items")
  - May override normal selection order (e.g., "do the logging bug first")
- **Override**: Can direct specific workscope creation when needed
- **Investigation**: Can review workscope files for quality assurance

## Integration with Other Systems

### Checkboxlist System Integration
- Workscopes are derived from checkboxlist items
- `[*]` state indicates workscope assignment
- Parent-child state relationships reflect workscope progress
- Checkboxlist updates occur only through workscope completion

### Agent System Integration
- Workscope ID replaces verbose workscope descriptions
- User Agents receive workscope filename from Task Master
- Special Agents read workscope files directly
- Communication simplified through ID references

### Documentation System Integration
- Workscope files stored in `dev/workscopes/archive/`
- Follow standard timestamp naming convention
- Permanent records not subject to cleanup
- Part of project's audit trail

### Work Journal Integration
- Work Journal references workscope ID
- Both use same timestamp format (YYYYMMDD-HHMMSS)
- Together provide complete session documentation
- Enable full reconstruction of work performed

## Critical Rules & Best Practices

### Immutability Rules
- **Permanently immutable**: Created once by Task-Master, never modified
- **Never reuse** workscope IDs
- **Never delete** workscope files
- **Always preserve** complete workscope definition

### Selection Rules
- **Always respect** Phase 0 priority, which are BLOCKING to any items in the rest of the checkboxlist
- **Always check** for `[*]` items before selection
- **Always follow** links to find deepest work. **VIOLATION WARNING**: Assigning a task that contains a reference without following that reference to find the actual checkboxlist is a CRITICAL VIOLATION that defeats the entire purpose of the hierarchical system. For example, if a task says "Implement feature (see docs/feature.md)", you MUST navigate to feature.md and find the actual implementation tasks within
- **Always create** workscope file before returning

### Communication Rules
- **Always reference** workscope ID, not description
- **Always include** workscope ID in reports
- **Always read** workscope file for authoritative definition
- **Never interpret** or paraphrase workscope content

### Quality Rules
- **Ensure coherence** in selected tasks
- **Verify sizing** is appropriate for one session
- **Document path** for traceability
- **Include context** for User Agent success

## Success Principles

Effective workscope management requires:

1. **Formalization**: Every workscope has an official, immutable definition
2. **Traceability**: Complete audit trail from selection to completion
3. **Consistency**: All agents work from the same authoritative source
4. **Simplicity**: Communication reduced to workscope ID references
5. **Reliability**: Workscope definitions cannot degrade or evolve during execution

This workscope system ensures that work assignments remain clear, consistent, and traceable throughout their lifecycle, providing the foundation for efficient parallel execution and continuous process improvement.
