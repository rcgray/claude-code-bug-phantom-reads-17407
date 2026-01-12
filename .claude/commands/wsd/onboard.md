---
description: Collect onboarding context from Project-Bootstrapper for custom workscopes
---

# User Agent Onboarding

This command collects additional onboarding requirements and expectations for User Agent behavior.

## Usage

```
/wsd:onboard
```

## Examples

```
/wsd:onboard
```

---

## User Agent Onboarding

After (or during) your initialization command (with `/wsd:init --custom`), you should now have:
- A Work Journal in the archive location (`dev/journal/archive/Journal-Workscope-[Workscope ID].md`)
- Optionally, a description of a workscope or an area that you will be working with. Alternatively, the User may provide this to you AFTER you finish this onboarding.

Consult @agent-project-bootstrapper and provide them with a description of your workscope (if it was provided to you). The Project-Bootstrapper has complete instructions in its definition and will provide the necessary on-boarding that you need to prevent you from making mistakes that would ultimately disqualify your work. DO NOT EXECUTE YOUR WORKSCOPE YET. Simply read the files provided to you and append your report to your Work Journal before moving on to the next step. Include this list of all files you are supposed to read in this Work Journal update.

After reviewing your new materials, echo a clear message confirming you have done so.

MANDATORY: Put the following text at the END of your reply, verbatim:
**"WORKSCOPE ONBOARDING (/wsd:onboard) COMPLETE."**

Then, either return to your previous execution point in the calling command (such as `/wsd:init` or `/wsd:prepare`). If not called from another command, simply halt and wait for review and further instruction.

## Error Handling

The command should handle these error conditions:

1. **Agent communication failures**: Retry agent communications if they fail
