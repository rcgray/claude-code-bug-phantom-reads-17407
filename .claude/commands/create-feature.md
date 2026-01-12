---
description: Create Feature Specification
argument-hint: [feature-name]
---

# Create Feature Specification

This command formalizes a feature design conversation into a Feature Overview specification. It is invoked after you and the User have had a discovery conversation exploring the feature idea, clarifying requirements, and making design decisions.

**Feature Name:** $ARGUMENTS

## Usage

```
/create-feature [feature-name]
```

Where:
- `[feature-name]` is a kebab-case identifier for the feature (e.g., `design-decisions`, `user-authentication`). If not provided, derive an appropriate name from the conversation context.

## Prerequisites

Before running this command, you should have:
1. Had a discovery conversation with the User about the feature
2. Asked clarifying questions and received answers
3. Identified edge cases, relationships to existing systems, and design constraints
4. Reached agreement on the key decisions

If you have NOT had this conversation, STOP and inform the User that `/create-feature` is meant to formalize an existing design discussion, not start one from scratch.

## Workflow Overview

This command executes four phases:
1. **Audit & Brief Creation** - Research integration points and create a Feature Brief artifact
2. **Feature-Writer Invocation** - Call the Feature-Writer agent to generate the Feature Overview
3. **Design Owner Review** - You review and correct the Feature-Writer's output
4. **Presentation** - Present the completed specification to the User

---

## Phase 1: Audit & Brief Creation

### Step 1.1: Conduct Integration Audit

Before writing the brief, gather concrete data about the feature's integration points:

1. **Search for related files** - Use Grep/Glob to find files that will need updates
2. **Verify patterns** - Confirm existing conventions the feature should follow
3. **Quantify scope** - Count files by category (agents, commands, docs, etc.)
4. **Identify exemplars** - Find similar existing features to reference

Record your audit findings. You will include them in the brief.

### Step 1.2: Create Feature Brief

Create a Feature Brief artifact at `docs/workbench/[feature-name]-feature-brief.md`.

The brief MUST capture ALL decisions from your conversation with the User. The Feature-Writer agent cannot see your conversation - it can only read this brief. Anything not in the brief may be lost or misinterpreted.

**Required Brief Structure:**

```markdown
# Feature Brief: [Feature Name]

**Date**: [Current date]
**Prepared by**: User Agent (Workscope-[ID])
**For**: Feature-Writer Agent

---

## Executive Summary
[1-2 sentence description of what this feature does]

---

## Problem Statement
[Description of the problem being solved, with concrete examples if discussed]

---

## Solution Overview
[High-level description of the solution approach]

---

## Relationship to Existing Systems
[How this feature connects to, complements, or differs from existing components]

---

## Deliverables

[Numbered list of specific files to create or update, organized by category.
Include specific file paths from your audit.]

### 1. New File: `[path]`
[Purpose and key characteristics]

### 2. Updates: [category]
**Files to update** ([count]):
- `[specific/file/path.md]`
- `[another/file/path.md]`
...

---

## Design Constraints
[Explicit constraints, forbidden approaches, or fixed decisions from conversation]

---

## Out of Scope
[What this feature explicitly does NOT include]

---

## Success Criteria
[Measurable outcomes that indicate the feature is complete]

---

## Implementation Notes
[File counts, summaries, any pre-approved content like templates or seed entries.
If User approved specific content during conversation, include it here or note
that User will provide it during implementation.]

---

## Questions for Feature-Writer
[Ideally "None - this brief captures all design decisions."
If truly ambiguous areas remain, list specific questions.]
```

