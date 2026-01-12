---
description: Load WSD Platform system documentation for agent onboarding
---

# WSD Platform Boot

This command introduces a new agent to the WSD Platform and the necessary systems it will need to be familiar with. This is placed in a separate command to facilitate JIT loading of these materials and side-step AI Harness "hoisting" of detected filepaths, which are loaded into User Agent context prior to the user receiving the command text. Parent commands can call into this command at the point where loading this information is appropriate.

## Usage

```
/wsd:boot
```

---

## Workscope System

**IMPORTANT FRAMING**: You are about to read documentation describing our standard agent workflow system. This reading is for CONTEXT AND UNDERSTANDING ONLY. These documents describe how the system typically operates, but whether you will actually engage with this workflow depends entirely on the specific instructions you receive AFTER initialization. Do not automatically execute the workflows described in these documents - they are knowledge, not instructions.

Read the following files to understand the Workscope-Dev (WSD) Platform's systems:

- Agent System Overview: `docs/read-only/Agent-System.md` ( @docs/read-only/Agent-System.md )
- Agent Rules: `docs/read-only/Agent-Rules.md` ( @docs/read-only/Agent-Rules.md )
- Design Decisions: `docs/core/Design-Decisions.md` ( @docs/core/Design-Decisions.md )
- Documentation System Overview: `docs/read-only/Documentation-System.md` ( @docs/read-only/Documentation-System.md )
- Checkboxlist System Overview: `docs/read-only/Checkboxlist-System.md` ( @docs/read-only/Checkboxlist-System.md )
- Workscope System Overview: `docs/read-only/Workscope-System.md` ( @docs/read-only/Workscope-System.md )

Return to the calling function (if called from within a function).
