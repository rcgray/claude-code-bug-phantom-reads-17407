# WSD-Dev-02 Trial Collection Analysis

**Date**: 2026-01-19
**Collection**: `dev/misc/wsd-dev-02/`
**Trials Analyzed**: 7
**Analysis Workscope**: 20260119-163530

---

## Trial Collection Overview

Seven trials were conducted using Experiment-Methodology-02 against the WSD Development project, triggering multi-file read operations via the `/refine-plan` command.

### Results Summary

| Trial ID | Outcome | Pre-Op | Headroom | Resets | Reset Pattern |
|----------|---------|--------|----------|--------|---------------|
| 20260119-131802 | SUCCESS | 85K (43%) | 115K | 2 | EARLY + LATE |
| 20260119-132353 | FAILURE | 110K (55%) | 90K | 4 | EARLY + MID/LATE |
| 20260119-133027 | FAILURE | 86K (43%) | 114K | 4 | EARLY + MID/LATE |
| 20260119-133726 | FAILURE | 86K (43%) | 114K | 2 | LATE CLUSTERED |
| 20260119-140145 | FAILURE | 83K (41%) | 117K | 3 | EARLY + MID/LATE |
| 20260119-140906 | FAILURE | 96K (48%) | 104K | 4 | EARLY + MID/LATE |
| 20260119-142117 | SUCCESS* | 87K (43%) | 113K | 2 | EARLY + LATE |

*Trial 142117 showed context cleared on second `/context` call but no phantom reads were self-reported.

---

## Key Finding: Reset Timing Theory

Analysis revealed that **reset timing pattern** is more predictive than either headroom or reset count alone.

### Pattern Classification

| Pattern | Description | Risk | Trials |
|---------|-------------|------|--------|
| **EARLY + LATE** | First reset <50%, last reset >90%, no mid-session | LOW | 131802, 142117 |
| **EARLY + MID/LATE** | Early reset plus one or more mid-session (50-90%) | HIGH | 132353, 133027, 140145, 140906 |
| **LATE CLUSTERED** | All resets >80% and close together | HIGH | 133726 |

### Critical Evidence: Trial 133726

This trial had identical metrics to successful trials (86K pre-op, 114K headroom, 2 resets) but FAILED due to LATE CLUSTERED timing (resets at 83% and 97%). This proves timing matters more than count or headroom.

Full theory documented in: `docs/core/Reset-Timing-Theory.md`

---

## File Read Data Extraction

### Capability Confirmed

The session `.jsonl` files contain complete records of all `Read` tool invocations, including:
- **File paths**: Full absolute paths to each file read
- **Sequence**: Line numbers in the session file indicate order
- **Batching**: Multiple reads in the same assistant message represent parallel operations

### Extraction Method

Read operations are stored in the session file as `tool_use` blocks within `assistant` message content:

```json
{
  "type": "assistant",
  "message": {
    "content": [{
      "type": "tool_use",
      "name": "Read",
      "input": {
        "file_path": "/path/to/file.md"
      }
    }]
  }
}
```

### Read Counts by Trial

| Trial | Outcome | Read Operations |
|-------|---------|-----------------|
| 20260119-131802 | SUCCESS | 9 |
| 20260119-132353 | FAILURE | 19 |
| 20260119-133027 | FAILURE | 20 |
| 20260119-133726 | FAILURE | 12 |
| 20260119-140145 | FAILURE | 17 |
| 20260119-140906 | FAILURE | 13 |
| 20260119-142117 | SUCCESS | 11 |

**Observation**: Failed trials tend to have more Read operations (12-20) than successful trials (9-11). This could indicate:
- More aggressive investigation → more context pressure → more resets
- Or simply correlation, not causation

### Unique Files Across All Trials

31 unique file paths were read across all 7 trials, including:
- Work journals (`dev/journal/archive/`)
- Feature specifications (`docs/features/`)
- Core documentation (`docs/core/`)
- Source scripts (`dev/scripts/`)
- Persisted tool outputs (`tool-results/`) — indicates some trials followed up on persisted reads

---

## Next Steps for Investigation

### Priority 1: Additional Trials (Essential)

The current 7-trial dataset is too small for statistical confidence. Recommend:
- **10-15 additional trials** using identical methodology
- Same build, model, project, commands, and target WPD
- Goal: Validate Reset Timing Theory pattern classification

### Priority 2: File Token Count Collection

**User action required**: Anthropic API call to get token counts for all files involved.

**Rationale**: Understanding exact token counts would help:
1. Calculate whether there's a consistent reset threshold
2. Determine if file size correlates with reset timing
3. Identify potential "safe batch sizes" for multi-file operations

**Capability**: The session files contain all file paths read, so a complete list can be extracted programmatically.

### Priority 3: Reset-to-Read Correlation

Map reset timing against specific read operations:
- Which files were read immediately before each reset?
- Are certain file sizes more likely to trigger resets?
- Does reading a persisted output (follow-up read) correlate with reset occurrence?

### Priority 4: Mitigation Testing

If Reset Timing Theory holds, test strategies to achieve "EARLY + LATE" pattern:
- Pre-warm sessions with throwaway context consumption
- Break operations into smaller batches
- Strategic pauses between read operations

---

## Data Collection for Token Count Request

To support the User's token count collection effort, the following can be extracted from current trial data:

1. **Complete file list**: All unique file paths read across all trials
2. **Per-trial file lists**: Which files were read in each specific trial
3. **Read order**: Sequence of files within each trial

**Note**: Some reads target `tool-results/` persisted outputs, which are ephemeral files created during the session. These would need special handling for token counting (content may not still exist).

---

## Open Questions

1. **What determines reset timing?** Is it threshold-based, time-based, or operation-triggered?

2. **Why do identical workloads produce different patterns?** Same `/refine-plan` command yields different reset timing across trials.

3. **Are certain files "reset triggers"?** Does file size or content type affect when resets occur?

4. **Does read count causally affect outcome?** Or is higher read count simply a symptom of the investigation process before failure?

5. **What is the base context level (~21K)?** Consistently all resets drop to approximately 21K tokens. What comprises this baseline?

---

## Appendix: Reset Timing Details

### Reset Position by Trial

| Trial | Outcome | Reset Positions (% through session) |
|-------|---------|-------------------------------------|
| 131802 | SUCCESS | 42%, 97% |
| 132353 | FAILURE | 40%, 64%, 81%, 98% |
| 133027 | FAILURE | 30%, 62%, 74%, 98% |
| 133726 | FAILURE | 83%, 97% |
| 140145 | FAILURE | 29%, 75%, 98% |
| 140906 | FAILURE | 47%, 78%, 91%, 98% |
| 142117 | SUCCESS | 45%, 98% |

### Token Progression Patterns

**SUCCESS Pattern** (Trial 131802):
```
Early phase: 33K → 77K → 82K
RESET (42%): 82K → 21K
Mid phase: 21K → 86K → 122K → 144K
RESET (97%): 144K → 21K
```

**FAILURE Pattern - Mid-Session Resets** (Trial 132353):
```
Early phase: 17K → 77K → 99K
RESET (40%): 99K → 21K
Continued: 21K → 132K
RESET (64%): 132K → 21K
Continued: 21K → 147K
RESET (81%): 147K → 21K
Final: 21K → 148K
RESET (98%): 148K → 21K
```

**FAILURE Pattern - Late Clustered** (Trial 133726):
```
Long build-up: 17K → 77K → 108K → 134K
RESET (83%): 134K → 21K
Immediately: 21K → 136K
RESET (97%): 136K → 21K
```

---

*Analysis performed: 2026-01-19*
*Workscope ID: 20260119-163530*
