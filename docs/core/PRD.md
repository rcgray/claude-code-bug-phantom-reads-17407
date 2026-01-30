# Project: Claude Code Phantom Reads Reproduction

## Overview

This project provides a reproducible demonstration of the "Phantom Reads" bug in Claude Code (Issue #17407). The repository serves as both documentation of the issue and a practical tool for other users to verify its occurrence on their own systems.

The Phantom Reads bug causes Claude Code to believe it has successfully read file contents when it has not. The bug manifests through two distinct mechanisms depending on Claude Code version: in older versions (2.0.59 and earlier), read results are cleared from context with `[Old tool result content cleared]` messages; in newer versions (2.0.60 and later), large read results return `<persisted-output>` markers that the agent fails to follow up on. In both cases, Claude proceeds as if it received the actual content, operating on incomplete or non-existent information without awareness of the gap.

## Product Vision

### Core Problem

Claude Code exhibits a bug where file read operations fail silently, leaving the AI assistant believing it has read file contents when it has not. The bug manifests differently across versions:

- **Era 1 (versions 2.0.59 and earlier)**: Read results are cleared from context, replaced with `[Old tool result content cleared]` messages. The agent proceeds without the content.
- **Era 2 (versions 2.0.60 and later)**: Large read results are persisted to disk, returning `<persisted-output>` markers. The agent fails to issue follow-up reads to retrieve the persisted content.

In both cases, Claude proceeds with its task, potentially confabulating information about files it never actually read. No "safe" version has been identified—all tested versions from 2.0.54 through 2.1.22 have exhibited phantom read behavior under certain conditions. Server-side variability means even the same build can show phantom reads one day and not the next.

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

4. **Temporary Workaround**: A validated workaround using the MCP Filesystem server that bypasses Claude Code's native Read tool entirely, achieving 100% success rate in preventing phantom reads. This allows users to continue productive work while the underlying bug remains unfixed.

## Terms and Definitions

In addition to the Terms and Definitions you learned as part of the Workscope-Dev system, this specific project has a few more:

- "Session Agent": The agent that was working in an example session that experienced and reported a phantom read (or didn't in the case of a success example). This is distinct from a "User Agent" (which is _you_) and a Special Agent that you would work with during a workscope lifecycle.
- "Phantom Read": A phenomenon that occurs in the AI harness where a Read operation conducted by the Session Agent does not result in the contents of the file being correctly inserted into the Session Agent's context.
- "Inline Read": When the Session Agent received the contents of a file directly.
- "Deferred Read": When the Session Agent received the contents of a file through some intermediary step, such as a reference to a persisted output or a text file created by a tool internal to the AI harness. Not all deferred reads are presumed to be phantom reads (i.e., it may be the case that the agent correctly followed up on the read after the intermediary message), but we suspect that deferred reads are the cause of phantom reads.
- "Era 1": (mentioned above) Refers to sessions that took place in builds up to `2.0.59`, after which a key change occurred in how deferred reads were conducted by the Claude Code harness. For example, we have a pair of sessions in `dev/misc/example-sessions/` called `2.0.58-good` (success) and `2.0.58-bad` (phantom read) that were generated in that build.
- "Era 2": (mentioned above) Refers to sessions that took place in builds `2.0.60` and later, where deferred reads are handled differently by the Claude Code harness. For example, we have a pair of sessions in `dev/misc/example-sessions/` called `2.1.6-good` (success) and `2.1.6-bad` (phantom read) that were generated in that build.
- "karpathy script": An alternative to traditional programming (e.g., Python), where a repeatable, software operation is designed as an agent-interpretable instruction (possibly with associated traditional scripts). These are not perfectly deterministic as a traditional script would be, due to the stochastic elements of the LLM model, but they are faster to implement and particularly well-suited for complex tasks involving NLP.
- "Flat Architecture": A session (`.jsonl` files) in which the core session file and the breakout agent session files are stored adjacent in a directory, with only their session IDs to link them. This is an older architecture that changed somewhere between build `2.0.60` and `2.1.3`.
- "Hierarchical Architecture": A session (`.jsonl` files) in which the core session file is accompanied by a directory of the same name, which stores all of the breakout agent session files associated with that core session as well as any tool outputs. This is the newer (current) architecture that changed somewhere between build `2.0.60` and `2.1.3`.
- "Hybrid Architecture": A session (`.jsonl` files) in which the core session file is accompanied by a directory of the same name AND breakout agent session files stored adjacent in the same directory. We have seen sessions in build `2.0.60` use this pattern.
- "Trial": A single run of an experiment (described in one--likely our latest--Experiment-Methodology file in `/docs/experiments/methodologies/`. A trial is recorded to `dev/misc/[collection]` as a folder containing the export of the chat session between the User and the Session Agent, the `.jsonl` files generated by Claude Code during the session, and a pre-processing artifact `trial_data.json` containing a summary of the salient aspects of the trial generated by our `/update-trial-data` karpathy script.
- "Collection": A set of trials collected together and residing as a folder (of trials) under `dev/misc`

## Aims

This project aims to achieve the following goals:

1) Understand the nature and cause of phantom reads. We perform experiments to reveal how the issue triggers, running "Trials" of different projects in various file read situations to collect data developing analysis tools to help us better understand Trial data, deriving theories from our findings, and evaluating those theories through subsequent experiments.

2) Find a temporary workaround to relieve our readers who are suffering with this issue. In fact, it is essential to our own success, because we also endure phantom read errors in our own pursuit to fix the issue. Discovery of a workaround is an early aim in this investigation so that we can move forward with an ability to trust in our work in measuring trustworthiness.

3) Create a dependable reproduction case. In fact, we're aiming to create three repeatable experiments that we can offer our readers: an "Easy" case intended to always succeed with no phantom reads, a "Hard" case intended to trigger phantom reads 100% of the time, and a "Medium" case intended to trigger with 50% likelihood. This aim is assisted by growing success in Aim #1, since the more we understand the issue, the better equipped we are to tune our scenarios that intentionally trigger or avoid the phenomenon.

