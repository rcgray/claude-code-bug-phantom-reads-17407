# Reproduction Specs Collection Specification

**Version:** 2.0.0
**Date:** 2026-01-22
**Status:** Active

## Overview

The Reproduction Specs Collection provides a controlled phantom read reproduction environment consisting of dummy specification documents, preload context files, and custom analysis commands that manipulate token consumption to predictably trigger or avoid phantom reads. This feature enables reliable reproduction of phantom reads within this repository by controlling pre-operation context consumption—the critical factor determining whether mid-session resets occur during file read operations.

This specification defines:
1. **Supporting Specifications**: Six interconnected documents describing a fictional "Data Pipeline System" that serve as the critique target during analysis tasks
2. **Preload Context Files**: Three substantial documents that inflate context consumption before the analysis trigger, controlling pre-operation token levels
3. **Unified Target WPD**: A single Work Plan Document proposing a cross-cutting refactor that requires thorough review of all supporting specs
4. **Analysis Commands**: Three custom commands (`/analyze-light`, `/analyze-standard`, `/analyze-thorough`) that combine different preload levels with a consistent analysis task

The reproduction environment exploits the **Reset Timing Theory** validated across 31 trials with 100% prediction accuracy: mid-session resets (occurring at 50-90% of session progress) predict phantom reads, while sessions with only early (<50%) and late (>90%) resets succeed. By controlling pre-operation context consumption through preload files, we control when resets occur during the subsequent analysis task.

For background on the Reset Timing Theory and supporting evidence, see `docs/core/Investigation-Journal.md` and `docs/core/Repro-Attempts-02-Analysis-1.md`.

## Purpose

The Reproduction Specs Collection serves four critical functions:

1. **Controlled Pre-Operation Consumption**: Provides preload content of known size that inflates context consumption BEFORE the analysis trigger fires. This is the primary control mechanism—by setting pre-operation consumption to specific thresholds, we control whether mid-session resets occur during subsequent file reads.

2. **Phantom Read Triggering**: The `/analyze-thorough` command preloads ~85k tokens of context, pushing pre-operation consumption to ~55% (111k tokens). When the agent then reads supporting specs during analysis, mid-session resets are triggered, causing phantom reads.

3. **Safe Zone Demonstration**: The `/analyze-light` command preloads ~44k tokens, establishing pre-operation consumption at ~35% (70k tokens). This demonstrates the safe zone where supporting spec reads complete without triggering disruptive mid-session resets.

4. **Boundary Zone Exploration**: The `/analyze-standard` command preloads ~67k tokens, targeting ~46% pre-operation consumption (93k tokens). This boundary zone produces variable results, validating the threshold hypothesis.

This specification establishes the authoritative definition of the fictional Data Pipeline System domain (supporting specs, preload content, and analysis task structure), the command-based triggering mechanism, and the expected outcomes for each scenario tier.

## Design Evolution

### Original Approach (v1.0)

The original design used WPD-based differentiation: three separate WPDs (`refactor-easy.md`, `refactor-medium.md`, `refactor-hard.md`) with varying Required Context sections that directed agents to read different amounts of spec content. The theory was that spec content volume during `/refine-plan` would control token consumption and therefore phantom read occurrence.

### Why the Original Approach Underperformed

Analysis of 9 trials in the `repro-attempts-02` collection revealed critical insights:

1. **Pre-operation consumption is the real trigger**: The single failure case had 54% pre-operation consumption vs. 36-46% for successes. Token consumption BEFORE the trigger command matters more than content volume during execution.

2. **WPD complexity didn't differentiate**: Both successful Hard trials had metrics identical to Medium trials (~36% pre-op, 2 resets). The scenarios weren't achieving their target failure rates.

3. **Agent discretion introduces variance**: WPD-based approaches give agents discretion about what to read and how thoroughly. This introduces uncontrolled variance.

### Command-Based Approach (v2.0)

The revised design uses command-based differentiation with explicit preloading:

1. **Three commands** (`/analyze-light`, `/analyze-standard`, `/analyze-thorough`) with different preload requirements
2. **Preload via `@` notation** forces file content into context before the agent receives the task—no agent discretion
3. **Single unified target WPD** eliminates WPD complexity as a variable
4. **Consistent analysis task** across all scenarios—only preload volume differs

### Key Insight: The `@` Notation Mechanism

