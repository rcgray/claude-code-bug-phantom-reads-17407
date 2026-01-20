# Trial Analysis Guide

This document serves as the comprehensive onboarding resource for User Agents assigned to analyze Phantom Reads trial data. It consolidates the research background, running theories, and analysis procedures into a single reference.

**Purpose**: Enable new User Agents to immediately begin productive analysis of trial data without needing to read multiple source documents.

**Scope**: Background knowledge + forward-looking analysis procedures for evaluating trial data against running theories.

---

## Part 1: Research Background

### 1.1 The Phantom Reads Problem

**Definition**: Phantom Reads is a bug in Claude Code where file read operations fail silently. The AI assistant believes it has successfully read file contents when it has not, proceeding confidently with incomplete or non-existent information.

**Why It Matters**:
1. **Silent failure**: The agent shows no awareness that it missed content
2. **Intermittent occurrence**: The bug doesn't manifest consistently, making it hard to identify
3. **Masked by capability**: Claude's reasoning abilities allow plausible "gap filling," producing outputs that seem reasonable but are based on assumptions
4. **UI deception**: The Claude Code UI displays successful reads even when they're phantom reads

**GitHub Issue**: https://github.com/anthropics/claude-code/issues/17407

### 1.2 Two Eras of Phantom Reads

Phantom reads manifest through two distinct mechanisms depending on Claude Code version:

| Era | Versions | Error Marker | Mechanism |
|-----|----------|--------------|-----------|
| **Era 1** | ≤2.0.59 | `[Old tool result content cleared]` | Content cleared from context (likely context window management) |
| **Era 2** | ≥2.0.60 | `<persisted-output>Tool result saved to: /path/to/file.txt\n\nUse Read to view</persisted-output>` | Content persisted to disk; agent fails to follow up with a Read call |

**Critical**: No "safe" version has been identified. All tested versions (2.0.54 through 2.1.6+) can exhibit phantom reads under certain conditions.

### 1.3 The Session File Discrepancy

**Critical Discovery**: The session `.jsonl` file does NOT capture phantom read markers.

When examining session files from trials where agents self-reported phantom reads:
- The session `.jsonl` records **actual file content** in all `tool_result` entries
- The phantom read markers (`[Old tool result content cleared]` or `<persisted-output>`) appear NOWHERE in the session files
- The only place these markers appear is in conversation text where agents discuss experiencing them

**Hypothesis**: The session `.jsonl` is a log of tool execution results, NOT a representation of what the model receives in its context window. Content clearing/persistence happens AFTER the session file is written but BEFORE content is sent to the model.

**Implication**: Direct programmatic detection of phantom reads from session files is impossible. We must use proxy indicators and correlational analysis.

---

## Part 2: Running Theories

We have developed two complementary theories that together explain phantom read occurrence.

### 2.1 The Reset Theory

**Core Claim**: Phantom reads correlate with **context reset frequency**. Sessions with phantom reads exhibit approximately 2x the number of context resets compared to successful sessions.

**What is a Context Reset?**

A context reset is detected when the `cache_read_input_tokens` field in assistant messages drops significantly (>10,000 tokens) between consecutive messages. This indicates the system cleared older context to make room for new content.

All observed resets drop to approximately **~20,000 tokens** - the "base level" representing the persistent system prompt and command definitions.

**Evidence**:

| Session | Context Resets | Phantom Reads? |
|---------|---------------|----------------|
| 2.0.58-good | 1 | No |
| 2.0.58-bad | 3 | Yes |
| 2.1.6-good | 2 | No |
| 2.1.6-bad | 4 | Yes |

**The Mechanism**:

When context grows too large, the system clears older tool results. The sequence is:
1. Read tool executes successfully (content recorded in session file)
2. Context management triggers a reset
3. Recently-read content is cleared from the model's context window
4. Model receives a placeholder marker instead of actual content
5. Model proceeds without awareness of the gap

**More resets = more opportunities for critical content to be cleared = higher phantom read risk.**

### 2.2 The Headroom Theory

**Core Claim**: **Starting context consumption** before a multi-file read operation is a critical predictor of phantom read occurrence - more predictive than total content size or final token consumption.

**Definition**:
```
Headroom = Context Window Size - Current Token Consumption
```

For a 200K context window:
- Starting at 85K = 115K headroom (LOW RISK)
- Starting at 126K = 74K headroom (HIGH RISK)

**Evidence**:

| Trial | Pre-Operation | Post-Operation | Headroom | Result |
|-------|---------------|----------------|----------|--------|
| WSD Dev Good | 85K (42%) | 159K (79%) | 115K | Success |
| WSD Dev Bad | 126K (63%) | 142K (71%) | 74K | **PHANTOM READS** |

