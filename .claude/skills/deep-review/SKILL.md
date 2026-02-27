---
name: deep-review
description: Orchestrates multi-agent review of large, intersectional specification documents. Use when a specification exceeds single-agent review capacity due to size or intersectional complexity.
argument-hint: [target-doc-path] [optional directive]
disable-model-invocation: true
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
---

# Deep Review

Orchestrate a multi-agent review of a specification document by decomposing it into focused review tasks, dispatching specialized agents to review each task, synthesizing findings into categorized edit recommendations, and applying changes in partnership with the User.

This skill is reserved for large, heavily intersectional specifications where single-agent review produces diminishing returns. Typical indicators: the document exceeds approximately 400 lines, intersects with five or more external documents, or has been through multiple review cycles without convergence.

## Invocation

```
/deep-review [target-doc-path] [optional directive]
```

The target document path is required. The optional directive focuses the review on a specific concern without eliminating other review tasks.

Examples:
```
/deep-review docs/features/setup-command/Setup-Command-Overview.md
/deep-review docs/features/setup-command/Setup-Command-Overview.md Focus on TypeScript configuration consistency
```

The target document is not restricted to Work Plan Documents. Any specification or documentation file can be reviewed.

## Context Budget Management

Throughout this workflow, preserve your context for meaningful conversation with the User:

- **Information barrier.** Deep-Reviewers write findings exclusively to disk and return only brief completion confirmations via the Task tool. You never see findings content. The Review-Synthesizer reads findings from disk and compresses them into the synthesis report, which is the ONLY findings-derived artifact you read.
- **Read only the review plan and synthesis report.** Do not read any files in the `findings/` directory. On-demand reads are permitted ONLY if the User explicitly requests to examine a particular reviewer's findings during Step 10 discussion.
- **The workspace directory is shared memory.** Agents communicate through files written to disk, not through your context.

### Token Estimation

File size in bytes multiplied by 0.277 provides an approximate raw token count. Claude Code adds approximately 40% overhead when reading files, so effective tokens consumed equals file_bytes multiplied by 0.277 multiplied by 1.4.

### Budget Allocation

Each agent operates within an approximate 200k total token context. The allocations below describe target budgets, not hard limits. Note that parallel Deep-Reviewer execution does not increase total token consumption—each reviewer operates in its own independent context.

**Your budget (User Agent):**

| Item | Estimated Tokens |
|------|-----------------|
| Skill instructions | ~5-10k |
| Target document | ~15-25k |
| Review plan | ~5-10k |
| Synthesis report | ~15-25k |
| Conversation with User | ~40-60k |
| On-demand findings reads | ~0-20k |
| Overhead and buffer | ~20-30k |

**Deep-Reviewer budget:**

| Item | Estimated Tokens |
|------|-----------------|
| Agent definition and task definition | ~5-10k |
| Input corpus (target sections plus external docs) | ~100k target max |
| Reasoning and output | ~40-60k |
| Overhead and buffer | ~30-40k |

**Review-Synthesizer budget:**

| Item | Estimated Tokens |
|------|-----------------|
| Agent definition and instructions | ~5-10k |
| All findings files | ~15-25k |
| Target document | ~15-25k |
| Reasoning and output | ~40-60k |
| Overhead and buffer | ~30-40k |

The Review-Planner estimates corpus size per review task and flags any task that would exceed the approximately 100k token input target for Deep-Reviewers.

## Workflow

Execute the following 11 steps. Do not skip steps or reorder them. Most steps are sequential, but Step 6 (Deep-Reviewer invocations) executes in parallel to minimize wall-clock time.

### Step 1: Invocation

Parse the arguments provided with `/deep-review`:
- **First argument**: The target document path (required).
- **Remaining arguments**: The optional directive (concatenate all remaining arguments as a single directive string).

**Error handling:** If no target document path is provided, report to the User:
```
Error: No target document path provided.
Usage: /deep-review [target-doc-path] [optional directive]
```
Halt. Do not proceed.

Verify the target document exists by reading it (or attempting to). If the file does not exist:
```
Error: Target document not found at '[path]'.
Verify the file path and try again.
```
Halt. Do not proceed.

### Step 2: Workspace Setup

Generate a timestamp in `YYYYMMDD-HHMMSS` format using the system `date` command. Create the workspace directory and findings subdirectory:

```
dev/diagnostics/deep-review-[YYYYMMDD-HHMMSS]/
└── findings/
```

The `dev/diagnostics/` location follows the Documentation System's guidelines for throwaway development artifacts. The timestamp ensures each run gets a fresh workspace, preventing artifacts from previous runs from polluting current analysis.

**Error handling:** If the directory cannot be created, report:
```
Error: Cannot create workspace directory 'dev/diagnostics/deep-review-[timestamp]/'.
Check directory permissions and available disk space.
```
Halt. Do not proceed.

### Step 3: Target Document Read

Read the full target document. This is required for two reasons: the Edit tool requires that you have read a file before editing it, and you need familiarity with the document for informed discussion with the User about proposed changes.

**Error handling:** If the target document cannot be read, report which step failed and halt. The workspace artifacts created so far are preserved.

### Step 4: Review-Planner Invocation

Invoke the Review-Planner agent via the Task tool:

- **Agent**: `review-planner` (use `subagent_type` or reference `.claude/agents/review-planner.md`)
- **Provide**: The target document path, the optional directive (if any), and the workspace path.
- **Instruct the agent** to write its output to `[workspace-path]/review-plan.md`.

The Review-Planner will read the target document, identify thematic concerns, extract cross-references, create review tasks with file assignments, and estimate corpus size per task. It writes the review plan to the workspace.

**Error handling:** If the Task tool invocation fails or `review-plan.md` is not created in the workspace after the agent completes, report:
```
Error: Review-Planner failed to produce review-plan.md.
Step 4 of 11 failed. Workspace artifacts are preserved at: [workspace-path]
```
Halt. Do not proceed.

### Step 5: User Checkpoint — Plan Review

Read `[workspace-path]/review-plan.md` and present it to the User. Show:
- The identified review tasks with their scope descriptions
- File assignments per task
- Corpus size estimates and any budget warnings

Ask the User to approve the plan. The User may:
- Approve the plan as-is
- Adjust concerns (add, remove, or modify review tasks)
- Modify file lists for specific tasks
- Request task splits for tasks exceeding the token budget

**Contract:** Deep-Reviewer invocations in Step 6 MUST NOT begin until the User explicitly approves the review plan. Wait for the User's response before continuing.

**Error handling:** If the review plan cannot be read, report which step failed and halt.

### Step 6: Deep-Reviewer Invocations

Invoke ALL Deep-Reviewer agents in parallel via the Task tool using a single message with multiple tool uses. For each approved review task in the plan:

- **Agent**: `deep-reviewer` (use `subagent_type` or reference `.claude/agents/deep-reviewer.md`)
- **Provide**: The workspace path and the review task definition from the plan (scope description, target document sections, external file paths, and key questions). Do NOT include output file paths — the Deep-Reviewer derives its own output path from the workspace path and task name.

**Execute all review tasks in parallel** by making multiple Task tool invocations in a single message. This dramatically reduces wall-clock time (potentially 5-10x faster for reviews with 5-10 tasks) with zero architectural risk. Deep-Reviewers are independent (separate scopes), isolated (write to separate output files), and stateless (no inter-dependencies).

Report status to the User when invocations begin:
```
All [M] review tasks started in parallel.
```

And when all complete:
```
All [M] review tasks completed.
```

**CRITICAL — Information Barrier:**

Deep-Reviewers write findings ONLY to disk. Their Task tool responses contain ONLY a brief completion confirmation (e.g., "Review of [task-name] complete. Findings written to disk."). There is no findings content to read or process in the Task results. Simply confirm all tasks completed and move to Step 7.

Do NOT read any files in the `findings/` directory. Do NOT attempt to verify findings file contents or existence. Findings flow from Deep-Reviewers to the Review-Synthesizer via disk — they never pass through your context. The Review-Synthesizer will discover and read all findings files in Step 7.

On-demand reads of specific findings files are permitted ONLY if the User explicitly requests to examine a particular reviewer's findings during Step 10 discussion.

**Error handling:** If a Deep-Reviewer Task invocation itself fails (the Task tool returns an error), report:
```
Error: Deep-Reviewer failed on task '[task-name]'.
Step 6 of 11 failed. Completed [N] of [M] review tasks before failure.
Workspace artifacts from completed steps are preserved at: [workspace-path]
```
Halt. Do not proceed.

