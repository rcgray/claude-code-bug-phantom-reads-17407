# Karpathy Scripts

A karpathy script is a hybrid software artifact that combines natural language instructions (interpreted by an LLM agent) with traditional deterministic code (executed by a machine) to create a repeatable, reliable operation. The practice of karpathy scripting centers on identifying — for any given task — the optimal boundary between what should be expressed as prompt and what should be expressed as code, then formalizing both into a cohesive artifact that can be invoked repeatedly with consistent results.

The term is not capitalized. It is a term of art — like "boolean" or "gaussian" — whose etymology is self-evident but whose usage is general.

## Etymology and Intellectual Lineage

The term "karpathy script" draws from two sources.

The first is **Andrej Karpathy's Software 3.0 framework**. In his June 2025 talk "Software Is Changing (Again)" at YCombinator's AI Startup School, Karpathy articulated a taxonomy of software paradigms: Software 1.0 (traditional code that programs a CPU), Software 2.0 (neural network weights that program a neural net), and Software 3.0 (natural language prompts that program an LLM). He observed that "prompts are programs that program the LLM" and that "remarkably, we are now programming computers in English." This framing provides the conceptual foundation: a karpathy script is, at its core, a Software 3.0 program — but one that has been refined into a reliable, repeatable operation through deliberate methodology.

The second source is the **cowpath principle** from urban planning — the practice of observing where people (or, in the Boston legend, cows) naturally walk before deciding where to pave roads. The phonetic similarity between a "cowpathy" methodology and the "karpathy" paradigm is intentional. The karpathy script methodology aims to observe where the agent naturally reaches for deterministic code before deciding what to formalize (i.e., pave the cowpaths).

## The Problem Karpathy Scripts Solve

Modern LLM agents are capable of performing complex, multi-step tasks when given natural language instructions. For many tasks — especially those involving natural language processing, judgment, evaluation, or semantic reasoning — prompt-based instruction dramatically outperforms traditional code in both development speed and capability. However, pure prompt-based execution has a fundamental reliability problem.

When an agent encounters a subtask that requires deterministic processing (data transformation, file parsing with exact format requirements, structured computations), it will typically generate a helper script on the fly — a traditional code artifact created to assist with the deterministic portion of the work. This works well enough in isolation, but when the same operation is repeated across multiple invocations, each invocation may generate a slightly different helper script. Most of these scripts will be correct. Some will not. The agent is effectively rolling the dice on something that could be fixed, introducing unnecessary variance into an operation that should be reliable.

Karpathy scripts solve this by identifying which parts of a task belong in the stochastic domain (agent interpretation) and which belong in the deterministic domain (traditional code), then formalizing both into a single cohesive artifact. The result is an operation that is reliable enough for repeated use while retaining the NLP-native capabilities that make LLM agents valuable.

## Anatomy of a Karpathy Script

A karpathy script consists of two types of components working in concert:

**The prompt component** contains natural language instructions that the agent interprets and executes. This is where judgment, semantic processing, contextual reasoning, and NLP tasks live. The prompt component may include conditional logic, checkpoint directives, input/output specifications, and references to the code components. It is Software 3.0 — English as a programming language.

**The code component** encompasses anything fixed and deterministic that the agent references rather than reinventing. This most commonly takes the form of traditional scripts (Python, shell, JavaScript, etc.), but it also includes schemas, configuration files, templates, data fixtures, or even well-defined directory structures and naming conventions. What unifies these is that they are pre-verified, permanent, and not subject to the agent's stochastic interpretation. A JSON schema that defines the expected output format is as much a code component as a Python script that performs data extraction — both remove a degree of freedom from the agent and replace it with something fixed.

Neither component is sufficient alone. The prompt component without the code component would force the agent to regenerate deterministic logic on every invocation, introducing variance. The code component without the prompt component would lack the semantic reasoning and NLP capabilities that motivated the approach in the first place. The karpathy script is their union — prompt guidance directing the agent's judgment, fixed elements anchoring the agent's execution. Together they create the "leash" that keeps the operation reliable while reducing the cognitive and computational burden on the agent itself.