The bad trial consumed **fewer total tokens** but experienced phantom reads because it **started at higher consumption** with less headroom available.

**The Mechanism**:

Low headroom → context fills quickly → reset threshold reached sooner → more resets → more phantom reads.

### 2.3 How the Theories Relate

The theories are **complementary**, not competing:

| Theory | Explains |
|--------|----------|
| **Reset Theory** | The MECHANISM - context resets clear content before the model processes it |
| **Headroom Theory** | The TRIGGER - low starting headroom causes earlier/more frequent resets |

**Combined Causal Chain**:
```
High pre-operation consumption
        ↓
Low headroom available
        ↓
Multi-file read operation begins
        ↓
Context fills quickly
        ↓
Reset threshold reached sooner
        ↓
Context reset occurs
        ↓
Recently-read content cleared
        ↓
Model receives placeholder instead of content
        ↓
PHANTOM READ
        ↓
(Cycle repeats for subsequent files)
```

### 2.4 Risk Classification

Based on current evidence:

| Risk Level | Context Consumption | Headroom | Expected Outcome |
|------------|---------------------|----------|------------------|
| Low | <50% | >100K tokens | Likely success |
| Medium | 50-60% | 80-100K tokens | Elevated risk |
| High | >60% | <80K tokens | Likely phantom reads |

**Note**: These thresholds are hypotheses derived from limited data. Your analysis may refine them.

---

## Part 3: Trial Data Structure

### 3.1 What Gets Collected

Each trial produces the following artifacts:

1. **Chat Export** (`.txt` file)
   - Human-readable transcript of the session
   - Contains the agent's self-report on phantom read occurrence
   - Contains `/context` output showing token consumption

2. **Main Session File** (`{uuid}.jsonl`)
   - Line-delimited JSON of all messages in the session
   - Contains `cache_read_input_tokens` data for reset analysis
   - Contains tool_result entries (which show actual content, not phantom markers)

3. **Session Subdirectory** (`{uuid}/`) - may contain:
   - `subagents/` - JSONL files for sub-agent sessions (Task tool invocations)
   - `tool-results/` - Persisted tool outputs (presence indicates persistence occurred)

### 3.2 Directory Organization

Trials are organized by **Workscope ID** (format: `YYYYMMDD-HHMMSS`):

```
dev/misc/wsd-dev-02/
├── 20260119-120000/           # Trial directory (named by Workscope ID)
│   ├── 20260119-120000.txt    # Chat export
│   ├── {uuid}.jsonl           # Main session file
│   └── {uuid}/                # Session subdirectory
│       ├── subagents/
│       │   └── agent-{shortId}.jsonl
│       └── tool-results/
│           └── toolu_{toolUseId}.txt
├── 20260119-130000/           # Another trial
└── ...
```

### 3.3 Session File Structure Types

Three distinct session structures exist (independent of Era):

| Structure | Agent Files | Session Subdirectory | Notes |
|-----------|-------------|---------------------|-------|
| **Flat** | Root level | Does not exist | Older builds |
| **Hybrid** | Root level | Exists (tool-results/ only) | Transitional |
| **Hierarchical** | In subagents/ | Exists (subagents/ + tool-results/) | Current builds |

**For analysis purposes**: The structure type doesn't affect your analysis approach - you'll examine the main session `.jsonl` file regardless of structure.

### 3.4 Key Data Points in Session Files

**Assistant messages** contain usage data:
```json
{
  "type": "assistant",
  "message": {
    "usage": {
      "cache_read_input_tokens": 85234,
      "cache_creation_input_tokens": 12500,
      "input_tokens": 150,
      "output_tokens": 2340
    }
  }
}
```

The `cache_read_input_tokens` field is your primary metric for reset detection.

**Tool result entries** show Read operations:
```json
{
  "type": "user",
  "message": {
    "content": [{
      "type": "tool_result",
      "tool_use_id": "toolu_01ABC...",
      "content": "     1→# File content here..."
    }]
  }
}
```

Remember: These show actual content even in phantom read sessions - the discrepancy happens after logging.

---

## Part 4: Analysis Procedures

### 4.1 Pre-Analysis: Trial Classification

Before detailed analysis, classify each trial:

1. **Read the chat export** to determine outcome:
   - **SUCCESS**: Agent reports no phantom reads; all file content received inline
   - **FAILURE**: Agent confirms phantom reads; one or more files returned markers

2. **Note the Workscope ID** for reference throughout analysis

3. **Record basic metadata**:
   - Claude Code version (if known)
   - Date/time of trial
   - Which WPD was targeted (if applicable)

### 4.2 Context Consumption Analysis

