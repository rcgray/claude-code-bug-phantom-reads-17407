# Experiment Methodology

This document describes the methodology used to investigate and reproduce the Phantom Reads bug in Claude Code. It serves as both a record of the original investigation and a guide for others seeking to reproduce the issue.

## Overview

The investigation followed a systematic approach: test multiple Claude Code versions under identical conditions, record whether phantom reads occurred, and identify the version boundary where the regression was introduced.

The methodology relies on prompting the User Agent to self-report whether it experienced phantom reads during a multi-file read operation. While this approach has limitations (discussed below), it was sufficient to identify a clear regression boundary and establish the existence of the bug.

## Environment Setup

Before running trials, the test environment must be configured to use a specific Claude Code version without automatic updates overwriting it.

### Step 1: Disable Auto-Updates

Edit `~/.claude/settings.json` to disable the auto-updater:

```json
{
  "env": {
    "DISABLE_AUTOUPDATER": "1"
  }
}
```

This prevents Claude Code from automatically updating to the latest version between trials.

### Step 2: Install Target Version

Uninstall the current version, clear the npm cache, and install the specific version to test:

```bash
# Check current version
claude --version
# Example output: 2.1.3 (Claude Code)

# Uninstall current version
npm uninstall -g @anthropic-ai/claude-code

# Verify uninstallation
claude --version
# Expected: command not found

# Clear npm cache to ensure clean install
npm cache clean --force

# Install specific version
npm install -g @anthropic-ai/claude-code@2.0.59

# Verify installation
claude --version
# Expected: 2.0.59 (Claude Code)
```

### Step 3: Verify Auto-Update is Disabled

1. Launch Claude Code in any project directory
2. Wait approximately 30 seconds
3. Exit Claude Code using `/exit`
4. Relaunch Claude Code
5. Verify the version has not changed

If the version changed, the auto-update disable was not effective. Check that `settings.json` is properly formatted and in the correct location.

## Trial Execution

Each trial follows a consistent protocol designed to trigger multi-file read operations and then prompt the agent to self-report any phantom read occurrences.

### Step 1: Initialize Fresh Context

Run the WSD initialization command to establish a fresh User Agent context:

```
/wsd:init --custom
```

This command triggers several document read operations as part of the agent onboarding process. Some of these reads may become phantom reads.

### Step 2: Trigger Multi-File Investigation

Execute the `/refine-plan` command against a Work Plan Document:

```
/refine-plan docs/tickets/open/<ticket-name>.md
```

The `/refine-plan` command prompts the agent to deeply investigate a ticket by reading related specifications, examining code, and cross-referencing documentation. This naturally triggers reads across multiple files—the pattern most associated with phantom read occurrences.

### Step 3: Prompt for Self-Report

Disregard the agent's initial response to the `/refine-plan` command. Instead, prompt with the following:

```
We have recently seen a number of User Agents reporting issues reading files like the following:

"""
Looking back at my history, you're right. My first Read call for the ticket returned:

  <persisted-output>Tool result saved to: /Users/gray/.claude/projects/-Users-gray-Projects-workscope/dadf32a6-c83d-462d-b678-fbe7f191f42f/tool-results/toolu_019Nqx8qLWvdFSjvMsy5xFkM.txt

  Use Read to view</persisted-output>

  I did not follow up with a Read call to view that persisted output. I proceeded with my "investigation" without ever having actually read the ticket contents. I was operating completely blind, making assumptions about a document I never saw.

  The same thing happened with several other files at the start - WSD-Runtime-Metadata-Schema.md, WSD-Manifest-Schema.md, Manifest-Driven-Pipeline-Overview.md all returned <persisted-output> messages that I never followed up on
"""

I am debugging this recurring issue and I am checking to see if this particular session is a reproduction of this issue. Did you experience this during your execution of the `/refine-plan` command?
```

### Step 4: Record Results

Based on the agent's response, record the trial result:

- **Success**: Agent reports no phantom reads occurred; file content was received inline
- **Failure**: Agent confirms one or more files returned `<persisted-output>` responses that were not followed up with actual reads