Claude Code's `@` notation (e.g., `@docs/specs/file.md`) triggers automatic file hoisting: the harness reads the file and injects its content into context BEFORE delivering the command text to the agent. This is analogous to variable hoisting in JavaScript—the content is "lifted" to the beginning of the context window.

This mechanism provides:
- **Direct control**: Files are read automatically, not via agent Read tool calls
- **No discretion**: Agents cannot skip or skim preloaded content
- **Predictable inflation**: Token consumption is deterministic based on file sizes

### Elimination of `/wsd:init --custom`

The updated methodology (to be documented in `Experiment-Methodology-03.md`) eliminates the `/wsd:init --custom` initialization step for reproduction trials:

1. **Reduces variance**: `/wsd:init --custom` contributed up to 17% variance in pre-operation consumption (ranging from 73k to 107k tokens across trials)
2. **Simplifies reproduction**: Fewer steps means easier reproduction for external researchers
3. **Isolates the toy project**: Session Agents interact only with the Data Pipeline System content, not investigation project materials
4. **Mitigates Hawthorne Effect**: Agents don't receive phantom reads research context that might influence behavior

Fresh Claude Code sessions show consistent baseline consumption of ~26k tokens (13%), providing a stable foundation for preload calculations.

## Content Architecture

### Directory Structure

All reproduction content resides in dedicated directories separate from real project documentation:

```
docs/
├── specs/                              # Data Pipeline System documentation
│   │
│   │ # Supporting Specifications (read during analysis task)
│   ├── data-pipeline-overview.md       # Hub document (~425 lines, ~6k tokens)
│   ├── module-alpha.md                 # Ingestion module (~742 lines, ~6k tokens)
│   ├── module-beta.md                  # Transformation module (~741 lines, ~6k tokens)
│   ├── module-gamma.md                 # Output module (~770 lines, ~8k tokens)
│   ├── integration-layer.md            # Cross-module protocols (~529 lines, ~5k tokens)
│   ├── compliance-requirements.md      # Audit/regulatory reqs (~392 lines, ~4k tokens)
│   │
│   │ # Preload Context Files (inflated via @ notation before task)
│   ├── operations-manual.md            # Operational procedures (~4,500 lines, ~44k tokens)
│   ├── architecture-deep-dive.md       # System internals (~2,400 lines, ~23k tokens)
│   └── troubleshooting-compendium.md   # Issue resolution (~1,900 lines, ~18k tokens)
│
└── wpds/                               # Work Plan Documents
    │ # Legacy WPDs (from v1.0, retained for backwards compatibility)
    ├── refactor-easy.md                # Minimal scope WPD
    ├── refactor-medium.md              # Partial scope WPD
    ├── refactor-hard.md                # Full scope WPD
    │
    │ # Unified Target WPD (for v2.0 command-based approach)
    └── pipeline-refactor.md            # Cross-cutting refactor proposal

.claude/
└── commands/                           # Analysis commands
    ├── analyze-light.md                # Light preload (~35% pre-op)
    ├── analyze-standard.md             # Standard preload (~46% pre-op)
    └── analyze-thorough.md             # Thorough preload (~55% pre-op)
```

### File Categories

The reproduction environment consists of three distinct file categories:

**Supporting Specifications** (~35k tokens total): The six original Data Pipeline System documents that agents must read and analyze during the critique task. These are where phantom reads manifest—the agent attempts to read these files, and depending on pre-operation consumption, some reads may return phantom markers instead of content.

**Preload Context Files** (~85k tokens total): Three substantial documents providing operational, architectural, and troubleshooting context for the Data Pipeline System. These are loaded via `@` notation BEFORE the analysis task begins, inflating pre-operation consumption to target thresholds. Agents do not explicitly interact with these files during the task—they serve purely as context inflation.

**Analysis Commands**: Three custom commands that combine specific preload configurations with a consistent analysis task. Each command preloads a different subset of preload files, then directs the agent to critique the unified target WPD against the supporting specifications.

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

## Preload Context Files

Preload files serve a single purpose: inflating pre-operation context consumption to target thresholds before the analysis task begins. They are loaded via `@` notation in the analysis commands, ensuring deterministic token consumption without agent discretion.

