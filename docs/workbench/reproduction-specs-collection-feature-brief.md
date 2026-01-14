# Feature Brief: Reproduction Specs Collection

**Date**: 2026-01-14
**Prepared by**: User Agent (Workscope-20260114-085103)
**For**: Feature-Writer Agent

---

## Executive Summary

Create a collection of interconnected specification documents and test Work Plan Documents (WPDs) that enable controlled reproduction of phantom reads within this repository by manipulating token consumption during `/refine-plan` operations.

---

## Problem Statement

This repository cannot currently reproduce phantom reads because its `/refine-plan` operations consume insufficient tokens (~120K average) to trigger the ~140K threshold that causes context resets leading to phantom reads. All reproduction trials using existing content consistently succeed.

The investigation discovered that phantom reads correlate with context reset frequency, and context resets occur when token consumption crosses approximately 140K tokens. Sessions with 4+ resets consistently experience phantom reads, while sessions with 1-2 resets typically succeed.

**Current state (baseline trials on this repo)**:
- Average max tokens: ~120,285
- Average context resets: 2
- Outcome: 100% success (no phantom reads)

**Target state**:
- "Hard" WPD: Forces ~170K+ tokens → 4+ resets → consistent phantom reads
- "Easy" WPD: Stays at ~90K tokens → 1-2 resets → consistent success
- "Medium" WPD (optional): ~145K tokens → 2-3 resets → ~50% failure rate

---

## Solution Overview

Create a fictional "Data Pipeline System" specification set in `docs/specs/` comprising six interconnected documents totaling ~3,900 lines (~47K tokens). Then create test WPDs in `docs/wpds/` that reference varying amounts of this content to control token consumption during `/refine-plan` execution.

The specs describe a three-module data processing pipeline (ingest, transform, output) with integration and compliance layers. The content must be technically plausible (not lorem ipsum) to ensure agents investigate normally.

---

## Relationship to Existing Systems

### Relationship to Session Analysis Scripts Feature

The Session Analysis Scripts feature (`docs/features/session-analysis-scripts/`) provides tools for analyzing session files. The Reproduction Specs Collection complements it by providing **controlled test cases** that generate sessions for analysis.

Once both features are implemented:
1. Run `/refine-plan` on a test WPD → generates a session
2. Use Session Analysis Scripts → analyze the session for phantom reads

### Relationship to `/refine-plan` Command

The `/refine-plan` command (`.claude/commands/refine-plan.md`) triggers deep investigation of a WPD. This feature exploits that behavior by creating WPDs that force the command to read varying amounts of content.

### Relationship to Existing Docs Directories

- `docs/specs/` - **NEW directory** for dummy specification content
- `docs/wpds/` - **NEW directory** for test WPDs (separate from real features/tickets)
- `dev/misc/self-examples/` - **EXISTING** for storing trial session files

---

## Deliverables

### 1. New Directory: `docs/specs/`

Create a directory containing six interconnected specification documents describing a fictional Data Pipeline System.

### 2. New File: `docs/specs/data-pipeline-overview.md`

**Purpose**: Hub document providing system architecture and referencing all other specs.

**Requirements**:
- Target size: 400-600 lines
- Must contain explicit file references to ALL other spec files
- Sections: System Purpose, Architecture Diagram (ASCII), Module Summary, Data Flow, Cross-Cutting Concerns, Compliance Overview

### 3. New File: `docs/specs/module-alpha.md`

**Purpose**: Specification for data ingestion module.

**Requirements**:
- Target size: 700-900 lines
- Must define at least 5 named constants (e.g., `DEFAULT_BATCH_SIZE`)
- Must have substantial error handling section (150+ lines)
- Sections: Overview, Input Sources, Data Structures, Validation Rules (10+), Error Handling, Configuration, Integration Points, Compliance
- Must reference `integration-layer.md` and `compliance-requirements.md`

### 4. New File: `docs/specs/module-beta.md`

**Purpose**: Specification for data transformation module.