4) Create tools for analyzing Claude Code token management behavior. This grows out of necessity of the pursuit of Aim #1, but it is a nice side effect of our investigative work that we also end up with tools that assist future investigations.

**Status (Jan 30, 2026)**: Aim #2 is solved (MCP Filesystem workaround, 100% success rate). Aim #1 is substantially achieved — the root cause chain is fully mapped (persistence → marker substitution → agent ignores markers), and the Server-Side Variability Theory explains why outcomes vary across sessions. Aim #4 is achieved organically through `trial_data.json` preprocessing (Schema 1.3), `collect_trials.py`, and analysis tooling. Aim #3 (calibrated reproduction) proved infeasible under server-side variability — the server controls the persistence decision, making fixed Easy/Medium/Hard calibration impossible. The investigation has shifted from experimental work to documentation and public reporting. See the [Build-Scan Discrepancy Analysis](../experiments/results/Build-Scan-Discrepancy-Analysis.md) closure assessment for details.

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
- A Work Plan Document (WPD) that serves as the analysis target
- Custom commands (`/analyze-wpd`, `/setup-easy`, `/setup-medium`, `/setup-hard`) that control context consumption and trigger multi-file reads
- Scenario-specific preloading that inflates baseline context via hoisted files

The current methodology (Experiment-Methodology-04) uses the fictional "Data Pipeline System" specification set as the trigger payload, with scenario commands controlling pre-operation context levels. The Barebones-216 experiment validated that this reproduction works in a minimal 20-file repository without any WSD framework overhead, confirming the trigger is multi-file read operations under context pressure—not any particular project structure.

### 3. Session Analysis Tools

Python scripts in `src/` that:
- Parse Claude Code session `.jsonl` files and associated session artifacts
- Detect phantom read conditions using proxy indicators, since phantom read markers (`<persisted-output>`, `[Old tool result content cleared]`) are NOT recorded in session `.jsonl` files (the `.jsonl` logs tool execution results before context management transforms them):
  - **Context reset detection**: Drops in `cache_read_input_tokens` between assistant messages correlate with phantom read occurrence
  - **Persistence detection**: Presence of a `tool-results/` directory in session data indicates the harness persisted tool results to disk
  - **Token timeline analysis**: Structured `trial_data.json` files track cumulative token consumption across session turns
- Handle all three Claude Code session storage structures (flat, hybrid, hierarchical) transparently
- Report phantom read risk indicators with file paths and conversation context

These tools provide objective, programmatic evidence of phantom read conditions. Direct detection of phantom reads from session files is not possible because the `.jsonl` records actual file content even when the model received phantom read markers (see `docs/experiments/results/Example-Session-Analysis.md` for the foundational analysis).

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
| 2   | 2.0.60 - 2.1.22+ | `<persisted-output>`                | Disk persistence mechanism (server-controlled) |

