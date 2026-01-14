# Update Session Analysis Spec to Use Workscope ID

**Date Reported:** 2026-01-13
**Status**: Open

## Problem Description

The `docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md` specification currently defines a `/start-trial` command and "Trial Identifier" pattern for marking sessions as trials. However, the existing `/wsd:init --custom` command already generates a Workscope ID (`YYYYMMDD-HHMMSS` format) that serves the same purpose.

Since `/wsd:init --custom` is already part of the reproduction steps for each trial, every trial session automatically contains a Workscope ID. Creating a separate `/start-trial` command is redundant and adds unnecessary complexity.

## Current State

The specification references the `/start-trial` command and "Trial Identifier" in:

1. **Overview section**: Mentions `/start-trial` command for session marking
2. **Purpose section**: References `/start-trial` for trial identification
3. **Trial Identification System section**: Defines "Trial Identifier" format and `/start-trial` command behavior
4. **Collection Algorithm**: Uses `extract_trial_id()` function with "Trial Identifier" pattern
5. **Error Handling**: References `/start-trial` in error messages
6. **Testing Scenarios**: References `/start-trial` in test cases
7. **Best Practices**: Recommends running `/start-trial` after `/wsd:init --custom`
8. **Examples**: Shows `/start-trial` in workflow examples
9. **FIP Phase 1.2**: Task to create the `/start-trial` command

## Proposed Solution

Replace all references to `/start-trial` and "Trial Identifier" with the existing Workscope ID mechanism:

1. **Pattern change**: `Trial Identifier: YYYYMMDD-HHMMSS` → `Workscope ID: YYYYMMDD-HHMMSS`
2. **Function rename**: `extract_trial_id()` → `extract_workscope_id()`
3. **Remove command**: Eliminate all references to `/start-trial` command
4. **Update workflow**: Show that `/wsd:init --custom` already provides the identifier
5. **Remove FIP task 1.2**: The command creation task is no longer needed

## Expected Benefits

1. **Simpler workflow**: Investigators don't need to run an extra command
2. **No new command to maintain**: Reduces project complexity
3. **Consistent naming**: Uses existing Workscope ID terminology throughout
4. **Already works**: Current sample data already uses Workscope ID pattern

## Risk Assessment

**Low risk**: This is a documentation-only change. No code has been written yet for the `/start-trial` command or collection scripts, so there's nothing to migrate.

## Related Files

**Primary Target:**
- `docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md` - Main specification to update

**Reference (already updated):**
- `docs/core/Example-Session-Analysis.md` - Already uses Workscope ID pattern

## Developer Notes

This ticket emerged from the session file structure investigation where we discovered that the Workscope ID already appears in both session files and chat exports, providing the same linking capability that was proposed for the Trial Identifier.

The spec should be rewritten cleanly using Workscope ID as if that was the original design, following Rule 5.2 (no backward compatibility references).

## Action Plan

### Phase 1: Update Trial Identification System

- [ ] **1.1** - Update Overview section
  - [ ] **1.1.1** - Remove mention of `/start-trial` command
  - [ ] **1.1.2** - Reference Workscope ID from `/wsd:init` as the linking mechanism

- [ ] **1.2** - Rewrite Trial Identification System section
  - [ ] **1.2.1** - Rename section to "Workscope ID System" or similar
  - [ ] **1.2.2** - Update identifier format to `Workscope ID: YYYYMMDD-HHMMSS`
  - [ ] **1.2.3** - Remove `/start-trial` command subsection entirely
  - [ ] **1.2.4** - Explain that `/wsd:init` generates the identifier automatically

### Phase 2: Update Algorithm Code Examples

- [ ] **2.1** - Update collection algorithm
  - [ ] **2.1.1** - Rename `extract_trial_id()` to `extract_workscope_id()`
  - [ ] **2.1.2** - Update regex pattern to match `Workscope ID:`
  - [ ] **2.1.3** - Update variable names (trial_id → workscope_id)

- [ ] **2.2** - Update file naming references
  - [ ] **2.2.1** - Keep `trial-{YYYYMMDD-HHMMSS}.jsonl` naming (trial is still appropriate for results)

### Phase 3: Update Prose and Examples

- [ ] **3.1** - Update Error Handling section
  - [ ] **3.1.1** - Remove "Run /start-trial" guidance from error messages
  - [ ] **3.1.2** - Reference Workscope ID in "No Trial Sessions Found" error

- [ ] **3.2** - Update Testing Scenarios section
  - [ ] **3.2.1** - Remove `/start-trial` from test descriptions
  - [ ] **3.2.2** - Update workflow to show Workscope ID is automatic

- [ ] **3.3** - Update Best Practices section
  - [ ] **3.3.1** - Remove recommendation to run `/start-trial`
  - [ ] **3.3.2** - Note that `/wsd:init --custom` provides the identifier

- [ ] **3.4** - Update Examples section
  - [ ] **3.4.1** - Remove `/start-trial` from Example 1 workflow
  - [ ] **3.4.2** - Show that Workscope ID output comes from `/wsd:init`

### Phase 4: Update Feature Implementation Plan

- [ ] **4.1** - Remove obsolete FIP tasks
  - [ ] **4.1.1** - Delete Phase 1.2 (Create `/start-trial` command)
  - [ ] **4.1.2** - Remove task 4.1.1 (Add `/start-trial` step to methodology)
  - [ ] **4.1.3** - Remove task 5.1.1 (Run `/start-trial` and verify format)

- [ ] **4.2** - Renumber remaining FIP tasks if needed