**Requirements**:
- Target size: 700-900 lines
- Must define at least 5 named constants
- Must have substantial error handling section (150+ lines)
- Sections: Overview, Transformation Pipeline, Data Structures, Transformation Rules (15+), Error Handling, Configuration, Integration Points, Compliance
- Must reference both Alpha and Gamma modules, `integration-layer.md`, `compliance-requirements.md`

### 5. New File: `docs/specs/module-gamma.md`

**Purpose**: Specification for data output module.

**Requirements**:
- Target size: 700-900 lines
- Must define at least 5 named constants
- Must describe acknowledgment/confirmation flow
- Sections: Overview, Output Destinations, Data Structures, Formatting Rules (5+), Error Handling, Configuration, Integration Points, Compliance
- Must reference `integration-layer.md` and `compliance-requirements.md`

### 6. New File: `docs/specs/integration-layer.md`

**Purpose**: Cross-module integration protocols and message formats.

**Requirements**:
- Target size: 500-700 lines
- Must define message schemas
- Must describe error propagation in detail (key for "hard" WPD refactor)
- Sections: Overview, Message Formats, Alpha-to-Beta Protocol, Beta-to-Gamma Protocol, Error Propagation, Monitoring, Configuration
- Must reference all three modules

### 7. New File: `docs/specs/compliance-requirements.md`

**Purpose**: Audit, regulatory, and compliance requirements.

**Requirements**:
- Target size: 300-500 lines
- Must have numbered sections for module-specific references
- Must define requirements that span multiple modules
- Sections: Overview, Audit Logging, Module Alpha Compliance, Module Beta Compliance, Module Gamma Compliance, Security, Reporting

### 8. New Directory: `docs/wpds/`

Create a directory for test Work Plan Documents.

### 9. New File: `docs/wpds/refactor-easy.md`

**Purpose**: Test WPD that references minimal content → always succeeds.

**Requirements**:
- Proposes isolated change: "Rename `DEFAULT_BATCH_SIZE` to `INITIAL_BATCH_SIZE` in Module Alpha"
- Required Context section references ONLY `module-alpha.md`
- Expected reads: ~1,300 lines additional
- Expected outcome: ~90-100K tokens, 1-2 resets, SUCCESS
- Must include checkboxlist with 3-5 tasks

### 10. New File: `docs/wpds/refactor-hard.md`

**Purpose**: Test WPD that references ALL content → always fails (phantom reads).

**Requirements**:
- Proposes cross-cutting change: "Refactor error handling to use centralized Error Registry"
- Required Context section MUST explicitly require reading ALL six spec files
- Must use language like "You MUST thoroughly review" and "Each module's error handling must be analyzed in detail"
- Expected reads: ~4,000+ lines additional
- Expected outcome: ~170K+ tokens, 4+ resets, FAILURE
- Must include checkboxlist with 10-15 tasks spanning all modules

### 11. New File: `docs/wpds/refactor-medium.md`

**Purpose**: Test WPD with mixed required/optional context → ~50% failure rate.

**Requirements**:
- Proposes partial change: "Update data handoff protocol between Alpha and Beta for streaming mode"
- Required Context section has two tiers:
  - "Primary Files (MUST review)": alpha, beta, integration-layer
  - "Supporting Context (recommended)": overview, compliance
- Expected reads: 2,100-3,400 lines depending on agent thoroughness
- Expected outcome: ~130-155K tokens, 2-3 resets, MIXED results
- Must include checkboxlist with 6-8 tasks

### 12. Documentation Update: `README.md`

Update the README to document how to use the reproduction environment:
- Reference `docs/specs/` and `docs/wpds/`
- Explain expected outcomes for each WPD
- Link to validation methodology

---

## Design Constraints

1. **Content must be meaningful**: Spec content must be technically plausible, not lorem ipsum. Nonsense content may cause agents to behave abnormally during `/refine-plan`.

2. **Reference graph is critical**: The WPDs' "Required Context" sections control what agents read. The wording must be precise and directive.

