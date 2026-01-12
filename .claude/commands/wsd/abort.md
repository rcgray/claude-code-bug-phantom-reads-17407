---
description: Cancel workscope and restore checkboxlists to previous state
argument-hint: [closing-note]
---

# Abort and Close Assigned Workscope

This command is issued after an agent has received their workscope, but the User has decided to cancel the workscope. This command handles the cleanup and restoration of the system.

## Usage

```
/wsd:abort [closing-note]
```

Where:
- `[closing-note]` is an optional message from the User that should be taken into context while aborting and closing the workscope. It may contain adjustments, clarifications, or important points to consider or mention in your Work Journal before you archive it.

## Examples

```
/wsd:abort
```

```
/wsd:abort You were improperly assigned this workscope and we need to make adjustments to the Task-Master agent.
```

```
/wsd:abort We have to abandon this workset due to the issue we just found and filed that ticket for. Since the issue is blocking, we have to abort the current workscope and fix that first in a new Session before we return to this feature work.
```

```
/wsd:abort Even though you were assigned 17.3 - 17.6 for this workscope, we found that 17.4 was much more complicated than we thought, and the User Agent ran out of context in the current session, preventing us from continuing.
```

---

If the User provided a closing note with this command, it appears below:

$ARGUMENTS

Respond to any closing note above if one was provided. Bear the contents of this note in mind as you complete the following steps. If questions or necessary clarifications emerge from your processing of the closing note, HALT and ask for clarification before continuing.

## Update Work Journal

Append to your Work Journal:

```
## SESSION ABORTED
Reason: [Include the closing-note if provided]
Timestamp: [Current date/time]
```

## Update Checkboxlists

Consult @agent-task-master to report the fact that the workscope is being abandoned. The Task-Master has complete instructions in its definition and will perform the following actions:
- Revert any `[*]` items back to their previous states
- Note that the workscope was aborted
- Update any parent task states as needed

Provide the workscope ID so the Task Master can update the correct checkboxlist items.

## Final Message

Return to the User with a message confirming:

Include:
- Confirmation that the workscope has been aborted
- Confirmation of checkboxlist reversion
- Note that the Work Journal has been archived with ABORTED status

MANDATORY: Put the following text at the END of your reply, verbatim:
**"WORKSCOPE ABORTED (/wsd:abort) SUCCESSFULLY. Checkboxlists restored."**

## Error Handling

The command should handle these error conditions:

1. **Agent communication failures**: Retry agent communications if they fail