A karpathy script may be simple (a single prompt file referencing a single helper script) or complex (a multi-step prompt orchestrating several code artifacts with intermediate judgment steps). The complexity should match the task, not an abstract ideal. Notably, Claude Code's "skills" feature provides a native container format for karpathy scripts: a skill is a directory with a `SKILL.md` entry point (the prompt component) alongside bundled scripts, templates, schemas, and data files (the code components) — all invocable as a single slash command.

## Core Characteristics

Beyond the hybrid anatomy, several characteristics distinguish karpathy scripts from adjacent practices and help clarify what qualifies as one.

**Repeatability.** A karpathy script is designed to be executed multiple times, not crafted for a single use. This is perhaps the sharpest distinction from ordinary prompting. A one-off prompt that produces a useful result is good prompt engineering. A prompt that can be invoked repeatedly across varying inputs and reliably produce consistent results is approaching karpathy script territory — and becomes one when it incorporates deterministic code to stabilize its operation.

**Hybrid composition.** Both prompt and code components are present, working in concert. A pure prompt with no code components is just a prompt, however sophisticated. A traditional script that happens to call an LLM API is just a script with an API integration. The karpathy script is specifically the artifact that weaves both paradigms together, with each handling the aspects of the task where it excels.

**Structured agent direction.** A karpathy script constrains the agent's autonomy without eliminating it. Karpathy describes an "autonomy slider" in LLM tooling — from minimal AI involvement (tab completion) to full agentic mode (unrestricted autonomous operation). A karpathy script deliberately positions itself on this slider: the agent operates with significant capability but within a defined corridor of steps, inputs, and expected outputs. It is what Karpathy calls the Iron Man suit rather than the Iron Man robot — an augmentation of human capability, not a replacement for human oversight.

**Software 3.0 as a deliberate choice.** A karpathy script uses prompt-driven LLM execution because it is the right tool for the job — but "right tool" encompasses more than just NLP-native capability. Certainly, tasks involving semantic analysis, judgment calls, natural language summarization, and contextual interpretation are natural fits where traditional code would be impractical or impossibly complex. But development speed alone can be sufficient justification. A purely computational task might be expressible in Python with a complicated regex, but if explaining the desired behavior to an agent in English produces reliable results in a fraction of the development time, that is a valid reason to choose Software 3.0. The paradigm is defined by the tools used to create the solution, not by the domain of the task.

**Designed for agent psychology.** Karpathy describes LLMs as "people spirits" — stochastic simulations of humans with encyclopedic knowledge but also hallucination tendencies, jagged intelligence (superhuman in some domains, inexplicably weak in others), and anterograde amnesia (no memory between sessions). Effective karpathy scripts are written with this psychology in mind: explicit enough to compensate for amnesia, structured enough to route around jagged intelligence, and constrained enough to limit the impact of hallucination — while still leveraging the encyclopedic knowledge and reasoning that make the approach worthwhile.

**The inversion.** The industry has abundant examples of traditional code that calls LLMs — agent frameworks like LangChain, CI pipelines with AI-generated summaries, scripts that hit an API endpoint for classification. In all of these, Software 1.0 is the host and the LLM is a guest: a service invoked by deterministic orchestration. A karpathy script inverts this relationship. The natural language instruction is the host — the primary program — and traditional code is the guest, invoked *by the agent* as a tool when it needs deterministic support. The orchestration lives in Software 3.0, not Software 1.0. This is not just a technical distinction. It represents a fundamentally different mental model of what is in charge. The industry has good language for "code that calls an LLM." It does not yet have good language for "LLM instructions that call code." That is the gap the term fills.