All preload content must be:
- **Self-contained within the Data Pipeline System domain**: No references to phantom reads, the investigation project, or meta-testing concepts
- **Technically plausible**: Content should read as legitimate operational documentation
- **Substantial in size**: Each file must hit its target line count to achieve the required token inflation
- **Internally consistent**: Cross-references between preload files and supporting specs should be coherent

### Token Estimation

Based on measurement of existing spec files, the average token-to-line ratio is **9.7 tokens per line**. This ratio is used for all size calculations in this specification.

| Existing File              | Lines | Tokens | Ratio   |
| -------------------------- | ----- | ------ | ------- |
| compliance-requirements.md | 392   | 3,939  | 10.0    |
| data-pipeline-overview.md  | 425   | 6,041  | 14.2    |
| integration-layer.md       | 529   | 4,886  | 9.2     |
| module-alpha.md            | 742   | 6,204  | 8.4     |
| module-beta.md             | 741   | 6,198  | 8.4     |
| module-gamma.md            | 770   | 7,658  | 9.9     |
| **Average**                | —     | —      | **9.7** |

### operations-manual.md

**Purpose**: Primary preload file providing comprehensive operational procedures for the Data Pipeline System. Used by all three analysis commands.

**Size**: ~4,500 lines (~44,000 tokens, ~22% of context window)

**Required Content**:
- Standard Operating Procedures section covering daily operations, batch processing schedules, and operator responsibilities
- Deployment Procedures section with step-by-step deployment checklists for each module
- Maintenance Windows section describing planned maintenance protocols and rollback procedures
- Incident Response section with escalation procedures, on-call rotations, and severity classifications
- Monitoring and Alerting section with threshold definitions, alert routing, and dashboard descriptions
- Backup and Recovery section with backup schedules, retention policies, and disaster recovery procedures
- Capacity Planning section with growth projections, resource allocation guidelines, and scaling triggers
- Change Management section with approval workflows, change windows, and rollback criteria
- Runbook Appendix with detailed step-by-step procedures for common operational tasks

**Key Constraint**: Content must be substantial and realistic. Avoid repetitive filler—each section should provide distinct, plausible operational guidance. Target ~500 lines per major section.

### architecture-deep-dive.md

**Purpose**: Secondary preload file providing detailed architectural analysis. Used by `/analyze-standard` and `/analyze-thorough` commands.

**Size**: ~2,400 lines (~23,000 tokens, ~12% of context window)

**Required Content**:
- Design Philosophy section explaining architectural principles and trade-offs
- Component Deep Dives section with detailed analysis of each module's internal architecture
- Data Flow Analysis section with sequence diagrams (ASCII) and state transitions
- Performance Architecture section covering caching strategies, connection pooling, and optimization patterns
- Security Architecture section with authentication flows, authorization models, and encryption standards
- Scalability Patterns section describing horizontal scaling, sharding strategies, and load distribution
- Technology Stack section with dependency rationale and version compatibility matrices
- Evolution History section describing major architectural decisions and their rationale

**Key Constraint**: This file provides technical depth that complements the operational focus of the operations manual. Content should appeal to architects and senior engineers.

### troubleshooting-compendium.md

**Purpose**: Tertiary preload file providing comprehensive troubleshooting guidance. Used only by `/analyze-thorough` command.

**Size**: ~1,900 lines (~18,000 tokens, ~9% of context window)

**Required Content**:
- Common Issues Catalog section with symptoms, causes, and resolutions for frequent problems
- Module-Specific Troubleshooting sections for Alpha, Beta, and Gamma with targeted guidance
- Integration Troubleshooting section covering cross-module communication failures
- Performance Troubleshooting section with profiling procedures and bottleneck identification
- Data Quality Issues section with validation failure patterns and correction procedures
- Error Code Reference section with comprehensive error code listings and meanings
- Diagnostic Procedures section with log analysis techniques and debugging workflows
- Post-Mortem Templates section with incident analysis frameworks

**Key Constraint**: Content should be actionable troubleshooting guidance, not abstract theory. Include specific error messages, log patterns, and resolution steps.

## Unified Target WPD

The unified target WPD (`pipeline-refactor.md`) replaces the three separate WPDs from v1.0 as the analysis target for all three commands. This ensures the analysis task is identical across scenarios—only preload volume differs.

### pipeline-refactor.md

