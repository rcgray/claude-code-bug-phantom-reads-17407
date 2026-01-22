# Reproduction Specs Collection Specification

**Version:** 1.0.0
**Date:** 2026-01-14
**Status:** Draft

## Overview

The Reproduction Specs Collection provides a controlled phantom read reproduction environment by delivering dummy specification documents and test Work Plan Documents (WPDs) that manipulate token consumption during `/refine-plan` operations. This feature enables predictable reproduction of phantom reads within this repository by providing content of known complexity levels that trigger specific token consumption patterns.

This specification defines the complete set of files comprising the reproduction environment: six interconnected specification documents describing a fictional "Data Pipeline System" and three test WPDs that reference varying amounts of this content. The specs and WPDs are designed to exploit the ~140K token threshold discovery documented in `docs/core/Context-Reset-Analysis.md`, allowing researchers to reliably trigger or avoid phantom read conditions.

For background on the token threshold discovery and context reset correlation, see `docs/core/Context-Reset-Analysis.md`.

## Purpose

The Reproduction Specs Collection serves four critical functions:

1. **Controlled Token Manipulation**: Provides content of known size and complexity that, when referenced by WPDs, forces predictable token consumption levels during `/refine-plan` operations. This enables researchers to reliably cross or stay below the ~140K token threshold that correlates with context resets.

2. **Phantom Read Triggering**: Supplies a "hard" WPD that forces investigation of all six spec files (~47K tokens of additional content), pushing total session consumption above 150K tokens and triggering 4+ context resets that consistently produce phantom reads.

3. **Baseline Establishment**: Provides an "easy" WPD that restricts investigation to a single spec file (~9K tokens), keeping total session consumption below 100K tokens with 1-2 resets, consistently avoiding phantom reads.

4. **Threshold Exploration**: Offers a "medium" WPD that targets the boundary zone (~130-155K tokens), producing mixed results that validate the threshold hypothesis and enable calibration of detection sensitivity.

This specification establishes the authoritative definition of the fictional Data Pipeline System domain (spec file structure, content themes, and interconnections), the WPD reference patterns that control agent investigation scope, and the expected outcomes for each difficulty tier.

## Spec Files Architecture

### Directory Structure

All reproduction content resides in dedicated directories separate from real project documentation:

```
docs/
├── specs/                              # Dummy specification files
│   ├── data-pipeline-overview.md       # Hub document (~500 lines)
│   ├── module-alpha.md                 # Ingestion module (~800 lines)
│   ├── module-beta.md                  # Transformation module (~800 lines)
│   ├── module-gamma.md                 # Output module (~800 lines)
│   ├── integration-layer.md            # Cross-module protocols (~600 lines)
│   └── compliance-requirements.md      # Audit/regulatory reqs (~400 lines)
└── wpds/                               # Test Work Plan Documents
    ├── refactor-easy.md                # Minimal scope WPD
    ├── refactor-medium.md              # Partial scope WPD
    └── refactor-hard.md                # Full scope WPD
```

### Content Theme

All specs describe a fictional **Data Pipeline System** consisting of three core modules (ingest, transform, output) with supporting integration and compliance layers. This theme was chosen because it is:

- **Technically plausible**: Content reads as legitimate technical documentation, ensuring agents investigate normally rather than recognizing it as test content
- **Naturally modular**: Distinct but interconnected components enable controlled reference patterns
- **Rich in cross-cutting concerns**: Error handling, logging, and compliance requirements span multiple documents, providing natural justification for cross-document investigation
- **Domain-familiar**: Data pipelines are a common pattern that agents can reason about without special domain knowledge

### Reference Graph

The specs form an intentional dependency graph that the WPDs exploit:

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

The hub document (`data-pipeline-overview.md`) references all other specs, each module references the integration and compliance specs, and the integration spec references all modules. This creates natural pathways for both narrow and broad investigation.

## Spec File Requirements

### data-pipeline-overview.md

**Purpose**: Hub document providing system architecture and referencing all other specs.

**Size**: 400-600 lines (~6,000 tokens)

**Required Content**:
- System Purpose section explaining the fictional pipeline's role
- ASCII Architecture Diagram showing module relationships
- Module Summary section with brief descriptions of Alpha, Beta, and Gamma
- Data Flow section describing the pipeline stages
- Cross-Cutting Concerns section referencing integration and compliance
- Explicit file references to ALL other spec files using relative paths