**Efficiency and potency.** Every aspect of a task that is offloaded to a fixed code component is an aspect the agent does not need to reason about, generate, or hold in its context window. This has practical consequences beyond reliability. It reduces token consumption — which matters for cost, but more importantly, it preserves the agent's limited context window for the work that actually requires its judgment. An agent executing a karpathy script with well-extracted code components can accomplish more in a single session than one that must regenerate boilerplate on every invocation, because its cognitive budget is spent on the hard parts rather than the solved parts.

**Platform independence.** A karpathy script is a design pattern, not a feature of any particular tool. Claude Code's skills feature provides an excellent native container for karpathy scripts, but the concept exists independently of it. A karpathy script could be implemented as a Claude Code skill, a Cursor rule with associated scripts, a markdown file loaded into any LLM agent, a custom IDE plugin, or even a set of verbal instructions consistently given alongside a collection of helper scripts. If Claude Code disappears tomorrow, karpathy scripts survive — because they describe a way of building reliable agent-driven operations, not a feature of a specific platform. This platform independence is what makes the concept a *design pattern* rather than a *product feature*, and it is the reason the term has value beyond any single tool's ecosystem.

**Intermediate artifact.** The karpathy script itself is an auditable, versionable document that sits between human intent and agent execution. Karpathy illustrates this pattern with his education example: rather than telling an AI "teach me physics" (where it "gets lost in the woods"), you create an intermediate artifact — a course — that can be inspected, refined, and improved independently of the execution. The karpathy script serves this same function. It is a reviewable specification of what the agent should do, not an ephemeral conversation that vanishes after execution.

## Discovering the Boundary

The most distinctive aspect of karpathy scripting is how the boundary between prompt and code is determined. The core question is always the same: for each aspect of the task, which paradigm — stochastic interpretation or deterministic execution — will produce more reliable results? Several approaches to answering this question are available, and they are not mutually exclusive.

**Empirical observation (the cowpath approach).** The original and most organic method. Begin with a pure prompt that describes the entire task. Execute it repeatedly across different inputs. Observe what the agent does consistently — which helper scripts it generates, which procedures it follows, which tools it reaches for. These repeated behaviors are the cowpaths. When the agent repeatedly generates nearly identical code for a deterministic operation, that code is a candidate for extraction: take a verified instance, make it permanent, and rewire the prompt to reference it instead of regenerating it. The boundary reveals itself through accumulated evidence.

**Agent-assisted analysis.** Rather than (or in addition to) observing behavior across many executions, consult the agent directly. Present a karpathy script draft and ask: "Which parts of this task would you handle with traditional code if you were executing it? What helper scripts would you create?" The agent's self-assessment of where it needs deterministic support can accelerate boundary discovery, particularly for tasks where repeated execution is expensive or impractical. This approach trades the empirical rigor of observation for speed, and the results should be validated against actual execution.

**Architectural reasoning.** For some tasks, the boundary is apparent from the nature of the work. File format parsing, mathematical computation, data validation against a fixed schema, and cryptographic operations are almost always better served by code. Semantic evaluation, summarization, contextual interpretation, and natural language generation are almost always better served by prompt. When the task decomposes cleanly along these lines, the boundary can be drawn before any execution occurs. The risk is that some tasks have subtler boundaries than they appear, and a boundary drawn from intuition may not match the agent's actual capabilities.

**Iterative refinement.** In practice, boundary discovery is often iterative regardless of the starting approach. A karpathy script deployed with an initial boundary may reveal — through subsequent use — that some prompt-handled tasks would be more reliable as code, or that some code components are unnecessarily rigid and could benefit from agent judgment. The boundary is a living decision, revisited as the task evolves and as agent capabilities change.

The key principle across all approaches is the same: **don't roll the dice on what can be fixed.** When the agent repeatedly generates nearly-identical code to perform a deterministic operation, each regeneration is a fresh opportunity for subtle errors. Whether that pattern is discovered through observation, self-assessment, or reasoning, the response is the same — extract it, verify it, cement it.

## Design Principles