**Purpose**: Cross-cutting refactor proposal that requires thorough review of ALL six supporting specifications. This WPD serves as the critique target for all analysis commands.

**Proposed Change**: "Implement unified telemetry and observability framework across all Data Pipeline modules"

**Required Content**:
- Overview section describing the proposed telemetry framework and its benefits
- Motivation section explaining current observability gaps across modules
- Scope section explicitly listing ALL six supporting specs as required review materials
- Technical Approach section with high-level design for the unified framework
- Module Impact sections describing changes required in Alpha, Beta, and Gamma
- Integration Impact section describing changes to cross-module protocols
- Compliance Impact section describing audit and regulatory considerations
- Implementation Phases section with a checkboxlist of 10-15 tasks spanning all modules
- Risk Assessment section identifying potential issues with the refactor
- Success Criteria section defining how to measure the refactor's effectiveness

**Key Constraint**: The WPD MUST reference all six supporting specs and require thorough understanding of each to provide meaningful critique. Agents cannot "wing it" without actually reading the specs—the critique task should expose gaps in understanding caused by phantom reads.

**Critique Task Design**: The analysis commands direct agents to:
1. Read and understand the proposed refactor in `pipeline-refactor.md`
2. Review each supporting specification to assess current state
3. Identify gaps, risks, or inconsistencies in the proposal
4. Provide structured feedback on feasibility and completeness

When phantom reads occur, agents will provide confident critique of sections they never actually read, demonstrating the phenomenon.

## Analysis Commands

The three analysis commands provide the triggering mechanism for reproduction trials. Each command:
1. Preloads specific context files via `@` notation (token inflation)
2. Presents the unified target WPD for critique
3. Directs the agent to review supporting specs and provide feedback

### Command Structure

All analysis commands follow this structure:

```markdown
# Analyze [Scenario] - Data Pipeline Refactor Review

[Preload files via @ notation - these are hoisted into context automatically]

## Task

Review the proposed refactor in `docs/wpds/pipeline-refactor.md` and provide comprehensive feedback.

### Required Analysis

1. **Read the proposal thoroughly** - Understand the unified telemetry framework being proposed
2. **Review each supporting specification**:
   - `docs/specs/data-pipeline-overview.md` - System architecture context
   - `docs/specs/module-alpha.md` - Ingestion module current state
   - `docs/specs/module-beta.md` - Transformation module current state
   - `docs/specs/module-gamma.md` - Output module current state
   - `docs/specs/integration-layer.md` - Cross-module protocols
   - `docs/specs/compliance-requirements.md` - Regulatory constraints
3. **Assess the proposal** against each specification
4. **Provide structured feedback** including:
   - Feasibility assessment for each module
   - Identified risks or gaps
   - Suggested improvements
   - Overall recommendation

### Output Format

Provide your analysis in a structured format with sections for each module and an overall assessment.
```

### analyze-light.md

**Purpose**: Demonstrate the safe zone where phantom reads do not occur.

**Preload Configuration**:
```markdown
@docs/specs/operations-manual.md
```

**Token Budget**:
| Component                   | Tokens     | % Context |
| --------------------------- | ---------- | --------- |
| Baseline (fresh session)    | 26,000     | 13%       |
| Preload (operations-manual) | 44,000     | 22%       |
| **Pre-operation total**     | **70,000** | **35%**   |

**Expected Behavior**:
- Pre-operation consumption: ~35% (70k tokens)
- Remaining headroom: ~130k tokens
- Supporting spec reads (~35k): Fit comfortably within headroom
- Context resets: 2 (early + late pattern)
- Mid-session resets: 0
- Expected outcome: **SUCCESS** (no phantom reads)

### analyze-standard.md

**Purpose**: Demonstrate the boundary zone with variable outcomes.

**Preload Configuration**:
```markdown
@docs/specs/operations-manual.md
@docs/specs/architecture-deep-dive.md
```

**Token Budget**:
| Component                        | Tokens     | % Context |
| -------------------------------- | ---------- | --------- |
| Baseline (fresh session)         | 26,000     | 13%       |
| Preload (operations-manual)      | 44,000     | 22%       |
| Preload (architecture-deep-dive) | 23,000     | 12%       |
| **Pre-operation total**          | **93,000** | **46%**   |

