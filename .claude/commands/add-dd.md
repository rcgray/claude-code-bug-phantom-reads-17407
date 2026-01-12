---
description: Add a new design decision to Design-Decisions.md
argument-hint: [message]
---

# Add Design Decision

This command adds a new design decision to the `docs/core/Design-Decisions.md` file. Design decisions capture project-specific architectural philosophies that all agents must follow.

**Message:** $ARGUMENTS

## Current Design Decisions

@docs/core/Design-Decisions.md

## Usage

```
/add-dd [message]
```

Where:
- `[message]` is an optional description of the design decision to add. If omitted, the command uses surrounding conversation context.

## Examples

```
/add-dd
```
(Uses recent conversation context to understand the decision)

```
/add-dd We should always validate user input at the API boundary, not deep in business logic
```
(Creates a decision based on the explicit message)

```
/add-dd regarding the error handling pattern we just discussed
```
(References specific conversation context)

## Description

This command enables capturing design decisions at the moment they emerge during development. It writes directly to `docs/core/Design-Decisions.md` rather than creating a draft for review, reducing friction for recording decisions. The User reviews changes via git diff before committing.

For the complete specification of the Design Decisions System, see `docs/features/design-decisions/Design-Decisions-Overview.md`.

### When to Use This Command

Use `/add-dd` when:
- A philosophical choice arises about how the application should work
- An architectural decision is made that future agents should follow
- A pattern emerges that should be consistently applied across the codebase
- A mistake reveals a principle that should be documented

### Decision Entry Format

Every decision entry includes five required fields:

1. **Context**: Describes the situation or scenario where this decision applies. Helps agents recognize when they are in a situation where this decision is relevant.

2. **Decision**: The actual architectural choice or philosophy. This is the directive that agents must follow. Written as a clear statement of what to do (or not do).

3. **Rationale**: Explains why this decision was made. Helps agents understand the reasoning so they can apply the spirit of the decision even in edge cases.

4. **Example**: Shows the wrong approach versus the right approach, typically with code snippets. Makes the decision concrete and unambiguous.

5. **Applies to**: Identifies where this decision is relevant (e.g., "WSD Runtime scripts", "User-facing error messages", "Configuration handling"). Helps agents quickly assess applicability.

### Writing Effective Decisions

**Target Length**: 10-20 lines per decision maximum. Entries must balance completeness with conciseness since every agent reads this file.

**Be Specific**: Include concrete examples showing wrong vs. right approaches. Agents understand patterns better with examples.

**Scope Appropriately**: Clearly define where the decision applies to prevent over-application or under-application.

**Stay Evergreen**: Avoid references to specific versions, dates, or temporary conditions that would require updates.

## Implementation

The command should:

1. **Analyze Context**: Parse the `[message]` argument if provided, or analyze recent conversation to understand the design decision being captured.

2. **Read Current Decisions**: Read `docs/core/Design-Decisions.md` to understand existing decisions and determine the next available number.

3. **Generate Next Number**: Scan existing decision headers (e.g., `## 1.`, `## 2.`) to determine the next sequential number. Decision numbers are permanent; gaps are allowed if decisions are later removed.

4. **Guide Entry Creation**: Create a well-formed entry with all five required fields:
   - **Context**: When/where this decision applies
   - **Decision**: The actual architectural choice
   - **Rationale**: Why this was decided
   - **Example**: Code showing wrong vs. right approach
   - **Applies to**: Where this decision is relevant

5. **Validate Entry Quality**: Before writing, verify the entry:
   - Contains all five required fields
   - Falls within 10-20 lines target length
   - Uses evergreen language (no dates, versions, or temporary references)
   - Includes concrete code examples where applicable

6. **Check for Duplicates**: Scan existing decisions to identify potential duplicates. If a similar decision exists, ask the User whether to proceed (creating an intentional expansion) or cancel (to avoid redundancy).

7. **Append to Document**: Add the new decision entry to the end of `docs/core/Design-Decisions.md`, maintaining the established format:
   ```markdown
   ---

   ## [N]. [Decision Title]

   **Context**: [Situation where this decision applies]

   **Decision**: [The actual decision/philosophy]

   **Rationale**: [Why this decision was made]

   **Example**:
   [Code showing wrong vs right approach]

   **Applies to**: [Where this decision is relevant]
   ```

8. **Report Completion**: Inform the User of:
   - The decision number assigned
   - A brief summary of what was captured
   - Reminder to review via `git diff` before committing

## Error Handling

### Duplicate Detection
If a potential duplicate is detected, present the existing decision and ask the User to confirm before proceeding.

### Missing Context
If no `[message]` is provided and the conversation lacks clear context about a design decision, ask the User to clarify what decision should be captured.

### Write Permission Error
If unable to write to `Design-Decisions.md`, report the error clearly and suggest the User check file permissions.

## Related Commands

- `/new-rule` - Adds rules to `Agent-Rules.md` (governs agent behavior, not project design)
- `/new-doc` - Creates general documentation (for non-decision content)
- `/open-ticket` - Creates work item tickets (for actionable tasks)