Several principles guide the creation of effective karpathy scripts:

**Determinism where possible, judgment where necessary.** The goal is not to maximize the amount of natural language instruction or to minimize the amount of code. The goal is to place each aspect of the task in the domain where it will be handled most reliably. Data parsing with exact format requirements belongs in code. Evaluating whether a result is meaningful or anomalous belongs in prompt. If you're unsure, start with prompt and let experience reveal the answer.

**Reliable consistency.** A well-designed karpathy script should produce consistent results when given the same (or equivalent) inputs. "Consistent" does not mean "identical" — the phrasing of a natural language summary may vary between runs — but the substantive output that downstream processes or human consumers depend on should be stable. When a karpathy script produces materially different results on repeated runs with the same input, that is a signal that more of the task should be moved into the code component.

**Keep the agent on the leash.** Karpathy himself stresses that unconstrained agent autonomy leads to unreliable results. A karpathy script structures the agent's work into a defined corridor — specific steps, specific expectations — while still leveraging its judgment within that corridor. The generation-verification loop that Karpathy describes (the agent generates, the human verifies) should spin fast: concrete instructions increase the probability of successful verification, reducing wasted cycles.

**Accept stochastic tolerance.** A karpathy script will never be as deterministic as a pure traditional script. That is the trade-off. The output may vary in phrasing, formatting, or incidental details across runs. What matters is that the salient aspects — the parts that downstream processes depend on — are reliable. Define what "reliable enough" means for your use case and optimize for that threshold, not for an unattainable ideal of perfect reproducibility.

## When to Use a Karpathy Script

Karpathy scripts occupy a specific niche in the solution space. They are not appropriate for every problem, and understanding when to use them (and when not to) is essential.

**Use a karpathy script when:**

- The task involves a blend of NLP-native work (judgment, semantic analysis, natural language processing) and deterministic work (data transformation, file operations, structured computations).
- Development speed matters and a formal feature workflow would be disproportionately expensive relative to the task's complexity or expected lifetime.
- The task is repeatable — it will be executed multiple times across similar inputs.
- The acceptable error tolerance is non-zero but bounded. You need reliability, not perfection.

**Use a formal feature (traditional code) when:**

- The task is entirely deterministic with no NLP component.
- The task is critical infrastructure where any stochastic variance is unacceptable.
- The task requires comprehensive automated testing and regression prevention.
- The solution must operate without an LLM agent available.

**Use a pure prompt when:**

- The task is one-off and will not be repeated.
- The task is exploratory and the approach is not yet understood.
- The task is entirely NLP-native with no deterministic components.
- You are still in the early stages of understanding the task and haven't yet identified where the boundaries lie.

The boundaries between these categories are not rigid. A task that starts as a pure prompt may evolve into a karpathy script as it matures. A karpathy script that grows sufficiently complex and critical may eventually warrant promotion to a formal feature. The karpathy script practice is a point on a continuum, not a permanent classification.

## Karpathy Scripts in WSD

Within the Workscope-Dev framework, karpathy scripts have a natural home. WSD projects already provide the infrastructure that karpathy scripts require: slash command definitions (the delivery mechanism for prompt components), utility script directories (the home for code components), and an agent workflow system that regularly executes repeatable operations.

**Custom commands and skills.** Claude Code provides two mechanisms for packaging repeatable agent instructions, and understanding their relationship to karpathy scripts clarifies how the concept fits into practice.

*Custom commands* (`.claude/commands/`) are single markdown files injected into the agent's context when invoked. The agent can choose to follow them, partially follow them, or disregard them entirely — they are context, not execution. A custom command can contain a karpathy script's prompt component, but any code components must live elsewhere and be referenced by path. This works but means the karpathy script is split across multiple locations.

