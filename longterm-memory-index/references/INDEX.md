# Long-term Memory v2 — Index (L2)

This module builds a low-token retrieval index from L1 ledgers:
- `ledgers/INVARIANTS.md`
- `ledgers/DECISIONS.md`
- `ledgers/CHANGES.md`

## DB
- `data/ledger_index.sqlite`

## Build
```bash
python3 memory-index/scripts/index_build.py --workspace . --db data/ledger_index.sqlite
```

## Query
```bash
python3 memory-index/scripts/index_query.py --db data/ledger_index.sqlite --q "keyword engine" --limit 5
python3 memory-index/scripts/index_query.py --db data/ledger_index.sqlite --q "trends" --project keyword-engine --limit 10
```

## Notes
- Keeps output small: summaries are capped to 160 chars.
- Normalizes older entries that contain literal `\\n` sequences.
