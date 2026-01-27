---
description: Process prompt log into core documentation
argument-hint: <path-to-prompt-log>
---

# Process Prompt Log

This command processes a historical prompt log file to extract discoveries, experiments, and findings, then updates the core documentation files accordingly.

## Usage

```
/process-prompt-log <path-to-prompt-log>
```

Where:
- `<path-to-prompt-log>` is the path to the prompt log file (typically in `dev/prompts/archive/`). This argument is required.

The target prompt log to process:

$ARGUMENTS

## Examples

```
/process-prompt-log dev/prompts/archive/Prompts-2026-01-19_104652.txt
```

---

## Purpose

Prompt logs contain the raw record of our investigation sessions. They capture:
- Experiment execution and results
- Discoveries about Claude Code behavior
- Theoretical developments and refinements
- Tool limitations and workarounds found
- Decisions made during the investigation

Note: these prompt archives only contain the User portion of the discussions, but they still contain vital information, particularly regarding theories, results, and a timeline of events. Prompts filenames reflect the timestamp at which they are created, showing their timing in the project-long conversation.

This command extracts that knowledge and ensures it's properly recorded in our core documentation.

## Target Documents

Important note: the following documents are updated regularly as the project progresses. Your focus should be on missing information discovered in the Prompt logs that may have been missed so that we can make sure nothing "falls through the cracks." This is primarily a _verification_ task, to ensure that key insights are not lost.

You will update the following files as needed:

### 1. `docs/core/Timeline.md`
**Add dated entries for:**
- Experiments run (with outcomes)
- Features/tools completed
- Key discoveries made
- Methodology changes

**Format:** Follow existing date-based structure. Keep entries concise and scannable.

### 2. `docs/core/Investigation-Journal.md`
**Add or update sections for:**
- Detailed experiment narratives (if not already covered)
- Theory developments and refinements
- Critical discoveries requiring explanation
- Open questions identified

**Format:** Follow existing narrative style with dated section headers.

### 3. `docs/core/Research-Questions.md`
**Add or update:**
- New research questions discovered
- Evidence for existing questions
- Status changes (OPEN → ANSWERED, etc.)
- **Discovered Behaviors** (see below)

**IMPORTANT - Discovered Behaviors Section:**
Research-Questions.md should include a "Category I: Discovered Behaviors" section for knowledge that:
- Is NOT a question but a confirmed fact about Claude Code behavior
- Was discovered during experimentation
- Affects our methodology or approach
- Would be valuable for future investigators to know

Examples of Discovered Behaviors:
- "The `/context` command cannot be called by agents - it requires manual user invocation"
- "Files hoisted via `@` notation have a ~25K token limit per file"
- "Session `.jsonl` files record actual content, not what the model receives"

If this section doesn't exist, create it.

---

## Your Mission

### Phase 1: Read and Extract

1. **Read the prompt log thoroughly.** Prompt logs are formatted as:
   - Model information at top
   - Session markers: `## New Session: ...`
   - User prompts separated by `---`
   - Commands, experiment results, and discussions

2. **Extract the following:**
   - **Experiments:** What was run? What were the results?
   - **Discoveries:** What new facts were learned?
   - **Questions:** What new questions were raised?
   - **Behaviors:** What Claude Code behaviors were observed?
   - **Decisions:** What methodological decisions were made?
   - **Tool/Feature completions:** What was built or finished?

3. **Note the date** from the filename (format: `Prompts-YYYY-MM-DD_HHMMSS.txt`)

### Phase 2: Cross-Reference

Before updating documents, check what's already recorded:
- Read `docs/core/Timeline.md` for that date range
- Scan `docs/core/Investigation-Journal.md` for related entries
- Check `docs/core/Research-Questions.md` for related questions

**Only add NEW information** that isn't already documented.

Note: The project directory structure may have changed since the time of the Prompt log. Some files that may have existed under `docs/core/` at the time of the prompt may have moved elsewhere (often an organization folder underneath `docs/experiments/`).

### Phase 3: Report Findings

Present your findings as a structured report:

```
## Prompt Log Analysis: [filename]
**Date:** YYYY-MM-DD
**Sessions:** [number of sessions in log]

### Experiments Found
1. [Experiment name/ID] - [Brief outcome]
2. ...

### Discoveries
1. [Discovery] - [Significance]
2. ...

### New Research Questions
1. [Question]
2. ...

### Discovered Behaviors
1. [Behavior] - [How discovered]
2. ...

### Already Documented
- [Items that are already in our docs]

### Proposed Updates
**Timeline.md:**
- [Specific additions]

**Investigation-Journal.md:**
- [Specific additions or updates]

**Research-Questions.md:**
- [New questions to add]
- [Status updates]
- [Discovered behaviors to add]
```

### Phase 4: Discuss and Update

After presenting findings:
1. **Wait for user approval** before making updates
2. **Make the approved updates** to each document
3. **Report what was updated** with specific line/section references

---

## Guidelines

### What to Include

- **Significant experiments** with clear outcomes
- **Confirmed discoveries** (not speculation)
- **Methodology learnings** that affect future work
- **Tool behaviors** that investigators should know
- **Theory developments** with supporting evidence

### What to Exclude

- Routine session activity (file reads, basic commands)
- Tentative ideas that weren't pursued
- Debugging steps that didn't reveal anything
- Redundant information already in docs

### Tone and Style

- **Timeline.md:** Brief, scannable, factual
- **Investigation-Journal.md:** Narrative, detailed, contextual
- **Research-Questions.md:** Structured, evidence-based, actionable

### Handling Uncertainty

If you're unsure whether something is significant enough to document:
- **Include it in your report** but mark as "Possibly significant"
- **Let the user decide** whether to include it
- **Err on the side of inclusion** for unusual Claude Code behaviors

---

## After Processing

When finished, confirm for the user the file you processed and present your results.