*Skills* (`.claude/skills/`) are the evolution of custom commands. A skill is a directory with a `SKILL.md` entry point alongside supporting files — scripts, templates, schemas, data fixtures — all bundled together and invocable as a single slash command. Skills also support YAML frontmatter configuration, argument passing via `$ARGUMENTS`, dynamic context injection (`` !`command` `` syntax that executes code and injects its output into the prompt before the agent sees it), and per-skill tool permissions. This makes skills a native container format for karpathy scripts: both the prompt component and the code components live in one self-contained directory.

Neither mechanism makes something a karpathy script automatically. A simple custom command or skill that says "list all open tickets" is just a saved prompt. The mechanism becomes a karpathy script when it incorporates the defining characteristics: hybrid prompt-and-code composition, structured multi-step agent direction, and repeatable execution with consistent results.

**Relationship to the WSD workflow.** Karpathy scripts complement, rather than replace, the formal feature workflow. They are appropriate for tasks that are too complex for ad-hoc prompting but too lightweight (or too time-sensitive) for a full Feature Overview, FIP, and multi-workscope implementation cycle. They fill the gap between "ask the agent once" and "build a formal tool."

**WSD's own karpathy scripts.** Several WSD slash commands are themselves karpathy scripts. `/wsd:init`, for example, contains conditional branching, variable generation, subroutine calls to other commands, file I/O operations (Work Journal creation via a shell script), and defined completion behavior — including evaluation of the Task-Master agent's output as a double-check against potential errors, which is the kind of semantic reasoning that a karpathy script is well suited for. These were developed organically — built to solve practical workflow problems — before the term existed, and they illustrate the principle that karpathy scripts often emerge from practice before they are recognized as such. WSD currently delivers these via the older custom commands structure (`.claude/commands/`); migration to skills is a natural evolution path that would allow each command to bundle its associated scripts and fixed elements into self-contained directories.

## Relationship to Adjacent Concepts

**Prompt engineering** is the practice of crafting effective prompts. Karpathy scripting subsumes prompt engineering for the prompt component but goes further by integrating deterministic code and deliberately identifying the boundary between what the agent should interpret and what a machine should execute.

**Prompt templates** parameterize prompts with variable substitution (fill in the blanks). Karpathy scripts are procedural — they define sequences, conditionals, checkpoints, and references to external code. A prompt template might say "Summarize {document}." A karpathy script says "Run `validate_format.py` against the input, then evaluate the validated output for anomalies, classify each finding by severity, and produce a structured report."

**Agent frameworks** (LangChain, CrewAI, etc.) orchestrate LLM calls programmatically in Software 1.0 — traditional code that invokes an LLM API. Karpathy scripts invert this: the natural language instruction is primary, and traditional code is invoked *by the agent* as a tool. The orchestration lives in Software 3.0, not Software 1.0.

**Claude Code skills** are a packaging mechanism that provides an excellent native container for karpathy scripts. The relationship between them — and why the concepts are distinct despite their natural affinity — is explored in detail in the section "Design Pattern vs. Packaging Mechanism" below.

**Vibe coding**, as Karpathy himself coined it, is the practice of building software through conversational, improvisational interaction with an LLM. Karpathy scripts are what vibe coding produces after it matures. Vibe coding is the exploration phase; karpathy scripting is the formalization phase. You vibe code first, observe what works, and then crystallize it into a karpathy script.

## What a Karpathy Script Is Not

Drawing negative boundaries helps clarify the concept. The following are common patterns that may superficially resemble karpathy scripts but lack defining characteristics.

**A custom GPT or system prompt is not a karpathy script.** Platforms like ChatGPT allow users to create "custom GPTs" with persistent instructions that shape the model's behavior. These are sophisticated prompts — sometimes very effective ones — but they lack code components. There is no deterministic element that the agent invokes; the entire operation is stochastic. A custom GPT is prompt engineering, not karpathy scripting.

**A traditional script that calls an LLM API is not a karpathy script.** A Python script that sends text to an API endpoint, receives a response, and processes it is Software 1.0 orchestrating an LLM call. The deterministic code is the host; the LLM is a service being consumed. This is the conventional agent framework pattern — the inverse of a karpathy script, where natural language is the host and code is the tool.