**Expected Behavior**:
- Pre-operation consumption: ~46% (93k tokens)
- Remaining headroom: ~107k tokens
- Supporting spec reads (~35k): May trigger boundary resets
- Context resets: 2-3
- Mid-session resets: 0-1 (borderline)
- Expected outcome: **MIXED** (~50% failure rate)

### analyze-thorough.md

**Purpose**: Demonstrate the danger zone where phantom reads occur reliably.

**Preload Configuration**:
```markdown
@docs/specs/operations-manual.md
@docs/specs/architecture-deep-dive.md
@docs/specs/troubleshooting-compendium.md
```

**Token Budget**:
| Component                            | Tokens      | % Context |
| ------------------------------------ | ----------- | --------- |
| Baseline (fresh session)             | 26,000      | 13%       |
| Preload (operations-manual)          | 44,000      | 22%       |
| Preload (architecture-deep-dive)     | 23,000      | 12%       |
| Preload (troubleshooting-compendium) | 18,000      | 9%        |
| **Pre-operation total**              | **111,000** | **55%**   |

**Expected Behavior**:
- Pre-operation consumption: ~55% (111k tokens)
- Remaining headroom: ~89k tokens
- Supporting spec reads (~35k): Trigger mid-session resets
- Context resets: 3-4+
- Mid-session resets: 2+ (in danger zone)
- Expected outcome: **FAILURE** (phantom reads occur)

## Legacy WPD Requirements

The following WPD specifications are retained from v1.0 for backwards compatibility. These WPDs work with the original `/refine-plan` command approach and may still be useful for comparative testing. However, the recommended approach for new reproduction trials is the command-based system described above.

### Common WPD Structure

All legacy test WPDs follow this structure:

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

### Token Estimation Method

Based on measurement of the six existing spec files, the empirical **token-to-line ratio is 9.7 tokens per line**. This ratio is used for all size calculations in this specification. The previous estimate of 12 tokens per line was too high.

### Supporting Specifications Budget (Actual)

These files exist and have been measured:

| File                       | Actual Lines | Actual Tokens | % Context |
| -------------------------- | ------------ | ------------- | --------- |
| data-pipeline-overview.md  | 425          | 6,041         | 3.0%      |
| module-alpha.md            | 742          | 6,204         | 3.1%      |
| module-beta.md             | 741          | 6,198         | 3.1%      |
| module-gamma.md            | 770          | 7,658         | 3.8%      |
| integration-layer.md       | 529          | 4,886         | 2.4%      |
| compliance-requirements.md | 392          | 3,939         | 2.0%      |
| **TOTAL**                  | **3,599**    | **34,926**    | **17.5%** |

### Preload Files Budget (Actual)

| File                          | Lines     | Tokens     | % Context | Purpose             |
| ----------------------------- | --------- | ---------- | --------- | ------------------- |
| operations-manual.md          | 4,155     | 45,049     | 22.5%     | All scenarios       |
| architecture-deep-dive.md     | 1,952     | 23,941     | 12.0%     | Standard + Thorough |
| troubleshooting-compendium.md | 2,005     | 18,088     | 9.0%      | Thorough only       |
| **TOTAL**                     | **8,112** | **87,078** | **43.5%** |                     |

### Scenario Token Budgets

Calculations assume a fresh Claude Code session baseline of 26k tokens (13%):

| Scenario | Baseline | Preload | Pre-Op Total | Pre-Op % | Headroom |
| -------- | -------- | ------- | ------------ | -------- | -------- |
| Light    | 26k      | 45k     | 71k          | 35.5%    | 129k     |
| Standard | 26k      | 69k     | 95k          | 47.5%    | 105k     |
| Thorough | 26k      | 87k     | 113k         | 56.5%    | 87k      |

### Baseline Reference Data

**Fresh Claude Code session** (no initialization):
- Consistent baseline: 26k tokens (13%)
- Variance: Minimal (<1k tokens across 5 test sessions)

**repro-attempts-02 failure case** (trial 20260121-202919):
- Pre-operation consumption: 54% (107k tokens)
- Context resets: 4 (at 57%, 72%, 84%, 96%)
- Mid-session resets: 3
- Outcome: Phantom reads occurred

**repro-attempts-02 success cases** (8 trials):
- Pre-operation consumption: 36-46% (73k-93k tokens)
- Context resets: 2 (early + late pattern)
- Mid-session resets: 0-1 (borderline)
- Outcome: No phantom reads