**Important**: The original investigation incorrectly concluded that versions 2.0.58 and earlier were unaffected. Subsequent testing confirmed that ALL tested versions can exhibit phantom reads—the mechanism simply differs between eras.

The transition from Era 1 to Era 2 occurs at the 2.0.59/2.0.60 boundary, suggesting a change in how Claude Code handles large tool results around that release.

### Trigger Conditions

Based on 55+ controlled trials across multiple collections (WSD-Dev-02, repro-attempts-02, Barebones-216, Barebones-2120, build scan collections, and schema-13 experiments), the investigation has identified **tool result persistence** (`has_tool_results`) as the primary outcome discriminator: sessions where the harness persists tool results to disk produce phantom reads; sessions where it does not persist are safe. Whether persistence is enabled is controlled by server-side state that varies over time (see [Server-Side-Variability-Theory.md](../theories/Server-Side-Variability-Theory.md)).

Within sessions where persistence is active, **reset timing** was identified as a secondary predictor. Early analysis of 31 trials (22 WSD-Dev-02 + 9 repro-attempts-02) established the patterns below:

| Pattern      | Description                                 | Outcome      |
| ------------ | ------------------------------------------- | ------------ |
| EARLY + LATE | First reset early, last reset late (after work), no mid-session resets | 100% SUCCESS |
| SINGLE_LATE  | Single reset late in session (after work)   | 100% SUCCESS |
| MID-SESSION  | Multiple resets during active file processing (50-90% of session) | 100% FAILURE |

**Boundary note**: The original 22-trial WSD-Dev-02 dataset had clean separations (success first resets <50%, last resets >95%). The 9-trial repro-attempts-02 dataset revealed that boundaries are approximate: success trials showed first resets at 49-64% and last resets at 88-90%. A single borderline mid-session reset (50-65%) appears survivable; the critical failure condition is **multiple mid-session resets** (the sole repro-02 failure had 3 consecutive resets at 57%, 72%, 84%).

**Key findings:**

1. **Reset timing is critical**: When context resets occur matters more than how many occur or total context consumed
2. **Multiple mid-session resets predict failure**: Resets during active file processing (50-90% of session) predict phantom reads, especially when multiple resets cluster mid-session. A single borderline reset (~50-65%) may be survivable, but 2+ mid-session resets correlate with guaranteed failure
3. **The "Clean Gap" pattern**: Successful sessions show early resets (before main work) and late resets (after work completes), with uninterrupted file reading in between. Success requires a sustained processing gap of approximately 25-30% of session duration
4. **No fixed token threshold**: Resets occur at widely varying cumulative token counts (82K-383K), ruling out a simple threshold model
5. **Accumulation rate matters**: Rapid batch reads without processing pauses appear to trigger mid-session resets more readily

**Contributing factors** (from original investigation, still relevant):
- Multi-file operations triggered by custom commands (e.g., `/refine-plan`, `/analyze-wpd`)
- Large file sets requiring numerous related document reads

**Revised understanding (Jan 30, 2026)**: The Build-Scan Discrepancy Investigation revealed that the reset timing patterns above are valid only within sessions where tool result persistence is active. The actual outcome discriminator is the `has_tool_results` field in trial data: `false` = 100% success (14/14 trials), `true` = 85% failure (17/20 non-overload trials). Reset timing predictions were systematically violated in Experiment-04, where SINGLE_LATE patterns (previously 100% SUCCESS) produced FAILURE when Y was increased to 57K tokens. Additionally, server-side variability means the same build, protocol, and files can produce opposite outcomes on different days — build 2.1.22 showed 100% failure on Jan 28 and 100% success on Jan 29. Task agent delegation (where the Session Agent delegates file reads to sub-agents) emerged as an additional confounding variable that structurally avoids the persistence trigger. See [Server-Side-Variability-Theory.md](../theories/Server-Side-Variability-Theory.md) and [Build-Scan-Discrepancy-Analysis.md](../experiments/results/Build-Scan-Discrepancy-Analysis.md).

**Environment independence**: The Barebones-216 experiment (Jan 27) confirmed that phantom reads are a Claude Code harness issue, not specific to any particular project framework. A stripped-down repository containing only 20 files (no WSD framework, no hooks, no investigation infrastructure) reproduced phantom reads at 100% (4/4 valid trials), matching the full investigation repository's failure rate. This rules out WSD framework interactions, hook systems, and project complexity as contributing factors.

## Experiment Methodology

### Current Methodology

