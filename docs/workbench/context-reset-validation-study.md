# Context Reset Validation Study - Handoff Document

**Created**: 2026-01-13
**Purpose**: Guide the next User Agent in validating the context reset correlation theory against Era 2 session logs

---

## Background

### The Discovery

While analyzing Era 1 (2.0.58) session files, I discovered that the `cache_read_input_tokens` field in assistant messages shows **context resets** - dramatic drops in cached tokens that correlate with phantom read occurrence.

**Era 1 Findings**:

| Session | Context Resets | Phantom Reads? |
|---------|---------------|----------------|
| 2.0.58-good | 1 | No |
| 2.0.58-bad | 3 | Yes |

All resets drop to approximately **~20K tokens** (the apparent "base" level of system prompt/commands).

### The Theory

Context resets occur when the system clears older tool results to make room for new context. When this happens:
1. The session file has ALREADY recorded the actual content
2. But the model's context window is cleared of that content
3. The model sees a placeholder marker instead

**More resets = more opportunities for critical content to be cleared = higher phantom read risk.**

---

## Your Task

Validate whether this context reset correlation holds true in **Era 2** (2.0.60+) sessions.

### Hypothesis to Test

If the context reset theory is correct, Era 2 sessions should show the same pattern:
- Good sessions (no phantom reads): Fewer context resets
- Bad sessions (phantom reads): More context resets

### Sample Files to Analyze

Located in `dev/misc/session-examples/`:

**Era 2 Sessions**:
- `2.1.6-good/0357781f-d024-4cef-8496-56501c76afb3.jsonl`
- `2.1.6-bad/bf88e2ff-ac8b-4f29-8dbf-c2467325fe4e.jsonl`

**Additional samples if available**:
- `2.0.60-good/` (check if exists)
- `2.0.60-bad/` (check if exists)

### Analysis Method

Use this Python snippet to count context resets in a session file:

```python
import json

def count_context_resets(session_path: str, threshold: int = 10000) -> list[tuple[int, int, int]]:
    """
    Count context resets in a session file.
    
    A reset is detected when cache_read_input_tokens drops by more than
    the threshold between consecutive assistant messages.
    
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

# Usage:
# resets = count_context_resets('/path/to/session.jsonl')
# print(f"Total resets: {len(resets)}")
# for line, before, after in resets:
#     print(f"  Line {line}: {before} -> {after}")
```

### Expected Outcomes

**If theory is validated**:
- 2.1.6-good: 0-1 context resets
- 2.1.6-bad: 2+ context resets

**If theory is NOT validated**:
- No clear correlation between reset count and phantom read occurrence
- Or the "base" level after reset differs significantly from Era 1 (~20K)

### Additional Investigations

1. **Check the "base" level**: Do Era 2 resets also drop to ~20K tokens? Or a different level?

2. **Map resets to tool calls**: What happens right before each reset? Is it always a Read operation?

3. **Check subagent files**: Do resets occur in subagent contexts too? Analyze:
   - `2.1.6-bad/bf88e2ff-.../subagents/agent-a57399f.jsonl`

4. **Cross-reference with tool-results directory**: Era 2 has a `tool-results/` directory with persisted content. Does the presence/count of files there correlate with reset count?

---

## Recording Your Findings

Update `docs/core/Example-Session-Analysis.md` with a new section:

```markdown
## Question 7: Context Reset Correlation in Era 2

**Question**: Does the context reset correlation discovered in Era 1 hold true for Era 2 sessions?

### Findings

[Your analysis here]
```

Also update `docs/core/Investigation-Journal.md` with a new dated entry summarizing your findings.

---

## If Theory is Validated

If you confirm the correlation holds in Era 2:

1. **Update the Session Analysis Scripts spec** (`docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md`):
   - Add context reset counting as a detection/risk-scoring mechanism
   - Revise the "Phantom Read Detection Algorithm" section
   - Add a "Risk Scoring" output to the analysis report

2. **Create implementation tasks** in the FIP for:
   - Context reset detection function
   - Risk classification logic (low/medium/high)
   - Updated report format showing risk scores

3. **Document the theory** formally in the PRD or a new design document

---

## If Theory is NOT Validated

If Era 2 doesn't show the same correlation:

1. **Document the negative result** - this is still valuable information

2. **Investigate differences**:
   - Does Era 2 use a different context management mechanism?
   - Is the `tool-results/` directory a replacement for context clearing?
   - Are there other fields that might indicate phantom reads in Era 2?

3. **Consider era-specific detection**:
   - Era 1: Context reset counting
   - Era 2: Alternative indicators (TBD)

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `docs/core/Example-Session-Analysis.md` | Investigation findings - update with Q7 |
| `docs/core/Investigation-Journal.md` | Chronological discovery log - add new entry |
| `docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md` | Feature spec - may need revision |
| `dev/misc/session-examples/` | Sample session data |

---

## Questions to Answer

1. **Does Era 2 show the same context reset correlation as Era 1?**
2. **What is the "base" token level after resets in Era 2?**
3. **Do resets occur in subagent contexts?**
4. **Is there a relationship between `tool-results/` directory contents and reset count?**
5. **Can we use context reset counting as a reliable risk indicator across both eras?**

---

*Good luck with the investigation. The context reset discovery may be the key to building a useful detection/risk-scoring system even though direct phantom read detection from session files is impossible.*
