# Synthesis Report Template

This template defines the structure for the synthesis report produced by the Review-Synthesizer agent. The Review-Synthesizer writes the synthesis in this format; the User Agent reads it to apply auto-fix edits and present judgment-call items to the User.

The synthesis report contains two main sections: Auto-Fixed Issues and Judgment-Call Issues. Every issue from the findings must appear in exactly one of these sections. The categorization is binary — there are no intermediate categories.

---

## Template

```markdown
# Synthesis Report

**Target Document:** [path to the target document]
**Review Tasks Synthesized:** [number of findings files read]
**Total Issues:** [count] ([auto-fix count] auto-fix, [judgment-call count] judgment-call)

---

## Auto-Fixed Issues (AF)

Issues where the correct resolution is unambiguous and does not involve a design decision. The User Agent applies these edits mechanically.

### AF-1: [Short descriptive title]

**Description:**
[Clear description of the issue]

**Location:**
Line [line-number]: [Section heading or specific context]

**Rationale:**
[Why this fix is unambiguous — cite the authoritative source or established pattern that determines the correct value]

**Edit:**
```
old_text:
[Exact text currently in the target document that must be replaced. Copy precisely — whitespace, punctuation, and formatting must match the document exactly.]

new_text:
[The corrected text that should replace old_text.]
```

**Source Findings:** [F-1 from task-name, F-3 from other-task-name]

---

### AF-2: [Short descriptive title]

[Same structure as above for each additional auto-fix issue]

---

## Judgment-Call Issues (JC)

Issues where multiple valid resolutions exist or a design decision is required. The User Agent presents these to the User for decision.

### JC-1: [Short descriptive title]

**Description:**
[Clear description of the issue and why it requires a decision]

**Location:**
Line [line-number]: [Section heading or specific context]

**Impact:**
[Why this decision matters — what's at stake if the wrong choice is made, or what consequences flow from this choice]

**Question:**
[The specific question the User must answer, framed clearly and concisely]

**Option A: [Option title]**

*Rationale:* [Why someone might choose this option]

```
old_text:
[Exact text currently in the target document]

new_text:
[The replacement text if this option is chosen]
```

**Option B: [Option title]**

*Rationale:* [Why someone might choose this option]

```
old_text:
[Exact text currently in the target document — may be the same as Option A's old_text]

new_text:
[The replacement text if this option is chosen]
```

**Source Findings:** [F-2 from task-name]

---

### JC-2: [Short descriptive title]

[Same structure as above for each additional judgment-call issue]

---

## Cross-Finding Patterns

[Summary of patterns observed across independent findings: corroborated issues, systemic problems, or conflicting reviewer assessments. This section provides context for understanding the overall state of the specification beyond individual issues.]

## Summary

**Auto-Fix Issues:** [count] applied mechanically
**Judgment-Call Issues:** [count] requiring User decision
**Overall Assessment:** [Brief characterization of the specification's quality based on synthesized findings]
```

---

## Field Descriptions

**Target Document:** The path to the specification that was reviewed. Identifies which document the edit pairs reference.

**Review Tasks Synthesized:** How many Deep-Reviewer findings files were consumed. Provides a sense of review breadth.

**Total Issues:** Aggregate count broken down by category. Gives the User an immediate sense of the review's outcome.

### Auto-Fix Section

**Issue Identifier:** Sequential AF-1, AF-2, etc. The User Agent references these when reporting applied changes.

**Description:** What the issue is, stated clearly enough to be understood without reading the original findings.

**Location:** Where in the target document the issue exists. MUST include the specific line number followed by section heading or context. Format: "Line [number]: [section/context]". Line numbers are critical for the User to locate issues in large specifications.

**Rationale:** Why the resolution is unambiguous. This must cite a specific authority: an authoritative external document that defines the correct value, an established pattern within the target document that determines the consistent form, or a factual error with only one correct answer.

**Edit Pair:** The `old_text` and `new_text` that the User Agent passes to the Edit tool. The `old_text` must be an exact substring of the target document's current content. The `new_text` contains the corrected version.

**CRITICAL — Edit Pair Precision:**
- Copy `old_text` directly from the target document. Do not paraphrase or approximate.
- Include enough surrounding context in `old_text` to ensure uniqueness — the Edit tool requires that `old_text` appears exactly once in the file.
- Preserve all formatting: indentation, line breaks, markdown syntax, whitespace.
- If multiple edits affect nearby text, order them from bottom to top in the document to prevent earlier edits from invalidating later edit pairs.

**Source Findings:** Which original Deep-Reviewer findings support this issue. References use the format "F-N from task-name" to trace back to the original evidence.

**Auto-Fix Criteria:**
- Formatting inconsistencies (heading levels, numbering errors, markdown formatting)
- Clearly broken cross-references (references to sections or documents that do not exist or use incorrect names)
- Missing items with unambiguous correct values (fields or entries that are clearly required based on established patterns and have only one correct value)
- Inconsistencies where one source is explicitly authoritative (the target document contradicts an authoritative external source that owns the concept)
- Undeclared dependencies (adding a cross-reference to a document the specification depends on but does not reference)

### Judgment-Call Section

**Issue Identifier:** Sequential JC-1, JC-2, etc. The User Agent presents these by number for User selection.

**Impact:** Why this decision matters. Explains the stakes: what breaks if the wrong choice is made, what constraints are created by each option, or what downstream consequences flow from this decision. Provides the User with context about the importance and ramifications of their choice.

**Question:** The decision the User must make, framed as a clear question. The question should make sense without requiring the User to read the full findings — it should stand alone.

**Options:** Two to three options, each with rationale explaining why someone might choose it. Each option includes its own complete edit pair (old_text showing the current text being discussed, new_text showing the proposed change), so the User Agent can apply the selected option immediately.

**Judgment-Call Criteria:**
- Contradictions where both versions could be correct (two documents disagree and neither is definitively authoritative for the concept in question)
- Missing specifications requiring design decisions (gaps that cannot be filled without choosing between alternatives)
- Ambiguous requirements with multiple valid interpretations (language that could reasonably be read in more than one way)
- Scope questions (whether a concept belongs in this specification versus another)
- Architectural philosophy (anything touching design decisions or establishing new patterns)

**When in doubt, classify as judgment-call.** The cost of presenting an unnecessary decision to the User is low. The cost of making a design decision without User authority is high.

### Cross-Finding Patterns

Observations that emerge only when viewing findings from multiple independent reviewers together. Individual findings are addressed in the AF and JC sections above; this section captures meta-observations about the specification's overall quality and any systemic issues that individual findings hint at but no single finding fully describes.