The investigation has evolved through four methodology iterations:

**[Experiment-Methodology-01.md](../experiments/methodologies/Experiment-Methodology-01.md)** - Original version-boundary testing (historical)
**[Experiment-Methodology-02.md](../experiments/methodologies/Experiment-Methodology-02.md)** - Controlled trial protocol with `/context` measurements (historical)
**[Experiment-Methodology-03.md](../experiments/methodologies/Experiment-Methodology-03.md)** - Scenario-targeted commands with hoisted preloading (historical, never produced valid trials)
**[Experiment-Methodology-04.md](../experiments/methodologies/Experiment-Methodology-04.md)** - Current methodology: separated setup/analysis commands with explicit user context measurements

### Methodology Evolution

**Phase 1: Self-Report Protocol (Methodology 01)**
The original investigation used self-report methodology: trigger multi-file read operations via `/wsd:init --custom` followed by `/refine-plan`, then prompt the agent to report phantom reads.

**Phase 2: Controlled Trial Collection (Methodology 02)**
Enhanced methodology adding `/context` measurements and artifact collection via `collect_trials.py`:
1. Fresh Claude Code sessions with `/wsd:init --custom`
2. Trigger via `/refine-plan` against WSD documentation
3. Session data extraction via `/update-trial-data` preprocessing tool
4. Programmatic analysis of `trial_data.json` files across trials

**Phase 3: Scenario-Targeted Commands (Methodology 03, superseded)**
Replaced `/wsd:init --custom` with `/wsd:getid` and introduced scenario commands (`/analyze-light`, `/analyze-standard`, `/analyze-thorough`). All 9 trials succeeded due to discovery that hoisted files exceeding ~25K tokens are silently ignored and that `/context` cannot be called by agents.

**Phase 4: Separated Setup/Analysis (Methodology 04, current)**
Restructured around the discoveries from Methodology 03:
1. Scenario-specific initialization commands (`/setup-easy`, `/setup-medium`, `/setup-hard`) preload context via hoisted files
2. Explicit user `/context` calls at baseline, post-preload, and post-analysis
3. Unified `/analyze-wpd` command triggers multi-file read operations
4. Session data extraction via `/update-trial-data` preprocessing tool

### Key Findings Evolution

**Original findings** (later revised):
- Pre-2.0.59 versions appeared unaffected
- Post-2.0.59 versions showed consistent failures

**Revised understanding**:
- ALL tested versions can exhibit phantom reads
- Era 1 (2.0.59 and earlier): `[Old tool result content cleared]` mechanism
- Era 2 (2.0.60 and later): `<persisted-output>` mechanism

**Current understanding** (31-trial analysis):
- Reset Timing Theory validated with 100% prediction accuracy
- Mid-session resets (50-90%) are the critical failure condition
- No fixed token threshold exists (82K-383K range observed)

For ongoing investigation notes, see `Investigation-Journal.md`. For detailed analysis, see `docs/experiments/results/WSD-Dev-02-Analysis-1.md`, `docs/experiments/results/WSD-Dev-02-Analysis-2.md`, `docs/experiments/results/WSD-Dev-02-Analysis-3.md`, and `docs/experiments/results/Repro-Attempts-02-Analysis-1.md`.

### Limitations

The self-report methodology has inherent limitations (model incentives, introspection accuracy, non-determinism). The programmatic analysis tools address these limitations by examining session logs directly, removing the model from the detection loop. However, detecting phantom reads programmatically remains challenging—we rely on correlating context reset patterns with self-reported outcomes.

## Architecture Overview

### Repository Structure

```
├── README.md                        # User-facing documentation
├── WORKAROUND.md                    # MCP bypass workaround instructions
├── docs/
│   ├── core/
│   │   ├── PRD.md                  # This document (internal)
│   │   ├── Action-Plan.md          # Implementation checkboxlist
│   │   ├── Design-Decisions.md     # Project design rationale
│   │   ├── Investigation-Journal.md # Running log of discoveries
│   │   └── Research-Questions.md   # Catalog of research questions
│   ├── experiments/
│   │   ├── methodologies/          # Experiment protocols
│   │   ├── results/                # Analysis documents
│   │   ├── planning/               # Experiment planning docs
│   │   └── guides/                 # Analysis guides
│   ├── theories/                   # Theoretical frameworks
│   ├── mitigations/                # Workaround documentation
│   ├── read-only/                  # WSD standards (read triggers)
│   ├── tickets/
│   │   └── open/                   # WPD targets for /refine-plan
│   └── workbench/                  # Working documents
├── dev/
│   └── misc/
│       ├── example-sessions/       # Session samples (good/bad by version)
│       └── wsd-dev-02/             # 22-trial collection
│           ├── */trial_data.json   # Preprocessed trial data per trial
│           └── file_token_counts.json # Token counts for analyzed files
├── src/
│   ├── cc_version.py               # Claude Code version setting utility
│   └── collect_trials.py           # Tool for gathering trial data
└── .claude/
    └── commands/
        ├── refine-plan.md          # Trigger command
        └── update-trial-data.md    # Trial preprocessing command
```