**Objective**: Extract pre-operation and post-operation token consumption to evaluate Headroom Theory.

**Method 1: From Chat Export**

Search for `/context` output patterns:
```
Context: 85k/200k tokens (42%)
```

Record:
- Pre-operation consumption (before `/refine-plan` or trigger command)
- Post-operation consumption (after trigger command completes)
- Delta (post - pre)

**Method 2: From Session File**

Extract `cache_read_input_tokens` progression:
```python
import json

def extract_token_progression(session_path):
    """Extract cache_read_input_tokens from all assistant messages."""
    progression = []
    with open(session_path, 'r') as f:
        for line in f:
            msg = json.loads(line)
            if msg.get('type') == 'assistant':
                usage = msg.get('message', {}).get('usage', {})
                cache_read = usage.get('cache_read_input_tokens', 0)
                if cache_read > 0:
                    progression.append(cache_read)
    return progression
```

### 4.3 Context Reset Detection

**Objective**: Count context resets to evaluate Reset Theory.

**Definition**: A reset occurs when `cache_read_input_tokens` drops by >10,000 tokens between consecutive assistant messages.

**Algorithm**:
```python
def count_context_resets(session_path, threshold=10000):
    """
    Count context resets in a session file.

    Returns list of (line_number, before_value, after_value) tuples.
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

**What to Record**:
- Total reset count
- Reset points (line numbers)
- Token values before/after each reset
- Pattern of resets (clustered vs distributed)

### 4.4 Tool Results Directory Analysis

**Objective**: Determine if persistence occurred during the session.

**Method**:
1. Check if `{uuid}/tool-results/` directory exists
2. If present, list the files and their sizes
3. Cross-reference with Read operations in the session file

**Interpretation**:
- Presence of `tool-results/` indicates persistence occurred (Era 2 mechanism)
- Absence suggests either Era 1 or no large tool results
- Files in `tool-results/` can be matched to `tool_use_id` values in the session

### 4.5 Correlation Analysis

**Objective**: Evaluate whether trial outcomes correlate with theory predictions.

For each trial, compile:

| Metric | Value | Theory Prediction |
|--------|-------|-------------------|
| Pre-op consumption | X% | Headroom Theory: >60% = high risk |
| Headroom | XK tokens | Headroom Theory: <80K = high risk |
| Reset count | N | Reset Theory: >2 = high risk |
| Actual outcome | SUCCESS/FAILURE | Does it match predictions? |

**Questions to Answer**:
1. Did high-risk trials (per theories) actually fail?
2. Did low-risk trials actually succeed?
3. Are there anomalies that challenge the theories?

---

## Part 5: Reporting Template

When analyzing trials, document your findings using this structure:

### Trial Summary Table

Create a summary table for all trials analyzed:

```markdown
| Trial ID | Pre-Op | Post-Op | Headroom | Resets | Outcome | Notes |
|----------|--------|---------|----------|--------|---------|-------|
| 20260119-120000 | 85K (42%) | 159K (79%) | 115K | 2 | SUCCESS | |
| 20260119-130000 | 126K (63%) | 142K (71%) | 74K | 4 | FAILURE | Clustered resets |
```

### Individual Trial Analysis

For each trial requiring detailed examination:

```markdown
## Trial: [Workscope ID]

**Classification**: SUCCESS / FAILURE
**Pre-operation consumption**: X tokens (X%)
**Post-operation consumption**: X tokens (X%)
**Headroom at trigger**: X tokens
**Context resets**: N (at lines X, Y, Z)

### Token Progression
[List or visualize cache_read_input_tokens progression]

### Reset Analysis
[Details on when resets occurred relative to read operations]

### Theory Evaluation
- Headroom Theory prediction: [HIGH RISK / LOW RISK]
- Reset Theory prediction: [HIGH RISK / LOW RISK]
- Actual outcome: [MATCHES / CONTRADICTS] predictions

### Observations
[Notable patterns, anomalies, or insights]
```

### Cross-Trial Analysis

After analyzing multiple trials:

```markdown
## Cross-Trial Summary

### Theory Validation
- Headroom Theory: X/Y trials matched prediction (X%)
- Reset Theory: X/Y trials matched prediction (X%)

### Threshold Refinement
Based on this data:
- Observed danger zone appears to be [consumption range]
- Reset threshold appears to trigger at approximately [X tokens]

