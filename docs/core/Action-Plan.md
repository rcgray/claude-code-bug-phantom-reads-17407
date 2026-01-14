# Action Plan

This document contains the implementation checkboxlist for the Claude Code Phantom Reads Reproduction project. For project context and goals, see `docs/core/PRD.md`.

The following are the steps for implementing the project, where the full list is split over two files:

- **Action Plan Archive**: `docs/references/Action-Plan-Archive.md` - Completed phases
- **Action Plan**: `docs/core/Action-Plan.md` - In-progress and future phases


## Phase 0: Blocking Tasks

- [ ] **0.1** - Remove mentions of `/start-trial` command (see `docs/tickets/open/update-session-analysis-spec-use-workscope-id.md`)

## Phase 1: Reproduction Environment - Trigger Ticket

- [ ] **1.1** - Create trigger ticket using `/open-ticket` command
  - [ ] **1.1.1** - Design ticket scope (e.g., "Add Ruby language support to WSD")
  - [ ] **1.1.2** - Execute `/open-ticket` to generate the ticket with appropriate checkboxlist
  - [ ] **1.1.3** - Review generated ticket for sufficient complexity to trigger multi-file reads

## Phase 2: Reproduction Environment - Initial Validation

- [ ] **2.1** - Execute manual reproduction trial
  - [ ] **2.1.1** - Run `/wsd:init --custom` in a fresh Claude Code session
  - [ ] **2.1.2** - Run `/refine-plan` against the trigger ticket created in Phase 1
  - [ ] **2.1.3** - Prompt agent for phantom read self-report per methodology
  - [ ] **2.1.4** - Document trial results in Work Journal
- [ ] **2.2** - Evaluate reproduction sufficiency
  - [ ] **2.2.1** - Assess whether phantom reads occurred in the trial
  - [ ] **2.2.2** - If successful: document which files were affected and proceed to Phase 4
  - [ ] **2.2.3** - If unsuccessful: proceed to Phase 3 to add dummy project complexity

## Phase 3: Reproduction Environment - Dummy Project (Conditional)

- [ ] **3.1** - Design dummy project
  - [ ] **3.1.1** - Determine minimal project type (simple CLI tool recommended)
  - [ ] **3.1.2** - Design file structure to maximize read operations during `/refine-plan`
- [ ] **3.2** - Implement dummy project
  - [ ] **3.2.1** - Create source files with inter-dependencies
  - [ ] **3.2.2** - Create associated documentation and specifications
  - [ ] **3.2.3** - Create a ticket targeting the dummy project for `/refine-plan`
- [ ] **3.3** - Re-validate reproduction with dummy project
  - [ ] **3.3.1** - Execute manual reproduction trial using dummy project ticket
  - [ ] **3.3.2** - Document results and confirm phantom reads are reproducible

## Phase 4: Analysis Tools

- [ ] **4.1** - Create analysis scripts feature (see `docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md`)

## Phase 5: Experiment Execution

- [ ] **5.1** - Create `/results` directory structure
  - [ ] **5.1.1** - Create `/results/README.md` explaining the directory purpose and contents
  - [ ] **5.1.2** - Create placeholder structure for exported session logs
- [ ] **5.2** - Execute reproduction trials across Claude Code versions
  - [ ] **5.2.1** - Set up environment for version 2.0.58 (control - expected no failures)
  - [ ] **5.2.2** - Run 2+ trials on 2.0.58, export session logs to `/results`
  - [ ] **5.2.3** - Set up environment for version 2.0.59 (regression boundary)
  - [ ] **5.2.4** - Run 2+ trials on 2.0.59, export session logs to `/results`
  - [ ] **5.2.5** - Set up environment for current version
  - [ ] **5.2.6** - Run 2+ trials on current version, export session logs to `/results`
- [ ] **5.3** - Analyze captured sessions
  - [ ] **5.3.1** - Run analysis tool against all exported session logs
  - [ ] **5.3.2** - Compare programmatic detection results with self-report results
  - [ ] **5.3.3** - Document any discrepancies between detection methods
- [ ] **5.4** - Document experiment results
  - [ ] **5.4.1** - Create `/results/FINDINGS.md` summarizing reproduction results

## Phase 6: Documentation and Publication

- [ ] **6.1** - Draft README.md
  - [ ] **6.1.1** - Write issue overview section linking to GitHub Issue #17407
  - [ ] **6.1.2** - Write symptoms and impact section explaining how phantom reads manifest
  - [ ] **6.1.3** - Write version history section summarizing the regression boundary findings
  - [ ] **6.1.4** - Write reproduction steps section with environment setup and trial execution
  - [ ] **6.1.5** - Write analysis tools section explaining how to use the detection scripts
  - [ ] **6.1.6** - Write results directory section explaining the `/results` folder structure
- [ ] **6.2** - Documentation polish
  - [ ] **6.2.1** - Review Experiment-Methodology.md for accuracy after experiment execution
  - [ ] **6.2.2** - Ensure all user-facing documentation is free of internal process references

## Phase 7: Validation and Cleanup

- [ ] **7.1** - End-to-end validation
  - [ ] **7.1.1** - Fresh clone of repository to clean directory
  - [ ] **7.1.2** - Follow README instructions as a new user would
  - [ ] **7.1.3** - Verify reproduction steps work without additional guidance
  - [ ] **7.1.4** - Verify analysis tools work on exported session logs
- [ ] **7.2** - Repository cleanup
  - [ ] **7.2.1** - Review for any files that should not be published
  - [ ] **7.2.2** - Verify `.gitignore` excludes appropriate files
  - [ ] **7.2.3** - Final review of repository structure against PRD architecture
