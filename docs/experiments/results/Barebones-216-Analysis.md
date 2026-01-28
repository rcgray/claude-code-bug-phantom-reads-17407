# Barebones-216 Analysis

**Experiment ID**: Barebones-216
**Collection**: `dev/misc/repro-attempts-04-barebones/`
**Date Conducted**: 2026-01-27
**Date Analyzed**: 2026-01-27
**Claude Code Version**: 2.1.6 (locked)

---

## Executive Summary

The Barebones-216 experiment tested whether the Phantom Reads bug manifests in a minimal environment stripped of all non-essential project infrastructure. By removing the Workscope-Dev (WSD) framework and all auxiliary files, we isolated the reproduction scenario to only the files necessary for triggering and observing phantom reads.

**Result**: 4 valid failures, 1 invalid trial (protocol violation) → **100% failure rate among valid trials**

This confirms phantom reads are a **Claude Code harness issue**, not an artifact of the WSD framework or our investigation repository's complexity.

---

## Trial Data Summary

| Trial ID   | Outcome     | Resets | Reset Positions | Pattern             | Files Affected | Total Reads | has_tool_results |
| ---------- | ----------- | ------ | --------------- | ------------------- | -------------- | ----------- | ---------------- |
| **092331** | **INVALID** | 1      | 83%             | SINGLE_LATE         | 0              | 6           | false            |
| 092743     | FAILURE     | 2      | 63%, 86%        | OTHER               | 3              | 11          | true             |
| 093127     | FAILURE     | 3      | 27%, 54%, 93%   | EARLY_PLUS_MID_LATE | 9 (ALL)        | 45          | true             |
| 093818     | FAILURE     | 2      | 75%, 90%        | OTHER               | 3              | 11          | true             |
| 094145     | FAILURE     | 3      | 51%, 61%, 87%   | OTHER               | 4              | 19          | true             |

### Notable Observations

- **All valid trials** had `has_tool_results: true` (persistence occurred) and experienced phantom reads
- **Trial 092331** was a **protocol violation** (agent failed to read all suggested files) and is excluded from failure rate calculation
- **Trial 093127** was catastrophic: agent chased 45 reads through 6+ levels of nested `<persisted-output>` redirects, never receiving content, and fabricated an entire 12-point analysis with invented quotes

### Affected Files by Trial

| Trial  | Affected Files                                                              |
| ------ | --------------------------------------------------------------------------- |
| 092331 | N/A (INVALID - protocol violation)                                          |
| 092743 | module-alpha.md, module-beta.md, module-gamma.md                            |
| 093127 | ALL 9 spec files + WPD                                                      |
| 093818 | module-alpha.md, module-beta.md, module-gamma.md                            |
| 094145 | data-pipeline-overview.md, module-alpha.md, module-beta.md, module-gamma.md |

---

## Research Question Analysis

### RQ-BB216-1: Does removing WSD framework eliminate phantom reads?

**Status**: ANSWERED - **NO**

#### Evidence

The barebones repository contained NO:
- WSD framework files (`docs/read-only/`, agent definitions)
- Investigation documentation (`docs/core/`, `docs/theories/`)
- Analysis scripts (`src/`, `scripts/`)
- Hook systems (`.claude/hooks/protect_files.py`)
- MCP Filesystem configuration (`.mcp.json`)
- Permission denials (`.claude/settings.local.json`)

Yet phantom reads occurred in **4 of 4 valid trials (100%)**:

| Environment                          | Framework        | Failure Rate   |
| ------------------------------------ | ---------------- | -------------- |
| Full investigation repo (Method-04)  | Full WSD + hooks | 100% (8/8)     |
| **Barebones repo (this experiment)** | **None**         | **100% (4/4)** |
| WSD Development project              | Full WSD         | 77% (17/22)    |

**Additional validation**: The User ran 4 additional informal trials beyond the recorded 5, all showing failure. This further confirms the 100% failure rate.

#### Significance

**This definitively confirms that the Phantom Reads bug is a Claude Code harness issue, NOT:**
- A WSD framework interaction
- A side effect of investigation documentation
- Caused by the `protect_files.py` hook
- An artifact of repository complexity

The bug exists at the Claude Code infrastructure level and will affect **any** user who triggers multi-file read operations under context pressure—regardless of what framework or tools they use.

#### Implications

1. **For Users**: The bug affects ALL Claude Code users, not just those using WSD or similar frameworks
2. **For Reproduction**: A minimal reproduction case is now validated—users can reproduce without complex setup
3. **For Anthropic**: The bug report is strengthened by evidence from a stripped-down environment

---

### RQ-BB216-2: How does barebones context consumption compare to the full repo?

**Status**: ANSWERED

#### Methodology

Extracted `/context` measurements from chat exports for all trials in both collections. Compared three measurement points:
1. **Baseline**: Fresh session before any commands
2. **Post-Setup (X)**: After `/setup-hard` command
3. **Post-Analysis**: After `/analyze-wpd` command

#### Barebones Context Measurements (valid trials only)

