# Context Reset Analysis

This document tracks the investigation into **context resets** as a potential mechanism underlying phantom reads in Claude Code. The analysis examines the `cache_read_input_tokens` field in session files to understand how context management relates to phantom read occurrence.

**Status**: Active investigation
**Related**: [Investigation-Journal.md](Investigation-Journal.md), [Example-Session-Analysis.md](Example-Session-Analysis.md)

---

## Executive Summary

Analysis of session files across Era 1 (2.0.58) and Era 2 (2.1.6) reveals a consistent correlation between **context reset frequency** and **phantom read occurrence**. Sessions with phantom reads exhibit approximately 2x the number of context resets compared to successful sessions.

| Session | Context Resets | Phantom Reads? |
|---------|---------------|----------------|
| 2.0.58-good | 1 | No |
| 2.0.58-bad | 3 | Yes |
| 2.1.6-good | 2 | No |
| 2.1.6-bad | 4 | Yes |

This correlation holds across both eras despite different phantom read mechanisms (`[Old tool result content cleared]` vs `<persisted-output>`), suggesting context resets may be a fundamental factor in phantom read occurrence.

---

## Background

### Discovery Context

While analyzing Era 1 (2.0.58) session files for the phantom reads investigation, we discovered that the `cache_read_input_tokens` field in assistant messages shows dramatic drops - "context resets" - that correlate with phantom read reports.

### What is a Context Reset?

A **context reset** occurs when the `cache_read_input_tokens` value drops significantly (>10,000 tokens) between consecutive assistant messages. This indicates the system cleared older context to make room for new content.

All observed resets drop to approximately **~20,000 tokens**, which appears to be the "base" level representing the persistent system prompt and command definitions.

### The Hypothesis

Context resets occur when the system clears older tool results to manage the context window. When this happens:

1. The session `.jsonl` file has ALREADY recorded the actual file content
2. But the model's context window is cleared of that content
3. The model receives a placeholder marker instead (`[Old tool result content cleared]` or `<persisted-output>`)

**More resets = more opportunities for critical file content to be cleared before the model processes it = higher phantom read risk.**

---

## Findings

### Era 1 Analysis (2.0.58)

**Sample files**: `dev/misc/session-examples/2.0.58-good/` and `2.0.58-bad/`

| Session | Resets | Reset Points | Base Level |
|---------|--------|--------------|------------|
| 2.0.58-good | 1 | Line 36 (82K → 20K) | ~20K |
| 2.0.58-bad | 3 | Lines 36, 57, 69 | ~20K |

The bad session had 3x the resets of the good session. The agent in the bad session explicitly reported seeing `[Old tool result content cleared]` markers for multiple files.

### Era 2 Analysis (2.1.6)

**Sample files**: `dev/misc/session-examples/2.1.6-good/` and `2.1.6-bad/`

| Session | Resets | Reset Points | Base Level |
|---------|--------|--------------|------------|
| 2.1.6-good | 2 | Lines 34, 80 | ~20,558 |
| 2.1.6-bad | 4 | Lines 43, 63, 71, 94 | ~20,595 |

The bad session had 2x the resets of the good session. Notably, the bad session showed **clustered resets** at lines 63 and 71 (only 8 lines apart), suggesting aggressive context clearing.

### Cross-Era Consistency

The pattern holds across both eras:

1. **Base level consistency**: All resets drop to ~20K tokens regardless of era or build
2. **Ratio consistency**: Bad sessions have approximately 2x the resets of good sessions
3. **Mechanism independence**: The correlation exists despite different phantom read mechanisms between eras

### Token Progression Patterns

**2.1.6-good** cache_read_input_tokens progression:
```
32K → 77K → 81K → [RESET to 20K] → 84K → 105K → 137K → 143K → [RESET to 20K]
```

**2.1.6-bad** cache_read_input_tokens progression:
```
32K → 77K → 98K → [RESET to 20K] → 108K → 129K → [RESET to 20K] → 133K → [RESET to 20K] → 132K → 142K → [RESET to 20K]
```

The bad session shows more frequent resets at lower peak values, suggesting more aggressive context management that interrupts reads before they can be fully processed.

---

## Key Questions

The correlation between context resets and phantom reads raises several questions that warrant further investigation:

### 1. Temporal Correlation Analysis

**Question**: Do phantom-read files get read immediately before a reset?

If we can show "File X was read at line 42, reset occurred at line 43, File X was reported as phantom-read" - that establishes causation, not just correlation.

**Method**: Map each reset to the Read operations that occurred in the preceding lines. Cross-reference with agent self-reports of which files were phantom-read.

### 2. Reset Trigger Threshold

