# Add NLP-Based Outcome Detection to Trial Data Extraction

**Date Reported:** 2026-01-21
**Status**: Open

## Problem Description

The `/update-trial-data` command's outcome detection logic has a regression bug introduced when the command was refactored from a Karpathy script (LLM-interpreted instructions) to a traditional Python script (`dev/karpathy/extract_trial_data.py`). The Python script uses simple substring matching to determine whether a trial resulted in SUCCESS or FAILURE, which fails to handle natural language nuances.

**Example failure case:**

The Session Agent responded: "No, I did not experience the phantom read issue during this session."

- The substring `"no phantom read"` is NOT present (actual text has "No, I did not experience the phantom read")
- The substring `"phantom read"` IS present (matches "the phantom read issue")
- Result: Incorrectly classified as FAILURE instead of SUCCESS

This demonstrates that semantic understanding is required for outcome detection—exactly the kind of task that LLMs excel at and traditional scripts cannot reliably handle.

## User Journey & Integration

**Entry Point:** User runs `/update-trial-data <trial-folder-path>` to generate structured analysis data.

**Trigger Conditions:** When processing a trial folder containing a chat export with the Session Agent's self-reported outcome.

**Integration Points:** The `extract_trial_data.py` script handles deterministic extraction; the outcome detection should be performed by the executing LLM agent.

**Success Indicators:** The `trial_data.json` file contains:
- The correct `self_reported` outcome that matches what the Session Agent actually stated
- A meaningful `notes` field summarizing the Session Agent's experience

**Current Issues:**

1. **False Negatives**: SUCCESS trials are incorrectly classified as FAILURE when the agent discusses "phantom reads" or "persisted-output" while explaining they didn't experience them.

2. **Substring Limitations**: The current logic cannot distinguish between "I experienced phantom reads" and "I did not experience phantom reads".

3. **Lost LLM Advantage**: By freezing the entire command into a Python script, we lost the NLP capabilities that made the original Karpathy script robust.

4. **Empty Notes Field**: Schema 1.2 sets `notes: ""` by default, losing the detailed contextual notes that earlier schemas extracted (e.g., "Agent confirmed phantom reads on all 11 standards files" or "Agent explicitly stated: 'No, I did not experience the phantom read issue'"). Extracting meaningful summary notes also requires semantic understanding.

## Suspected Cause

The refactoring that introduced `dev/karpathy/extract_trial_data.py` moved ALL extraction logic into Python, including the outcome detection which requires semantic understanding. The Python implementation uses simple pattern matching:

```python
if "no phantom read" in lower_chat or "received inline" in lower_chat:
    self_reported = "SUCCESS"
elif "phantom read" in lower_chat or "persisted-output" in lower_chat:
    self_reported = "FAILURE"
```

This approach is fundamentally inadequate for understanding natural language statements about whether phantom reads occurred.

## Investigation & Analysis

**Sanity Check Results (Trial 20260119-131802):**

| Version               | Outcome Detected | Actual Outcome | Correct? |
| --------------------- | ---------------- | -------------- | -------- |
| Schema 1.0 (Karpathy) | SUCCESS          | SUCCESS        | ✅        |
| Schema 1.2 (Python)   | FAILURE          | SUCCESS        | ❌        |

**Chat Export Evidence:**
```
Line 659: ⏺ No, I did not experience the phantom read issue during this session.
Line 673: did not receive any <persisted-output> redirections that would have required
```

The Session Agent explicitly stated SUCCESS, but the Python script's substring matching detected "phantom read" and "persisted-output" in these denial statements and incorrectly classified as FAILURE.

## Proposed Solution

Implement a **hybrid approach** that leverages each tool for what it does best:

| Task                                | Handler       | Rationale                           |
| ----------------------------------- | ------------- | ----------------------------------- |
| Parse JSONL structure               | Python script | Deterministic, structured data      |
| Track token progression             | Python script | Numerical comparison                |
| Detect context resets               | Python script | Threshold-based logic               |
| Match tool_use → tool_result        | Python script | ID matching                         |
| Detect read success/failure         | Python script | Check for `<tool_use_error>` tag    |
| **Determine self-reported outcome** | **LLM agent** | **Requires semantic understanding** |
| **Extract contextual notes**        | **LLM agent** | **Requires summarization ability**  |

### Implementation Approach

1. **Update `extract_trial_data.py`**: Output `"self_reported": "PENDING_NLP"` and `"notes": "PENDING_NLP"` instead of attempting pattern-based detection or leaving notes empty

2. **Update `/update-trial-data` command**: After running the Python script, the executing agent reads the chat export and:
   - Determines the actual outcome using its NLP capabilities
   - Extracts a concise summary note describing the Session Agent's experience

3. **Agent updates `trial_data.json`**: Replace both `"PENDING_NLP"` placeholders with the determined values

## Expected Benefits

1. **Accurate Classification**: LLM can understand negation, context, and nuance in natural language

2. **Robust to Phrasing Variations**: No need to enumerate all possible ways an agent might report success/failure

3. **Maintainable**: No complex regex or pattern lists to maintain

4. **Leverages Tool Strengths**: Python handles structured data; LLM handles semantic understanding

5. **Informative Notes**: LLM can extract and summarize relevant details (affected files, explicit statements) that provide context for analysis

## Risk Assessment

**Low Risk**: This is a fix to a diagnostic/analysis tool, not production code.

**Mitigation**:
- The Python script still handles all deterministic extraction correctly
- Only the outcome field changes behavior
- Easy to validate by comparing against known trial outcomes

## Related Files

**Primary Implementation:**
- `.claude/commands/update-trial-data.md` - Command definition (needs update)
- `dev/karpathy/extract_trial_data.py` - Helper script (needs update)

**Test Data:**
- `dev/experiments/schema-12-sanity-check/` - Contains test files showing the regression
- `dev/misc/wsd-dev-02/20260119-131802/` - Trial that demonstrates the bug

**Documentation:**
- `docs/tickets/closed/investigate-trial-data-failed-read-recording.md` - Original ticket that introduced the regression
- `docs/archive/trial-data-failed-read-investigation-findings.md` - Investigation findings

## Developer Notes

This issue was discovered during a sanity check of the Schema 1.2 upgrade. The file read success/failure tracking (the primary goal of the original ticket) works correctly. Only the outcome detection regressed.

The hybrid approach aligns with the project's philosophy of using "Karpathy scripts" for tasks requiring NLP while using traditional scripts for deterministic operations. This ticket restores that balance.

## Implementation Plan

### Phase 1: Update Helper Script

- [x] **1.1** - Modify `extract_trial_data.py` to output `"self_reported": "PENDING_NLP"` instead of attempting pattern detection
- [x] **1.2** - Modify `extract_trial_data.py` to output `"notes": "PENDING_NLP"` instead of empty string
- [x] **1.3** - Remove the pattern-based outcome detection code from the Python script
- [x] **1.4** - Add a comment explaining that outcome and notes fields are handled by the executing agent

### Phase 2: Update Command Definition

- [x] **2.1** - Update `/update-trial-data` command to include post-script NLP analysis step
- [x] **2.2** - Add instructions for the agent to read the chat export file
- [x] **2.3** - Add instructions for determining SUCCESS/FAILURE/UNKNOWN based on semantic analysis of the Session Agent's response
- [x] **2.4** - Add instructions for extracting a concise summary note describing the Session Agent's experience (e.g., which files were affected, explicit statements made)
- [x] **2.5** - Add instructions to update `trial_data.json` with the determined outcome and notes

### Phase 3: Validation

- [-] **3.1** - Test on Trial 20260119-131802 (known regression case) - should now detect SUCCESS
- [-] **3.2** - Test on a known FAILURE trial to ensure correct detection
- [-] **3.3** - Test on a trial with ambiguous outcome to verify UNKNOWN handling
