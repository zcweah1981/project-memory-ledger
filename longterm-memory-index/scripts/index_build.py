#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build/update Long-term Memory v2 index (L2) from L1 ledgers.

Reads Markdown ledgers in `<workspace>/ledgers/*.md` and extracts appended blocks:

<!-- appended 2026-03-20 13:26 -->
- **Project**: keyword-engine
- **Change**: ...
- **Tags**: ...

Outputs SQLite index DB with FTS for fast retrieval.

Usage:
  python3 memory-index/scripts/index_build.py \
    --workspace /root/.openclaw/workspace-nero \
    --db /root/.openclaw/workspace-nero/data/ledger_index.sqlite
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

APPENDED_RE = re.compile(r"<!--\s*appended\s+([^>]+?)\s*-->")
FIELD_RE = re.compile(r"^-\s*\*\*(.+?)\*\*:\s*(.*)$")


@dataclass
class Block:
    doc: str
    header: str
    header_line: int
    body: str


def iter_blocks(md_text: str, doc: str) -> List[Block]:
    lines = md_text.splitlines()
    idxs = []
    for i, line in enumerate(lines, start=1):
        if APPENDED_RE.search(line):
            idxs.append(i)
    blocks: List[Block] = []
    for n, start in enumerate(idxs):
        end = (idxs[n + 1] - 1) if n + 1 < len(idxs) else len(lines)
        header = lines[start - 1]
        body = "\n".join(lines[start:end]).strip()  # exclude header line
        blocks.append(Block(doc=doc, header=header, header_line=start, body=body))
    return blocks


def parse_fields(body: str) -> dict:
    out = {}
    tags = None
    for raw in body.splitlines():
        m = FIELD_RE.match(raw.strip())
        if not m:
            continue
        k = m.group(1).strip().lower()
        v = m.group(2).strip()
        out[k] = v
        if k == 'tags':
            tags = v
    # normalize
    if tags is not None:
        parts = [p.strip() for p in tags.split(',')]
        out['tags_list'] = [p for p in parts if p]
    else:
        out['tags_list'] = []
    return out


def infer_type(fields: dict, doc: str) -> str:
    if doc.lower().startswith('invariants'):
        return 'invariant'
    if doc.lower().startswith('decisions'):
        return 'decision'
    if doc.lower().startswith('changes'):
        return 'change'
    # fallback
    if 'decision' in fields:
        return 'decision'
    if 'change' in fields:
        return 'change'
    return 'note'


def one_liner(fields: dict, typ: str) -> str:
    # prefer explicit field
    key = 'decision' if typ == 'decision' else ('change' if typ == 'change' else 'invariant')
    s = (fields.get(key) or fields.get('summary') or '').strip()
    if not s:
        # take first non-empty line
        for ln in (fields.get('decision') or fields.get('change') or '').splitlines():
            ln = ln.strip()
            if ln:
                s = ln
                break
    # hard cap
    s = re.sub(r"\s+", " ", s)
    return s[:160]


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def init_db(db: Path) -> None:
    con = sqlite3.connect(str(db))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS ledger_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project TEXT,
          doc TEXT,
          type TEXT,
          date TEXT,
          summary TEXT,
          tags_json TEXT,
          source_path TEXT,
          source_line INTEGER,
          source_hash TEXT UNIQUE,
          created_at TEXT
        )
        """
    )
    # FTS (summary + tags + project)
    # Contentless FTS index (we manage rows manually)
    con.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS ledger_items_fts
        USING fts5(summary, project, tags, source, content='');
        """
    )
    con.commit()
    con.close()


def upsert(con: sqlite3.Connection, item: dict) -> None:
    con.execute(
        """
        INSERT OR IGNORE INTO ledger_items(
          project, doc, type, date, summary, tags_json,
          source_path, source_line, source_hash, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            item.get('project'),
            item.get('doc'),
            item.get('type'),
            item.get('date'),
            item.get('summary'),
            json.dumps(item.get('tags_list') or [], ensure_ascii=False),
            item.get('source_path'),
            int(item.get('source_line') or 0),
            item.get('source_hash'),
            item.get('created_at'),
        ),
    )


def rebuild_fts(con: sqlite3.Connection) -> None:
    # Contentless FTS tables can't be DELETE'd directly. Rebuild by drop+create.
    con.execute("DROP TABLE IF EXISTS ledger_items_fts")
    con.execute(
        """
        CREATE VIRTUAL TABLE ledger_items_fts
        USING fts5(summary, project, tags, source, content='');
        """
    )
    con.execute(
        """
        INSERT INTO ledger_items_fts(rowid, summary, project, tags, source)
        SELECT id,
               COALESCE(summary,''),
               COALESCE(project,''),
               COALESCE(tags_json,''),
               COALESCE(source_path,'') || ':' || COALESCE(source_line,0)
        FROM ledger_items
        """
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workspace', required=True)
    ap.add_argument('--db', required=True)
    args = ap.parse_args()

    ws = Path(args.workspace)
    ledgers = ws / 'ledgers'
    db = Path(args.db)
    db.parent.mkdir(parents=True, exist_ok=True)

    init_db(db)

    con = sqlite3.connect(str(db))
    con.execute("PRAGMA journal_mode=WAL;")

    inserted = 0
    for p in sorted(ledgers.glob('*.md')):
        doc = p.stem
        text = p.read_text(encoding='utf-8', errors='ignore')
        for blk in iter_blocks(text, doc):
            # Some ledger entries were written with literal "\\n" sequences.
            # Normalize them back to real newlines for parsing.
            body_norm = (blk.body or '').replace('\\n', '\n')
            fields = parse_fields(body_norm)
            project = (fields.get('project') or '').strip()
            typ = infer_type(fields, doc)

            # date from header
            m = APPENDED_RE.search(blk.header)
            header_ts = (m.group(1).strip() if m else '')
            date = header_ts.split()[0] if header_ts else ''

            item = {
                'project': project,
                'doc': doc.lower(),
                'type': typ,
                'date': date,
                'summary': one_liner(fields, typ),
                'tags_list': fields.get('tags_list') or [],
                'source_path': str(p.relative_to(ws)),
                'source_line': blk.header_line,
                'source_hash': sha1(f"{p}:{blk.header_line}:{body_norm}"),
                'created_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
            }
            upsert(con, item)
            inserted += con.total_changes

    rebuild_fts(con)
    con.commit()
    con.close()

    print(f"OK: index built db={db} inserted={inserted}")


if __name__ == '__main__':
    main()