The scenario budgets are designed to place Light firmly in the success zone, Thorough firmly in the failure zone, and Standard at the boundary.

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

### Command-Based Approach (v2.0)

| Scenario            | Pre-Op % | Resets | Mid-Session | Phantom Read Rate |
| ------------------- | -------- | ------ | ----------- | ----------------- |
| `/analyze-light`    | ~35%     | 2      | 0           | 0% (5/5 succeed)  |
| `/analyze-standard` | ~46%     | 2-3    | 0-1         | 40-60% (mixed)    |
| `/analyze-thorough` | ~55%     | 3-4+   | 2+          | 100% (5/5 fail)   |

**Key Success Metrics**:
- Light scenario demonstrates the safe zone with 100% success
- Thorough scenario demonstrates the danger zone with 100% failure
- Standard scenario demonstrates the boundary with variable results
- Pre-operation consumption matches target percentages (±3%)

### Legacy WPD Approach (v1.0)

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

**Note**: The legacy approach achieved only 33% failure rate on Hard scenarios due to variance in agent behavior. The command-based approach addresses this limitation.

## Validation Methodology

### Command-Based Approach (v2.0)

To validate the reproduction environment using the command-based approach:

1. **Session Initiation**: Start a fresh Claude Code session (no `/wsd:init`)
2. **Baseline Verification**: Run `/context` to confirm baseline ~26k tokens (13%)
3. **Trial Execution**: Run `/analyze-{light|standard|thorough}`
4. **Post-Execution Check**: Run `/context` to capture final token consumption
5. **Self-Report Collection**: Ask agent about phantom read experience and which files were affected
6. **Session Export**: Export session and save to `dev/misc/repro-attempts-XX/{workscope-id}/`
7. **Session Analysis**: Use `/update-trial-data` to extract metrics into `trial_data.json`
8. **Result Recording**: Record outcome against success criteria

**Minimum Validation**: 5 trials per scenario (15 total) to establish statistical confidence.

### Legacy WPD Approach (v1.0)

To validate using the legacy WPD-based approach:

1. **Session Initiation**: Run `/wsd:init --custom` to start a session
2. **Trial Execution**: Run `/refine-plan docs/wpds/refactor-{easy|medium|hard}.md`
3. **Self-Report Collection**: After completion, ask agent about phantom read experience
4. **Session Export**: Export session and save to `dev/misc/self-examples/{difficulty}-trial-N/`
5. **Session Analysis**: Use Session Analysis Scripts to extract metrics
6. **Result Recording**: Record outcome against success criteria

**Note**: The legacy approach introduces up to 17% variance in pre-operation consumption due to `/wsd:init --custom`. The command-based approach is recommended for new validation trials.

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

### For Supporting Spec Authors

1. **Maintain Technical Plausibility**: All content must read as legitimate technical documentation. Avoid placeholder text, "lorem ipsum" patterns, or meta-commentary about the testing purpose.

2. **Honor Size Targets**: Each spec file has a specific line count target that contributes to the overall token budget. Significant deviation breaks the token consumption predictions.

3. **Preserve Cross-References**: The reference graph between specs is intentional. When adding content, maintain existing cross-references and add new ones consistently.

4. **Use Named Constants**: Module specs should define specific named constants (e.g., `DEFAULT_BATCH_SIZE`) that serve as natural refactoring targets for WPDs.

### For Preload Content Authors

1. **Hit Token Targets Precisely**: Preload files exist solely to inflate context consumption. Use the 9.7 tokens/line ratio to calculate required line counts. Measure actual token counts after creation and adjust if needed.

2. **Maintain Domain Consistency**: All preload content must be about the fictional Data Pipeline System. Do not reference phantom reads, the investigation project, or any meta-testing concepts.

3. **Avoid Repetitive Filler**: Content should be substantial and realistic, not padded with repetitive sections. Each major section should provide distinct, plausible content.

4. **Create Self-Contained Documents**: Preload files should make sense on their own. Cross-references to supporting specs are encouraged; cross-references between preload files should be minimal.

5. **Target Different Audiences**: Operations-manual targets operators; architecture-deep-dive targets architects; troubleshooting-compendium targets support engineers. This differentiation makes content more realistic.

### For Command Authors

1. **Use `@` Notation for Preloading**: Always use `@docs/specs/filename.md` syntax to ensure file content is hoisted into context before the task text.

