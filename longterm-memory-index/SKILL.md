---
name: longterm-memory-index
description: |
  Build and query a low-token retrieval index (SQLite + FTS) for OpenClaw long-term memory ledgers (INVARIANTS/DECISIONS/CHANGES).
  Use when the user asks to: (1) make long-term memory searchable, (2) create an index + one-line summaries from conversation/ledger entries,
  (3) reduce token usage by retrieving only top relevant items, (4) rebuild/reindex memory, (5) query "what did we decide/change" quickly.
---

# Long-term Memory Index (L2)

## What this skill does
- Builds an **L2 retrieval index** (`ledger_index.sqlite`) from L1 ledgers:
  - `<workspace>/ledgers/INVARIANTS.md`
  - `<workspace>/ledgers/DECISIONS.md`
  - `<workspace>/ledgers/CHANGES.md`
- Supports fast queries that return **one-line summaries + pointers** (file + line), so the agent does not need to load entire ledgers.

## Files
- Scripts:
  - `scripts/index_build.py`
  - `scripts/index_query.py`
- Reference:
  - `references/INDEX.md`

## Commands (runbook)

### Build / rebuild index
```bash
python3 skills/longterm-memory-index/scripts/index_build.py \
  --workspace <workspace> \
  --db <workspace>/data/ledger_index.sqlite
```

### Query
```bash
python3 skills/longterm-memory-index/scripts/index_query.py \
  --db <workspace>/data/ledger_index.sqlite \
  --q "keyword engine" \
  --limit 5

python3 skills/longterm-memory-index/scripts/index_query.py \
  --db <workspace>/data/ledger_index.sqlite \
  --q "trends" \
  --project keyword-engine \
  --limit 10
```

## Output discipline (token control)
- Default: return top 5 items.
- Each item summary is capped to 160 chars.
- Only open the referenced L1 lines when more detail is required.

## Control Panel (L0)
Generate a short (≤30 lines) Control Panel for a project, then optionally publish to a Drive GDoc.

Generate:
```bash
python3 skills/longterm-memory-index/scripts/control_panel_generate.py \
  --db <workspace>/data/ledger_index.sqlite \
  --project keyword-engine \
  > /tmp/control_panel_keyword_engine.md
```

Publish to Drive (prepend into doc):
```bash
python3 skills/longterm-memory-index/scripts/control_panel_publish_drive.py \
  --doc-id <GDocId> \
  --text-file /tmp/control_panel_keyword_engine.md
```

Note: v1 publish prepends content (may duplicate if re-run). Replace-in-place can be added later.