**Critical Requirements:**
- Include SPECIFIC file paths from your audit, not vague descriptions
- Capture design DECISIONS, not open questions
- Note any content the User will provide during implementation (don't invent it)
- Aim for a brief that requires NO clarification from Feature-Writer

### Step 1.3: User Approval Checkpoint

After creating the brief, present a summary to the User:

```
## Feature Brief Created

**Location**: `docs/workbench/[feature-name]-feature-brief.md`

### Summary
- [Key deliverables count]
- [Integration points count]
- [Any notable constraints or decisions]

### Audit Findings
- [X] files in [category] need updates
- [Y] files in [category] need updates
...

**Ready to invoke Feature-Writer?** Reply 'yes' to proceed, or provide feedback on the brief.
```

**HALT and wait for User approval before proceeding to Phase 2.**

---

## Phase 2: Feature-Writer Invocation

### Step 2.1: Invoke Feature-Writer Agent

Use the Task tool to invoke the Feature-Writer agent with this prompt structure:

```
You are tasked with creating a Feature Overview specification for "[Feature Name]".

## Your Task
Read the Feature Brief at `docs/workbench/[feature-name]-feature-brief.md` and create a comprehensive Feature Overview specification following the project's conventions.

## Key Context
[2-3 sentence summary of what the feature does - enough for Feature-Writer to understand the domain]

## Important Notes
- The Feature Overview should be created at `docs/features/[feature-name]/[Feature-Name]-Overview.md`
- Include a Feature Implementation Plan (FIP) at the end with numbered checkboxlist tasks

## References to Read
1. `docs/workbench/[feature-name]-feature-brief.md` - The complete Feature Brief
2. `docs/references/templates/Feature-Overview-Writing-Guide.md` - For Feature Overview writing instructions
3. `docs/references/templates/Feature-Overview-Template.md` - For main template to use
4. `docs/references/templates/Feature-Overview-Template-Elements.md` - For explanation of the template
5. `docs/references/templates/Feature-Overview-Checklist.md` - For checklist to evaluate proper Feature Overview draft
6. [Any other relevant references specific to this feature]
```

### Step 2.2: Receive Feature-Writer Output

The Feature-Writer will create the Feature Overview and return a summary. Do NOT trust the summary alone - you must read the actual output in Phase 3.

---

## Phase 3: Design Owner Review

You participated in the design conversation and have the deepest understanding of the feature's intent. This review is a critical quality gate.

### Step 3.1: Read the Full Feature Overview

Read the complete Feature Overview at `docs/features/[feature-name]/[Feature-Name]-Overview.md`.

Do NOT skip this step. Do NOT rely on the Feature-Writer's summary.

### Step 3.2: Verify Against Design Decisions

Check each of these against your conversation with the User:

- [ ] **Deliverables complete** - All items from the brief are represented in the spec and FIP
- [ ] **Relationships accurate** - Connections to existing systems correctly described
- [ ] **Constraints reflected** - Design constraints from conversation are in the spec
- [ ] **Out of scope noted** - Excluded items are documented
- [ ] **FIP tasks appropriate** - Tasks have right granularity, cover all deliverables
- [ ] **No invented content** - Feature-Writer didn't make up content that should come from User
- [ ] **Conventions followed** - Standard Feature Overview structure and formatting

### Step 3.3: Check Template Rules

The Feature-Writer is given explicit instructions regarding the FIP:
- [ ] The FIP should be the final section of the document. No other content should come after the checkboxlist of the FIP
- [ ] There should exist NO Phase 0. Phase 0 is reserved for issues that _emerge_ during FIP execution; it is not appropriate in the planning stage.
- [ ] There should exist no task that directs an agent to violate a Rule in Agent-Rules.md. For example, there should be no command directing the agent to use a _write_ git command (and thus would force them to violate Rule 2.2).

### Step 3.4: Make Corrections

**For minor issues** (typos, small omissions, clarifications):
- Edit the Feature Overview directly using your Edit tool
- Note what you corrected

**For major issues** (missing sections, fundamental misunderstandings, structural problems):
- Resume the Feature-Writer agent conversation using the agent ID
- Provide specific feedback on what needs to change
- Review the updated output
- Repeat until satisfactory

### Step 3.4: Document Review

Record in your Work Journal:
- What you verified
- Any corrections made (minor edits or Feature-Writer iterations)
- Final assessment

---

## Phase 4: Presentation

### Step 4.1: Present Completed Specification

Present the finished Feature Overview to the User with this format:

```
## Feature Specification Complete

**Feature Overview**: `docs/features/[feature-name]/[Feature-Name]-Overview.md`
**Feature Brief**: `docs/workbench/[feature-name]-feature-brief.md`

### Review Summary
- [Note any corrections made]
- [Confirm alignment with design conversation]

### FIP Overview
| Phase   | Tasks | Description         |
| ------- | ----- | ------------------- |
| Phase 1 | [N]   | [Brief description] |
| Phase 2 | [N]   | [Brief description] |
...

**Total**: [X] phases, [Y] tasks

### Artifacts Created
1. Feature Brief (workbench) - captures design decisions
2. Feature Overview (features/) - formal specification with FIP

### Next Steps
1. Review the Feature Overview specification
2. [Note any content User must provide during implementation]
3. Link to Action Plan when ready to begin implementation
4. Archive (move from `docs/workbench` to `docs/archive/`) the Feature Brief after implementation completes
```

### Step 4.2: Await User Feedback

The User may:
- **Approve** - Feature specification is complete
- **Request changes** - Make edits and re-present
- **Ask questions** - Clarify aspects of the specification

---

## Error Handling

### Brief Creation Errors

**Insufficient conversation context**: If you don't have enough information from the conversation to write a complete brief, STOP and tell the User what's missing. Do not guess.

**Audit reveals unexpected complexity**: If your audit shows the feature is much larger than discussed, present findings to User before proceeding.

### Feature-Writer Errors

**Feature-Writer doesn't create file**: Check the response for errors, retry invocation if needed.

**Feature-Writer misunderstands brief**: This indicates the brief was unclear. Consider whether to iterate with Feature-Writer or revise the brief and re-invoke.

### Review Errors

**Major discrepancies found**: If Feature-Writer's output fundamentally misses the mark, you may need to:
1. Resume Feature-Writer conversation with detailed feedback
2. Or, revise the brief to be clearer and re-invoke fresh

---

## Best Practices

### For Brief Writing

- **Be specific** - File paths, not "relevant files"
- **Be complete** - If it was decided in conversation, it goes in the brief
- **Be structured** - Follow the template; Feature-Writer expects this format
- **Note what's deferred** - Mark content User will provide during implementation

### For Review

- **Read everything** - The summary is not sufficient
- **Check the FIP** - Every deliverable should map to tasks
- **Trust your understanding** - You know the intent better than Feature-Writer!
- **Fix what you can** - Don't over-rely on Feature-Writer iterations for small issues

### For Presentation

- **Summarize changes** - What did you correct during review?
- **Highlight User actions** - What does User need to provide or decide?
- **Provide counts** - Phases, tasks, files - helps User understand scope
