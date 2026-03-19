# Project Memory Ledger (OpenClaw Skill)

Durable, low-pollution **engineering project memory** with evidence + rollback.

This skill maintains a ledger split into three “books”:
- **Invariants**: hard rules / stable facts
- **Decisions**: tradeoffs + rationale
- **Changes**: what changed + why + evidence + impact + rollback

It supports multiple storage backends:
- **local**: markdown files only (always works)
- **drive**: Google Docs in Drive (requires a Drive backend)
- **both**: write local + drive

> v1 Drive implementation uses the `gws` CLI. If Drive is not available, switch to `local`.

---

## Files

- Skill folder: `skills/project-memory-ledger/`
- Main script: `skills/project-memory-ledger/scripts/ledger.py`
- Templates: `skills/project-memory-ledger/references/ledger_templates.md`
- Default config template: `skills/project-memory-ledger/references/default_config.json`

Local output directory (default):
- `/root/.openclaw/workspace-nero/ledgers/`
  - `INVARIANTS.md`
  - `DECISIONS.md`
  - `CHANGES.md`
  - `PROJECTS.md` (when registering projects)

---

## Quick start

### 1) Create config

Recommended path:
- `/root/.openclaw/workspace-nero/config/project_memory_ledger.json`

Minimal config (local-only):
```json
{
  "language": "zh",
  "backend": "local",
  "default_project": "project-memory-ledger",
  "local_dir": "/root/.openclaw/workspace-nero/ledgers",
  "doc_titles": {
    "invariants": "System Invariants & Rules（总账）",
    "decisions": "Decision Log（总账）",
    "changes": "Change Log（总账）"
  },
  "docs": {
    "invariants_doc_id": "",
    "decision_log_doc_id": "",
    "change_log_doc_id": ""
  }
}
```

Drive/both config (adds `shared_folder_id`):
```json
{
  "language": "zh",
  "backend": "both",
  "default_project": "project-memory-ledger",
  "local_dir": "/root/.openclaw/workspace-nero/ledgers",
  "shared_folder_id": "<Drive folder id for Shared/>",
  "doc_titles": {
    "invariants": "System Invariants & Rules（总账）",
    "decisions": "Decision Log（总账）",
    "changes": "Change Log（总账）"
  },
  "docs": {
    "invariants_doc_id": "",
    "decision_log_doc_id": "",
    "change_log_doc_id": ""
  }
}
```

### 2) Init

```bash
python3 skills/project-memory-ledger/scripts/ledger.py init \
  --config /root/.openclaw/workspace-nero/config/project_memory_ledger.json
```

- `local`: creates local ledger files
- `drive/both`: also creates/links 3 Google Docs in the `Shared/` Drive folder

### 3) Append an entry

```bash
python3 skills/project-memory-ledger/scripts/ledger.py append \
  --config /root/.openclaw/workspace-nero/config/project_memory_ledger.json \
  --doc changes \
  --project "Keyword Engine" \
  --text "- **Interfaces**: hunter-system ↔ keyword-engine\n- **Change**: ...\n- **Why**: ...\n- **Evidence**: ...\n- **Rollback**: ...\n"
```

### 4) Register a project (optional)

```bash
python3 skills/project-memory-ledger/scripts/ledger.py register-project \
  --config /root/.openclaw/workspace-nero/config/project_memory_ledger.json \
  --name "My New Project" \
  --purpose "Why it exists + success criteria" \
  --interfaces "hunter-system ↔ keyword-engine" \
  --notes "optional"
```

---

## Conventions

### Project tagging

Project values are **case-insensitive** and normalized to slugs.

Recommended project slugs:
- `hunter-system`
- `keyword-engine`
- `common` (cross-project rules/methods; not global AGENTS/MEMORY)

`shared` is disabled. For cross-project coupling, use an explicit field:
- `Interfaces: a ↔ b`

### Default project

If you omit `--project`, the script injects:
- `Project: project-memory-ledger`

This is intended for changes/requirements about the skill itself.

---

## Drive backend options

Drive mode is a **pluggable backend**:
- Option 1 (default / v1 implemented): `gws` CLI (installed + authenticated)
- Option 2: Google API / service account (good for servers/CI)
- Option 3: third-party Drive tooling

If Drive isn’t available, use `backend=local`.

---

## Publishing

### GitHub
Commit the folder:
- `skills/project-memory-ledger/`

### ClawHub (later)
Once ready, publish from the skill folder:
```bash
clawhub publish ./skills/project-memory-ledger \
  --slug project-memory-ledger \
  --name "Project Memory Ledger" \
  --version 0.1.0 \
  --changelog "Initial release"
```