### Step 7: Review-Synthesizer Invocation

Invoke the Review-Synthesizer agent via the Task tool:

- **Agent**: `review-synthesizer` (use `subagent_type` or reference `.claude/agents/review-synthesizer.md`)
- **Provide**: The workspace path (containing all findings files in the `findings/` subdirectory) and the target document path.
- **Instruct the agent** to write its output to `[workspace-path]/synthesis.md`.

The Review-Synthesizer will read all findings files and the target document, categorize issues as auto-fix or judgment-call, and produce specific edit recommendations.

**Error handling:** If the Task tool invocation fails or `synthesis.md` is not created in the workspace, report:
```
Error: Review-Synthesizer failed to produce synthesis.md.
Step 7 of 11 failed. All findings files are preserved at: [workspace-path]/findings/
```
Halt. Do not proceed.

### Step 8: Synthesis Report Read

Read `[workspace-path]/synthesis.md`. This is the compressed output of the entire review — categorized issues with specific edit pairs ready for application.

**Error handling:** If the synthesis report cannot be read, report which step failed and halt. Workspace artifacts are preserved.

### Step 9: Auto-Fix Application

Apply all auto-fix (AF) edits from the synthesis report to the target document using the Edit tool. Work through them sequentially.

For each auto-fix edit:
1. Use the `old_text` and `new_text` from the synthesis report
2. Apply via the Edit tool
3. If the edit fails (old_text not found), log the failure and continue with remaining edits:
   ```
   Warning: Auto-fix edit failed to apply - old_text not found in target document.
   Issue: [AF identifier and description]
   Skipping this edit. Manual application may be needed.
   ```

After applying all auto-fixes, report to the User with a summary of each change made and any edits that failed to apply.

**Error recovery guarantee:** A failed `/deep-review` invocation MUST NOT leave the target document in a partially edited state without the User's knowledge. If the review fails before Step 9, the target document is untouched. If the review fails during Steps 9 or 10, edits that were successfully applied remain (they are individually valid), and you report exactly which edits were applied and which were not.

### Step 10: Judgment-Call Discussion

Present judgment-call (JC) items from the synthesis report to the User as a numbered list. For each item, provide:
- The line number and location (from the synthesis report)
- The description and context
- The impact (why this decision matters)
- The question being asked
- The available options with rationale for each
- **YOUR RECOMMENDATION**: After considering the options, state which option you recommend and why. Use your knowledge of the target document, the project context, and the synthesis report's impact explanation to make an informed recommendation. Present this as: "I recommend Option X because [rationale], but let me know your preference."

**CRITICAL — User Has No Prior Context:**
The User has NOT been following the review process. They have not seen the Deep-Reviewer findings or watched the synthesis process. Your presentation is their FIRST exposure to these issues. Include ALL necessary context:
- Concrete examples from the target document (quote the actual text being discussed)
- Line numbers for easy location in large specifications
- Clear explanation of what's at stake (use the Impact field from the synthesis)
- Enough context to understand the issue without reading the full findings

Do NOT assume the User knows what you're talking about. Do NOT use shorthand or abbreviations. Do NOT reference earlier conversations or findings the User hasn't seen.

**CRITICAL — Understanding the Nature of JC Changes:**

Judgment-call resolutions are NOT typo fixes. They are design decisions with systematic, spec-wide implications. Auto-fixes handle the typos. JCs represent consequential choices about:
- Naming conventions that must be consistent throughout
- Constraints that apply to multiple sections
- Architectural patterns that recur across the specification
- Cross-references that propagate through the document
- Design philosophies that affect multiple decisions

**When you apply a JC resolution, you are (often) performing a REFACTOR of the specification, not applying a patch.**

The edit pair in the synthesis report is an EXAMPLE of where the issue was discovered—it is NOT the complete fix. Your job is to think systematically about the implications of the User's decision and apply it consistently throughout the entire specification.

**Systematic Application Protocol:**

For EVERY JC resolution, before applying any edits:

1. **Analyze the decision's scope**: Does this affect naming? Constraints? Patterns? Cross-references? Think about what this decision means for the entire spec.

2. **Search the entire specification**: Use Grep to find ALL instances that need updating. Don't just apply the example edit pair—find every place the change applies.

3. **Apply consistently**: Make the change everywhere it belongs, maintaining spec-wide consistency.

