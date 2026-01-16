# Project: Claude Code Phantom Reads Reproduction

## Overview

This project provides a reproducible demonstration of the "Phantom Reads" bug in Claude Code (Issue #17407). The repository serves as both documentation of the issue and a practical tool for other users to verify its occurrence on their own systems.

The Phantom Reads bug causes Claude Code to believe it has successfully read file contents when it has not. The bug manifests through two distinct mechanisms depending on Claude Code version: in older versions (2.0.59 and earlier), read results are cleared from context with `[Old tool result content cleared]` messages; in newer versions (2.0.60 and later), large read results return `<persisted-output>` markers that the agent fails to follow up on. In both cases, Claude proceeds as if it received the actual content, operating on incomplete or non-existent information without awareness of the gap.

## Product Vision

### Core Problem

Claude Code exhibits a bug where file read operations fail silently, leaving the AI assistant believing it has read file contents when it has not. The bug manifests differently across versions:

- **Era 1 (versions 2.0.59 and earlier)**: Read results are cleared from context, replaced with `[Old tool result content cleared]` messages. The agent proceeds without the content.
- **Era 2 (versions 2.0.60 and later)**: Large read results are persisted to disk, returning `<persisted-output>` markers. The agent fails to issue follow-up reads to retrieve the persisted content.

In both cases, Claude proceeds with its task, potentially confabulating information about files it never actually read. No "safe" version has been identified—all tested versions from 2.0.54 through 2.1.6 have exhibited phantom read behavior under certain conditions.

This bug is particularly insidious because:

1. **Silent Failure**: Claude exhibits no awareness that it missed file content, continuing confidently with incomplete information.

2. **Intermittent Occurrence**: The bug does not manifest consistently, making it difficult to identify as a systematic issue rather than occasional model error.

3. **Masked by Capability**: Claude's strong reasoning abilities allow it to "gap fill" plausibly from contextual clues, producing outputs that appear reasonable but are based on assumptions rather than actual file content.

4. **Compounding Context**: Over multi-turn conversations, successful reads in later turns can mask earlier phantom reads, as Claude incorporates corrected information without recognizing the initial failure.

### Solution

This repository provides:

1. **Documentation**: A comprehensive README explaining the Phantom Reads phenomenon, its symptoms, and its suspected cause.

2. **Reproduction Environment**: A structured project with inter-related documents that triggers multi-file read operations, creating conditions where phantom reads are likely to manifest.

3. **Analysis Tools**: Python scripts that examine Claude Code session logs to programmatically detect phantom read occurrences, removing reliance on the AI's self-reporting.

## Terms and Definitions

In addition to the Terms and Definitions you learned as part of the Workscope-Dev system, this specific project has a few more:

- "Session Agent": The agent that was working in an example session that experienced and reported a phantom read (or didn't in the case of a success example). This is distinct from a "User Agent" (which is _you_) and a Special Agent that you would work with during a workscope lifecycle.
- "Phantom Read": A phenomenon that occurs in the AI harness where a Read operation conducted by the Session Agent does not result in the contents of the file being correctly inserted into the Session Agent's context.
- "Inline Read": When the Session Agent received the contents of a file directly.
- "Deferred Read": When the Session Agent received the contents of a file through some intermediary step, such as a reference to a persisted output or a text file created by a tool internal to the AI harness. Not all deferred reads are presumed to be phantom reads (i.e., it may be the case that the agent correctly followed up on the read after the intermediary message), but we suspect that deferred reads are the cause of phantom reads.
- "Era 1": (mentioned above) Refers to sessions that took place in builds up to `2.0.59`, after which a key change occurred in how deferred reads were conducted by the Claude Code harness. For example, we have a pair of sessions in `dev/misc/example-sessions/` called `2.0.58-good` (success) and `2.0.58-bad` (phantom read) that were generated in that build.
- "Era 2": (mentioned above) Refers to sessions that took place in builds `2.0.60` and later, where deferred reads are handled differently by the Claude Code harness. For example, we have a pair of sessions in `dev/misc/example-sessions/` called `2.1.6-good` (success) and `2.1.6-bad` (phantom read) that were generated in that build.
- "Flat Architecture": A session (`.jsonl` files) in which the core session file and the breakout agent session files are stored adjacent in a directory, with only their session IDs to link them. This is an older architecture that changed somewhere between build `2.0.60` and `2.1.3`.
- "Hierarchical Architecture": A session (`.jsonl` files) in which the core session file is accompanied by a directory of the same name, which stores all of the breakout agent session files associated with that core session as well as any tool outputs. This is the newer (current) architecture that changed somewhere between build `2.0.60` and `2.1.3`.
- "Hybrid Architecture": A session (`.jsonl` files) in which the core session file is accompanied by a directory of the same name AND breakout agent session files stored adjacent in the same directory. We have seen sessions in build `2.0.60` use this pattern.

## Key Features

### 1. Public README

A user-facing README.md that:
- Links to the official GitHub issue (#17407)
- Explains the Phantom Reads phenomenon in accessible terms
- Documents the experiment methodology and findings
- Provides step-by-step reproduction instructions
- Includes guidance on installing specific Claude Code versions for testing

### 2. Reproduction Experiment

A structured environment designed to trigger phantom reads:
- Inter-related documentation files that prompt multi-file read operations
- A Work Plan Document (ticket) that serves as the target for the `/refine-plan` command
- The `/refine-plan` custom command, which triggers deep investigation across specifications and documentation

The experiment leverages the Workscope-Dev (WSD) framework already present in this repository. The `/refine-plan` command naturally triggers reads across multiple files in `docs/read-only/standards/`, `docs/core/`, and related locations—the exact pattern observed to trigger phantom reads in the original investigation.

### 3. Session Analysis Tools

Python scripts in `src/` that:
- Parse Claude Code session `.jsonl` files
- Identify Read tool invocations that returned phantom read indicators:
  - Era 2: `<persisted-output>` responses without follow-up reads
  - Era 1: `[Old tool result content cleared]` messages
- Report phantom read occurrences with file paths and conversation context

These tools provide objective, programmatic detection that does not rely on the AI's self-assessment of whether it experienced phantom reads.

## Technical Background

### How Claude Code Handles Large Outputs

When a tool result exceeds a size threshold, Claude Code persists the output to disk and returns a marker in this format:

```
<persisted-output>Tool result saved to: /path/to/file.txt

Use Read to view</persisted-output>
```

The AI is expected to recognize this marker and issue a follow-up Read command to retrieve the actual content. The Phantom Reads bug causes Claude to treat this marker as if it were the actual content, proceeding without the follow-up read.

### Version History

Testing across Claude Code versions revealed two distinct eras of phantom read behavior:

| Era | Versions        | Error Mechanism                     | Notes                      |
| --- | --------------- | ----------------------------------- | -------------------------- |
| 1   | 2.0.54 - 2.0.59 | `[Old tool result content cleared]` | Context clearing mechanism |
| 2   | 2.0.60 - 2.1.6+ | `<persisted-output>`                | Disk persistence mechanism |

**Important**: The original investigation incorrectly concluded that versions 2.0.58 and earlier were unaffected. Subsequent testing confirmed that ALL tested versions can exhibit phantom reads—the mechanism simply differs between eras.

The transition from Era 1 to Era 2 occurs at the 2.0.59/2.0.60 boundary, suggesting a change in how Claude Code handles large tool results around that release.

### Trigger Conditions

Based on the original investigation, phantom reads appear more likely to occur when:

1. **Multi-file operations**: Commands that trigger reads across multiple files in a single conversation turn
2. **Custom commands**: Execution context initiated via slash commands (e.g., `/refine-plan`)
3. **Large file sets**: Operations involving numerous related documents

The exact conditions that determine whether a specific read becomes a phantom read remain under investigation.

## Experiment Methodology

The original investigation followed a systematic protocol to test multiple Claude Code versions and identify version boundaries. The full methodology from the original investigation is preserved in:

**[Experiment-Methodology-01.md](Experiment-Methodology-01.md)** (historical document with addendum)

### Summary

The investigation used a self-report methodology: trigger multi-file read operations via `/wsd:init --custom` followed by `/refine-plan`, then prompt the agent to report whether any phantom reads occurred.

**Original findings** (later revised):
- Pre-2.0.59 versions appeared unaffected
- Post-2.0.59 versions showed consistent failures

**Revised understanding**:
- ALL tested versions can exhibit phantom reads
- Era 1 (2.0.59 and earlier): `[Old tool result content cleared]` mechanism
- Era 2 (2.0.60 and later): `<persisted-output>` mechanism
- The original investigation likely conflated the two mechanisms

For ongoing investigation notes, see `Investigation-Journal.md`.

### Limitations

The self-report methodology has inherent limitations (model incentives, introspection accuracy, non-determinism). Additionally, the original investigation failed to distinguish between the two phantom read mechanisms, leading to incorrect conclusions about "safe" versions. The analysis tools in this repository address these limitations by examining session logs programmatically, removing the model from the detection loop.

## Architecture Overview

### Repository Structure

```
├── README.md                        # User-facing documentation
├── docs/
│   ├── core/
│   │   ├── PRD.md                  # This document (internal)
│   │   ├── Action-Plan.md          # Implementation checkboxlist
│   │   ├── Design-Decisions.md     # Project design rationale
│   │   ├── Investigation-Journal.md # Running log of discoveries
│   │   └── Experiment-Methodology-01.md # Original methodology (historical)
│   ├── read-only/                  # WSD standards (read triggers)
│   ├── tickets/
│   │   └── open/                   # WPD targets for /refine-plan
│   └── workbench/                  # Working documents
├── dev/
│   └── misc/                       # Session samples (good/bad cases by version)
├── src/
│   ├── cc_version.py               # Claude Code version setting utility
│   └── collect_trials.py           # Tool for gathering trial data
└── .claude/
    └── commands/
        └── refine-plan.md          # Trigger command
```

### Key Components

**Trigger Mechanism**: The `/refine-plan` command executed against a ticket in `docs/tickets/open/`. This command prompts deep investigation across multiple documentation files, creating the multi-file read pattern associated with phantom reads.

**Detection Mechanism**: Python scripts that parse `.jsonl` session files from `~/.claude/projects/`, identifying both Era 1 (`[Old tool result content cleared]`) and Era 2 (`<persisted-output>`) phantom read indicators.

**Documentation**: README.md serves as the public-facing explanation; PRD.md and related docs/ files serve internal development purposes.

## Design Principles

### Separation of Concerns

This repository serves dual purposes:
1. **Public experiment**: Materials for end-users to reproduce the issue
2. **Development infrastructure**: WSD framework for building the experiment

These concerns are kept separate:
- User-facing materials (README, analysis scripts) contain no references to internal development processes
- Internal documents (PRD, Action Plan) may reference development methodology freely
- The WSD infrastructure enables development but also serves as part of the reproduction trigger

### Hawthorne Effect Consideration

A noted concern is whether a User Agent operating in a project explicitly dedicated to detecting phantom reads might behave differently (be less likely to exhibit phantom reads). This is documented as a concern to investigate if reproduction results differ significantly from the original investigation. The working hypothesis is that the bug is at the harness/infrastructure level, not influenced by project content.

### Minimal Viable Reproduction

The initial approach uses the existing WSD documentation as the multi-file read trigger. If this proves insufficient to reliably trigger phantom reads, the design allows for adding a "dummy project" (simple CLI tool or similar) to provide additional file complexity.

## Success Metrics

This project achieves its goals when:

1. **Documented**: README clearly explains the Phantom Reads phenomenon and links to the official issue

2. **Reproducible**: End-users can follow the instructions to trigger phantom reads on affected Claude Code versions

3. **Verifiable**: Analysis tools can programmatically detect phantom reads in session logs, providing objective evidence beyond AI self-reporting

4. **Accessible**: Instructions are clear enough for users unfamiliar with WSD to execute the reproduction experiment

## Future Direction

### Potential Enhancements

If the core reproduction is successful, future work might include:

1. **Minimal reproduction case**: Identifying the smallest set of conditions that reliably triggers phantom reads
2. **Automated trial runner**: Scripts that execute multiple trials and aggregate statistics
3. **Real-time monitoring**: Tools that detect phantom reads during active sessions
4. **Mitigation strategies**: Workarounds users can employ while the bug remains unfixed

### Out of Scope

This project explicitly does not aim to:
- Fix the bug (that responsibility lies with Anthropic)
- Provide production-grade tooling
- Support all possible Claude Code configurations
- Guarantee reproduction (the bug is intermittent by nature)

## References

- GitHub Issue: https://github.com/anthropics/claude-code/issues/17407
- Claude Code Documentation: https://docs.anthropic.com/en/docs/claude-code
- Opus 4.5 Release: 2025-11-24
