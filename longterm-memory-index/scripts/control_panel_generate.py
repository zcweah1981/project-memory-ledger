#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a low-token Control Panel (L0) for a project from the L2 index.

Output is plain text (Markdown-friendly) capped to ~30 lines.

Usage:
  python3 skills/longterm-memory-index/scripts/control_panel_generate.py \
    --db <workspace>/data/ledger_index.sqlite \
    --project keyword-engine \
    --limit-decisions 5 --limit-changes 5

Notes:
- This script does NOT load full ledgers; it only uses the indexed one-liners.
- Invariants are currently referenced by link to ledgers/INVARIANTS.md (kept short).
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone


def ymd_today_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def sanitize_fts(q: str) -> str:
    q = re.sub(r"[^0-9A-Za-z_\s]", " ", q or "").strip()
    return q


def query(con: sqlite3.Connection, q: str, project: str, typ: str, limit: int):
    q = sanitize_fts(q)
    sql = """
    SELECT li.project, li.type, li.date, li.summary, li.tags_json, li.source_path, li.source_line
    FROM ledger_items_fts fts
    JOIN ledger_items li ON li.id = fts.rowid
    WHERE ledger_items_fts MATCH ?
      AND li.project = ?
      AND li.type = ?
    ORDER BY li.date DESC, li.id DESC
    LIMIT ?
    """
    rows = con.execute(sql, (q, project, typ, int(limit))).fetchall()
    out = []
    for r in rows:
        out.append({
            'date': r[2],
            'summary': r[3],
            'tags': json.loads(r[4] or '[]'),
            'source': f"{r[5]}:{r[6]}",
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--project', required=True)
    ap.add_argument('--limit-decisions', type=int, default=5)
    ap.add_argument('--limit-changes', type=int, default=5)
    ap.add_argument('--q', default='', help='Optional extra query term; default uses project name')
    args = ap.parse_args()

    con = sqlite3.connect(args.db)

    q = args.q.strip() or args.project

    decisions = query(con, q, args.project, 'decision', args.limit_decisions)
    changes = query(con, q, args.project, 'change', args.limit_changes)

    con.close()

    lines = []
    lines.append(f"# Control Panel — {args.project}")
    lines.append(f"Updated: {ymd_today_utc()} (UTC)")
    lines.append("")

    lines.append("## Invariants (L1)")
    lines.append("- See: ledgers/INVARIANTS.md (search for this project + common)")
    lines.append("")

    lines.append("## Latest Decisions (top)")
    if not decisions:
        lines.append("- (none indexed yet)")
    else:
        for it in decisions:
            lines.append(f"- {it['date']} | {it['summary']}  ({it['source']})")
    lines.append("")

    lines.append("## Latest Changes (top)")
    if not changes:
        lines.append("- (none indexed yet)")
    else:
        for it in changes:
            lines.append(f"- {it['date']} | {it['summary']}  ({it['source']})")
    lines.append("")

    lines.append("## Fast Query")
    lines.append(f"- Query: python3 skills/longterm-memory-index/scripts/index_query.py --db data/ledger_index.sqlite --q \"{args.project}\" --limit 5")

    print("\n".join(lines).strip())


if __name__ == '__main__':
    main()
