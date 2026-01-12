---
description: Execute the assigned workscope with quality assurance checks
argument-hint: [adjustment-note]
---

# Execute Assigned Workscope

This command is issued after an agent has received their workscope, the User has reviewed their Work Journal and provided any necessary corrections or clarifications, and the work is ready to be performed.

## Usage

```
/wsd:execute [adjustment-note]
```

Where:
- `[adjustment-note]` is an optional message from the User that should be taken into context while executing the workscope. It may contain adjustments, clarifications, or important points to consider in the implementation and quality assurance checks.

## Examples

```
/wsd:execute
```

```
/wsd:execute Change the filename from your current plan to `docs/core/new_file.md` instead. Remember that the test for 14.3 needs to be a manual test performed by a human developer.
```

```
/wsd:execute To answer your numbered questions: (1) Yes, please update the spec. (2) Go with Option B that you proposed.
```

---

## Acknowledge User Adjustment Notes

If the User provided an adjustment note with this command, it appears below:

$ARGUMENTS

Respond to any adjustment note above if one was provided. Bear the contents of this note in mind as ESSENTIAL CONTEXT while you complete the following steps. If you have any questions or there is any part of your workscope that requires clarification, ensure that you ask these questions now before executing your workscope.

It is time to execute your workscope. Note that in EVERY one of the following steps, you should do the following:

- If there any significant issues discovered, critical inconsistencies found, or questions that need clarification, halt and immediately escalate to the User.
- After each step, append a report of the result of that step to your Work Journal. If the step involved communicating with another agent, provide a full record of that agent's reply.

**CRITICAL EXECUTION ORDER:**
- Step 5 (Execute Workscope) MUST complete BEFORE steps 6-9 can begin
- Steps 6-9 (Quality Assurance) may THEN be run in parallel with each other
- Steps 10-11 (Completion) can run in parallel ONLY AFTER steps 6-9 ALL pass
- DO NOT skip ahead or combine phases

## Execution Phase

5. **[BLOCKING - Must Run ALONE First]**: Execute your workscope as assigned to you until it is complete. Now is the point where you may actually execute the tasks you have been preparing for. If there are any significant difficulties, sub-tasks that cannot be completed, inconsistencies in the project requirements, or other blockers, halt and immediately escalate to the User. Otherwise, append your report to your Work Journal before moving on to the next step.

**WAIT FOR COMPLETION**: Do not proceed until your workscope execution is complete; all future steps depend on having completed work to review.

**STOP HERE**: Only AFTER completing Step 5 can you continue.

## Quality Assurance Exception Assessment

Occasionally, there are workscopes that perform an audit, an investigation, or an experiment. If it is the case that your Execution Phase (Step 5) changed NO CODE OR DOCUMENTATION (outside of the workbench), you may be eligible to skip the "Quality Assurance Phase" (Steps 6-9) below:

- If you **do not qualify** (i.e., your work made a change to the code or documentation of the project), continue on to "Quality Assurance Phase" to run steps 6-9 in parallel.

- If you **believe your workscope qualifies for exception**, you must request User approval:
  1. Present your reasoning for why the exception applies
  2. **HALT** - End your message with ONLY the following prompt:

     `"QA EXCEPTION REQUEST: This workscope made no code or documentation changes. Reply 'yes' to skip Steps 6-9, or 'no' to require QA review."`

  3. **DO NOT PROCEED** - Wait for User response before continuing
  4. Follow User's decision: 'yes' skips to "Execution Complete", 'no' proceeds to QA Phase

**CRITICAL**: An exception means SKIP. Do not run QA agents "for thoroughness" or "to be safe" when you qualify for an exception—that wastes resources. If you qualify, request the exception and wait.

## Quality Assurance Phase

**⚠️ CRITICAL - AGENT UNAVAILABILITY PROTOCOL:**
  If ANY QA agent returns "not found" or fails to respond:
  1. **RETRY ONCE** - Agent invocations can be flaky
  2. **IF RETRY FAILS** - **HALT IMMEDIATELY** and escalate to User
  3. **FORBIDDEN**: Running tests, health checks, or any QA validation yourself as a "substitute" for the agent. This is a **CRITICAL VIOLATION** that defeats the purpose of the QA system.

**Apply your Situational Awareness**: Special Agents assess the codebase objectively—they don't know your ticket's phase structure. Use the context you synthesized during `/wsd:prepare` to distinguish issues you introduced from pre-existing conditions already planned for resolution.

<WORKSCOPE-DEV wsd-execute-workflow>

6. **[Requires Completed Workscope from Step 5]** (May be run in parallel with steps 7-9): Consult @agent-documentation-steward to review your COMPLETED work against specifications. Provide your Workscope ID and a summary of what was completed. The Documentation-Steward has complete instructions in its definition and will perform specification compliance review. Continue to work with the Documentation-Steward until they are satisfied. If a significant documentation discrepancy is discovered, halt and immediately escalate to the User. Otherwise, append the Documentation-Steward's full report to your Work Journal before moving on to the next step.