### Anomalies
[Trials that didn't match predictions and possible explanations]

### New Observations
[Any patterns that suggest additional factors or refined theories]
```

---

## Part 6: Open Questions

Your analysis should attempt to address these open questions:

### 6.1 Threshold Questions

1. **Is there a precise headroom threshold?** Current hypothesis: ~80K. Can we narrow this?
2. **What triggers a context reset?** Is it a fixed token count (~140K) or relative to something?
3. **Is there a "safe window" after resets?** Are reads immediately following a reset protected?

### 6.2 Mechanism Questions

4. **Does reset timing matter?** If a reset occurs AFTER a file is fully processed, is content "safe"?
5. **Are some files more vulnerable?** Does file size, position in read sequence, or content type affect risk?
6. **Do subagents have independent context?** Do they experience separate reset behavior?

### 6.3 Pattern Questions

7. **Does read operation count matter more than total content?** 10 small files vs 2 large files with same tokens?
8. **Are clustered resets worse?** Does the bad trial pattern of rapid consecutive resets indicate higher risk?

---

## Part 7: Quick Reference

### Key Metrics to Extract

| Metric | Source | Purpose |
|--------|--------|---------|
| Pre-op tokens | Chat export (`/context`) or session file | Headroom calculation |
| Post-op tokens | Chat export (`/context`) or session file | Delta calculation |
| Reset count | Session file (`cache_read_input_tokens` drops) | Reset Theory evaluation |
| Reset positions | Session file (line numbers) | Temporal correlation |
| Outcome | Chat export (agent self-report) | Ground truth |

### Risk Indicators (Current Hypotheses)

| Indicator | Low Risk | High Risk |
|-----------|----------|-----------|
| Pre-op consumption | <50% (100K) | >60% (120K) |
| Headroom | >100K tokens | <80K tokens |
| Reset count | 0-1 | 3+ |
| Reset pattern | Single, isolated | Multiple, clustered |

### Detection Algorithm Summary

```python
# Pseudocode for trial analysis

def analyze_trial(trial_dir):
    # 1. Classify outcome from chat export
    outcome = extract_outcome(chat_export)  # SUCCESS or FAILURE

    # 2. Extract token consumption from /context calls
    pre_op, post_op = extract_context_calls(chat_export)
    headroom = 200000 - pre_op

    # 3. Count resets from session file
    resets = count_context_resets(session_file)

    # 4. Evaluate against theories
    headroom_prediction = "HIGH_RISK" if headroom < 80000 else "LOW_RISK"
    reset_prediction = "HIGH_RISK" if len(resets) > 2 else "LOW_RISK"

    # 5. Check for correlation
    matches_headroom = (headroom_prediction == "HIGH_RISK") == (outcome == "FAILURE")
    matches_reset = (reset_prediction == "HIGH_RISK") == (outcome == "FAILURE")

    return {
        "outcome": outcome,
        "pre_op": pre_op,
        "headroom": headroom,
        "resets": len(resets),
        "matches_headroom_theory": matches_headroom,
        "matches_reset_theory": matches_reset
    }
```

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Phantom Read** | A Read operation where the agent believes it received content but did not |
| **Context Reset** | A dramatic drop (>10K tokens) in `cache_read_input_tokens` between messages |
| **Headroom** | Available buffer space: Context Window Size - Current Consumption |
| **Era 1** | Builds ≤2.0.59; phantom reads show `[Old tool result content cleared]` |
| **Era 2** | Builds ≥2.0.60; phantom reads show `<persisted-output>` markers |
| **Workscope ID** | Timestamp identifier (YYYYMMDD-HHMMSS) used to coordinate trial artifacts |
| **Session ID / UUID** | Claude Code's internal identifier for a session (appears in filenames) |
| **Base Level** | The ~20K token floor that resets drop to (system prompt + commands) |
| **Danger Zone** | The consumption range (>60%) where phantom reads become likely |

## Appendix B: File Locations

| Artifact | Location Pattern |
|----------|-----------------|
| Trial data | `dev/misc/{collection-name}/{workscope-id}/` |
| Chat export | `{trial-dir}/{workscope-id}.txt` |
| Session file | `{trial-dir}/{uuid}.jsonl` |
| Subagents | `{trial-dir}/{uuid}/subagents/` |
| Tool results | `{trial-dir}/{uuid}/tool-results/` |

## Appendix C: Related Documents

For deeper background on specific topics:

| Document | Content |
|----------|---------|
| `docs/core/PRD.md` | Project overview and goals |
| `docs/core/Investigation-Journal.md` | Chronological discovery log |
| `docs/core/Context-Reset-Analysis.md` | Detailed Reset Theory analysis |
| `docs/core/Headroom-Theory.md` | Detailed Headroom Theory analysis |
| `docs/core/Example-Session-Analysis.md` | Session file structure details |
| `docs/core/Experiment-Methodology-02.md` | Trial execution protocol |

---

*Document created: 2026-01-19*
*Purpose: User Agent onboarding for Phantom Reads trial analysis*
