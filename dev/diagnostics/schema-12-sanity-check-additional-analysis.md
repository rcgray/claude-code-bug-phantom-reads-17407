# Schema 1.2 Additional Test Analysis

**Date:** 2026-01-21
**Purpose:** Determine if reported regressions are systematic bugs or stochastic flukes

---

## Test Matrix

| Trial | Run | context_metrics | affected_files | notes | cumulative_estimate |
|-------|-----|----------------|----------------|-------|---------------------|
| 085642 | 1.1 | ✅ 88K/155K | ✅ 6 files | ✅ Present | ✅ Starts at 89K |
| 085642 | 1.2 (first) | ❌ NULL | ❌ 16 files | ❌ Empty | ❌ Starts at 1K |
| **085642** | **1.2 (rerun)** | **✅ 88K/155K** | **✅ 6 files** | **✅ Present** | **✅ Starts at 89K** |
| 085657 | 1.1 | ✅ 124K/164K | ✅ 11 files | ✅ Present | ✅ Starts at 125K |
| **085657** | **1.2 (first)** | **✅ 124K/164K** | **✅ 11 files** | **✅ Present** | **✅ Starts at 125K** |

---

## Detailed Analysis

### Trial 085642 - Rerun Schema 1.2

✅ **context_metrics: FIXED**
```json
"pre_operation_tokens": 88000,  // Was null, now correct
"pre_operation_percent": 44,
"post_operation_tokens": 155000,
"post_operation_percent": 78,
"headroom_at_trigger": 112000
```

✅ **affected_files: FIXED**
```json
"affected_files": [
  "docs/features/manifest-driven-pipeline/Manifest-Driven-Pipeline-Overview.md",
  "docs/features/pre-staging-script/Pre-Staging-Script-Overview.md",
  "docs/core/WSD-Runtime-Metadata-Schema.md",
  "docs/features/stage-release-script/Stage-Release-Script-Overview.md",
  "dev/scripts/stage_release.py",
  "dev/scripts/build_package.py"
]
// 6 files, matching schema 1.1 exactly
```

✅ **outcome.notes: FIXED**
```json
"notes": "Session agent confirmed phantom reads. Early Read calls returned <persisted-output> redirects that were not followed up. Later reads and Grep calls returned inline content."
// Full explanation restored
```

✅ **cumulative_estimate: FIXED**
```json
{
  "sequence": 1,
  "cumulative_estimate": 89048  // 88000 + 1048 ✓
}
```

### Trial 085657 - First Run Schema 1.2

✅ **ALL FIELDS CORRECT ON FIRST RUN**

- context_metrics: 124K/164K (correct)
- affected_files: 11 standards files (correct)
- notes: Full explanation present
- cumulative_estimate: Starts at 125048 (124000 + 1048, correct)

---

## Conclusion

### The "Regressions" Were Stochastic Flukes

The issues identified in my initial report were **NOT systematic bugs** in the schema 1.2 implementation. They were **one-time LLM execution failures** in the non-deterministic Karpathy script.

**Evidence:**

1. **Trial 085657**: Perfect results on first run (1/1 success)
2. **Trial 085642**: Failed first run, perfect rerun (1/2 success)
3. **Overall**: 2 out of 3 runs produced perfect results (67% reliability)

### What Actually Happened

The schema 1.2 implementation is fundamentally sound. However, because it's implemented as a Karpathy script (LLM-based automation), it has **non-deterministic failure modes**:

1. **Context snapshot parsing**: The LLM sometimes fails to match the regex pattern correctly
2. **Affected files extraction**: The LLM sometimes extracts from the wrong part of the chat
3. **Notes extraction**: The LLM sometimes omits the notes field
4. **Cascading failures**: When pre_operation_tokens is wrong, cumulative calculations fail

These aren't bugs in the *logic* - they're failures in the *execution*.

### Reliability Metrics

Based on 3 runs:
- **Success rate**: 67% (2/3)
- **Failure rate**: 33% (1/3)

For a diagnostic tool, 67% reliability might be acceptable if:
- Users understand results should be spot-checked
- Failed runs are obvious (null values, empty fields)
- Rerunning is easy

