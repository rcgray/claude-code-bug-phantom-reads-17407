# Work Journal - 2026-01-21 15:22
## Workscope ID: Workscope-20260121-152246

## Initialization

Initialized with `/wsd:init --custom` flag. Will receive custom workscope from User after onboarding.

## Project-Bootstrapper Onboarding

### Files Read During Onboarding

**System Files (read during /wsd:boot):**
1. `docs/read-only/Agent-System.md` - Agent collaboration system and workflow standards
2. `docs/read-only/Agent-Rules.md` - Strict rules all agents must follow
3. `docs/core/Design-Decisions.md` - Project-specific design philosophies
4. `docs/read-only/Documentation-System.md` - Documentation organization system
5. `docs/read-only/Checkboxlist-System.md` - Task management and checkbox states
6. `docs/read-only/Workscope-System.md` - Work assignment and tracking mechanism

**Project-Specific Files (read during /wsd:onboard):**
7. `docs/core/PRD.md` - Project Requirements Document for Phantom Reads Investigation
8. `README.md` - Public-facing documentation about the project
9. `docs/core/Action-Plan.md` - Implementation checkboxlist showing current project status
10. `docs/read-only/standards/Coding-Standards.md` - Universal coding principles
11. `docs/read-only/standards/Python-Standards.md` - Python-specific requirements

### Key Rules and Conventions

**Three Most Violated Rules to Avoid:**
1. **Rule 5.1 (NO BACKWARD COMPATIBILITY)** - This project has NOT shipped. No migration solutions, legacy support, or backward compatibility code.
2. **Rule 3.4 (NO META-PROCESS REFERENCES IN PRODUCT ARTIFACTS)** - No phase numbers, task IDs, or workscope references in shipping code. Only allowed in process documents (specs, tickets, Action Plans).
3. **Rule 3.11 (COPY READ-ONLY FILES TO WORKBENCH)** - If need to edit files in `docs/read-only/` or `.claude/`, copy to `docs/workbench/` first.

**Critical Rules:**
- Rule 4.4: `cat >> file << EOF` is FORBIDDEN - use standard tools (Read, Edit, Write)
- Rule 4.2: Read ENTIRE files unless otherwise directed
- Rule 3.5: Specifications must be updated when changing code
- Rule 3.12: Do NOT accept Special Agent reports without proper proof of work

**Checkbox States:**
- `[ ]` = Unaddressed (available for selection)
- `[%]` = Incomplete/Unverified - treat EXACTLY like `[ ]`, have FULL implementation responsibility
- `[*]` = Assigned to active workscope (unavailable)
- `[x]` = Completed
- `[-]` = Intentionally skipped (requires User authorization)

### Project Context

This is the **Phantom Reads Investigation** project - a git repository documenting and reproducing Claude Code Issue #17407. The bug causes Claude Code to believe it has read file contents when it has not.

**Current Status:** Phase 4 (Analysis Tools) - tasks 4.5.1, 4.5.2, 4.5.3 remain. Tasks 1.3 and 3.5.4 are marked `[*]` (assigned to other workscopes).

**Key Findings:**
- Reset timing pattern is the dominant predictor (100% accuracy on 22 trials)
- Mid-session resets (50-90% through session) predict phantom reads
- MCP Filesystem bypass provides 100% success rate workaround

---

## Custom Workscope: Schema 1.2 Sanity Check

**Task:** Verify the schema 1.1 → 1.2 upgrade of `trial_data.json` generation is correct.

### Files Examined

1. `dev/experiments/schema-12-sanity-check/20260120-085645.trial_data.schema11.json` - Previous schema
2. `dev/experiments/schema-12-sanity-check/20260120-085645.trial_data.schema12.postfreeze2.json` - New schema
3. `.claude/commands/update-trial-data.md` - Command specification
4. `dev/karpathy/extract_trial_data.py` - Static helper script
5. `docs/tickets/closed/investigate-trial-data-failed-read-recording.md` - Ticket context
6. `docs/archive/trial-data-failed-read-investigation-findings.md` - Investigation findings