**A CI/CD pipeline with an AI step is not a karpathy script.** A GitHub Action that uses an LLM to generate PR summaries or review code is traditional automation with an LLM bolted on. The pipeline is deterministic orchestration; the LLM is one step in a fixed sequence. No agent is interpreting natural language instructions and exercising judgment about how to proceed.

**A one-off prompt, however complex, is not a karpathy script.** A carefully crafted prompt that produces an excellent result on a single execution is good prompt engineering. It becomes a karpathy script only when it is designed for repeated execution and incorporates fixed elements to stabilize that repetition. The distinction is between a conversation and a program.

**A pure automation workflow is not a karpathy script.** If every step is deterministic and the LLM could be replaced with a sufficiently complex traditional program, there is no karpathy script — there is just a script. The NLP-native component is not optional dressing; it is the reason the stochastic trade-off is justified in the first place.

## Design Pattern vs. Packaging Mechanism

Claude Code's skills feature provides a native container format for karpathy scripts: a directory bundling a prompt entry point (`SKILL.md`) with scripts, schemas, templates, and data files, all invocable as a single slash command. The affinity is natural and the fit is excellent. This raises an important question: if skills already provide the packaging, what does "karpathy script" add? Why not just call them skills?

The answer is the same reason we don't call the Strategy Pattern "using Java interfaces." Skills describe a delivery format. Karpathy scripts describe a design pattern — one that includes intent, methodology, failure theory, and guidance for when and how to apply it. The pattern exists at a different level of abstraction than the mechanism, and it survives independently of any particular tool.

**What skills provide.** Skills provide a container format: a directory structure, a frontmatter configuration language, argument passing, dynamic context injection, tool permissions, and an invocation mechanism. These are valuable infrastructure. A team building a karpathy script in the Claude Code ecosystem should absolutely use skills as the delivery mechanism.

**What skills don't provide.** Skills are agnostic about what you put in them and why. They don't provide:

*Boundary methodology.* Skills don't tell you how to determine what belongs in the prompt vs. the code. You could put everything in `SKILL.md` and leave the `scripts/` directory empty, or put everything in `scripts/` and reduce `SKILL.md` to "run the script." The karpathy script concept says this boundary has consequences, and offers methodology — cowpath observation, agent-assisted analysis, architectural reasoning, iterative refinement — for finding the right one.

*The inversion as a named pattern.* Skills don't require that natural language be the orchestrator. You could write a skill where the prompt merely launches a Python script that does all the work — that's just a script with a skill wrapper, not a karpathy script. The concept specifically identifies the Software 3.0-as-host pattern and names it as the structurally novel thing worth discussing.

*A development lifecycle.* Skills are static packages: you create them and deploy them. The karpathy script practice includes the arc from pure prompt to observed cowpaths to extracted code to stable hybrid — a development methodology for arriving at the artifact, not just a format for housing it.

*Failure theory.* When does this approach break? What does "rolling the dice" look like in practice? What's the cowpath risk? What happens when underlying models change? Skills documentation is silent on these questions because they're questions about the *pattern*, not the *packaging*.

**The design patterns analogy.** Design patterns survived even though the Gang of Four's original examples were in C++ and Smalltalk. "Refactoring" survived even though Fowler's examples were in Java. The insight transcended the implementation language because it described something real about how software should be structured, not something specific to a particular tool. Karpathy scripts occupy the same position relative to skills: the pattern describes something real about how to build reliable hybrid prompt-and-code artifacts. Skills are the current best implementation mechanism in the Claude Code ecosystem. If Cursor, Windsurf, or a future tool adds a similar packaging mechanism, those would also be valid containers for karpathy scripts — and the methodology, failure theory, and design principles would transfer unchanged.

