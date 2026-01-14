# Reproduction Environment Plan

**Created**: 2026-01-14
**Purpose**: Document findings and plan for creating a controlled reproduction environment for phantom reads within this repository.

---

## Background

### The Problem

Currently, phantom read reproduction requires using sessions from the WSD Development project, which has sufficient complexity to trigger the bug. Attempts to reproduce phantom reads in this repository using `/refine-plan docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md` have consistently succeeded (no phantom reads).

### The Goal

Create a self-contained reproduction environment within this repository that can:
1. **Reliably trigger phantom reads** ("hard" case)
2. **Reliably avoid phantom reads** ("easy" case)
3. **Optionally**: Produce 50/50 outcomes for apples-to-apples comparison ("medium" case)

---

## Key Finding: The 140K Token Threshold

### Context Reset Correlation

Analysis of session files revealed that phantom reads correlate with **context reset frequency**:

| Session | Context Resets | Phantom Reads? |
|---------|---------------|----------------|
| 2.0.58-good | 1 | No |
| 2.0.58-bad | 3 | Yes |
| 2.1.6-good | 2 | No |
| 2.1.6-bad | 4 | Yes |

Context resets occur when the `cache_read_input_tokens` field drops significantly (>10K tokens), indicating the system cleared older content from the context window.

### The ~140K Threshold

Sessions that experienced phantom reads (WSD project "bad" sessions) consistently crossed ~140K tokens multiple times, triggering multiple context resets. The token count drops to a "base" level of ~20K tokens after each reset.

Sessions that succeeded stayed below or barely touched the 140K threshold.

---

## Baseline Analysis: This Repository

### Methodology

Analyzed three identical trials from this repository:
- Trial command: `/wsd:init --custom` followed by `/refine-plan docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md`
- Session files stored in: `dev/misc/self-examples/2.1.6-good-baseline-{1,2,3}/`

### Results

| Metric | Baseline 1 | Baseline 2 | Baseline 3 | Average |
|--------|-----------|-----------|-----------|---------|
| Max Tokens | 126,848 | 118,500 | 115,507 | **120,285** |
| Context Resets | 2 | 2 | 2 | 2 |
| Read Operations | 15 | 12 | 14 | ~14 |
| Lines Read | 2,921 | 2,258 | 2,597 | ~2,600 |
| Final Tokens | 20,068 | 20,122 | 20,177 | ~20,122 |

### Key Insights

1. **Already at 2 resets**: Baseline trials have the same reset count as successful WSD sessions
2. **Gap to danger zone**: ~20K tokens below the 140K threshold
3. **Content volume**: ~2,600 lines read across ~14 operations
4. **Reset timing**: First reset around 78-85K tokens, second around 115-127K tokens

### Token Budget Calculation

To trigger phantom reads reliably, we need to add content that pushes total consumption past 140K multiple times:
- **Current max**: ~120K tokens
- **Target for "hard" case**: ~170K+ tokens
- **Additional content needed**: ~50K+ tokens (~4,000+ lines)

---

## Proposed Solution: Controlled Complexity Documents

### Design Approach

Create a fictional "Data Pipeline System" with interconnected specifications. The WPDs will propose refactors that require reading varying amounts of this content.

### Directory Structure

```
docs/
├── specs/                          # NEW: Dummy interconnected specs
│   ├── data-pipeline-overview.md   # System overview (~500 lines)
│   ├── module-alpha.md             # Module spec A (~800 lines)
│   ├── module-beta.md              # Module spec B (~800 lines)
│   ├── module-gamma.md             # Module spec C (~800 lines)
│   ├── integration-layer.md        # Integration spec (~600 lines)
│   └── compliance-requirements.md  # Standards refs (~400 lines)
│                                   # TOTAL: ~3,900 lines
│
└── wpds/                           # NEW: Test WPDs for reproduction
    ├── refactor-easy.md            # References 1 module
    ├── refactor-hard.md            # References ALL modules + standards
    └── refactor-medium.md          # References 2 modules (optional)
```

### Content Requirements

The dummy specs must contain **meaningful content** (not lorem ipsum) because:
- The `/refine-plan` command analyzes content semantically
- Nonsense content might cause the agent to behave abnormally
- Realistic content ensures genuine investigation patterns

### Spec Content Design

**Data Pipeline Overview** (~500 lines):
- High-level architecture description
- Module responsibilities summary
- Data flow diagrams (text-based)
- Cross-references to all module specs

**Module Alpha/Beta/Gamma** (~800 lines each):
- Interface definitions
- Data structures
- Processing logic description
- Error handling approach
- Integration points with other modules
- Compliance requirements references

**Integration Layer** (~600 lines):
- Module interaction patterns
- Message formats
- Sequencing requirements
- Failure handling

**Compliance Requirements** (~400 lines):
- Standards the system must follow
- Audit requirements
- Security considerations

---

## WPD Design

### Easy Case: `refactor-easy.md`

**Objective**: Propose a small, isolated change that requires reading minimal content.

**Example Task**: "Rename the `BATCH_SIZE` constant in Module Alpha to `DEFAULT_BATCH_SIZE`"

**Expected Reads**:
- The WPD itself
- `module-alpha.md` only
- Total additional lines: ~800

