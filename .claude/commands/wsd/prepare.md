---
description: Collect context from Special Agents before workscope execution
---

# Prepare for Workscope Assignment

This command collects additional context to aid the User Agent with their workscope assignment.

## Usage

```
/wsd:prepare
```

## Examples

```
/wsd:prepare
```

---

## Workscope Review and Preparation

After your initialization command has completed, you should now have:
- A Workscope ID (in the format YYYYMMDD-HHMMSS) generated during `/wsd:init`
- A Work Journal in the archive location (`dev/journal/archive/Journal-Workscope-[Workscope ID].md`)
- Optionally, a workscope file (`dev/workscopes/archive/Workscope-[Workscope ID].md` created by Task-Master in `/wsd:init` if `--custom` flag was not used)

Continue immediately with the following steps to prepare your workscope. Note that in EVERY one of the following steps, you should do the following:

- If there any significant issues discovered, critical inconsistencies found, or questions that need clarification, halt and immediately escalate to the User.
- After each step, append a report of the result of that step to your Work Journal. If the step involved communicating with another agent, provide a full record of that agent's reply.

Reference your Workscope ID when communicating with other agents in the following steps.

**EXECUTION ORDER:**
Steps 2-4 may be run in parallel with each other after Step 1 is complete.

## Context Acquisition

2. (May be run in parallel with steps 3-4): Consult @agent-context-librarian and provide them with your ACTUAL Workscope ID. The Context-Librarian has complete instructions in its definition and will determine what additional context (e.g., feature-specific specification, reference documentation) you need now that you have been given your workscope. DO NOT EXECUTE YOUR WORKSCOPE YET. Simply read the files provided to you and append your report to your Work Journal before moving on to the next step. DO NOT FAIL TO READ THESE FILES IN FULL (Rule 4.2). Especially if your workscope involves a ticket, READ THE ENTIRE TICKET to avoid embarrassing omissions and errors in your work. Include this list of all files you are supposed to read in this Work Journal update.

3. (May be run in parallel with steps 2 and 4): Consult @agent-codebase-surveyor and provide them with your ACTUAL workscope ID. The Codebase-Surveyor has complete instructions in its definition and will determine what code files you need to understand in order to complete your workscope.

   **CRITICAL - SCOPE DISCIPLINE**:
   - Read the files the codebase-surveyor identifies as necessary for your specific tasks
   - It's GOOD to understand completed work (`[x]` tasks) in your phase as context for how your tasks build upon them
   - DO NOT "investigate" or "verify" completed work - it was already exhaustively verified before being marked complete
   - DO NOT repeat testing or validation of completed tasks
   - Example: If assigned 3.5-3.7, you may read 3.1-3.4 to understand context, but don't re-test or re-verify them
   - Focus your EXECUTION effort on your assigned task numbers only

   If your task requires modifying or writing code, such as a feature implementation or a bug fix, it is essential that you have a solid understanding of how your changes will affect the codebase. If you have been assigned a non-coding task, such as writing documentation for a new feature, it will still be essential for you to understand the relevant parts of the codebase in order to determine how the feature will be integrated. DO NOT EXECUTE YOUR WORKSCOPE YET. Simply read the files and append your report to your Work Journal before moving on to the next step.

4. (May be run in parallel with steps 2-3): Speak to @agent-project-bootstrapper and provide them with a description of your workscope along with your ACTUAL Workscope ID. The Project-Bootstrapper has complete instructions in its definition and will provide the necessary on-boarding that you need to prevent you from making mistakes that would ultimately disqualify your work. DO NOT EXECUTE YOUR WORKSCOPE YET. Simply read the files provided to you and append your report to your Work Journal before moving on to the next step. DO NOT FAIL TO READ THESE FILES IN FULL (Rule 4.2). Include this list of all files you are supposed to read in this Work Journal update.

Wait until all above steps are complete. Do not proceed if there are conversations still pending. If any of the above attempts to contact a Special Agent failed, then retry them until they succeed.

## Situational Awareness Synthesis

After gathering context, write a brief **"Situational Awareness"** section in your Work Journal answering:

1. **End goal**: What is the ticket/feature trying to accomplish overall?
2. **Phase structure**: What does each phase do? Which phase am I executing?
3. **Deferred work**: What is explicitly scheduled for later phases?
4. **Expected test state (IFF Assessment)**: Should tests currently PASS, or are there In-Flight Failures (IFFs) expected from earlier phases? If IFFs are expected:
   - Which phases caused the test breakage?
   - Which phase will resolve them?
   - Which test files/patterns are likely affected?

This synthesis ensures you understand not just *what* you're doing, but *how it fits into the larger arc*. The IFF assessment is critical for the QA phase—you will provide this context to the Test-Guardian to distinguish failures you introduced (which you must fix) from IFFs (which are scheduled for later resolution). See Rule 3.20 in Agent-Rules.md for IFF terminology.

## User Approval

After reviewing your new materials, return to the User with a clear message at the END of your reply:

MANDATORY: Put the following text at the END of your reply, verbatim:
**"WORKSCOPE PREPARATION (/wsd:prepare) COMPLETE. To continue this work, run `/wsd:execute`. To abandon, run `/wsd:abort`."**

## Error Handling

The command should handle these error conditions:

1. **Agent communication failures**: Retry agent communications if they fail