7. **[Requires Completed Workscope from Step 5]** (May be run in parallel with steps 6, 8-9): Consult @agent-rule-enforcer to review your COMPLETED work for rule compliance. Provide your Workscope ID and a summary of what was completed. The Rule-Enforcer has complete instructions in its definition and will perform rules and standards compliance review. Continue to work with the Rule-Enforcer until they are satisfied. If a significant rule violation is discovered, or _especially_ if the Rule-Enforcer is demanding changes outside of your workscope, halt and immediately escalate to the User. Otherwise, append the Rule-Enforcer's full report to your Work Journal before moving on to the next step.

</WORKSCOPE-DEV>

**DO NOT RUN QA YOURSELF**: If an agent is found to be unavailable, try them again (this has been happening lately with our AI harness) and escalate to the User if the second attempt fails.

**WAIT FOR ALL QUALITY CHECKS**: Do not proceed until ALL of steps 6-9 have passed. Every quality assurance agent must approve your work.

**CONFIRM PROOF OF WORK**: Special Agents may also have **Proof of Work** that they provide you (e.g., the Health-Inspector's Summary Report, the Test-Guardian's Test Results Report). Do not accept approval if the Special Agent failed to provide you with their appropriate Proof of Work.

## Execution Complete

Once all quality assurance checks (steps 6-9) have passed, your workscope execution is complete.

**QA Discovery Checkpoint (Rule 3.16)**: Did ANY Special Agent mention ANY issue—even "non-blocking," even unrelated to your workscope, even if they approved? Report it in USER ACTION ITEMS. The User cannot see these conversations. You must fix issues you caused; you must *report* everything.

**Review for User Actions**: Explicitly review your work and identify any actions that may require User intervention:
- Any files you created in `docs/workbench/` - do they need promotion to permanent locations (e.g., `docs/references/`, `docs/read-only/standards/`)?
- Any standards, references, or guidelines created - where should they permanently reside?
- Any configuration changes suggested but not implemented
- Any system settings that need User adjustment
- Any decisions that require User authority to finalize
- ANY issue that was raised by the QA Special Agents, even if they were resolved, if they are unrelated to your workscope, or if they appear trivial (warning, non-blocking). Be specific and provide details (file number, section names, line numbers, test names, etc.) - pretend the User is unaware of the concern and don't make them have to search through files to figure out what you're discussing.
- **IFF Section Updates**: If you discovered any **IFF (NEW)** failures during Step 8 (test failures that are in-flight but not yet documented in the ticket's IFF section), recommend that User add them to maintain an accurate record for future workscopes.

NOT User Action Items:
- Updating checkboxes in tickets (normal project work)
- Deciding whether to close tickets (normal project work)
- The state of the git repository or suggestions to commit the changed files (normal project work)
- Required changes that are already fully covered by future work items or phases (no User action required, because it is already in the plan).
- Run more workscopes to continue the project's development after this workscope (normal project work)

ARE User Action Items:
- "I created docs/workbench/new-coding-standard.md - should it be promoted to docs/read-only/standards/?"
- "I drafted a configuration file at config.example.toml but need you to set the API key value"
- "I found three different approaches (A, B, C) and need your decision on which to pursue"
- "I discovered 2 IFF (NEW) failures not in the ticket's IFF section: `test_install_error.py`, `test_update_rollback.py`. Recommend adding these to the IFF section."

Create a clear **"USER ACTION ITEMS"** section listing each item that needs User attention, with specific recommendations for each. These should be SPECIFIC, not lazy directions like "review the documentation in `docs/workbench/`.

Write the User Action Items to your Work Journal. This is key for creating a permanent record for later review. If no actions are identified at this stage, explicitly state **"NO IMMEDIATE USER ACTIONS IDENTIFIED"**.

**Important:** Writing your Work Journal at the conclusion of this command is your most frequent point of violations of Rules 4.4 and 4.5. You've done so well so far using your proper tools to edit files, remember that `cat >> file << EOF` is FORBIDDEN, even as you are nearing the end and excited because because you can see the finish line.

After reviewing your work, return to the User with a clear message at the END of your reply:

Display your "USER ACTION ITEMS" list (if any) prominently. The User will then decide whether to accept or reject the completed work.

MANDATORY: Put the following text at the END of your reply, verbatim:
**"WORKSCOPE EXECUTION (/wsd:execute) COMPLETE. All quality checks have passed. To accept this work, run `/wsd:close`. To abandon completely, run `/wsd:abort`."**

## Error Handling

The command should handle these error conditions:

1. **Agent communication failures**: Retry agent communications if they fail
