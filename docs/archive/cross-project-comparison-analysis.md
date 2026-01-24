# Cross-Project Comparison Analysis

## Objective

Identify the systematic differences between WSD-Dev trials (which reliably trigger phantom reads) and our Reproduction Environment trials (which do not trigger phantom reads) to inform the design of an effective reproduction scenario.

## Argument for This Analysis

We have a natural experiment sitting in our data:

| Dataset | Location | Trials | Outcomes |
|---------|----------|--------|----------|
| **WSD-Dev** | `dev/misc/wsd-dev-02/` | 22 | 5 SUCCESS (22.7%), 17 FAILURE (77.3%) |
| **Repro Environment** | `dev/misc/repro-attempts-02/` | TBD | TBD |

Both datasets use:
- Same methodology (`/wsd:init --custom` → `/refine-plan`)
- Same Claude Code version (2.1.6)
- Same model (Opus 4.5)
- Same general operation pattern (multi-file read triggered by custom command)

Yet one project reliably triggers phantom reads and the other doesn't. **The gap itself is the research opportunity.**

Rather than collecting "more data" (same project) or "different data" (third project), we should first understand what we have. If we can identify WHAT makes WSD-Dev different, we advance both:
- **Thrust #1 (Understanding)**: Learn what triggers mid-session resets
- **Thrust #2 (Repro Design)**: Know exactly what to change in our reproduction environment

## Hypothesis

The WSD-Dev environment differs from our Repro Environment in one or more dimensions that cause mid-session context resets (50-90% through the session). Candidate dimensions:

1. **Pre-operation context consumption** - WSD-Dev may start `/refine-plan` with higher baseline token consumption due to more extensive onboarding
2. **File count during operation** - WSD-Dev may read more files, creating more opportunities for reset triggers
3. **Token accumulation rate** - WSD-Dev may cause faster/bursty token accumulation during the operation
4. **File interconnectedness** - WSD-Dev specs may have denser cross-references, causing deeper read chains
5. **Individual file sizes** - WSD-Dev may have larger individual files that stress context management

## Data Sources

### WSD-Dev Trials (`dev/misc/wsd-dev-02/`)

Each trial directory contains:
- `chat-export.md` - Full conversation including `/context` outputs
- `trial_data.json` - Preprocessed data (schema 1.1) with reset timing, token counts, file reads
- Session `.jsonl` files - Raw session data

Known trials with `trial_data.json`:
- 20260119-131802 (SUCCESS)
- 20260119-132353 (FAILURE)
- 20260119-133027 (FAILURE)
- 20260119-133726 (FAILURE)
- 20260119-140145 (FAILURE)
- 20260119-140906 (FAILURE)
- 20260119-142117 (SUCCESS)
- 20260120-085448 (FAILURE)
- 20260120-090047 (FAILURE)
- 20260120-090749 (FAILURE)
- 20260120-091421 (FAILURE)
- 20260120-092143 (FAILURE)
- 20260120-093204 (SUCCESS)
- 20260120-094012 (FAILURE)
- 20260120-094605 (FAILURE)
- 20260120-095152 (SUCCESS)
- 20260120-100042 (FAILURE)
- 20260120-100714 (FAILURE)
- 20260120-101415 (FAILURE)
- 20260120-102044 (FAILURE)
- 20260120-102909 (SUCCESS)
- 20260120-103814 (FAILURE)

### Repro Environment Trials (`dev/misc/repro-attempts-02/`)

To be collected using current repo state. Each trial directory will contain:
- `YYYYMMDD-HHMMSS.txt` - Chat export
- `trial_data.json` - Preprocessed data (schema 1.1)
- Session `.jsonl` files

Token counts file: `file_token_counts.json` (to be generated after trials)

## Methodology

### Phase 1: Data Inventory and Normalization

Ensure both datasets have comparable data extracted:

1. Verify repro trial structure and contents
2. Extract or generate `trial_data.json` for repro trials if missing
3. Confirm both datasets have: pre-op tokens, post-op tokens, reset counts, reset positions, files read

### Phase 2: Aggregate Metric Comparison

Compare high-level metrics between the two project populations:

| Metric | WSD-Dev (n=22) | Repro (n=?) |
|--------|----------------|-------------|
| Mean pre-op tokens | ? | ? |
| Mean post-op tokens | ? | ? |
| Mean delta (tokens added) | ? | ? |
| Mean reset count | ? | ? |
| Mean files read | ? | ? |
| Failure rate | 77.3% | ? |

### Phase 3: Reset Timing Pattern Analysis

Compare reset timing distributions:

1. Extract reset positions (as % of session) for all trials
2. Categorize by pattern (EARLY_PLUS_LATE, EARLY_PLUS_MID_LATE, etc.)
3. Compare pattern distributions between projects

**Key question**: Do repro trials simply not have mid-session resets, or do they have resets at different positions?

### Phase 4: File Read Pattern Analysis

Compare what files are read and in what pattern:

1. List all files read during `/refine-plan` in each project
2. Compare total file counts
3. Compare individual file sizes (tokens)
4. Analyze read sequence patterns (bursts vs steady)

### Phase 5: Onboarding Comparison

Compare what happens BEFORE `/refine-plan`:

1. What files are read during `/wsd:init --custom` and `/wsd:onboard` in each project?
2. How much context is consumed by onboarding in each?
3. Are there differences in the Project-Bootstrapper file recommendations?

### Phase 6: Synthesis and Recommendations

Based on findings, formulate:
1. **Primary differentiator(s)** - What most explains the gap?
2. **Reproduction design changes** - What should we modify in our repro environment?
3. **Testable predictions** - What should happen if we make those changes?

## Expected Outcomes

1. **Identification of key differentiator(s)** between projects
2. **Specific recommendations** for modifying our reproduction environment
3. **Testable predictions** that can validate our understanding
4. **Refined theory** of what triggers phantom reads

## Execution Checkboxlist

### Phase 1: Data Inventory and Normalization

- [ ] **1.1** - Inventory repro trial contents in `dev/misc/repro-attempts-02/`
- [ ] **1.2** - Generate `trial_data.json` for repro trials (via `/update-trial-data`)
- [ ] **1.3** - Create `file_token_counts.json` for repro trials
- [ ] **1.4** - Fill token counts and re-run `/update-trial-data`
- [ ] **1.5** - Verify WSD-Dev trial data completeness (22 trials with trial_data.json)
- [ ] **1.6** - Document any data gaps or limitations

### Phase 2: Aggregate Metric Comparison

- [ ] **2.1** - Extract aggregate metrics from WSD-Dev trials
- [ ] **2.2** - Extract aggregate metrics from Repro trials
- [ ] **2.3** - Create comparison table
- [ ] **2.4** - Identify statistically significant differences

### Phase 3: Reset Timing Pattern Analysis

- [ ] **3.1** - Extract reset positions for all trials in both projects
- [ ] **3.2** - Categorize reset patterns for each trial
- [ ] **3.3** - Compare pattern distributions
- [ ] **3.4** - Document findings

### Phase 4: File Read Pattern Analysis

- [ ] **4.1** - List files read during `/refine-plan` for sample WSD-Dev trials (2 SUCCESS, 2 FAILURE)
- [ ] **4.2** - List files read during `/refine-plan` for all Repro trials
- [ ] **4.3** - Compare file counts, sizes, and read sequences
- [ ] **4.4** - Document findings

### Phase 5: Onboarding Comparison

- [ ] **5.1** - Analyze onboarding file reads in WSD-Dev trials
- [ ] **5.2** - Analyze onboarding file reads in Repro trials
- [ ] **5.3** - Compare pre-operation context consumption
- [ ] **5.4** - Document findings

### Phase 6: Synthesis and Recommendations

- [ ] **6.1** - Synthesize findings across all phases
- [ ] **6.2** - Identify primary differentiator(s)
- [ ] **6.3** - Formulate reproduction design recommendations
- [ ] **6.4** - Define testable predictions
- [ ] **6.5** - Update Investigation-Journal.md with findings

---

## Notes for Continuation

If this analysis spans multiple agent sessions:

1. **Current progress** should be tracked via the checkboxlist above
2. **Intermediate findings** should be appended to the "Findings" section below
3. **Data extracts** can be placed in `dev/diagnostics/` for reference
4. **Final synthesis** should update `docs/core/Investigation-Journal.md`

---

## Findings

*(To be populated during execution)*