**Open frontiers.** Several areas of the karpathy script concept have depth that no packaging mechanism naturally provides, and developing these areas further distinguishes the pattern from any single tool's feature set:

*Composability.* Can karpathy scripts call other karpathy scripts? WSD already demonstrates this — `/wsd:init` calls `/wsd:boot`. But the theory of composition is unexplored. How do stochastic operations chain? How do errors propagate through composed karpathy scripts? What are the patterns for reliable composition?

*Testing methodology.* Skills provide no guidance on how to test what you've built. Could there be a formal approach to testing karpathy scripts — perhaps even using karpathy scripts to test other karpathy scripts, leveraging agent judgment to evaluate whether the output of another agent-driven process meets expectations?

*Version evolution.* How does a karpathy script evolve when the underlying model changes? When the task requirements shift? When new agent capabilities emerge? The prompt component may need re-tuning while the code component stays stable, or vice versa. Understanding this lifecycle — and developing practices for managing it — is work that lives at the pattern level, not the packaging level.

These are open questions, not solved problems. But they illustrate the depth available to a design pattern that a packaging format simply doesn't need to address.

## Limitations and Risks

Karpathy scripts are not without drawbacks, and intellectual honesty about their limitations is important.

**Stochastic variance is real.** Even with deterministic code components extracted, the prompt component introduces irreducible variance. The agent may phrase outputs differently, take slightly different approaches to judgment calls, or occasionally misinterpret instructions. Downstream consumers must be designed to tolerate this variance or the karpathy script is the wrong tool.

**Testing is informal.** Unlike traditional code, which can be covered by automated test suites, the prompt component of a karpathy script is tested primarily through repeated execution and evaluation of results. There is no `pytest` for natural language instructions. Regression detection depends on noticing degraded output quality, whether through human review or automated consistency checks on the deterministic portions of the output.

**Agent model dependency.** A karpathy script is tuned to the behavior of a particular class of LLM. Model updates, capability changes, or switching between providers may alter how the prompt component is interpreted. The code components are immune to this, but the prompt components may require re-tuning — much as Karpathy notes that LLM apps are somewhat analogous to apps built for a specific operating system.

**Cowpath risk.** The cowpath methodology can cement suboptimal patterns if the initial observation period is too short or the input diversity is too narrow. Just as the famous warning says "don't pave the cowpaths" when the paths themselves are wrong, a karpathy script developer must exercise judgment about whether the observed agent behavior represents a good solution or merely a habitual one.

These limitations are manageable in practice. They are the trade-offs accepted in exchange for the speed, capability, and NLP-native power that karpathy scripts provide. The key is understanding the trade-offs clearly and choosing karpathy scripts for tasks where the benefits outweigh the costs.

## Why the Term Matters

The practice of combining natural language instructions with fixed code artifacts is already happening — in WSD projects, in AI-assisted development workflows, in ad-hoc scripts that teams build and refine without a shared vocabulary to describe what they're doing. Naming the pattern makes it a practice rather than an accident.

"Refactoring" existed as an activity before Martin Fowler gave it a name, but the name made it teachable, discussable, and defensible. A developer could say "I'm not rewriting the code, I'm refactoring it" and everyone understood the intent, the constraints, and the expected outcome. The same dynamic applies here. When a team has a word for the hybrid artifact they're building — "this is a karpathy script" — they can reason about it as a category. They can ask whether a given task is better served by a karpathy script or a formal feature. They can discuss whether the boundary between prompt and code is in the right place. They can teach new team members the pattern instead of letting each person rediscover it independently.

The term also captures something about where we are in the evolution of software. Karpathy's Software 3.0 paradigm is real, but the industry is still in its earliest stages — the 1960s of this new computing era, as Karpathy himself puts it. We don't yet have mature tooling, established best practices, or a shared vocabulary for the patterns emerging in this space. Coining "karpathy script" is a small contribution to that vocabulary: a name for the specific, practical artifact that sits at the intersection of human language and machine code, leveraging the strengths of both.
