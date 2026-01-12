---
description: Open Ticket
argument-hint: [regarding]
---

# Open Ticket

This command creates a new actionable work item ticket in the `docs/tickets/open` directory.

## Usage

```
/open-ticket [regarding]
```

Where:
- `[regarding]` is an optional description of the work item. If omitted, the agent uses recent conversation context.

If the User provided context about this ticket, it appears below:

$ARGUMENTS

## Examples

```
/open-ticket regarding this security issue we just discovered
```

```
/open-ticket for implementing the --verbose flag in the CLI
```

```
/open-ticket to investigate why the cache validation is failing intermittently
```

## Description

**Purpose**: Tickets are specifically for work items that require action. Unlike `/new-doc` which can record decisions or research, tickets always represent tasks that need to be completed.

### Ticket Types
- **Bug Fixes** - Issues that need to be resolved
- **Feature Implementations** - New functionality to be added
- **Code Refactoring** - Improvements to existing code structure
- **Documentation Fixes** - Corrections or updates to documentation
- **Investigations** - Issues requiring analysis before determining the fix

### Key Differences from `/new-doc`
1. **Fixed Location**: Always created in `docs/tickets/open/` (no exceptions)
2. **Always Actionable**: Must have an implementation checkboxlist
3. **Structured Format**: Follows the ticket template strictly
4. **Work-Focused**: Not for recording decisions or research findings

This command will:

1. Analyze the recent conversation to understand the work item described in `<regarding>`
2. Create a descriptive kebab-case filename (5-7 words) like `fix-cache-validation-errors`
3. Generate a comprehensive ticket document following the template structure
4. Include a detailed implementation checkboxlist at the END of the document

## Ticket Structure (from Template)

Based on `docs/references/templates/Ticket-Template.md`, tickets should include:

1. **Title**: Clear description of the work item
2. **Date Reported**: When the ticket was created
3. **Problem Description**: Detailed explanation of the issue or requirement
4. **Suspected Cause** (if applicable): Root cause analysis for bugs
5. **Investigation & Analysis**: Research findings and current state
6. **Proposed Solution**: Approach to addressing the work item
7. **Expected Benefits**: What will be improved
8. **Risk Assessment**: Potential issues and mitigation
9. **Related Files**: Code and documentation references
10. **Developer Notes**: Additional context
11. **Action Plan**: Implementation checkboxlist (ALWAYS at the END and WITHOUT a Phase 0)
    - Starts with Phase 1 (there is never a Phase 0 in a new checkboxlist)
    - Testing Requirements
    - Documentation Updates
12. **Status**: Always "Open" for new tickets

## Critical Reminders Before Creating Ticket

⚠️ **PHASE 0 TRAP**: You WILL be tempted to create a "Phase 0" for fundamental work. DON'T. Phase 0 is ONLY for emergencies discovered during execution. Your ticket MUST start with Phase 1, no exceptions

## Implementation

The command should:

1. Parse the `<regarding>` argument to identify the work item type (bug, feature, refactor, etc.)

2. Create a new document in `docs/tickets/open/` directory (ALWAYS this location)
   - Generate kebab-case filename (5-7 words)
   - Example: `fix-authentication-cache-validation-errors.md`

3. Use the ticket template structure to create comprehensive documentation:
   - Include all relevant sections from the template
   - Add detailed problem description and analysis
   - Propose concrete solution approach
   - Reference related code files and documentation

4. Create a detailed implementation checkboxlist:
   - Follow the Checkboxlist System (`docs/read-only/Checkboxlist-System.md`)
   - Place at the END of the document under "Action Plan"
   - Include hierarchical numbered structure
   - Add testing requirements and documentation updates
   - Ensure all tasks are actionable and trackable

5. Set ticket status to "Open" and save the file

## Evaluation

After the ticket is written, evaluate it per the rules in the template:

- [ ] The Action Plan should be the final section of the document. No other content should come after the checkboxlist of the Action Plan
- [ ] There should exist NO Phase 0. Phase 0 is reserved for issues that _emerge_ during FIP execution; it is not appropriate in the planning stage.
- [ ] There should exist no task that directs an agent to violate a Rule in Agent-Rules.md. For example, there should be no command directing the agent to use a _write_ git command (and thus would force them to violate Rule 2.2).

Note: This command is very similar to `/new-docs`. However, unlike `/new-doc`, this command has no flexibility in location or structure. All tickets follow the same format and location to ensure consistent tracking and eventual closure when work is completed. Additionally, `/new-ticket` ALWAYS creates the new file in `docs/tickets/open/`.