| Trial ID | Baseline  | Post-Setup (X) | Post-Analysis | Outcome |
| -------- | --------- | -------------- | ------------- | ------- |
| 092743   | 20k (10%) | 116k (58%)     | 175k (87%)    | FAILURE |
| 093127   | 20k (10%) | 116k (58%)     | 177k (89%)    | FAILURE |
| 093818   | 20k (10%) | 116k (58%)     | 175k (87%)    | FAILURE |
| 094145   | 20k (10%) | 116k (58%)     | 175k (87%)    | FAILURE |

**Barebones averages**: Baseline 20k, Post-Setup 116k, Post-Analysis 176k

#### Full Repo Context Measurements (Method-04 Firstrun, Hard scenario)

| Trial ID | Baseline  | Post-Setup (X) | Post-Analysis | Outcome |
| -------- | --------- | -------------- | ------------- | ------- |
| 112940   | 23k (12%) | 120k (60%)     | 170k (85%)    | FAILURE |
| 113003   | 23k (12%) | 120k (60%)     | 189k (95%)    | FAILURE |
| 114431   | 23k (12%) | 120k (60%)     | 170k (85%)    | FAILURE |
| 114434   | 23k (12%) | 120k (60%)     | 170k (85%)    | FAILURE |

**Full repo averages**: Baseline 23k, Post-Setup 120k, Post-Analysis 175k

#### Comparison Summary

| Metric             | Barebones         | Full Repo (Hard)  | Difference    |
| ------------------ | ----------------- | ----------------- | ------------- |
| **Baseline**       | 20k (10%)         | 23k (12%)         | **-3k (-2%)** |
| **Post-Setup (X)** | 116k (58%)        | 120k (60%)        | **-4k (-2%)** |
| **Post-Analysis**  | 175-177k (87-89%) | 170-189k (85-95%) | Similar       |

#### Findings

1. **Baseline Overhead Difference**: Barebones has ~3k tokens less baseline overhead than the full investigation repo (20k vs 23k). This difference is attributable to:
   - Minimal CLAUDE.md (619 tokens in barebones vs larger in full repo)
   - No hooks, MCP configuration, or extensive project files for harness indexing
   - Fewer slash command definitions

2. **Post-Setup (X) Difference**: The ~4k difference (116k vs 120k) propagates from the baseline difference. The preloaded file content (via `/setup-hard`) is identical between environments.

3. **Post-Analysis Similarity**: Both environments reach similar post-analysis context levels (175-177k vs 170-189k), indicating Y (operation tokens) is comparable when the protocol is followed correctly.

4. **Consistent Failure**: Both environments show 100% failure rate when the protocol is followed, indicating the ~4k overhead difference (2% of context window) has no practical effect on phantom read occurrence.

#### Conclusion

**The hypothesis is confirmed**: Barebones does have marginally lower context consumption (~3-4k tokens less at baseline and post-setup), consistent with reduced project complexity.

**However**, this difference is negligible (~2% of context window) and **does NOT affect phantom read occurrence**. Both environments show 100% failure rate among valid trials, confirming that phantom reads are determined by the X+Y interaction with context thresholds, not by minor overhead variations.

---

### RQ-BB216-3: Why did trial 20260127-092331 "succeed"?

**Status**: ANSWERED - **Protocol Violation (Invalid Trial)**

#### Reframing: Not a Success, But a Malfunction

Initial analysis characterized trial 092331 as a "success" and drew conclusions about Y being "non-deterministic." Upon review, this characterization is incorrect.

**The correct interpretation**: Trial 092331 is an **invalid trial** due to protocol violation. The agent failed to read all files explicitly listed in the `/analyze-wpd` command's "Suggested Documentation" section.

#### Evidence of Protocol Violation

The `/analyze-wpd.md` command explicitly lists **8 spec files** under "Suggested Documentation":

```markdown
- docs/specs/data-pipeline-overview.md
- docs/specs/module-alpha.md      ← Agent SKIPPED
- docs/specs/module-beta.md       ← Agent SKIPPED
- docs/specs/module-gamma.md      ← Agent SKIPPED
- docs/specs/module-epsilon.md
- docs/specs/module-phi.md
- docs/specs/integration-layer.md
- docs/specs/compliance-requirements.md
```

**Files read by 092331**: 6 files (skipped module-alpha, module-beta, module-gamma)
**Files read by valid trials**: 9 files (all suggested files)

The agent in 092331 failed to follow the protocol by not reading 3 of the explicitly listed files.

#### Why "Y Non-Determinism" Is the Wrong Conclusion

The original analysis concluded that "Y is not deterministic" based on this trial. This conclusion is flawed:

1. **All operations involving LLMs have baseline non-determinism** - this is not a special property of Y
2. **The protocol explicitly specifies which files to read** - deviation from this is a protocol failure, not evidence of inherent variability
3. **Analogy**: Saying Y is non-deterministic because one agent malfunctioned is like saying dogs have a non-deterministic number of eyes because birth defects exist. Technically true, but misleading as a characterization of the system.