**Key Constraint**: MUST contain explicit file references (e.g., "See `module-alpha.md` for ingestion details") to all five other spec files. These references guide agent investigation during `/refine-plan`.

### module-alpha.md

**Purpose**: Specification for the data ingestion module.

**Size**: 700-900 lines (~9,600 tokens)

**Required Content**:
- Overview section describing ingestion responsibilities
- Input Sources section listing supported data sources
- Data Structures section with schema definitions
- Validation Rules section with at least 10 numbered rules
- Error Handling section of at least 150 lines
- Configuration section with at least 5 named constants (e.g., `DEFAULT_BATCH_SIZE`, `MAX_RETRY_COUNT`)
- Integration Points section referencing `integration-layer.md`
- Compliance section referencing `compliance-requirements.md`

**Key Constraint**: The constants defined here are the refactor targets for the "easy" WPD. Content MUST be substantial enough to support realistic investigation.

### module-beta.md

**Purpose**: Specification for the data transformation module.

**Size**: 700-900 lines (~9,600 tokens)

**Required Content**:
- Overview section describing transformation responsibilities
- Transformation Pipeline section with stage descriptions
- Data Structures section with intermediate format definitions
- Transformation Rules section with at least 15 numbered rules
- Error Handling section of at least 150 lines
- Configuration section with at least 5 named constants
- Integration Points section referencing `integration-layer.md`, `module-alpha.md`, and `module-gamma.md`
- Compliance section referencing `compliance-requirements.md`

**Key Constraint**: This module serves as the bridge between Alpha and Gamma, making it central to the "medium" WPD's scope.

### module-gamma.md

**Purpose**: Specification for the data output module.

**Size**: 700-900 lines (~9,600 tokens)

**Required Content**:
- Overview section describing output responsibilities
- Output Destinations section listing supported targets
- Data Structures section with output format definitions
- Formatting Rules section with at least 5 numbered rules
- Acknowledgment Flow section describing confirmation protocols
- Error Handling section of at least 150 lines
- Configuration section with at least 5 named constants
- Integration Points section referencing `integration-layer.md`
- Compliance section referencing `compliance-requirements.md`

### integration-layer.md

**Purpose**: Cross-module integration protocols and message formats.

**Size**: 500-700 lines (~7,200 tokens)

**Required Content**:
- Overview section describing integration purpose
- Message Formats section with schema definitions
- Alpha-to-Beta Protocol section with handoff details
- Beta-to-Gamma Protocol section with handoff details
- Error Propagation section with detailed cross-module error handling (critical for "hard" WPD)
- Monitoring section describing observability
- Configuration section with integration-level constants
- References to all three modules

**Key Constraint**: The Error Propagation section is the anchor for the "hard" WPD's cross-cutting refactor. This section MUST be substantial (~100+ lines) and reference error handling in all three modules.

### compliance-requirements.md

**Purpose**: Audit, regulatory, and compliance requirements spanning all modules.

**Size**: 300-500 lines (~4,800 tokens)

**Required Content**:
- Overview section explaining compliance framework
- Audit Logging section with logging requirements
- Module Alpha Compliance section (numbered requirements)
- Module Beta Compliance section (numbered requirements)
- Module Gamma Compliance section (numbered requirements)
- Security section with security requirements
- Reporting section with report format requirements

**Key Constraint**: Numbered sections enable module-specific compliance references from the module specs.

## WPD Requirements

### Common WPD Structure

All test WPDs MUST follow this structure:

```markdown
# [Title]

## Overview
[Brief description of proposed change]

## Required Context
[Files the agent MUST review to execute this refactor]

## Tasks
[Checkboxlist of implementation tasks]
```

The **Required Context** section is the critical lever controlling agent investigation scope and therefore token consumption.

### refactor-easy.md

**Purpose**: Test WPD that restricts investigation to minimal content, ensuring session success.

**Proposed Change**: "Rename `DEFAULT_BATCH_SIZE` to `INITIAL_BATCH_SIZE` in Module Alpha"

**Required Context Section**:
```markdown
## Required Context

To complete this refactor, review the following file:

- `docs/specs/module-alpha.md` - Contains the constant definition and all usage locations
```

**Expected Behavior**:
- Agent reads only `module-alpha.md` (~800 lines)
- Additional token consumption: ~9,600 tokens
- Total session tokens: ~90-100K
- Context resets: 1-2
- Expected outcome: SUCCESS (no phantom reads)

