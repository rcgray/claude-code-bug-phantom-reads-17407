# Reproduction Environment Feature - Requirements Draft

**Purpose**: This document specifies the requirements for creating a controlled phantom read reproduction environment within this repository. It is intended to serve as input for a formal Feature Overview.

**Created**: 2026-01-14
**Status**: Draft for discussion

---

## 1. Feature Overview

### 1.1 Problem Statement

This repository cannot currently reproduce phantom reads because its `/refine-plan` operations consume insufficient tokens (~120K) to trigger the ~140K threshold that causes context resets leading to phantom reads. All reproduction trials consistently succeed.

### 1.2 Solution

Create a set of dummy specification documents (`docs/specs/`) and test Work Plan Documents (`docs/wpds/`) that provide controlled complexity levels, allowing predictable phantom read reproduction.

### 1.3 Success Criteria

| Test Case | Metric | Target |
|-----------|--------|--------|
| Easy WPD | Phantom read rate | 0% (5/5 trials succeed) |
| Hard WPD | Phantom read rate | 100% (5/5 trials fail) |
| Medium WPD | Phantom read rate | 40-60% (mixed results) |

---

## 2. Spec Files Requirements

### 2.1 Directory Structure

```
docs/specs/
├── data-pipeline-overview.md
├── module-alpha.md
├── module-beta.md
├── module-gamma.md
├── integration-layer.md
└── compliance-requirements.md
```

### 2.2 Content Theme

All specs describe a fictional **"Data Pipeline System"** - a data processing system with three modules (ingest, transform, output) plus integration and compliance layers.

