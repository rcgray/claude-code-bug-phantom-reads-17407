---
description: Initialize a new workscope session with system files, ID generation, and task assignment
argument-hint: [--custom | workscope-directive]
---

# Initialize Workscope

This command introduces a new agent to the project and prepares them to receive their "workscope" assignment (the scope of work assigned to them for the current session).

**CRITICAL**: `<WORKSCOPE‑DEV>` tags contain critical project-specific content. Do not skip or skim these sections - they contain the most important customized instructions for this specific project. **Follow the instructions and rules within them.**

## Usage

```
/wsd:init [--custom | workscope-directive]
```

Where:
- `--custom` instructs the agent to skip Task-Master assignment and return to the User for a custom workscope
- `workscope-directive` is a message forwarded to Task-Master to guide workscope selection

These options are mutually exclusive. Most common usage is simply `/wsd:init` with no arguments.

## Examples

```
/wsd:init
```

```
/wsd:init Do all of Phase 5, but not Phase 6
```

```
/wsd:init --custom
```

---

## Project Introduction

<WORKSCOPE-DEV wsd-init-project-introduction>

This is the "Phantom Reads Investigation" project: a `git` repository intended for publishing on GitHub that provides an experiment to reproduce Claude Code Issue #17407 ("Phantom Reads"). The issue can be viewed publicly at: `https://github.com/anthropics/claude-code/issues/17407`. Users can clone this repository to read more about the issue, its discovery, and to reproduce the issue on their own machines.

Please read:
- `docs/core/PRD.md`
- `docs/core/Experiment-Methodology.md`
- `docs/core/Action-Plan.md`

</WORKSCOPE-DEV>

First Directive: Print a message acknowledging that you read the content in the `wsd-init-project-introduction` section immediately above and followed all directions therein.

## Workscope System

Run the `/wsd:boot` command to read the necessary files for understanding the Workscope-Dev Platform. When it is complete, return here and finish the remaining instructions.

## Workscope ID Generation

Generate a unique Workscope ID for this session based on the current timestamp:

1. Run the `date` command to get the current timestamp
2. Report your Workscope ID, which is derived from this timestamp according to the pattern: `YYYYMMDD-HHMMSS`

**Remember this Workscope ID** as you will use it throughout your session for:
- Work Journal naming
- Workscope file naming (if fetching from Task-Master)
- All agent communications

## Work Journal

Your next preparation task is to start a new "Work Journal" for YOUR fresh session with the Workscope ID:

**CRITICAL - Work Journal in Archive Location:**

Run the Work Journal initialization script, substituting your Workscope ID in the command below. Note that `[Workscope ID]` is strictly the `YYYYMMDD-HHMMSS` identifier, with no added prefix or suffix:

(bash):
   bash scripts/init_work_journal.sh "[Workscope ID]"

This script will create a new Work Journal directly in the archive location at `dev/journal/archive/Journal-Workscope-YYYYMMDD-HHMMSS.md`. Verify that this file exists and was properly formed (with the correct filename).

This file is now YOUR "Work Journal," and you will be continually adding to it over the course of YOUR session as you proceed through your workscope. Be sure to update your Work Journal after each step so this real time monitoring can take place.

**CRITICAL**: `cat >> file << EOF` IS FORBIDDEN. It is an anti-pattern that will likely result in full rejection of your contributions. Do NOT use terminal commands (such as `cat` or `echo` with `>>`) to write to files. Use your standard tools (e.g., Read, Edit, etc.) to interact with files throughout your session. You will be reminded of this as **Rule 4.4** in the Agent Rules.

## Task-Master Assignment (Conditional)

**IF `$1` is `--custom`:**
- Run the `/wsd:onboard` command and return to this command
- Skip the rest of this section and continue to "## Completion Behavior"
- You will receive your workscope directly from the User after this command completes

**OTHERWISE (including if `$1` is empty):**
- Consult @agent-task-master to fetch your workscope assignment
- Provide the Task-Master with your Workscope ID that you generated earlier
- Workscope directive (forward to Task-Master if provided): $1

The Task-Master has complete instructions in its definition and will:
  - Create a workscope file at `dev/workscopes/archive/Workscope-YYYYMMDD-HHMMSS.md`
  - Mark the selected tasks with `[*]` in the relevant checkboxlists
  - Return the workscope file path to you

Read the workscope file. **FUNDAMENTAL PRINCIPLE**: Your workscope will assign SPECIFIC TASK NUMBERS (e.g., "3.5, 3.6, 3.7") for execution. While you should understand the entire phase as context for how your tasks fit into the larger picture, you are responsible for EXECUTING only your assigned task numbers.

MANDATORY: After reading your workscope file, literally copy the ENTIRE, VERBATIM content of the workscope document into the Work Journal. Do this before moving on to the next step. The User will read your Work Journal, and if the User does not see the exact, verbatim text of your workscope file present in the Work Journal after it was assigned to you by the Task-Master agent, your entire session will be immediately terminated.

### Phase Inventory Validation

Before accepting, check the Phase Inventory for this error: "CLEAR (all [%])" or any "CLEAR" with a qualifier. Phases with `[%]` items are NOT CLEAR.

If you detect this error: Reject the workscope. Tell Task-Master to delete the invalid workscope file and redo the assignment correctly. This is the one exception to workscope immutability—an invalid workscope must be replaced.

## Completion Behavior

Upon completing the initialization steps above, return to the User with a clear message at the END of your reply.

MANDATORY: Put the following text at the END of your reply, verbatim:
**"WORKSCOPE INITIALIZATION (/wsd:init) COMPLETE. To continue this work: propose changes, describe the workscope, or `/wsd:prepare`. To abandon completely, `/wsd:abort`."**

## Error Handling

The command should handle these error conditions:

1. **Agent communication failures**: Retry agent communications if they fail