**Task Count**: 3-5 tasks focused on the rename operation

### refactor-hard.md

**Purpose**: Test WPD that forces investigation of ALL content, triggering phantom reads.

**Proposed Change**: "Refactor error handling to use centralized Error Registry pattern across all modules"

**Required Context Section**:
```markdown
## Required Context

This cross-cutting refactor requires thorough review of ALL specification files:

**You MUST thoroughly review each file listed below. Each module's error handling must be analyzed in detail to understand the current error patterns before designing the Error Registry.**

Primary Specifications:
- `docs/specs/data-pipeline-overview.md` - System architecture and module relationships
- `docs/specs/module-alpha.md` - Ingestion module error handling patterns
- `docs/specs/module-beta.md` - Transformation module error handling patterns
- `docs/specs/module-gamma.md` - Output module error handling patterns
- `docs/specs/integration-layer.md` - Cross-module error propagation (CRITICAL)
- `docs/specs/compliance-requirements.md` - Error logging compliance requirements
```

**Expected Behavior**:
- Agent reads all six spec files (~3,900 lines)
- Additional token consumption: ~47,000 tokens
- Total session tokens: ~170K+
- Context resets: 4+
- Expected outcome: FAILURE (phantom reads occur)

**Task Count**: 10-15 tasks spanning all modules and integration concerns

**Key Constraint**: The language MUST be directive ("You MUST thoroughly review", "Each module's error handling must be analyzed in detail"). Weak language allows agents to skip files.

### refactor-medium.md

**Purpose**: Test WPD targeting the threshold boundary, producing mixed results.

**Proposed Change**: "Update data handoff protocol between Alpha and Beta for streaming mode support"

**Required Context Section**:
```markdown
## Required Context

### Primary Files (MUST review)
- `docs/specs/module-alpha.md` - Source of handoff data
- `docs/specs/module-beta.md` - Receiver of handoff data
- `docs/specs/integration-layer.md` - Current handoff protocol specification

### Supporting Context (recommended if time permits)
- `docs/specs/data-pipeline-overview.md` - System context
- `docs/specs/compliance-requirements.md` - Audit requirements for protocol changes
```

**Expected Behavior**:
- Agent reads 3-5 spec files depending on thoroughness
- Additional token consumption: 25-42K tokens
- Total session tokens: ~130-155K
- Context resets: 2-3
- Expected outcome: MIXED (approximately 50% failure rate)

**Task Count**: 6-8 tasks focused on Alpha-Beta interface

**Key Constraint**: The two-tier structure ("MUST" vs "recommended") creates variability in agent behavior, producing the desired mixed results.

## Token Budget

### Spec Content Budget

| File                       | Target Lines | Estimated Tokens |
| -------------------------- | ------------ | ---------------- |
| data-pipeline-overview.md  | 500          | 6,000            |
| module-alpha.md            | 800          | 9,600            |
| module-beta.md             | 800          | 9,600            |
| module-gamma.md            | 800          | 9,600            |
| integration-layer.md       | 600          | 7,200            |
| compliance-requirements.md | 400          | 4,800            |
| **TOTAL**                  | **3,900**    | **~46,800**      |

### Token Estimation Method

The ~12 tokens per line estimate is derived from analysis of existing project documentation. This is approximate; actual token counts vary based on content density. The spec sizes include margin to ensure the "hard" WPD reliably exceeds the ~140K threshold.

### Baseline Comparison

Reference data from successful baseline trials (`dev/misc/self-examples/2.1.6-good-baseline-{1,2,3}/`):
- Average maximum tokens: ~120,285
- Average context resets: 2
- Outcome: 100% success

Reference data from failed sessions (`dev/misc/session-examples/2.1.6-bad/`):
- Maximum tokens: 141K
- Context resets: 4
- Outcome: Phantom reads occurred

The spec collection adds sufficient content to push the "hard" case well above the 141K failure threshold.

## Error Handling

### Error Categories

#### 1. Insufficient Token Consumption

**Error**: "Hard" WPD fails to trigger phantom reads

**Detection**: Post-trial session analysis shows fewer than 4 context resets

**Recovery**:
1. Verify agent read all six spec files (check session logs)
2. If files were skipped, strengthen directive language in Required Context
3. If files were read but tokens insufficient, increase spec file sizes