**Corrected understanding**: Y is effectively deterministic (within normal margins of error). When the protocol is followed correctly, agents read the specified files. Trial 092331 represents a rare protocol failure, not evidence that Y systematically varies.

#### Implications

1. **Official record**: 4/4 valid failures (100% failure rate), not 4/5 (80%)
2. **No "accidental success" concern**: We don't need to worry about agents accidentally avoiding phantom reads through strategic file omission—this was a one-off malfunction
3. **Methodology validated**: The `/analyze-wpd` command successfully guides agents to read the correct files in the vast majority of cases
4. **Additional validation**: The User ran 4 additional informal trials after the initial 5, all showing failure, further confirming 100% failure rate when protocol is followed

#### Token Accumulation Data (For Reference)

The invalid trial's data is retained for completeness but should not be used for theoretical conclusions:

**INVALID Trial (092331) - Protocol Violation**:
```
Sequence  Tokens   Event
────────────────────────────────
2         115,586  Post-setup baseline
4         115,716  Read WPD
6         117,844  Read integration-layer.md
8         125,204  Read compliance-requirements.md
10        133,009  Read module-epsilon.md
12        138,473  Read module-phi.md
14        149,347  Read data-pipeline-overview.md
15        160,167  Analysis complete (peak)
16        18,816   RESET (83% through session)
```

This trial reached lower peak tokens (160K vs 175K+ in valid trials) precisely because it read fewer files—a consequence of the protocol violation, not a meaningful experimental outcome.

---

### RQ-BB216-4: Does the `protect_files.py` hook contribute to phantom reads?

**Status**: ANSWERED - **NO**

#### Finding

Both environments show **100% failure rate** among valid trials:
- Full repo (with hook): 100% (8/8)
- Barebones (no hook): 100% (4/4)

#### Conclusion

The hook is **NOT the cause** of phantom reads (they occur without it), and it does **NOT contribute** to increased failure rate (both environments show identical 100% failure rates).

The original analysis noted an apparent 20% difference (80% vs 100%), but this was based on including the invalid trial 092331. With that trial correctly excluded, both environments show identical failure rates.

---

### RQ-BB216-5: Do standard theory predictions hold in the barebones environment?

**Status**: ANSWERED - **YES**

#### Theory Validation

1. **Reset Timing Theory**: All 4 valid failures show mid-session resets (50-90%) consistent with the theory
   - 092743: Resets at 63%, 86%
   - 093127: Resets at 27%, 54%, 93%
   - 093818: Resets at 75%, 90%
   - 094145: Resets at 51%, 61%, 87%

2. **X+Y Interaction**: All failures occurred with X ≈ 116K and Y ≈ 57K, consistent with the danger zone model

3. **Deferred Reads**: All failures showed `has_tool_results: true`, indicating content was persisted to disk (deferred reads occurred)

4. **Self-Report Accuracy**: All Session Agents correctly identified when phantom reads occurred (100% accuracy in this collection)

#### Conclusion

Standard theory predictions hold perfectly in the barebones environment. This confirms the theories describe the Claude Code harness behavior itself, not any interaction with WSD or other framework-specific factors.

---

## Cross-Collection Comparison

| Metric                 | Barebones-216                   | Method-04 Firstrun (Hard)       |
| ---------------------- | ------------------------------- | ------------------------------- |
| **Valid Trials**       | 4                               | 4                               |
| **Failure Rate**       | 100%                            | 100%                            |
| **Avg Baseline**       | 20k                             | 23k                             |
| **Avg Post-Setup (X)** | 116k                            | 120k                            |
| **Avg Post-Analysis**  | 176k                            | 175k                            |
| **Reset Patterns**     | Mixed (all include mid-session) | Mixed (all include mid-session) |
| **Theory Predictions** | 100% accurate                   | 100% accurate                   |

**Conclusion**: The two collections are statistically indistinguishable in terms of phantom read behavior. The only measurable difference is ~3-4k lower baseline overhead in barebones, which has no effect on outcomes.

---

## Conclusions

### Confirmed Findings

1. **Phantom reads are a harness-level bug** - They occur in minimal environments without any framework overhead
2. **The WSD framework is not the cause** - Removing it does not prevent phantom reads
3. **The `protect_files.py` hook is not a factor** - 100% failure rate both with and without it
4. **100% failure rate achieved** - All valid trials failed, matching Method-04 results
5. **Standard theories validated** - Reset timing, X+Y interaction, and deferred reads predictions all hold in barebones
6. **Trial 092331 was invalid** - A protocol violation, not evidence of Y non-determinism

### Key Takeaway

**The Barebones-216 experiment successfully demonstrates that phantom reads can be reproduced in a minimal environment**, providing a clean reproduction case for bug reporting and external validation. The bug is definitively a Claude Code harness issue affecting all users under the right context pressure conditions.

---

## Document History

- **2026-01-27**: Initial creation with RQ-BB216-1 analysis
- **2026-01-27**: Updated RQ-BB216-3 to correctly classify trial 092331 as protocol violation; updated all statistics to reflect 100% (4/4) valid failure rate; completed remaining RQ analyses
