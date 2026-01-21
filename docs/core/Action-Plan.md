# Action Plan

This document contains the implementation checkboxlist for the Claude Code Phantom Reads Reproduction project. For project context and goals, see `docs/core/PRD.md`.

The following are the steps for implementing the project, where the full list is split over two files:

- **Action Plan Archive**: `docs/references/Action-Plan-Archive.md` - Completed phases
- **Action Plan**: `docs/core/Action-Plan.md` - In-progress and future phases


## Phase 0: Blocking Tasks

- [x] **0.1** - Remove mentions of `/start-trial` command (see `docs/tickets/closed/update-session-analysis-spec-use-workscope-id.md`)
- [x] **0.2** - Investigate reads of missing files in our pre-processing of trials (see `docs/tickets/closed/investigate-trial-data-failed-read-recording.md`)
- [ ] **0.3** - Add NLP assessment to trial analysis in `/update-json-data` (see `docs/tickets/open/add-nlp-outcome-detection-to-trial-data-extraction.md`)

## Phase 1: Open-Ended Investigation

- [x] **1.1** - Create `docs/core/Investigation-Journal.md` and `docs/core/Experiment-Methodology-01.md`
- [x] **1.2** - Collect samples of success and failure cases, store in `dev/misc/example-sessions`
  - [x] **1.2.1** - Good/Bad examples for various builds (`2.0.58`, `2.0.59`, `2.0.60`, `2.1.3`, `2.1.6`)
- [*] **1.3** - Examine success/failure cases to find log evidence of phantom reads
  - [x] **1.3.1** - Create `docs/core/Example-Session-Analysis.md`
- [x] **1.4** - Publish to Github
- [x] **1.5** - Create feature plan for reproduction environment (Phase 3)

## Phase 2: Explore Temporary Workarounds

- [x] **2.1** - Brainstorm ideas and draft `docs/core/Possible-Workarounds.md`
- [x] **2.2** - Test "Warning in Onboarding" approach
- [x] **2.3** - Test "PostToolUse Detection Hook" approach
- [-] **2.4** - Test "Proof-of-Work Verification" approach
- [x] **2.5** - Test "PreToolUse Read Override" approach
- [x] **2.6** - Test "MCP Server Replacement" approach - SUCCESS
  - [x] **2.6.1** - Create `WORKAROUNDS.md` file

## Phase 3: Reproduction Environment - Three Specs

- [x] **3.1** - Create Reproduction-Specs-Collection feature (see `docs/features/reproduction-specs-collection/Reproduction-Specs-Collection-Overview.md`)
Collect-Trials-Script-Overview.md`)
- [x] **3.2** - Execute manual reproduction trial of the three specs created in previous Phase
  - [x] **3.2.1** - Run `/wsd:init --custom` in a fresh Claude Code session
  - [x] **3.2.2** - Run `/refine-plan` against the trigger WSDs
  - [x] **3.2.3** - Prompt agent for phantom read self-report per methodology
  - [x] **3.2.4** - Document results
  - [x] **3.2.5** - Save chat export and session `.jsonl` files in `dev/misc/self-examples`
- [x] **3.4** - Evaluate reproduction sufficiency
  - [x] **3.4.1** - Assess whether phantom reads occurred in the trials where they were expected
- [x] **3.5** - Update Documentation
  - [x] **3.5.1** - Ensure that `docs/core/Investigation-Journal.md` records the approach and results of Reproduction-Specs-Collection investigation
  - [x] **3.5.2** - Update `README.md` to reflect our current understanding of the issue and include directions on end-users running their own tests.
  - [x] **3.5.3** - Ensure that there is a clear `docs/core/Experiment-Methodology-#.md` that matches the most recent experiments run
  - [*] **3.5.4** - Refine `docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md` based on our latest findings and theory to ensure we're creating effective analysis scripts.

## Phase 4: Analysis Tools

- [x] **4.1** - Create the `cc_version.py` script (see `docs/features/cc-version-script/CC-Version-Script-Overview.md`)
- [x] **4.2** - Create the `collect_trials.py` script (see `docs/features/collect-trials-script/Collect-Trials-Script-Overview.md`)
- [x] **4.3** - Design and create analysis scripts feature
- [x] **4.4** - Run sample experiments as we would expect end-users to run them. Evaluate analysis scripts results.
- [ ] **4.5** - Update Documentation
  - [ ] **4.5.1** - Ensure that `docs/core/Investigation-Journal.md` records the approach and results of our Analysis Scripts.
  - [ ] **4.5.2** - Update `README.md` to reflect our current understanding of the issue and include directions on end-users running their own tests AND new analysis tools
  - [ ] **4.5.3** - Ensure that there is a clear `docs/core/Experiment-Methodology-#.md` that matches the most recent experiments run.