#### 2. Excessive Token Consumption in Easy Case

**Error**: "Easy" WPD triggers phantom reads when it should succeed

**Detection**: Post-trial session analysis shows 3+ context resets

**Recovery**:
1. Verify agent did not investigate beyond `module-alpha.md`
2. Remove any cross-references in `module-alpha.md` that could trigger expanded investigation
3. Weaken any language in the easy WPD that might encourage broader review

#### 3. Content Recognition

**Error**: Agent recognizes specs as test content and behaves abnormally

**Detection**: Agent commentary in session indicates recognition of fictional/test nature

**Recovery**:
1. Review spec content for obvious "lorem ipsum" patterns
2. Ensure technical content is plausible and domain-appropriate
3. Remove any meta-commentary about the testing purpose

#### 4. WPD Reference Failure

**Error**: Agent cannot locate spec files due to path errors

**Detection**: Read tool errors in session logs

**Recovery**:
1. Verify all paths in WPD Required Context sections are correct
2. Ensure `docs/specs/` directory exists with all expected files
3. Check for typos in filenames

### Error Recovery General Guidance

All errors in this feature manifest during trial execution and are detected through post-trial session analysis. Recovery involves iterating on spec or WPD content and re-running trials. There is no runtime error handling; the feature is static content consumed by the `/refine-plan` command.

## Testing Scenarios

### Basic Functionality Tests

1. **Easy WPD Success Rate**: Run 5 trials with `refactor-easy.md`; expect 5/5 success (no phantom reads reported)
2. **Hard WPD Failure Rate**: Run 5 trials with `refactor-hard.md`; expect 5/5 failure (phantom reads reported)
3. **Medium WPD Mixed Rate**: Run 5 trials with `refactor-medium.md`; expect 2-3 failures

### Edge Case Tests

1. **File Reference Validity**: Verify all file references in WPDs resolve to existing files
2. **Cross-Reference Integrity**: Verify all cross-references within specs point to valid sections
3. **Content Minimums**: Verify each spec meets its minimum line count requirement

### Integration Tests

1. **Session Analysis Compatibility**: Verify trial sessions can be processed by `collect_trials.py` and `analyze_trials.py` from the Session Analysis Scripts feature
2. **Token Counting Accuracy**: Compare estimated token counts (line count x 12) against actual session token consumption
3. **Context Reset Correlation**: Verify trials match the expected reset count for each difficulty tier

### Validation Tests

1. **Content Plausibility**: Have a human reviewer verify specs read as legitimate technical documentation
2. **Directive Strength**: Verify "hard" WPD language successfully forces complete file review
3. **Tier Separation**: Confirm clear separation between easy (<100K), medium (130-155K), and hard (>150K) token consumption

## Success Criteria

| Test Case  | Metric            | Target Value     |
| ---------- | ----------------- | ---------------- |
| Easy WPD   | Max tokens        | <100K            |
| Easy WPD   | Context resets    | 1-2              |
| Easy WPD   | Phantom read rate | 0% (5/5 succeed) |
| Hard WPD   | Max tokens        | >150K            |
| Hard WPD   | Context resets    | 4+               |
| Hard WPD   | Phantom read rate | 100% (5/5 fail)  |
| Medium WPD | Max tokens        | 120-150K         |
| Medium WPD | Context resets    | 2-3              |
| Medium WPD | Phantom read rate | 40-60% (mixed)   |

## Validation Methodology

To validate the reproduction environment:

1. **Session Initiation**: Run `/wsd:init --custom` to start a clean session
2. **Trial Execution**: Run `/refine-plan docs/wpds/refactor-{easy|medium|hard}.md`
3. **Self-Report Collection**: After completion, ask agent about phantom read experience
4. **Session Export**: Export session and save to `dev/misc/self-examples/{difficulty}-trial-N/`
5. **Session Analysis**: Use Session Analysis Scripts to extract max tokens, reset count, and files read
6. **Result Recording**: Record outcome against success criteria

Minimum validation requires 5 trials per difficulty tier (15 total trials) to establish statistical confidence.

## Design Philosophy

### Why Fictional Content

The reproduction environment uses fictional "Data Pipeline System" content rather than real project documentation for several reasons:

1. **Isolation**: Test content is clearly separated from actual project work, preventing confusion during investigation
2. **Control**: Content size and complexity are precisely controlled to hit token targets
3. **Stability**: Fictional content does not change with project evolution, ensuring reproducible trials
4. **Safety**: Agents cannot accidentally modify real specifications while investigating test WPDs

### Why Separate Directories

Using `docs/specs/` and `docs/wpds/` rather than placing content in existing directories (`docs/features/`, `docs/tickets/`) prevents:

1. **Discovery Confusion**: Context-Librarian does not surface fictional specs when searching for real project context
2. **Workscope Pollution**: Task-Master does not see test WPDs when selecting real work
3. **Navigation Errors**: Clear separation makes purpose immediately obvious from path

### Why Directive Language

The WPD Required Context sections use imperative language ("You MUST thoroughly review", "Each module's error handling must be analyzed in detail") because:

1. **Agent Compliance**: Agents interpret weak language ("consider reviewing", "may be helpful") as optional
2. **Predictable Behavior**: Strong directives produce consistent investigation patterns across trials
3. **Token Control**: The primary control mechanism is forcing or preventing file reads; directive language is the lever

## Best Practices

### For Spec Authors

1. **Maintain Technical Plausibility**: All content must read as legitimate technical documentation. Avoid placeholder text, "lorem ipsum" patterns, or meta-commentary about the testing purpose.

2. **Honor Size Targets**: Each spec file has a specific line count target that contributes to the overall token budget. Significant deviation breaks the token consumption predictions.

3. **Preserve Cross-References**: The reference graph between specs is intentional. When adding content, maintain existing cross-references and add new ones consistently.

4. **Use Named Constants**: Module specs should define specific named constants (e.g., `DEFAULT_BATCH_SIZE`) that serve as natural refactoring targets for WPDs.

### For WPD Authors

1. **Be Explicit About Required Files**: The Required Context section directly controls which files agents read. List files by exact path with no ambiguity.

2. **Use Tiered Language for Mixed Results**: The "medium" WPD achieves mixed results through two-tier required context (MUST vs. recommended). Preserve this pattern.

3. **Match Task Count to Scope**: Easy WPDs should have few tasks (3-5), hard WPDs should have many (10-15). Task count signals expected complexity to the agent.

### For Trial Runners

1. **Use Clean Sessions**: Always start trials with `/wsd:init --custom` to ensure consistent baseline token consumption.

2. **Export Before Analysis**: Session data must be exported before it can be analyzed. Save exports to `dev/misc/self-examples/` with descriptive naming.

3. **Record All Results**: Even unexpected results provide valuable data. Record successes and failures with full session context.

## Related Specifications


- **`docs/core/Context-Reset-Analysis.md`**: Documents the ~140K token threshold discovery that this feature exploits
- **`docs/core/PRD.md`**: Project overview and phantom reads background
- **`.claude/commands/refine-plan.md`**: The command whose token consumption this feature manipulates

---

*This specification defines the authoritative rules for the Reproduction Specs Collection including spec file requirements, WPD structures, token budgets, and success criteria. All implementations must conform to these specifications.*

## In-Flight Failures (IFF)

(None documented at specification time)

## Feature Implementation Plan (FIP)

### Phase 1: Directory Setup and Overview Document

- [x] **1.1** - Create directory structure for reproduction content
  - [x] **1.1.1** - Create `docs/specs/` directory
  - [x] **1.1.2** - Create `docs/wpds/` directory
- [x] **1.2** - Write `docs/specs/data-pipeline-overview.md`
  - [x] **1.2.1** - Write System Purpose section
  - [x] **1.2.2** - Create ASCII Architecture Diagram
  - [x] **1.2.3** - Write Module Summary section with Alpha, Beta, Gamma descriptions
  - [x] **1.2.4** - Write Data Flow section
  - [x] **1.2.5** - Write Cross-Cutting Concerns section with explicit references to integration and compliance specs
  - [x] **1.2.6** - Verify all six spec files are explicitly referenced

### Phase 2: Module Specifications

- [x] **2.1** - Write `docs/specs/module-alpha.md` (Ingestion Module)
  - [x] **2.1.1** - Write Overview and Input Sources sections
  - [x] **2.1.2** - Write Data Structures section with schema definitions
  - [x] **2.1.3** - Write Validation Rules section (minimum 10 rules)
  - [x] **2.1.4** - Write Error Handling section (minimum 150 lines)
  - [x] **2.1.5** - Write Configuration section with 5+ named constants including `DEFAULT_BATCH_SIZE`
  - [x] **2.1.6** - Write Integration Points and Compliance sections with cross-references
  - [x] **2.1.7** - Verify total length is 700-900 lines. This is non-negotiable.
