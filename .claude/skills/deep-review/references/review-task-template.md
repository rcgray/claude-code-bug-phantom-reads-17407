# Review Task Template

This template defines the structure for a single review task within a review plan. The Review-Planner writes tasks in this format; the Deep-Reviewer reads them to understand its assignment.

Each review task represents one focused concern that a single Deep-Reviewer agent will investigate. A review plan contains multiple review tasks, one per identified concern.

---

## Template

```markdown
### Task: [task-name]

**Scope Description:**
[A clear, specific description of the thematic concern this reviewer should focus on. The description should be precise enough that a reviewer starting fresh with no prior context can understand exactly what to investigate.]

**Target Document Sections:**
- [Section heading or line range in the target document relevant to this concern]
- [Additional relevant sections]

**External File Paths:**
- [Absolute or project-relative path to an external document the reviewer must read]
- [Additional external documents]

**Key Questions:**
1. [Specific question the reviewer should answer about this concern]
2. [Additional questions guiding the review focus]

**Corpus Size Estimate:**
- Target document: [size in bytes] ([estimated tokens] tokens)
- [external-file-name]: [size in bytes] ([estimated tokens] tokens)
- **Total effective tokens**: [sum] (file_bytes x 0.277 x 1.4)
- **Budget status**: [WITHIN BUDGET | APPROACHING LIMIT | EXCEEDS BUDGET]
```

---

## Field Descriptions

**Task Name:** A short, descriptive kebab-case identifier for this concern (e.g., `cross-reference-accuracy`, `error-handling-completeness`). Used as the filename for the findings report.

**Scope Description:** The thematic concern the reviewer investigates. Should be specific enough to focus the review but broad enough to produce meaningful findings. Examples: "consistency of configuration parameter names across the target document and all referenced configuration files", "completeness and accuracy of error handling guarantees and recovery procedures".

**Target Document Sections:** Which parts of the target document are relevant to this concern. Use section headings from the document. If the entire document is relevant, state "Entire document".

**External File Paths:** Documents outside the target that the reviewer must read to evaluate this concern. These are the intersection points where misalignment, contradiction, or missing cross-references may exist. Paths must be specific file paths, not vague references.

**Key Questions:** Focused questions that guide the reviewer's analysis. Each question should be answerable through careful reading of the assigned files. Questions help the reviewer stay within scope and ensure critical aspects of the concern are addressed.

**Corpus Size Estimate:** Token budget calculation for all files assigned to this task. Use the formula: effective_tokens = file_bytes x 0.277 x 1.4. Flag tasks where the total effective tokens approach or exceed 100,000 tokens. Budget statuses:
- WITHIN BUDGET: Total effective tokens below 80,000
- APPROACHING LIMIT: Total effective tokens between 80,000 and 100,000
- EXCEEDS BUDGET: Total effective tokens above 100,000 (consider splitting the task or reducing the file list)
