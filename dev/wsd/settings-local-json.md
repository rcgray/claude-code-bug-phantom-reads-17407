# Claude Code Local Settings for WSD Projects

This file documents the recommended `.claude/settings.local.json` configuration for WSD integration. These settings enhance the WSD experience by protecting sensitive files, auto-approving routine operations, and providing desktop notifications.

Unlike language-specific configuration files, `settings.local.json` applies to every WSD project regardless of whether the project uses Python, TypeScript, JavaScript, or no programming language at all.

---

## Purpose

Claude Code uses `settings.local.json` for project-level configuration that controls permissions, restrictions, and hooks. WSD recommends specific settings in three areas:

| Area | Purpose |
|------|---------|
| **Permissions (allow)** | Auto-approve routine WSD operations so agents can work without repeated permission prompts |
| **Permissions (deny)** | Protect sensitive directories from accidental reads or edits by AI agents |
| **Hooks** | Enforce file protection at the tool level and provide desktop notifications on macOS |

These settings are recommendations that improve the WSD workflow. WSD functions without them, but they provide meaningful quality-of-life improvements: deny rules prevent agents from accidentally editing protected documentation, the `protect_files.py` hook enforces file protection at the tool level, and notification hooks alert you when Claude Code needs attention.

---

## Recommended Configuration

A complete recommended `settings.local.json` for WSD projects:

```json
{
  "permissions": {
    "allow": [
      "Bash(scripts/init_work_journal.sh *)",
      "Bash(*/scripts/init_work_journal.sh *)",
      "Bash(bash scripts/init_work_journal.sh:*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./dev/prompts/**)",
      "Read(./dev/reports/**)",
      "Read(./dev/workbench/**)",
      "Edit(./docs/read-only/**)",
      "Edit(./docs/references/**)",
      "Edit(./docs/reports/**)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/protect_files.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "macos-notification",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/misc/macos-notification.sh \"Project Ready\""
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/misc/macos-notification.sh \"Input Required\""
          }
        ]
      }
    ]
  }
}
```

---

## Section Breakdown

### Permissions: Allow Rules

The `permissions.allow` array auto-approves specific Bash commands so that agents are not interrupted by permission prompts for routine WSD operations.

| Pattern | Purpose |
|---------|---------|
| `Bash(scripts/init_work_journal.sh *)` | Allow the work journal initialization script to run from the project root |
| `Bash(*/scripts/init_work_journal.sh *)` | Allow the script when invoked with a path prefix |
| `Bash(bash scripts/init_work_journal.sh:*)` | Allow the script when invoked explicitly with `bash` |

These three patterns cover the common ways that agents invoke the work journal initialization script during the `/wsd:init` command. Without these allow rules, agents would need to request permission each time a new workscope session begins.

**Customization:** If your project adds other WSD scripts that agents invoke frequently, you can add additional allow patterns following the same format. Each pattern should be as specific as possible to avoid granting overly broad permissions.

### Permissions: Deny Rules

The `permissions.deny` array prevents AI agents from reading or editing files that should remain untouched. Deny rules take two forms: `Read()` rules block file access entirely, and `Edit()` rules allow reading but prevent modifications.

#### Read Restrictions

| Pattern | Purpose |
|---------|---------|
| `Read(./.env)` | Protect environment secrets (API keys, passwords, tokens) from being read by agents |
| `Read(./dev/prompts/**)` | Protect prompt engineering files from agent access |
| `Read(./dev/reports/**)` | Protect tool-generated reports from agent access |
| `Read(./dev/workbench/**)` | Protect the development workbench from agent access |

#### Edit Restrictions

| Pattern | Purpose |
|---------|---------|
| `Edit(./docs/read-only/**)` | Prevent agents from modifying system documentation, rules, and standards |
| `Edit(./docs/references/**)` | Prevent agents from modifying reference materials and templates |
| `Edit(./docs/reports/**)` | Prevent agents from modifying tool-generated project reports |

**How deny rules work:** Claude Code checks these patterns before executing tool operations. When a deny rule matches, the operation is blocked and the agent receives a message explaining why access was denied. This provides a first line of defense against accidental modifications to protected content.

**Customization:** Add deny rules for any project-specific directories that agents should not access. For example, if your project has a `secrets/` directory, add `Read(./secrets/**)` to protect it.

### Hooks: PreToolUse (File Protection)

The `PreToolUse` hook runs before Claude Code executes a tool operation, providing an enforcement layer beyond the built-in deny rules.

```json
{
  "matcher": "Read",
  "hooks": [
    {
      "type": "command",
      "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/protect_files.py"
    }
  ]
}
```

**What it does:** The `protect_files.py` script intercepts `Read` tool operations and checks the target file path against the deny patterns defined in `settings.local.json`. If the file matches a `Read()` deny pattern, the hook blocks the operation and returns a security policy violation message to the agent.

**Why both deny rules and a hook?** The deny rules provide Claude Code's built-in permission checking, while the hook provides an additional programmatic enforcement layer. The hook reads the deny patterns from `settings.local.json` at runtime, so it automatically respects any custom deny rules you add.

**Requirements:** Python 3.10+ must be available on the system for the hook script to execute. The script must have execute permissions (WSD sets this during installation).

### Hooks: Stop (Desktop Notification)