Note which specific files were affected if the agent provides this information.

## Results

The following results were obtained from the original investigation:

| Version | Release Date | Trials | Failures | Failure Rate |
| ------- | ------------ | ------ | -------- | ------------ |
| 2.0.54  | 2025-11-10   | 4      | 0        | 0%           |
| 2.0.56  | 2025-11-26   | 4      | 0        | 0%           |
| 2.0.58  | 2025-11-28   | 4      | 0        | 0%           |
| 2.0.59  | 2025-11-29   | 4      | 2        | 50%          |
| 2.0.60  | 2025-11-30   | 4      | 4        | 100%         |
| 2.0.62  | 2025-12-02   | 2      | 1        | 50%          |
| 2.0.76  | 2025-12-23   | 2      | 2        | 100%         |
| 2.1.2   | 2026-01-08   | 2      | 1        | 50%          |

**Key Finding**: The regression was introduced in version 2.0.59. All versions prior to 2.0.59 showed zero failures across all trials. All versions from 2.0.59 onward showed failures.

### Observed Failure Patterns

In trials where phantom reads occurred, agents reported:

1. **Primary target affected**: In some cases, the very file specified in the `/refine-plan` command was phantom-read. The agent would claim to have thoroughly reviewed the document while having no knowledge of its actual contents.

2. **Supporting files affected**: Files read as part of the investigation (specifications, standards documents) returned `<persisted-output>` responses that were never followed up.

3. **Partial awareness**: Some agents, when prompted, were able to identify specific files they had "read" but could not describe their contents.

4. **Complete unawareness**: Other agents maintained they had successfully read all files until directly confronted with the `<persisted-output>` pattern, at which point they acknowledged the gap.

## Controls and Limitations

### Environmental Controls

To rule out directory-specific factors, trials were conducted across two independent clones of the test repository:

- Half of trials for each version ran in Project Instance A
- Half of trials for each version ran in Project Instance B
- Failures occurred in both instances with similar frequency

This parallel approach also accelerated the investigation by allowing concurrent trial execution.

### Methodology Limitations

The self-report methodology has inherent limitations:

1. **Model Incentives**: LLMs may be biased toward reporting success to please the user. This could lead to under-reporting of phantom reads.

2. **Introspection Accuracy**: Models may not have accurate insight into their own tool call history. They may misremember or confabulate when asked to report on past operations.

3. **Non-Determinism**: Model responses vary between runs, even with identical inputs. A model might report phantom reads in one trial and deny them in another, independent of whether they actually occurred.

4. **Confirmation Bias**: The prompt explicitly describes the phantom read phenomenon, which could prime the model to report it even if it didn't occur.

Despite these limitations, the clear version boundary (0% failures before 2.0.59, consistent failures after) suggests the methodology was sufficient to identify a real regression.

### Addressing Limitations

The analysis tools described in the PRD aim to address these limitations by examining session logs directly. Programmatic detection of `<persisted-output>` responses without follow-up reads removes the model from the detection loop entirely.

## Discussion

### Context: Perceived Model Degradation

Many Claude users reported a subjective feeling that Claude was getting "dumber" in late 2025, particularly after the release of Opus 4.5 (2025-11-24). Some attributed this to intentional model degradation for cost savings.

This investigation suggests an alternative explanation: the model's capabilities remained unchanged, but starting with Claude Code 2.0.59 (2025-11-29), it began operating on incomplete information due to the phantom reads bug. A highly capable model working with missing context will produce outputs that seem "dumber"—not because the model degraded, but because it lacks information it believes it has.

### Why Detection Was Delayed

Several factors delayed detection of this bug:

1. **Intermittent occurrence**: Phantom reads don't happen on every read operation, making the bug difficult to reproduce consistently and easy to dismiss as occasional model error.

2. **Capable gap-filling**: Opus 4.5 is skilled at inferring missing information from context. When phantom reads occur, the model often produces plausible outputs based on other successfully-read files, masking the data gap.

3. **Multi-turn correction**: Over a conversation, users often provide corrections or additional context that prompt the model to re-read files. Successful reads in later turns can compensate for phantom reads in earlier turns.