- [x] **2.2** - Write `docs/specs/module-beta.md` (Transformation Module)
  - [x] **2.2.1** - Write Overview and Transformation Pipeline sections
  - [x] **2.2.2** - Write Data Structures section with intermediate format definitions
  - [x] **2.2.3** - Write Transformation Rules section (minimum 15 rules)
  - [x] **2.2.4** - Write Error Handling section (minimum 150 lines)
  - [x] **2.2.5** - Write Configuration section with 5+ named constants
  - [x] **2.2.6** - Write Integration Points referencing Alpha, Gamma, and integration-layer
  - [x] **2.2.7** - Write Compliance section with cross-reference
  - [x] **2.2.8** - Verify total length is 700-900 lines. This is non-negotiable.
- [x] **2.3** - Write `docs/specs/module-gamma.md` (Output Module)
  - [x] **2.3.1** - Write Overview and Output Destinations sections
  - [x] **2.3.2** - Write Data Structures section with output format definitions
  - [x] **2.3.3** - Write Formatting Rules section (minimum 5 rules)
  - [x] **2.3.4** - Write Acknowledgment Flow section
  - [x] **2.3.5** - Write Error Handling section (minimum 150 lines)
  - [x] **2.3.6** - Write Configuration section with 5+ named constants
  - [x] **2.3.7** - Write Integration Points and Compliance sections with cross-references
  - [x] **2.3.8** - Verify total length is 700-900 lines. This is non-negotiable.

### Phase 3: Cross-Cutting Specifications

- [x] **3.1** - Write `docs/specs/integration-layer.md`
  - [x] **3.1.1** - Write Overview and Message Formats sections with schema definitions
  - [x] **3.1.2** - Write Alpha-to-Beta Protocol section
  - [x] **3.1.3** - Write Beta-to-Gamma Protocol section
  - [x] **3.1.4** - Write Error Propagation section (minimum 100 lines, references all modules)
  - [x] **3.1.5** - Write Monitoring and Configuration sections
  - [x] **3.1.6** - Verify all three modules are referenced
  - [x] **3.1.7** - Verify total length is 500-700 lines. This is non-negotiable.
- [x] **3.2** - Write `docs/specs/compliance-requirements.md`
  - [x] **3.2.1** - Write Overview and Audit Logging sections
  - [x] **3.2.2** - Write Module Alpha Compliance section (numbered requirements)
  - [x] **3.2.3** - Write Module Beta Compliance section (numbered requirements)
  - [x] **3.2.4** - Write Module Gamma Compliance section (numbered requirements)
  - [x] **3.2.5** - Write Security and Reporting sections
  - [x] **3.2.6** - Verify total length is 300-500 lines. This is non-negotiable.

### Phase 4: WPD Creation

- [x] **4.1** - Write `docs/wpds/refactor-easy.md`
  - [x] **4.1.1** - Write Overview describing `DEFAULT_BATCH_SIZE` rename
  - [x] **4.1.2** - Write Required Context section referencing ONLY `module-alpha.md`
  - [x] **4.1.3** - Write Tasks checkboxlist with 3-5 tasks
- [x] **4.2** - Write `docs/wpds/refactor-hard.md`
  - [x] **4.2.1** - Write Overview describing Error Registry refactor
  - [x] **4.2.2** - Write Required Context section with directive language requiring ALL six specs
  - [x] **4.2.3** - Write Tasks checkboxlist with 10-15 tasks spanning all modules
- [x] **4.3** - Write `docs/wpds/refactor-medium.md`
  - [x] **4.3.1** - Write Overview describing Alpha-Beta streaming handoff
  - [x] **4.3.2** - Write Required Context section with two-tier structure (MUST vs recommended)
  - [x] **4.3.3** - Write Tasks checkboxlist with 6-8 tasks

### Phase 5: Documentation and Validation

- [x] **5.1** - Verify content integrity
  - [x] **5.1.1** - Verify all file references in WPDs resolve correctly
  - [x] **5.1.2** - Verify all cross-references within specs are valid
  - [x] **5.1.3** - Verify each spec meets minimum line count

