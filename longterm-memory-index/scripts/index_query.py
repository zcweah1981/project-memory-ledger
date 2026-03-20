#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query Long-term Memory v2 index (L2) with low token output.

Usage:
  python3 memory-index/scripts/index_query.py --db data/ledger_index.sqlite \
    --q "keyword-pack" --project keyword-engine --limit 5
"""

from __future__ import annotations

import argparse
import json
import sqlite3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--q', required=True)
    ap.add_argument('--project', default='')
    ap.add_argument('--type', default='')
    ap.add_argument('--limit', type=int, default=5)
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    where = []
    params = []

    # FTS query on summary/project/tags_json
    fts_q = args.q

    sql = """
    SELECT li.id, li.project, li.doc, li.type, li.date, li.summary, li.tags_json, li.source_path, li.source_line
    FROM ledger_items_fts fts
    JOIN ledger_items li ON li.id = fts.rowid
    WHERE ledger_items_fts MATCH ?
    """
    params.append(fts_q)

    if args.project:
        sql += " AND li.project = ?"
        params.append(args.project)
    if args.type:
        sql += " AND li.type = ?"
        params.append(args.type)

    sql += " ORDER BY li.date DESC, li.id DESC LIMIT ?"
    params.append(int(args.limit))

    rows = con.execute(sql, params).fetchall()
    con.close()

    out = []
    for r in rows:
        out.append({
            'project': r['project'],
            'type': r['type'],
            'date': r['date'],
            'summary': r['summary'],
            'tags': json.loads(r['tags_json'] or '[]'),
            'source': f"{r['source_path']}:{r['source_line']}",
        })

    print(json.dumps({'q': args.q, 'count': len(out), 'items': out}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