**Question**: What triggers a context reset? Is there a consistent token threshold?

Both sessions approach ~140K tokens before major resets. Understanding the trigger threshold could help predict when resets will occur and which reads are at risk.

**Method**: Analyze the token count immediately before each reset across multiple sessions. Look for a consistent threshold or pattern.

### 3. "Safe Window" Hypothesis

**Question**: Are reads immediately after a reset protected?

If resets clear the buffer and start fresh, reads in the immediate aftermath may be "safe." This could explain why sessions with 1-2 resets still succeed - critical reads happened in the safe window.

**Method**: Identify which reads occurred immediately after each reset. Determine if those reads are ever reported as phantom reads.

### 4. Read Sequence vs Reset Timing

**Question**: Is there a predictable danger zone before resets?

Create a timeline overlay plotting Read operations and resets on the same axis. Look for patterns like "reads in the N lines before a reset are at high risk."

**Method**: Build a visualization of Read operations and reset events. Identify any consistent spatial relationship.

### 5. Subagent Reset Behavior

**Question**: Do context resets occur independently in subagent sessions?

The main session and subagents may have separate context windows with independent reset behavior. Phantom reads in subagent contexts might follow different patterns.

**Method**: Analyze subagent `.jsonl` files for context reset patterns. Compare to main session patterns.

### 6. File Size Correlation

**Question**: Are larger files more likely to trigger resets or be phantom-read?

Large files consume more context, potentially accelerating the approach to reset thresholds. This could inform mitigation strategies (chunk large reads).

**Method**: Correlate file sizes with phantom read occurrence. Analyze whether large file reads precede resets more frequently.

---

## Detection Algorithm

The following algorithm detects context resets in a session file:

```python
import json

def count_context_resets(session_path: str, threshold: int = 10000) -> list[tuple[int, int, int]]:
    """
    Count context resets in a session file.
    
    A reset is detected when cache_read_input_tokens drops by more than
    the threshold between consecutive assistant messages.
    
    Args:
        session_path: Path to the .jsonl session file
        threshold: Minimum drop in tokens to count as a reset (default 10,000)
    
    Returns:
        List of (line_number, before_value, after_value) tuples
    """
    resets = []
    prev_cache_read = 0
    
    with open(session_path, 'r') as f:
        for i, line in enumerate(f, 1):
            try:
                msg = json.loads(line)
                if msg.get('type') == 'assistant':
                    usage = msg.get('message', {}).get('usage', {})
                    cache_read = usage.get('cache_read_input_tokens', 0)
                    if cache_read > 0:
                        if prev_cache_read > 0 and cache_read < prev_cache_read - threshold:
                            resets.append((i, prev_cache_read, cache_read))
                        prev_cache_read = cache_read
            except json.JSONDecodeError:
                continue
    
    return resets
```

---

## Implications

### For Detection Strategy

Context reset counting provides a **quantifiable proxy** for phantom read risk, even though direct detection from session files is impossible (the phantom read markers aren't recorded in the `.jsonl`).

Potential risk classification:
- **Low risk**: 0-1 resets
- **Medium risk**: 2 resets
- **High risk**: 3+ resets

### For Mitigation Strategy

If context resets are indeed the mechanism, potential mitigations include:

1. **Chunked reading**: Break large files into smaller reads to reduce context pressure
2. **Read prioritization**: Ensure critical files are read early in a session (in the "safe window")
3. **Context monitoring**: Warn users when approaching reset thresholds
4. **Alternative read mechanisms**: The MCP Filesystem workaround bypasses native Read entirely

### For Understanding the Bug

The context reset correlation suggests phantom reads are a **context management issue**, not a tool execution issue. The Read tool executes correctly (content is recorded in the session file), but the context window management system clears the content before the model can process it.

---

## Next Steps

1. **Pursue Key Questions**: Investigate the questions outlined above, prioritizing temporal correlation analysis and reset trigger thresholds

2. **Expand Sample Size**: Analyze additional session samples (2.0.59, 2.0.60) to strengthen the correlation evidence

3. **Build Visualization Tools**: Create timeline visualizations that overlay Read operations and reset events

4. **Update Session Analysis Scripts Spec**: Incorporate context reset counting as a detection/risk-scoring mechanism

5. **Document in Investigation Journal**: Add findings to the chronological discovery log

---

## References

- [Investigation-Journal.md](Investigation-Journal.md) - Chronological discovery log
- [Example-Session-Analysis.md](Example-Session-Analysis.md) - Detailed session file analysis
- [PRD.md](PRD.md) - Project overview and phantom reads background
- Sample data: `dev/misc/session-examples/`

---

*Last updated: 2026-01-14*