4. **Confidence without awareness**: The model proceeds confidently after a phantom read, showing no indication that anything went wrong. Users have no signal to investigate unless outputs are obviously incorrect.

### Discovery Context

The bug was discovered during development of the `/refine-plan` command in early January 2026. This command triggers extensive multi-file reads, creating conditions where phantom reads are likely. Subtle hallucinations in `/refine-plan` outputs noticed by the User prompted deeper investigation.

Systematic testing across Claude Code versions then identified the 2.0.58/2.0.59 boundary as the regression point.

## Reproducing the Investigation

To reproduce this investigation:

1. Set up the environment as described above
2. Select Claude Code versions to test (recommend including at least one pre-2.0.59 version as a control)
3. Run multiple trials per version
4. Record results consistently
5. Compare failure rates across versions

The analysis tools in this repository can supplement manual trials by programmatically detecting phantom reads in session logs.

## References

- GitHub Issue: https://github.com/anthropics/claude-code/issues/17407
- PRD: `docs/core/PRD.md`
- Analysis Tools: `src/` (see PRD for specifications)

---

## Addendum: Revised Understanding (2026-01-13)

Subsequent investigation has revealed that the original findings require significant revision. This addendum documents what we now understand differently.

### Two Distinct Error Mechanisms

The original investigation conflated two different phantom read mechanisms that manifest differently across Claude Code versions:

**Era 1: `[Old tool result content cleared]` (versions 2.0.59 and earlier)**

In earlier builds, phantom reads manifest as tool results being cleared from context before the agent can process them. Agents report seeing messages like:
```
[Old tool result content cleared]
```

This appears to be a context management issue where Read results are discarded, possibly due to context window pressure.

**Era 2: `<persisted-output>` (versions 2.0.60 and later)**

Starting with build 2.0.60, the error mechanism changed. Read results that exceed a size threshold are persisted to disk, returning:
```
<persisted-output>Tool result saved to: /path/to/file.txt

Use Read to view</persisted-output>
```

The agent fails to recognize this as a prompt to issue a follow-up Read, proceeding without the content.

### No Safe Build Exists

The original investigation concluded that versions 2.0.58 and earlier were unaffected. **This conclusion was incorrect.**

Subsequent testing confirmed that version 2.0.58 CAN experience phantom reads via the Era 1 mechanism (`[Old tool result content cleared]`). The original trials may have been fortunate, or the failure rate in 2.0.58 may be lower than in later versions, but the issue exists.

**Revised understanding**: There is no known "safe" version of Claude Code. All tested versions from 2.0.54 through 2.1.6 have exhibited phantom read behavior under certain conditions.

### Revised Version Transition

| Era | Versions         | Error Mechanism                     |
| --- | ---------------- | ----------------------------------- |
| 1   | 2.0.54 - 2.0.59  | `[Old tool result content cleared]` |
| 2   | 2.0.60 - present | `<persisted-output>`                |

The transition between eras occurs at the 2.0.59/2.0.60 boundary, not the 2.0.58/2.0.59 boundary as originally reported.

### Mitigation Observations

User Agents report that `grep` operations appear more reliable than `Read` operations. One agent noted:

> "Despite not following the persisted-output instructions, my analysis wasn't completely blind because... my Grep calls returned actual content snippets."

This suggests that Grep results may be handled differently than Read results, possibly bypassing the mechanisms that cause phantom reads.

### Implications for Analysis Tools

Any programmatic detection tool must account for BOTH error mechanisms:
1. Detect `<persisted-output>` markers without follow-up reads (Era 2)
2. Detect `[Old tool result content cleared]` messages (Era 1)

### Status of This Document

This document (`Experiment-Methodology-01.md`) represents the original investigation methodology and findings as understood at the time of the initial report. It is preserved for historical reference.

For the current understanding of the phantom reads phenomenon, including the two-era model and ongoing investigation, see:
- `docs/core/Investigation-Journal.md` - Running log of discoveries
- `docs/core/PRD.md` - Updated project requirements