4. **Verify completeness**: After applying, search again to ensure:
   - No instances of the old pattern remain (unless intentionally excluded)
   - No new inconsistencies were introduced
   - The spec is internally consistent with the decision

5. **Report comprehensively**: Tell the User what you changed:
   ```
   Applied JC-1 (Option A: Rename "cache_size" to "cache_limit"):
   - Line 145: Configuration section example
   - Line 289: Default values table
   - Line 412: Error handling section
   - Line 523: Cross-reference to config
   Total: 4 instances updated across specification
   Verification: No remaining instances of "cache_size" found
   ```

**DO NOT:**
- Apply only the example edit pair and call it done
- Assume the synthesis report found all instances
- Leave the spec in an inconsistent state where the decision is half-implemented

**Iterative Resolution Protocol:**

The User's responses will vary in clarity. Some will be straightforward decisions; others will require clarification or additional discussion. Handle this iteratively:

1. **Parse User responses**: Categorize each response as either:
   - **Actionable**: Clear decision that you understand and can implement immediately
   - **Needs clarification**: Counter-argument, follow-up question, or ambiguous response requiring discussion

2. **Implement actionable decisions using the Systematic Application Protocol above**: This is not a quick edit—it's a thoughtful refactor that requires searching, applying, and verifying.

3. **Maintain two lists**:
   - **Resolved**: JCs that have been fully implemented (spec-wide, verified) and can be cleared
   - **Pending**: JCs still requiring discussion

4. **Report progress after each round**:
   ```
   ## Resolved and Implemented:
   - JC-1: [brief description] - Applied [selected option]
     Applied across [N] locations: [list]
   - JC-3: [brief description] - Applied [selected option]
     Applied across [N] locations: [list]

   ## Still Pending:
   - JC-2: [your response to User's counter-argument or follow-up question]
   - JC-5: [your clarifying question based on User's ambiguous response]
   ```

5. **Continue iteratively**: After reporting, wait for the User's next round of responses. Repeat steps 1-4 until all JCs are resolved.

6. **Handle edit failures**: If an edit fails to apply, report the failure and offer to apply it manually with adjusted text. This does not block resolution of other JCs.

This conversational pattern allows the User to provide varying levels of detail in their responses without forcing them to clarify everything upfront. You act on what's clear and discuss what needs refinement—but you act SYSTEMATICALLY, treating each decision as a spec-wide refactor.

### Step 11: Completion

Report a summary of all changes made to the target document:
- Auto-fixes applied (count and brief descriptions)
- Judgment-call edits applied (count and which options were selected)
- Any edits that failed to apply

The User can review all changes via `git diff`. If further refinement is needed, the User can invoke `/deep-review` again — subsequent runs should produce fewer findings as issues converge toward resolution.

## Issue Categorization Reference

When reviewing the synthesis report, use these criteria to verify the categorization is appropriate.

### Auto-Fix Criteria

An issue qualifies as auto-fix when the correct resolution is unambiguous and does not involve a design decision:

- **Formatting inconsistencies**: Inconsistent heading levels, numbering errors, or markdown formatting within the target document
- **Clearly broken cross-references**: References to sections or documents that do not exist or use incorrect names
- **Missing items with unambiguous correct values**: Fields, attributes, or entries that are clearly required based on established patterns in the document and have only one correct value
- **Inconsistencies where one source is explicitly authoritative**: When the target document contradicts an authoritative external source (such as a read-only standard or a specification that owns the concept), the authoritative source wins
- **Undeclared dependencies**: When the target specification depends on a document it does not cross-reference, adding the cross-reference is an auto-fix

### Judgment-Call Criteria

An issue qualifies as judgment-call when it requires a design decision or when multiple valid resolutions exist:

- **Contradictions where both versions could be correct**: When two documents disagree and neither is definitively authoritative over the other for the concept in question
- **Missing specifications requiring design decisions**: Gaps in the specification that cannot be filled without making a choice about system behavior
- **Ambiguous requirements with multiple valid interpretations**: Requirements language that could reasonably be read in more than one way
- **Scope questions**: Whether a concept belongs in this specification versus another
- **Architectural philosophy**: Anything touching design decisions or establishing new patterns

The categorization is binary — every issue MUST be classified as either auto-fix or judgment-call. There are no intermediate categories. If there is any doubt, the issue is a judgment-call.