### Key Components

**Trigger Mechanism**: Multi-file read operations that push context consumption into the danger zone. Originally discovered via the `/refine-plan` command against WSD tickets, the current methodology uses `/analyze-wpd` against a WPD in `docs/wpds/`, preceded by scenario-specific `/setup-*` commands that control pre-operation context levels via hoisted files.

**Detection Mechanism**: Python scripts that parse `.jsonl` session files and associated artifacts from `~/.claude/projects/`. Phantom read markers are not recorded in `.jsonl` files (the session log captures tool execution before context management transforms results), so detection relies on proxy indicators: context reset patterns (`cache_read_input_tokens` drops), `tool-results/` directory presence, and structured `trial_data.json` analysis.

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

A noted concern is whether a User Agent operating in a project explicitly dedicated to detecting phantom reads might behave differently (be less likely to exhibit phantom reads). The Barebones-216 experiment (Jan 27) provided strong evidence against this concern: a minimal repository with no investigation-related content reproduced phantom reads at 100% (4/4 valid trials), matching the full investigation repository. This supports the working hypothesis that the bug is at the harness/infrastructure level, not influenced by project content.

### Minimal Viable Reproduction

The initial approach used the existing WSD documentation as the multi-file read trigger. This was later supplemented by a fictional "Data Pipeline System" specification set (6 interconnected spec files plus 1 analysis target WPD = 7 Y-files, later expanded to 9 total with the addition of module-epsilon and module-phi specifications), and the Barebones-216 experiment confirmed that a minimal 20-file repository (without WSD framework) reproduces phantom reads at the same rate as the full project.

## Success Metrics

This project achieves its goals when:

1. **Documented**: README clearly explains the Phantom Reads phenomenon and links to the official issue

2. **Reproducible**: End-users can follow the instructions to trigger phantom reads on affected Claude Code versions

3. **Verifiable**: Analysis tools can programmatically detect phantom reads in session logs, providing objective evidence beyond AI self-reporting

4. **Accessible**: Instructions are clear enough for users unfamiliar with WSD to execute the reproduction experiment

5. **Mitigated**: A temporary workaround is documented and validated, allowing users to work productively while the bug remains unfixed

## Future Direction

### Achieved Goals

The following objectives from the original vision have been accomplished:

1. ✅ **Trigger conditions identified**: Reset Timing Theory provides 100% prediction accuracy on 22 trials
2. ✅ **Trial collection tools**: `/update-trial-data` preprocessor and `collect_trials.py` enable systematic data collection
3. ✅ **Mitigation strategy found**: MCP Filesystem bypass provides 100% success rate (see `WORKAROUND.md`)
4. ✅ **Quantitative analysis**: Token-based analysis across 22 trials with structured `trial_data.json` files

### Current Investigation Status

The investigation reached a major milestone on Jan 30, 2026 with the formalization of the Server-Side Variability Theory. Previously planned experiments (04M, 04B, 04F, 04G, 04C — see `docs/experiments/planning/Post-Experiment-04-Ideas.md`) have been **deprioritized** because server-side variability undermines the threshold analysis they were designed to perform. The investigation has shifted from experimental work to documentation and public reporting.

Completed experiment phases (Jan 25-26):
1. **Y Threshold Independence** (04A): Confirmed Y=57K succeeds when X≈0 — no absolute Y threshold
2. **Hoisting Behavior** (04L, 04D): Confirmed harness avoids redundant reads; hoisting is safe even under context saturation
3. **Context Window Relevance** (04K): Confirmed 1M model avoids phantom reads (diagnostic only, out of scope)

Key remaining unknowns (outside our observation boundary):
- What controls the server-side persistence decision?
- Is Anthropic's Jan 29 mitigation permanent or transient?
- Can agent recovery from `<persisted-output>` markers be made reliable?

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
