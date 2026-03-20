#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish a Control Panel (L0) into a Drive GDoc (prepend at top).

v1 behavior: insert at index=1 with a unique marker header.
If you re-run, you'll create duplicates (by design). Later we can implement
"replace between markers" with structural parsing.

Usage:
  python3 skills/longterm-memory-index/scripts/control_panel_publish_drive.py \
    --doc-id <gdoc_id> \
    --text-file /tmp/control_panel.md
"""

from __future__ import annotations

import argparse
from pathlib import Path
import json
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--doc-id', required=True)
    ap.add_argument('--text-file', required=True)
    args = ap.parse_args()

    text = Path(args.text_file).read_text(encoding='utf-8')
    payload = {
        'requests': [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': "\n\n" + text.strip() + "\n\n---\n\n",
                }
            }
        ]
    }
    subprocess.run(
        [
            'gws', 'docs', 'documents', 'batchUpdate',
            '--params', json.dumps({'documentId': args.doc_id}),
            '--json', json.dumps(payload, ensure_ascii=False),
        ],
        check=True,
    )
    print('OK: published control panel to doc', args.doc_id)


if __name__ == '__main__':
    main()