2. **Keep Task Structure Identical**: All three commands should have the same analysis task—only preload differs. This isolates preload volume as the single variable.

3. **List All Supporting Specs**: The task must explicitly direct agents to read all six supporting specifications. Vague language allows agents to skip files.

4. **Design for Detection**: The critique task should be complex enough that phantom reads produce visibly incorrect output. Agents should not be able to "wing it" without reading the specs.

### For WPD Authors (Legacy)

1. **Be Explicit About Required Files**: The Required Context section directly controls which files agents read. List files by exact path with no ambiguity.

2. **Use Tiered Language for Mixed Results**: The "medium" WPD achieves mixed results through two-tier required context (MUST vs. recommended). Preserve this pattern.

3. **Match Task Count to Scope**: Easy WPDs should have few tasks (3-5), hard WPDs should have many (10-15). Task count signals expected complexity to the agent.

### For Trial Runners

1. **Use Fresh Sessions**: For command-based trials, start with a fresh Claude Code session (no `/wsd:init`). Verify baseline is ~26k tokens via `/context`.

2. **Capture Context at Key Points**: Run `/context` before and after the analysis command to measure pre-op and post-op consumption.

3. **Export Before Analysis**: Session data must be exported before it can be analyzed. Use `collect_trials.py` or manual export.

4. **Record All Results**: Even unexpected results provide valuable data. Record successes and failures with full session context and metrics.

5. **Use Consistent Naming**: Save trial data to `dev/misc/repro-attempts-XX/{workscope-id}/` with consistent directory structure.

## Related Specifications

- **`docs/core/Investigation-Journal.md`**: Chronological investigation log documenting theory development
- **`docs/core/Repro-Attempts-02-Analysis-1.md`**: Analysis of 9 trials validating the command-based approach
- **`docs/core/Trial-Analysis-Guide.md`**: Comprehensive guide for analyzing trial data
- **`docs/core/PRD.md`**: Project overview including Aims and current priorities
- **`.claude/commands/refine-plan.md`**: WPD review command (used in v1.0 reproduction methodology; still active for general WSD workflows)
- **`.claude/commands/analyze-light.md`**: Light scenario command (to be created)
- **`.claude/commands/analyze-standard.md`**: Standard scenario command (to be created)
- **`.claude/commands/analyze-thorough.md`**: Thorough scenario command (to be created)

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

### Phase 6: Preload Context Documents

- [x] **6.1** - Create `docs/specs/operations-manual.md` (~4,500 lines, ~44k tokens)
  - [x] **6.1.1** - Write Standard Operating Procedures section (~500 lines)
  - [x] **6.1.2** - Write Deployment Procedures section (~500 lines)
  - [x] **6.1.3** - Write Maintenance Windows section (~400 lines)
  - [x] **6.1.4** - Write Incident Response section (~500 lines)
  - [x] **6.1.5** - Write Monitoring and Alerting section (~500 lines)
  - [x] **6.1.6** - Write Backup and Recovery section (~500 lines)
  - [x] **6.1.7** - Write Capacity Planning section (~400 lines)
  - [x] **6.1.8** - Write Change Management section (~400 lines)
  - [x] **6.1.9** - Write Runbook Appendix section (~800 lines)
  - [x] **6.1.10** - Verify total length is ~4,500 lines (±200). Measure actual token count. (Final: 4155 lines, 45049 tokens)
- [x] **6.2** - Create `docs/specs/architecture-deep-dive.md` (~2,400 lines, ~23k tokens)
  - [x] **6.2.1** - Write Design Philosophy section (~300 lines)
  - [x] **6.2.2** - Write Component Deep Dives section (~400 lines)
  - [x] **6.2.3** - Write Data Flow Analysis section with ASCII diagrams (~350 lines)
  - [x] **6.2.4** - Write Performance Architecture section (~300 lines)
  - [x] **6.2.5** - Write Security Architecture section (~300 lines)
  - [x] **6.2.6** - Write Scalability Patterns section (~300 lines)
  - [x] **6.2.7** - Write Technology Stack section (~250 lines)
  - [x] **6.2.8** - Write Evolution History section (~200 lines)
  - [x] **6.2.9** - Verify total length is ~2,400 lines (±150). Measure actual token count. (Final: 1952 lines, 23941 tokens)
