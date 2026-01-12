---
description: Accept completed workscope, archive documents, and update checkboxlists
argument-hint: [closing-note]
---

# Close and Accept Workscope

This command accepts the completed work from a workscope execution and handles all completion activities including archival suggestions and checkboxlist updates.

## Usage

```
/wsd:close [closing-note]
```

Where:
- `[closing-note]` is an optional message from the User that should be taken into context while closing the workscope. It may contain adjustments, clarifications, or a reply to a question.

## Examples

```
/wsd:close
```

```
/wsd:close I've made the appropriate adjustments to the checkboxlist, go ahead and proceed normally
```

---

This command is issued after `/wsd:execute` completes successfully and all quality checks have passed. The User has reviewed the work and decided to accept it.

**Prerequisites:**
- Workscope execution must be complete (after `/wsd:execute`)
- All quality assurance checks must have passed

If the User provided a closing note with this command, it appears below:

$ARGUMENTS

Acknowledge any closing note above if one was provided. If questions or necessary clarifications emerge from your processing of the closing note, HALT and ask for clarification before continuing.

## Workscope Acceptance

You are about to accept and finalize the completed workscope. This will:
1. Handle any archival suggestions
2. Update checkboxlists to mark tasks as complete

## Archival Suggestions

Consult @agent-context-librarian to review the completed work for archival opportunities. Provide:
- Your Workscope ID
- Summary of work completed
- List of workbench files that were used

The Context-Librarian has complete instructions in its definition and will:
- Review workbench documents for potential archival
- Suggest which documents are no longer needed
- Perform any necessary archival operations

**CRITICAL CHECKS**:
- If the Context-Librarian archives the plan/spec you were just working from and work remains in it, restore it immediately
- If the Context-Librarian attempts to archive a file NOT in `docs/workbench/`, REJECT and RESTORE immediately
- Document any restorations in your Work Journal

Append the Context-Librarian's response and any actions taken to your Work Journal.

## Update Checkboxlists

Consult @agent-task-master to finalize the workscope completion. Provide:
- Your Workscope ID
- Workscope completion status (which items were completed, skipped, etc.)

The Task-Master has complete instructions in its definition and will:
- Update the checkboxlist items from `[*]` to their final states (e.g., `[x]` for completed tasks)
- Process any parent-child state propagation
- Move any completed tickets from `open/` to `closed/` if applicable

## User Action Items Review

Before completing, review any USER ACTION ITEMS that were identified during execution:
- Files in `docs/workbench/` that may need promotion to permanent locations
- Standards or guidelines that need permanent homes
- Configuration changes that need User approval
- System settings requiring adjustment
- Decisions needing User authority

If there are outstanding USER ACTION ITEMS, remind the User of these in your final message.

## Completion Message

Return to the User with a message confirming the completion of the command:

Include:
- Summary of archival actions from Context-Librarian
- Confirmation of successful merge
- Summary of checkboxlist updates from Task-Master
- Reminder of any outstanding USER ACTION ITEMS (if applicable)

MANDATORY: Put the following text at the END of your reply, verbatim:
**"WORKSCOPE CLOSED (/wsd:close) SUCCESSFULLY. Archiving complete and checkboxlists updated."**

## Error Handling

The command should handle these error conditions:

1. **Agent communication failures**: Retry agent communications if they fail
2. **Archival issues**: Document and escalate any problematic archival attempts