**Expected Outcome**:
- Max tokens: ~90-100K
- Context resets: 1-2
- Result: Always succeeds

### Hard Case: `refactor-hard.md`

**Objective**: Propose a cross-cutting change that REQUIRES reading all specs.

**Example Task**: "Refactor the error handling approach across all modules to use a centralized error registry"

**Key Phrasing** (to force reads):
```markdown
## Scope

This refactor affects ALL modules. You MUST review:
- `docs/specs/module-alpha.md` - Current error handling (Section 5)
- `docs/specs/module-beta.md` - Current error handling (Section 5)
- `docs/specs/module-gamma.md` - Current error handling (Section 5)
- `docs/specs/integration-layer.md` - Error propagation patterns
- `docs/specs/compliance-requirements.md` - Error logging requirements
```

**Expected Reads**:
- The WPD itself
- ALL spec files
- Possibly some existing standards from `docs/read-only/`
- Total additional lines: ~4,000+

**Expected Outcome**:
- Max tokens: ~170K+
- Context resets: 4+
- Result: Always fails (phantom reads)

### Medium Case: `refactor-medium.md` (Optional)

**Objective**: Propose a change with some mandatory and some optional reads.

**Example Task**: "Update the data handoff protocol between Module Alpha and Module Beta"

**Key Phrasing** (mix of mandatory and optional):
```markdown
## Required Context
- `docs/specs/module-alpha.md` - Output interface (Section 3)
- `docs/specs/module-beta.md` - Input interface (Section 2)

## Related Context (recommended)
- `docs/specs/integration-layer.md` - May provide useful patterns
- `docs/specs/data-pipeline-overview.md` - Architecture context
```

**Expected Outcome**:
- Thorough agents read everything → ~145K tokens → phantom reads
- Efficient agents read only required → ~100K tokens → success
- Result: ~50/50

---

## Implementation Plan

### Phase 1: Create Directory Structure
- Create `docs/specs/` directory
- Create `docs/wpds/` directory

### Phase 2: Write Spec Content
- Draft `data-pipeline-overview.md` (~500 lines)
- Draft `module-alpha.md` (~800 lines)
- Draft `module-beta.md` (~800 lines)
- Draft `module-gamma.md` (~800 lines)
- Draft `integration-layer.md` (~600 lines)
- Draft `compliance-requirements.md` (~400 lines)

### Phase 3: Write WPDs
- Create `refactor-easy.md` with isolated scope
- Create `refactor-hard.md` with comprehensive scope
- Optionally create `refactor-medium.md` with mixed scope

### Phase 4: Validation
- Run trials with `refactor-easy.md` - confirm consistent success
- Run trials with `refactor-hard.md` - confirm consistent failure
- Analyze session files to verify token consumption matches predictions

### Phase 5: Documentation
- Update README with reproduction instructions
- Document expected outcomes for each WPD
- Add to `docs/core/Experiment-Methodology.md` or create new methodology doc

---

## Content Theme: Data Pipeline System

### Why This Theme?

A data processing pipeline is:
- **Technically plausible**: Readers won't question its existence
- **Naturally modular**: Easy to create interconnected but distinct modules
- **Rich in cross-cutting concerns**: Error handling, logging, compliance naturally span modules
- **Familiar to AI assistants**: Common enough that investigation will proceed normally

### High-Level Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Module    │────▶│   Module    │────▶│   Module    │
│   Alpha     │     │    Beta     │     │   Gamma     │
│  (Ingest)   │     │ (Transform) │     │  (Output)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Integration │
                    │   Layer     │
                    └─────────────┘
```

- **Module Alpha**: Data ingestion (sources, validation, buffering)
- **Module Beta**: Data transformation (parsing, normalization, enrichment)
- **Module Gamma**: Data output (formatting, delivery, acknowledgment)
- **Integration Layer**: Cross-module coordination, error propagation, monitoring

---

## Risk Considerations

### Hawthorne Effect

Agents working in a project explicitly dedicated to detecting phantom reads might behave differently. The dummy specs should appear as a legitimate subsystem, not as "phantom read bait."

**Mitigation**: The Data Pipeline System content should be written as if it's a real system being documented, not as test fixtures.

### Content Quality

Poor-quality or nonsensical content might cause `/refine-plan` to behave abnormally.

**Mitigation**: Invest in writing coherent, technically plausible specifications even though they describe a fictional system.

### Token Estimation Accuracy

Our estimates (~12 tokens per line) are rough. Actual consumption may vary.

**Mitigation**: Build in margin - target 4,500+ lines for "hard" case to ensure we clear 140K even with estimation error.

---

## Success Criteria

1. **Easy case**: 5 consecutive trials all succeed (no phantom reads)
2. **Hard case**: 5 consecutive trials all fail (phantom reads occur)
3. **Medium case** (optional): Approximately 50% success rate across 10 trials

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1: Create directory structure
3. Begin Phase 2: Draft spec content (most time-intensive)
4. Proceed through remaining phases

---

## References

- `docs/core/Context-Reset-Analysis.md` - Full context reset investigation
- `docs/core/Example-Session-Analysis.md` - Session file structure analysis
- `dev/misc/self-examples/` - Baseline trial session files
- `dev/misc/session-examples/` - WSD project session files for comparison

---

*This document captures the analysis and planning work performed on 2026-01-14.*