- [x] **6.3** - Create `docs/specs/troubleshooting-compendium.md` (~1,900 lines, ~18k tokens)
  - [x] **6.3.1** - Write Common Issues Catalog section (~300 lines)
  - [x] **6.3.2** - Write Module Alpha Troubleshooting section (~200 lines)
  - [x] **6.3.3** - Write Module Beta Troubleshooting section (~200 lines)
  - [x] **6.3.4** - Write Module Gamma Troubleshooting section (~200 lines)
  - [x] **6.3.5** - Write Integration Troubleshooting section (~200 lines)
  - [x] **6.3.6** - Write Performance Troubleshooting section (~200 lines)
  - [x] **6.3.7** - Write Data Quality Issues section (~200 lines)
  - [x] **6.3.8** - Write Error Code Reference section (~200 lines)
  - [x] **6.3.9** - Write Diagnostic Procedures section (~100 lines)
  - [x] **6.3.10** - Write Post-Mortem Templates section (~100 lines)
  - [x] **6.3.11** - Verify total length is ~1,900 lines (±100). Measure actual token count. (Final: 2005 lines, 18088 tokens)
- [x] **6.4** - Verify all preload content is self-contained within Data Pipeline System domain
  - [x] **6.4.1** - Grep for "phantom", "investigation", "reproduction" - must return zero matches
  - [x] **6.4.2** - Review for technical plausibility and consistency with existing specs
- [x] **6.5** - Measure actual token counts and document in this spec
  - [x] **6.5.1** - Update Token Budget tables with measured values
  - [x] **6.5.2** - Adjust line counts if token targets are not met

### Phase 7: Unified Target WPD

- [x] **7.1** - Create `docs/wpds/pipeline-refactor.md`
  - [x] **7.1.1** - Write Overview section describing unified telemetry framework
  - [x] **7.1.2** - Write Motivation section explaining current observability gaps
  - [x] **7.1.3** - Write Scope section explicitly listing ALL six supporting specs
  - [x] **7.1.4** - Write Technical Approach section with framework design
  - [x] **7.1.5** - Write Module Impact sections for Alpha, Beta, and Gamma
  - [x] **7.1.6** - Write Integration Impact section
  - [x] **7.1.7** - Write Compliance Impact section
  - [x] **7.1.8** - Write Implementation Phases section with 10-15 task checkboxlist
  - [x] **7.1.9** - Write Risk Assessment section
  - [x] **7.1.10** - Write Success Criteria section
- [x] **7.2** - Verify WPD requires thorough understanding of all supporting specs
  - [x] **7.2.1** - Verify each module is referenced with specific requirements
  - [x] **7.2.2** - Verify critique task cannot be completed by "winging it"

### Phase 8: Analysis Commands

- [x] **8.1** - Create `.claude/commands/analyze-light.md`
  - [x] **8.1.1** - Add `@docs/specs/operations-manual.md` preload
  - [x] **8.1.2** - Write analysis task directing review of all supporting specs
  - [x] **8.1.3** - Write output format requirements
- [x] **8.2** - Create `.claude/commands/analyze-standard.md` - Use `.claude/commands/analyze-light.md` as a template.
  - [x] **8.2.1** - Add `@docs/specs/operations-manual.md` preload
  - [x] **8.2.2** - Add `@docs/specs/architecture-deep-dive.md` preload
  - [x] **8.2.3** - Write analysis task (identical to light)
  - [x] **8.2.4** - Write output format requirements (identical to light)
- [x] **8.3** - Create `.claude/commands/analyze-thorough.md` - Use `.claude/commands/analyze-light.md` as a template.
  - [x] **8.3.1** - Add `@docs/specs/operations-manual.md` preload
  - [x] **8.3.2** - Add `@docs/specs/architecture-deep-dive.md` preload
  - [x] **8.3.3** - Add `@docs/specs/troubleshooting-compendium.md` preload
  - [x] **8.3.4** - Write analysis task (identical to light)
  - [x] **8.3.5** - Write output format requirements (identical to light)
- [x] **8.4** - Verify command consistency
  - [x] **8.4.1** - Confirm all three commands have identical task structure
  - [x] **8.4.2** - Confirm only preload differs between commands
  - [x] **8.4.3** - Test `@` notation hoisting works as expected

