# Project: Claude Code Phantom Reads Reproduction

## Overview

This project provides a reproducible demonstration of the "Phantom Reads" bug in Claude Code (Issue #17407). The repository serves as both documentation of the issue and a practical tool for other users to verify its occurrence on their own systems.

The Phantom Reads bug causes Claude Code to believe it has successfully read file contents when it has not. When file read operations return `<persisted-output>` responses (indicating results were saved to disk due to size), Claude proceeds as if it received the actual content, operating on incomplete or non-existent information without awareness of the gap.

## Product Vision

### Core Problem

Starting with Claude Code version 2.0.59 (released 2025-11-29), a regression was introduced that causes the AI assistant to fail to recognize when file read operations return `<persisted-output>` markers instead of actual file content. Rather than making follow-up read requests to retrieve the persisted content, Claude proceeds with its task, potentially confabulating information about files it never actually read.

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

Python scripts in `scripts/` that:
- Parse Claude Code session `.jsonl` files
- Identify Read tool invocations that returned `<persisted-output>` responses
- Detect whether follow-up reads were made to retrieve persisted content
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

Testing across Claude Code versions revealed a clear regression boundary:

| Version | Release Date | Trials | Failures | Notes |
|---------|--------------|--------|----------|-------|
| 2.0.54 | 2025-11-10 | 4 | 0 | No issues observed |
| 2.0.56 | 2025-11-26 | 4 | 0 | No issues observed |
| 2.0.58 | 2025-11-28 | 4 | 0 | Last known good version |
| 2.0.59 | 2025-11-29 | 4 | 2 | **Regression introduced** |
| 2.0.60 | 2025-11-30 | 4 | 4 | 100% failure rate |
| 2.0.62 | 2025-12-02 | 2 | 1 | Issue persists |
| 2.0.76 | 2025-12-23 | 2 | 2 | Issue persists |
| 2.1.2 | 2026-01-08 | 2 | 1 | Issue persists |

The 2.0.58 to 2.0.59 boundary represents a clear regression point, with zero failures observed in versions 2.0.58 and earlier, and consistent failures in 2.0.59 and later.

### Trigger Conditions

Based on the original investigation, phantom reads appear more likely to occur when:

1. **Multi-file operations**: Commands that trigger reads across multiple files in a single conversation turn
2. **Custom commands**: Execution context initiated via slash commands (e.g., `/refine-plan`)
3. **Large file sets**: Operations involving numerous related documents

The exact conditions that determine whether a specific read becomes a phantom read remain under investigation.

## Experiment Methodology

The original investigation followed a systematic protocol to test multiple Claude Code versions and identify the regression boundary. The full methodology, including step-by-step instructions, results analysis, and discussion of limitations, is documented in:

**[Experiment-Methodology.md](Experiment-Methodology.md)**

### Summary

The investigation used a self-report methodology: trigger multi-file read operations via `/wsd:init --custom` followed by `/refine-plan`, then prompt the agent to report whether any phantom reads occurred. Results were recorded as Success (no phantom reads) or Failure (phantom reads confirmed).

Key findings:
- **Pre-2.0.59**: 0 failures across 12 trials (versions 2.0.54, 2.0.56, 2.0.58)
- **Post-2.0.59**: 13 failures across 18 trials (versions 2.0.59 through 2.1.2)
- **Regression boundary**: Version 2.0.59 (released 2025-11-29)

### Limitations

The self-report methodology has inherent limitations (model incentives, introspection accuracy, non-determinism). The analysis tools in this repository address these limitations by examining session logs programmatically, removing the model from the detection loop.

## Architecture Overview

### Repository Structure

```
├── README.md                    # User-facing documentation
├── docs/
│   ├── core/
│   │   ├── PRD.md              # This document (internal)
│   │   ├── Action-Plan.md      # Implementation checkboxlist
│   │   └── Design-Decisions.md # Project design rationale
│   ├── read-only/              # WSD standards (read triggers)
│   ├── tickets/
│   │   └── open/               # WPD targets for /refine-plan
│   └── workbench/              # Working documents
├── scripts/
│   ├── archive_claude_sessions.py  # Session archival utility
│   └── analyze_phantom_reads.py    # Phantom read detector (to build)
└── .claude/
    └── commands/
        └── refine-plan.md      # Trigger command
```

### Key Components

**Trigger Mechanism**: The `/refine-plan` command executed against a ticket in `docs/tickets/open/`. This command prompts deep investigation across multiple documentation files, creating the multi-file read pattern associated with phantom reads.

**Detection Mechanism**: Python scripts that parse `.jsonl` session files from `~/.claude/projects/`, identify `<persisted-output>` responses, and determine whether follow-up reads occurred.

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
