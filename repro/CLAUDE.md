# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a documentation-only repository containing specifications for the **Data Pipeline System** - a three-stage data processing platform (ingestion, transformation, output) with supporting modules for caching and orchestration.

There is no source code in this repository. All files are Markdown specifications, Work Plan Documents (WPDs), and operational documentation.

## Repository Structure

```
docs/
├── specs/           # System specifications
│   ├── data-pipeline-overview.md    # Top-level architecture
│   ├── module-alpha.md              # Ingestion module
│   ├── module-beta.md               # Transformation module
│   ├── module-gamma.md              # Output module
│   ├── module-epsilon.md            # Caching layer
│   ├── module-phi.md                # Orchestration
│   ├── integration-layer.md         # Cross-module protocols
│   └── compliance-requirements.md   # Regulatory requirements
└── wpds/            # Work Plan Documents (proposed changes)
```

## Custom Commands

- `/analyze-wpd <path>` - Adversarial review of a Work Plan Document. Reads the WPD, cross-references with specifications, and identifies issues, gaps, and inconsistencies before implementation.
- `/setup-easy`, `/setup-medium`, `/setup-hard`, `/setup-none` - Generate Workscope IDs for trial coordination.

## System Architecture

The Data Pipeline System has five modules:

1. **Module Alpha (Ingestion)**: Source adapters, parsing, validation, buffering
2. **Module Beta (Transformation)**: Schema mapping, field transforms, enrichment, quality scoring
3. **Module Gamma (Output)**: Format rendering, delivery routing, acknowledgments, dead letter queue
4. **Module Epsilon (Caching)**: Multi-tier cache (L1/L2/L3) for enrichment and buffers
5. **Module Phi (Orchestration)**: Job scheduling, dependency resolution, failure recovery

Data flows: Sources → Alpha → Beta → Gamma → Destinations

Inter-module communication uses batch-based handoffs with checksums and acknowledgments. See `integration-layer.md` for protocol details.

## Working with WPDs

When reviewing or editing Work Plan Documents:

1. Cross-reference proposals against the relevant module specifications
2. Verify proposed changes are consistent with the integration layer protocols
3. Check compliance with requirements in `compliance-requirements.md`
4. Look for impacts across module boundaries (Alpha→Beta→Gamma flow)
