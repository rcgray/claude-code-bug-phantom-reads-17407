# Findings Report Template

This template defines the structure for a findings report produced by a Deep-Reviewer agent. The Deep-Reviewer writes findings in this format; the Review-Synthesizer reads them to aggregate and categorize issues across all review tasks.

Each findings report covers one focused concern and contains all issues discovered within that scope.

---

## Template

```markdown
# Findings: [task-name]

## Concern
[The scope description from the review task definition]

## Findings

### [F-1] [Short descriptive title]

**Severity:** [Critical | Major | Minor]

**Description:**
[Clear description of the issue discovered]

**Evidence:**
[Specific quotes, line references, or concrete observations from the documents reviewed. Include the document path and the relevant text.]

**Suggested Resolution:**
[What should change to address this finding. Be specific about which document and which text needs to change.]

---

### [F-2] [Short descriptive title]

[Same structure as above for each additional finding]

---

## Undeclared Dependencies

[List any documents that the target specification depends on but does not explicitly cross-reference. If none were discovered, state "None discovered."]

- **[document-path]**: [Brief explanation of how the target spec depends on this document and why it should be cross-referenced]

## Overall Assessment

**Rating:** [Sound | Needs minor fixes | Significant issues]

**Summary:**
[Brief assessment of the concern area's overall quality, noting patterns across findings and the general state of alignment between the target document and external documents.]
```

---

## Field Descriptions

**Task Name:** The task-name from the review task definition, used as the report heading.

**Concern:** Copied from the scope description in the review task definition. Establishes context for readers who have not seen the review plan.

**Findings:** A numbered list of issues discovered during the review. Each finding has a unique identifier (F-1, F-2, ...) within this report.

**Severity Levels:**
- **Critical:** Contradicts authoritative sources or creates implementation blockers. The target document makes a claim that is demonstrably wrong based on an authoritative external document, or defines behavior that cannot be implemented as specified.
- **Major:** Significant gap or ambiguity that could lead to incorrect implementation. The target document omits important information, uses ambiguous language, or has inconsistencies that an implementer might resolve incorrectly.
- **Minor:** Inconsistency or improvement opportunity that does not block implementation. Formatting issues, slightly imprecise language, or minor misalignments that are unlikely to cause implementation errors.

**Evidence:** Specific, verifiable references to the source material. Include document paths, section headings, and direct quotes where possible. Evidence must be concrete enough that another agent or human can verify the finding without re-reading the entire document.

**Suggested Resolution:** A concrete recommendation for how to fix the issue. Resolutions should work within the existing architecture of the specification — do not suggest redesigns or alternative approaches. The Review-Synthesizer will use these suggestions when producing edit pairs.

**Undeclared Dependencies:** Documents that the target specification assumes or depends on but does not explicitly list in its cross-references or related specifications sections. Each entry identifies the document and explains the nature of the dependency.

**Overall Assessment Ratings:**
- **Sound:** The concern area is well-specified with no significant issues. Minor findings may exist but the overall design is solid and aligned with external documents.
- **Needs minor fixes:** A few issues exist (typically Minor or isolated Major findings) but the overall design is correct and the fixes are straightforward.
- **Significant issues:** Substantial problems that need resolution before implementation. Multiple Major or any Critical findings indicate systemic misalignment or gaps in the specification.