The `Stop` hook fires when Claude Code finishes processing and returns control to the user.

```json
{
  "matcher": "macos-notification",
  "hooks": [
    {
      "type": "command",
      "command": "$CLAUDE_PROJECT_DIR/.claude/misc/macos-notification.sh \"Project Ready\""
    }
  ]
}
```

**What it does:** Sends a macOS desktop notification with the title "Project Ready" when Claude Code completes a task and is waiting for input. The notification includes context from the conversation transcript: the last user message as a subtitle and the last assistant message as the body text.

**Requirements:** This hook requires `terminal-notifier` to be installed on macOS. Install with `brew install terminal-notifier`. The notification sound is "Glass" by default. See the Platform Considerations section below for cross-platform guidance.

### Hooks: Notification (Input Required)

The `Notification` hook fires when Claude Code needs user input or attention.

```json
{
  "matcher": "",
  "hooks": [
    {
      "type": "command",
      "command": "$CLAUDE_PROJECT_DIR/.claude/misc/macos-notification.sh \"Input Required\""
    }
  ]
}
```

**What it does:** Sends a macOS desktop notification with the title "Input Required" when Claude Code is waiting for a user decision or response. The empty matcher (`""`) means this hook fires for all notification events. Like the Stop hook, it includes conversation context in the notification body.

**Requirements:** Same as the Stop hook — requires `terminal-notifier` on macOS.

---

## Platform Considerations

### macOS

All recommended settings work on macOS. The notification hooks require `terminal-notifier`:

```bash
brew install terminal-notifier
```

The notification script logs events to `~/.local/share/ccnotify/notifications.log` in JSON format, which can be useful for debugging notification issues.

### Linux and WSL

The permissions and PreToolUse hook work identically on Linux and WSL. However, the Stop and Notification hooks use `terminal-notifier`, which is a macOS-only tool. These hooks should be **omitted** on Linux and WSL systems.

**Recommended Linux/WSL configuration:** Use the full recommended configuration but remove the `Stop` and `Notification` sections from the `hooks` object:

```json
{
  "permissions": {
    "allow": [
      "Bash(scripts/init_work_journal.sh *)",
      "Bash(*/scripts/init_work_journal.sh *)",
      "Bash(bash scripts/init_work_journal.sh:*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./dev/prompts/**)",
      "Read(./dev/reports/**)",
      "Read(./dev/workbench/**)",
      "Edit(./docs/read-only/**)",
      "Edit(./docs/references/**)",
      "Edit(./docs/reports/**)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/protect_files.py"
          }
        ]
      }
    ]
  }
}
```

If you develop a cross-platform notification solution (e.g., using `notify-send` on Linux), you can add equivalent hooks targeting your notification tool.

---

## Merging with Existing Settings

If your project already has a `.claude/settings.local.json` with your own permissions or hooks, merge the WSD recommendations alongside your existing configuration rather than replacing it.

### Merging Permissions

The `allow` and `deny` arrays can contain entries from multiple sources. Add the WSD entries alongside your own:

```json
{
  "permissions": {
    "allow": [
      "Bash(scripts/init_work_journal.sh *)",
      "Bash(*/scripts/init_work_journal.sh *)",
      "Bash(bash scripts/init_work_journal.sh:*)",
      "Bash(my-custom-script.sh *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./dev/prompts/**)",
      "Read(./dev/reports/**)",
      "Read(./dev/workbench/**)",
      "Edit(./docs/read-only/**)",
      "Edit(./docs/references/**)",
      "Edit(./docs/reports/**)",
      "Read(./my-secrets/**)",
      "Edit(./my-protected-dir/**)"
    ]
  }
}
```

### Merging Hooks

Hooks are organized by event type (`PreToolUse`, `Stop`, `Notification`). Each event type holds an array of hook entries, so you can add WSD hooks alongside your own:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/protect_files.py"
          }
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/my-custom-write-hook.sh"
          }
        ]
      }
    ]
  }
}
```

### Conflict Resolution

If your existing settings conflict with WSD recommendations:

- **Deny rules:** WSD deny rules protect WSD-specific directories. If you have broader deny rules that already cover these paths, the WSD-specific rules are redundant but harmless.
- **Allow rules:** WSD allow rules are narrow and specific to WSD scripts. They should not conflict with existing allow rules.
- **Hooks:** Multiple hooks can coexist for the same event type. Each hook entry in the array runs independently.

---

## Complete Example

Here is the full recommended `.claude/settings.local.json` for a WSD project on macOS:

```json
{
  "permissions": {
    "allow": [
      "Bash(scripts/init_work_journal.sh *)",
      "Bash(*/scripts/init_work_journal.sh *)",
      "Bash(bash scripts/init_work_journal.sh:*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./dev/prompts/**)",
      "Read(./dev/reports/**)",
      "Read(./dev/workbench/**)",
      "Edit(./docs/read-only/**)",
      "Edit(./docs/references/**)",
      "Edit(./docs/reports/**)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/protect_files.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "macos-notification",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/misc/macos-notification.sh \"Project Ready\""
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/misc/macos-notification.sh \"Input Required\""
          }
        ]
      }
    ]
  }
}
```

---

*See `Integration-Guide.md` for complete WSD installation instructions and `User-Guide.md` for daily usage reference.*