**Why this theme:**
- Technically plausible (won't confuse investigating agents)
- Naturally modular (distinct but interconnected components)
- Rich in cross-cutting concerns (error handling, logging, compliance)
- Familiar enough that `/refine-plan` investigation proceeds normally

### 2.3 Individual Spec Requirements

#### 2.3.1 `data-pipeline-overview.md`

**Purpose**: High-level system architecture document that references all modules.

**Target Size**: 400-600 lines (~5,000-7,000 tokens)

**Required Sections**:
1. **System Purpose** - What the pipeline does, business context
2. **Architecture Diagram** - ASCII/text-based component diagram
3. **Module Summary** - Brief description of each module with explicit references:
   - "See `module-alpha.md` for ingestion details"
   - "See `module-beta.md` for transformation details"
   - "See `module-gamma.md` for output details"
4. **Data Flow** - How data moves through the system
5. **Cross-Cutting Concerns** - Error handling philosophy, logging approach, monitoring
6. **Compliance Overview** - Reference to `compliance-requirements.md`

**Key Requirement**: Must contain explicit file references to ALL other specs to serve as a "hub" document.

---

#### 2.3.2 `module-alpha.md`

**Purpose**: Specification for the data ingestion module.

**Target Size**: 700-900 lines (~8,000-11,000 tokens)

**Required Sections**:
1. **Module Overview** - Purpose and responsibilities
2. **Input Sources** - Types of data sources supported (files, APIs, streams)
3. **Data Structures** - Input record format, internal buffer structures
4. **Validation Rules** - Input validation logic (at least 10 distinct rules)
5. **Error Handling** - How ingestion errors are handled, retry logic
6. **Configuration** - Configurable parameters (batch size, timeout, etc.)
7. **Integration Points** - How it hands off to Module Beta
   - Must reference: "See `integration-layer.md` for handoff protocol"
8. **Compliance** - Audit logging requirements
   - Must reference: "See `compliance-requirements.md` Section 3"

**Key Requirements**:
- Must define at least 5 named constants (e.g., `DEFAULT_BATCH_SIZE`, `MAX_RETRY_COUNT`)
- Must describe error handling in sufficient detail for refactor scenarios
- Must have clear section numbers for targeted references

---

#### 2.3.3 `module-beta.md`

**Purpose**: Specification for the data transformation module.

**Target Size**: 700-900 lines (~8,000-11,000 tokens)

**Required Sections**:
1. **Module Overview** - Purpose and responsibilities
2. **Transformation Pipeline** - Stages of transformation (parse, normalize, enrich, validate)
3. **Data Structures** - Internal record format, transformation context
4. **Transformation Rules** - At least 15 distinct transformation operations
5. **Error Handling** - How transformation errors are handled, partial failure behavior
6. **Configuration** - Configurable parameters (parallelism, chunk size, etc.)
7. **Integration Points** - How it receives from Alpha, hands off to Gamma
   - Must reference: "See `integration-layer.md` for protocols"
8. **Compliance** - Data lineage tracking requirements
   - Must reference: "See `compliance-requirements.md` Section 4"

**Key Requirements**:
- Must define at least 5 named constants
- Error handling section must be substantial (150+ lines)
- Must have clear integration with both Alpha and Gamma

---

#### 2.3.4 `module-gamma.md`

**Purpose**: Specification for the data output module.

**Target Size**: 700-900 lines (~8,000-11,000 tokens)

**Required Sections**:
1. **Module Overview** - Purpose and responsibilities
2. **Output Destinations** - Types of outputs (files, databases, APIs, queues)
3. **Data Structures** - Output record format, delivery tracking
4. **Formatting Rules** - Output format specifications (at least 5 formats)
5. **Error Handling** - Delivery failure handling, dead letter queue
6. **Configuration** - Configurable parameters (retry policy, timeout, etc.)
7. **Integration Points** - How it receives from Beta
   - Must reference: "See `integration-layer.md` for protocols"
8. **Compliance** - Delivery confirmation and audit requirements
   - Must reference: "See `compliance-requirements.md` Section 5"

**Key Requirements**:
- Must define at least 5 named constants
- Must describe acknowledgment/confirmation flow
- Error handling must address partial delivery scenarios

---

#### 2.3.5 `integration-layer.md`

**Purpose**: Specification for cross-module integration protocols.

**Target Size**: 500-700 lines (~6,000-8,000 tokens)

**Required Sections**:
1. **Overview** - Purpose of the integration layer
2. **Message Formats** - Standard message structure for inter-module communication
3. **Alpha-to-Beta Protocol** - Handoff specification
4. **Beta-to-Gamma Protocol** - Handoff specification
5. **Error Propagation** - How errors flow between modules
6. **Monitoring Integration** - Health checks, metrics emission
7. **Configuration** - Timeout settings, buffer sizes

**Key Requirements**:
- Must define message schemas
- Must describe error propagation in detail (this is key for "hard" WPD)
- Must reference all three modules

---

#### 2.3.6 `compliance-requirements.md`

**Purpose**: Compliance, audit, and regulatory requirements.

**Target Size**: 300-500 lines (~4,000-6,000 tokens)

**Required Sections**:
1. **Overview** - Regulatory context
2. **Audit Logging** - What must be logged, retention requirements
3. **Module Alpha Compliance** - Ingestion-specific requirements
4. **Module Beta Compliance** - Transformation-specific requirements (data lineage)
5. **Module Gamma Compliance** - Output-specific requirements (delivery confirmation)
6. **Security Requirements** - Data protection, access control
7. **Reporting** - Required reports and their frequency

**Key Requirements**:
- Must have numbered sections that can be referenced from modules
- Must define requirements that span multiple modules (for cross-cutting refactors)

---

### 2.4 Total Spec Content Budget

| File | Target Lines | Est. Tokens |
|------|-------------|-------------|
| data-pipeline-overview.md | 500 | 6,000 |
| module-alpha.md | 800 | 9,600 |
| module-beta.md | 800 | 9,600 |
| module-gamma.md | 800 | 9,600 |
| integration-layer.md | 600 | 7,200 |
| compliance-requirements.md | 400 | 4,800 |
| **TOTAL** | **3,900** | **~46,800** |

This provides sufficient content to push token consumption past 140K when all files are read during `/refine-plan`.

---

## 3. WPD Files Requirements

### 3.1 Directory Structure

```
docs/wpds/
├── refactor-easy.md
├── refactor-hard.md
└── refactor-medium.md
```

### 3.2 WPD Format

All WPDs must follow the standard Work Plan Document format compatible with `/refine-plan`:
- Clear problem statement
- Scope definition
- Required context (file references)
- Proposed changes
- Checkboxlist (implementation tasks)

---

### 3.3 Individual WPD Requirements

#### 3.3.1 `refactor-easy.md` - Isolated Change

**Objective**: A small, self-contained change that requires reading only ONE spec file.

**Proposed Change**: "Rename the `DEFAULT_BATCH_SIZE` constant in Module Alpha to `INITIAL_BATCH_SIZE` and update all references"

**Required Context Section**:
```markdown
## Required Context

To assess this refactor, review:
- `docs/specs/module-alpha.md` - Contains the constant definition and all usages
```

**Expected Agent Behavior**:
- Reads the WPD (~50 lines)
- Reads module-alpha.md (~800 lines)
- Possibly glances at overview (~500 lines)
- Total additional reads: ~1,300 lines (~15K tokens)

**Expected Metrics**:
- Max tokens: ~90-100K (well below threshold)
- Context resets: 1-2
- Outcome: SUCCESS (no phantom reads)

**Checkboxlist** (3-5 items):
```markdown
## Implementation Plan

- [ ] **1.1** - Locate `DEFAULT_BATCH_SIZE` definition in module-alpha.md
- [ ] **1.2** - Rename to `INITIAL_BATCH_SIZE`
- [ ] **1.3** - Update all references within module-alpha.md
- [ ] **1.4** - Update any references in data-pipeline-overview.md if present
```

---

#### 3.3.2 `refactor-hard.md` - Cross-Cutting Change

**Objective**: A comprehensive change that REQUIRES reading ALL spec files.

**Proposed Change**: "Refactor error handling across ALL modules to use a centralized Error Registry pattern"

**Required Context Section** (CRITICAL - must force all reads):
```markdown
## Required Context

This refactor affects the entire system. You MUST thoroughly review:

**Module Specifications (ALL REQUIRED)**:
- `docs/specs/module-alpha.md` - Current error handling (Section 5)
- `docs/specs/module-beta.md` - Current error handling (Section 5)
- `docs/specs/module-gamma.md` - Current error handling (Section 5)

**Integration and Cross-Cutting (ALL REQUIRED)**:
- `docs/specs/integration-layer.md` - Error propagation patterns (Section 5)
- `docs/specs/compliance-requirements.md` - Error logging requirements (Section 2)

**System Context (REQUIRED)**:
- `docs/specs/data-pipeline-overview.md` - Cross-cutting concerns (Section 5)

Each module's error handling must be analyzed in detail before proposing changes.
```

**Expected Agent Behavior**:
- Reads the WPD (~100 lines)
- Reads ALL six spec files (~3,900 lines)
- May also read some `docs/read-only/standards/` files
- Total additional reads: ~4,000+ lines (~48K+ tokens)

**Expected Metrics**:
- Max tokens: ~170K+ (significantly above threshold)
- Context resets: 4+ (multiple threshold crossings)
- Outcome: FAILURE (phantom reads occur)

**Checkboxlist** (10-15 items spanning all modules):
```markdown
## Implementation Plan

### Phase 1: Error Registry Design
- [ ] **1.1** - Design the central Error Registry interface
- [ ] **1.2** - Define error categories and severity levels
- [ ] **1.3** - Specify error code format

### Phase 2: Module Alpha Updates
- [ ] **2.1** - Replace current error handling with Registry calls
- [ ] **2.2** - Update validation error reporting
- [ ] **2.3** - Update retry logic error handling

### Phase 3: Module Beta Updates
- [ ] **3.1** - Replace current error handling with Registry calls
- [ ] **3.2** - Update transformation error reporting
- [ ] **3.3** - Update partial failure handling

### Phase 4: Module Gamma Updates
- [ ] **4.1** - Replace current error handling with Registry calls
- [ ] **4.2** - Update delivery error reporting

### Phase 5: Integration Updates
- [ ] **5.1** - Update error propagation in integration-layer.md
- [ ] **5.2** - Update compliance error logging requirements
```

---

#### 3.3.3 `refactor-medium.md` - Partial Cross-Cutting Change

**Objective**: A change affecting SOME but not ALL specs, with optional additional context.

**Proposed Change**: "Update the data handoff protocol between Module Alpha and Module Beta to support streaming mode"

**Required Context Section** (mix of required and optional):
```markdown
## Required Context

**Primary Files (MUST review)**:
- `docs/specs/module-alpha.md` - Output interface (Section 7)
- `docs/specs/module-beta.md` - Input interface (Section 7)
- `docs/specs/integration-layer.md` - Alpha-to-Beta protocol (Section 3)

**Supporting Context (recommended for thoroughness)**:
- `docs/specs/data-pipeline-overview.md` - Architecture context
- `docs/specs/compliance-requirements.md` - May have streaming implications
```

**Expected Agent Behavior**:
- **Efficient agents**: Read only required files (~2,100 lines)
- **Thorough agents**: Read all suggested files (~3,400 lines)

**Expected Metrics**:
- Efficient path: ~130K tokens → SUCCESS
- Thorough path: ~155K tokens → FAILURE
- Outcome: ~50% success rate

**Checkboxlist** (6-8 items):
```markdown
## Implementation Plan

### Phase 1: Protocol Design
- [ ] **1.1** - Define streaming message format
- [ ] **1.2** - Specify flow control mechanism

### Phase 2: Module Alpha Changes
- [ ] **2.1** - Add streaming output mode to Alpha
- [ ] **2.2** - Update handoff logic

### Phase 3: Module Beta Changes
- [ ] **3.1** - Add streaming input mode to Beta
- [ ] **3.2** - Update buffer management

### Phase 4: Integration Updates
- [ ] **4.1** - Update integration-layer.md with streaming protocol
```

---

## 4. Dependency Graph

```
                    ┌─────────────────────────┐
                    │  data-pipeline-overview │
                    │      (hub document)     │
                    └───────────┬─────────────┘
                                │ references
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ module-alpha  │   │ module-beta   │   │ module-gamma  │
    └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
            │                   │                   │
            │         ┌─────────┴─────────┐         │
            │         │                   │         │
            ▼         ▼                   ▼         ▼
    ┌─────────────────────────────────────────────────────┐
    │              integration-layer                       │
    │         (cross-module protocols)                     │
    └─────────────────────────────────────────────────────┘
                                │
                                │ references
                                ▼
                    ┌─────────────────────────┐
                    │ compliance-requirements │
                    │    (audit/regulatory)   │
                    └─────────────────────────┘
```

**Reference Direction Summary**:
- `data-pipeline-overview.md` → all modules, integration, compliance
- Each module → `integration-layer.md`, `compliance-requirements.md`
- `integration-layer.md` → all modules (for protocol specs)
- `compliance-requirements.md` → standalone (referenced by others)

---

## 5. Validation Methodology

### 5.1 Trial Execution Protocol

For each WPD, execute the following:

1. **Fresh Session**: Start a new Claude Code session
2. **Initialize**: Run `/wsd:init --custom`
3. **Execute**: Run `/refine-plan docs/wpds/refactor-{easy|hard|medium}.md`
4. **Complete**: Let the agent complete its analysis
5. **Prompt**: Ask "Did you experience any phantom reads during your analysis?"
6. **Export**: Run `/export` to save the session
7. **Archive**: Copy session files to `dev/misc/self-examples/`

### 5.2 Session Archive Naming

```
dev/misc/self-examples/
├── easy-trial-1/          # refactor-easy.md trial 1
├── easy-trial-2/          # refactor-easy.md trial 2
├── ...
├── hard-trial-1/          # refactor-hard.md trial 1
├── hard-trial-2/          # refactor-hard.md trial 2
├── ...
├── medium-trial-1/        # refactor-medium.md trial 1
├── medium-trial-2/        # refactor-medium.md trial 2
└── ...
```

### 5.3 Metrics to Collect

For each trial session, analyze and record:

| Metric | How to Measure | Target (Easy) | Target (Hard) | Target (Medium) |
|--------|---------------|---------------|---------------|-----------------|
| Max tokens | Peak `cache_read_input_tokens` | <100K | >150K | 120-150K |
| Context resets | Count drops >10K in `cache_read_input_tokens` | 1-2 | 4+ | 2-3 |
| Phantom reads | Agent self-report | No | Yes | Mixed |
| Files read | Count `toolUseResult.file` entries | ~5 | ~15+ | ~8-12 |
| Lines read | Sum `numLines` from file reads | <1,500 | >4,000 | 2,000-3,500 |

### 5.4 Analysis Script

Use the same analysis approach as the baseline analysis:

```python
# Pseudo-code for validation analysis
for trial in trials:
    session = load_session(trial)
    metrics = {
        'max_tokens': get_max_cache_read_tokens(session),
        'reset_count': count_context_resets(session),
        'phantom_reads': extract_self_report(trial),
        'files_read': count_file_reads(session),
        'lines_read': sum_lines_read(session)
    }
    record_metrics(trial, metrics)
```

### 5.5 Success Criteria

| WPD | Required Outcome |
|-----|-----------------|
| Easy | 5/5 trials succeed (no phantom reads) |
| Hard | 5/5 trials fail (phantom reads occur) |
| Medium | 4-6/10 trials fail (demonstrable variance) |

If these criteria are not met, iterate on spec/WPD content sizes.

---

## 6. Implementation Phases

### Phase 1: Directory Setup
- Create `docs/specs/` directory
- Create `docs/wpds/` directory
- Estimated effort: Trivial

### Phase 2: Spec Content Creation
- Create all six spec files per requirements
- This is the most time-intensive phase
- Can be parallelized (modules are independent)
- Estimated effort: 6 workscopes (one per file) or 2-3 workscopes (batched)

### Phase 3: WPD Creation
- Create all three WPD files per requirements
- Depends on Phase 2 completion (need spec section numbers)
- Estimated effort: 1-2 workscopes

### Phase 4: Validation Trials
- Execute trials per methodology
- Collect and analyze session data
- Estimated effort: Manual (User runs trials)

### Phase 5: Iteration (if needed)
- Adjust content sizes if metrics don't meet targets
- Re-run validation trials
- Estimated effort: Variable

### Phase 6: Documentation
- Update README with reproduction instructions
- Document expected outcomes
- Estimated effort: 1 workscope

---

## 7. Open Questions for Discussion

1. **Spec content depth**: How much technical detail is needed? Should specs include pseudo-code, or is prose sufficient?

2. **Module differentiation**: Should the three modules be distinctly different, or can they follow a similar template with variation?

3. **Medium WPD design**: Is the "optional context" approach sufficient to create variance, or do we need a different mechanism?

4. **Standards integration**: Should the specs reference actual `docs/read-only/standards/` files, or remain self-contained?

5. **Maintenance burden**: Once created, will these specs need ongoing maintenance, or are they static test fixtures?

---

## 8. References

- `docs/core/Context-Reset-Analysis.md` - Token threshold discovery
- `docs/workbench/reproduction-environment-plan.md` - Initial planning document
- `dev/misc/self-examples/` - Baseline trial data
- `dev/misc/session-examples/` - WSD project comparison data

---

*This document is ready for discussion. Upon approval, use `/create-feature` to formalize as a Feature Overview.*