### Sanity Check Findings

#### ✅ CORRECT: file_reads success/failure tracking

The primary goal of the schema 1.2 upgrade was to track Read operation success/failure. This is working correctly:

- **New fields added:** `success` boolean on each read entry
- **New counters:** `successful_operations`, `failed_operations`
- **New array:** `failed_reads` for diagnostics
- **Trial 20260120-085645:** 15 operations, 15 successful, 0 failed (correct - no file errors in this trial)

#### ✅ CORRECT: Outcome field with PENDING_NLP

The two-step process is working:
1. Script outputs `"PENDING_NLP"` for `self_reported` and `notes`
2. Agent performs NLP analysis and updates to actual outcome
3. Current trial shows `"FAILURE"` with proper notes - correctly updated

#### ⚠️ SEMANTIC CHANGE: reset_analysis calculations

The reset position percentages changed because the calculation basis changed:

| Reset | v1.1 | v1.2 | Reason |
|-------|------|------|--------|
| 1 | 54.2% | 54.8% | total_events: 48 → 115 |
| 2 | 81.3% | 73.0% | Now uses session_line / total_lines |
| 3 | 97.9% | 90.4% | More accurate to session structure |

**Assessment:** The v1.2 calculation is more accurate and reproducible (uses actual session file line numbers). The session file has 115 lines, which matches `total_events: 115`. This is an improvement, not a bug.

#### ⚠️ SEMANTIC CHANGE: token_analysis.statistics.total_tokens_read

| Metric | v1.1 | v1.2 |
|--------|------|------|
| total_tokens_read | 126,745 | 141,990 |
| reads_with_tokens sum | 141,990 | 141,990 |

**Explanation:** v1.1 counted each unique file once; v1.2 counts ALL read operations (including re-reads). The trial has:
- 3 re-reads of Journal-Workscope file (1,048 × 3)
- 2 reads of Manifest-Driven-Pipeline-Overview (5,783 × 2)
- 2 reads of Stage-Release-Script-Overview (7,366 × 2)

**Assessment:** v1.2 is more appropriate for context pressure analysis since each read operation adds to context. This is an improvement.

#### 🔴 BUG: Missing context_reset events in timeline

| Event Type | v1.1 | v1.2 |
|------------|------|------|
| tool_batch | 15 | 15 |
| user_input | 0 | 19 |
| context_reset | **3** | **0** |

**Problem:** The v1.2 script detects resets and stores them in `reset_analysis.resets`, but does NOT add them to the `timeline` array. The v1.1 timeline included these events, making it easy to see when resets occurred relative to file reads.

**Location in code:** `dev/karpathy/extract_trial_data.py` lines 148-155 detect resets but never append them to `timeline`.

**Impact:** The timeline no longer shows the interleaved sequence of reads and resets, which was useful for visual analysis.

### Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| success/failure tracking | ✅ CORRECT | Primary goal achieved |
| PENDING_NLP workflow | ✅ CORRECT | Two-step process working |
| reset position_percent | ⚠️ CHANGED | More accurate calculation |
| total_tokens_read | ⚠️ CHANGED | Better for context analysis |
| timeline context_reset | 🔴 BUG | Regression - missing events |

**Recommendation:** Fix the timeline bug by adding context_reset events back to the timeline array in `extract_trial_data.py` around line 154.

---

## Bug Fix Applied

Added the missing `timeline.append()` call in `dev/karpathy/extract_trial_data.py` (line ~155) to add context_reset events to the timeline when resets are detected.

**Code Added:**
```python
# Add reset to timeline
timeline.append({
    "sequence": sequence_counter,
    "type": "context_reset",
    "session_line": line_num,
    "from_tokens": last_cache_tokens,
    "to_tokens": cache_tokens
})
```

**Verification:** Re-ran extraction on Trial 20260120-085642:
- Timeline events: 34 → 37 (added 3 context_reset events)
- All 3 resets now appear in timeline with correct data