3. **Token estimates are approximate**: The ~12 tokens per line estimate is rough. Build in margin - target 4,500+ lines for hard case.

4. **Separate from real features**: Use `docs/specs/` and `docs/wpds/` directories, NOT `docs/features/` or `docs/tickets/`, to avoid confusion with actual project work.

5. **No Phase 0 in FIP**: Phase 0 is reserved for emergent blocking issues, not initial planning.

---

## Out of Scope

1. **Actual implementation of Data Pipeline**: The specs describe a fictional system; no code implementation is needed or expected.

2. **Integration with Session Analysis Scripts**: While complementary, this feature doesn't modify or depend on the analysis scripts.

3. **Automated trial execution**: Users run trials manually; this feature only provides the test fixtures.

4. **Token counting tools**: We rely on session file analysis, not real-time token counting.

---

## Success Criteria

| Test Case | Metric | Target |
|-----------|--------|--------|
| Easy WPD | Max tokens | <100K |
| Easy WPD | Context resets | 1-2 |
| Easy WPD | Phantom read rate | 0% (5/5 succeed) |
| Hard WPD | Max tokens | >150K |
| Hard WPD | Context resets | 4+ |
| Hard WPD | Phantom read rate | 100% (5/5 fail) |
| Medium WPD | Max tokens | 120-150K |
| Medium WPD | Context resets | 2-3 |
| Medium WPD | Phantom read rate | 40-60% (mixed) |

Validation methodology:
1. Run `/wsd:init --custom` then `/refine-plan docs/wpds/refactor-{type}.md`
2. Ask agent for phantom read self-report
3. Export session and save to `dev/misc/self-examples/{type}-trial-N/`
4. Analyze session for max tokens, reset count, files read

---

## Implementation Notes

### Total Content Budget

| File | Target Lines | Est. Tokens |
|------|-------------|-------------|
| data-pipeline-overview.md | 500 | 6,000 |
| module-alpha.md | 800 | 9,600 |
| module-beta.md | 800 | 9,600 |
| module-gamma.md | 800 | 9,600 |
| integration-layer.md | 600 | 7,200 |
| compliance-requirements.md | 400 | 4,800 |
| **TOTAL** | **3,900** | **~46,800** |

### Dependency Graph

```
                    ┌─────────────────────────┐
                    │  data-pipeline-overview │
                    │      (hub document)     │
                    └───────────┬─────────────┘
                                │ references all
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ module-alpha  │   │ module-beta   │   │ module-gamma  │
    └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
            │                   │                   │
            └───────────────────┼───────────────────┘
                                │ all reference
                                ▼
                    ┌─────────────────────────┐
                    │   integration-layer     │
                    │ compliance-requirements │
                    └─────────────────────────┘
```

### Baseline Comparison Data

Reference data from `dev/misc/self-examples/2.1.6-good-baseline-{1,2,3}/`:
- Baseline max tokens: 115K-127K (avg 120K)
- Baseline resets: 2 each
- Baseline outcome: All succeed

Reference data from `dev/misc/session-examples/2.1.6-bad/`:
- Failed session max tokens: 141K
- Failed session resets: 4
- Failed session outcome: Phantom reads occurred

### FIP Phase Suggestions

**Phase 1**: Directory Setup and Overview (create directories, write overview doc)
**Phase 2**: Module Specifications (write alpha, beta, gamma)
**Phase 3**: Cross-Cutting Specs (write integration-layer, compliance)
**Phase 4**: WPD Creation (write easy, hard, medium WPDs)
**Phase 5**: Documentation (update README with reproduction instructions)

Each phase can be a separate workscope. Phases 2-3 could potentially be parallelized.

---

## Questions for Feature-Writer

None - this brief captures all design decisions from the User Agent's conversation with the User.

---

## References

- `docs/workbench/reproduction-environment-feature-draft.md` - Detailed requirements draft
- `docs/workbench/reproduction-environment-plan.md` - Initial planning document
- `docs/core/Context-Reset-Analysis.md` - Token threshold discovery
- `dev/misc/self-examples/` - Baseline trial data