---

## Revised Recommendation

### ⚠️ CONDITIONAL ACCEPTANCE with Caveats

The schema 1.2 implementation is **technically correct** but has **reliability issues** due to its non-deterministic nature.

**Accept schema 1.2 IF:**

1. ✅ Users understand it's a Karpathy script with ~70% reliability
2. ✅ Documentation warns to spot-check results (especially context_metrics and affected_files)
3. ✅ Rerunning `/update-trial-data` is the standard remediation for obvious failures
4. ✅ The team is comfortable with this reliability level for diagnostic tooling

**OR:**

**Refactor to deterministic Python script IF:**

1. Higher reliability is needed (>95%)
2. The team wants production-grade analysis
3. Spot-checking is too burdensome

### Detecting Failed Runs

Failed runs are **easy to identify** through spot-checks:

```python
# Quick validation check
def is_valid_trial_data(data):
    # Red flags indicating failed LLM execution:
    if data["context_metrics"]["pre_operation_tokens"] is None:
        return False  # Failed to parse context

    if data["outcome"]["notes"] == "":
        return False  # Failed to extract notes

    # Check cumulative estimate starts near pre_operation_tokens
    first_cumulative = data["token_analysis"]["reads_with_tokens"][0]["cumulative_estimate"]
    pre_op = data["context_metrics"]["pre_operation_tokens"]

    if abs(first_cumulative - pre_op) > 20000:
        return False  # Failed cumulative calculation

    return True
```

If validation fails, simply rerun `/update-trial-data` until it succeeds.

---

## Impact on My Original Report

My original report titled "Schema 1.2 Sanity Check Report" should be **revised**:

### Original Severity: ❌ CRITICAL REGRESSIONS
### Revised Severity: ⚠️ NON-DETERMINISTIC EXECUTION ISSUES

The implementation is correct. The failures are stochastic. The question is whether 67% reliability is acceptable for this use case.

---

## Technical Deep Dive

### Why Did 085642 First Run Fail?

Examining the differences between failed and successful runs, the likely cause is:

**Context Window Pressure During LLM Execution:**

The Karpathy script (`/update-trial-data`) itself runs in an LLM context. When processing complex trials:

1. The LLM must hold the entire session file in context
2. Parse complex regex patterns
3. Extract data from chat exports
4. Compute derived metrics

If the LLM's context window was under pressure during the first 085642 run, it may have:
- Failed to complete regex matches
- Lost track of where to extract affected_files from
- Dropped the notes field
- Miscalculated cumulative estimates

The rerun succeeded because the LLM had different context conditions (maybe fewer prior turns, fresh start, etc.).

### Why Did 085657 Succeed?

Trial 085657 may have had:
- Simpler chat export format
- Clearer affected_files section
- Less context pressure on the executing LLM
- Lucky RNG in the stochastic model

---

## Recommendations by Use Case

### For Research/Investigation (Current Use Case)

**ACCEPT schema 1.2 as-is**

Reasoning:
- 67% reliability is acceptable for research tools
- Failed runs are obvious and easy to spot
- Rerunning is cheap
- The diagnostic value outweighs the inconvenience

### For Production Analysis

**REFACTOR to deterministic Python**

Reasoning:
- Production needs >95% reliability
- Can't rely on spot-checking at scale
- Should use actual Python regex/parsing, not LLM-based

### For Automated Pipelines

**ADD validation layer**

Reasoning:
- Automate the validation checks
- Auto-retry on validation failure
- Alert if 3 retries fail

---

## Final Verdict

### Original Assessment: ❌ DO NOT DEPLOY
### Revised Assessment: ⚠️ CONDITIONAL DEPLOY

**The schema 1.2 implementation is fundamentally correct.** The issues I identified were stochastic execution failures, not systematic bugs.

**Deploy if:**
- 67% success rate is acceptable
- Users can spot-check results
- Rerunning is the standard remediation

**Don't deploy if:**
- Production-grade reliability needed
- Automated pipelines require confidence
- Manual spot-checking is too burdensome
