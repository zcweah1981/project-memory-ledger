#!/usr/bin/env python3
"""Drive Ledger utilities.

Requires: gws CLI already authenticated.

Usage:
  drive_ledger.py init --config <path>
  drive_ledger.py append --config <path> --doc <invariants|decisions|changes> --text <text>
  drive_ledger.py get-config-path

Notes:
- Stores doc ids back into the config json.
- Appends text to end of Google Doc.
"""

import argparse, json, os, shlex, subprocess, sys
from pathlib import Path


def run(cmd: str) -> str:
    p = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    return p.stdout.strip()


def jx(s: str):
    s = s.strip()
    i, j = s.find('{'), s.rfind('}')
    if i != -1 and j != -1 and j > i:
        s = s[i : j + 1]
    return json.loads(s)


def load_config(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_config(path: str, cfg: dict) -> None:
    Path(path).write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_doc_in_folder(folder_id: str, title: str) -> str | None:
    q = f"'{folder_id}' in parents and name = '{title}' and mimeType='application/vnd.google-apps.document' and trashed=false"
    params = json.dumps({"q": q, "pageSize": 5, "fields": "files(id,name)"})
    out = run("gws drive files list --params " + shlex.quote(params))
    files = jx(out).get("files", [])
    return files[0]["id"] if files else None


def create_doc(title: str) -> str:
    out = run("gws docs documents create --json " + shlex.quote(json.dumps({"title": title})))
    return jx(out)["documentId"]


def move_to_folder(file_id: str, folder_id: str) -> None:
    meta = jx(
        run(
            "gws drive files get --params "
            + shlex.quote(json.dumps({"fileId": file_id, "fields": "parents"}))
        )
    )
    parents = meta.get("parents", [])
    upd = {"fileId": file_id, "addParents": folder_id}
    if parents:
        upd["removeParents"] = ",".join(parents)
    run("gws drive files update --params " + shlex.quote(json.dumps(upd)) + " --json {}")


def append_text(document_id: str, text: str) -> None:
    doc = jx(run("gws docs documents get --params " + shlex.quote(json.dumps({"documentId": document_id}))))
    end = 1
    try:
        end = int(doc["body"]["content"][-1]["endIndex"])
    except Exception:
        end = 1

    # Append before final newline (Google Docs end index points after last element)
    insert_at = max(1, end - 1)
    req = [{"insertText": {"location": {"index": insert_at}, "text": text}}]
    run(
        "gws docs documents batchUpdate --params "
        + shlex.quote(json.dumps({"documentId": document_id}))
        + " --json "
        + shlex.quote(json.dumps({"requests": req}))
    )


def init_docs(cfg_path: str) -> dict:
    cfg = load_config(cfg_path)
    folder_id = cfg["shared_folder_id"]

    mapping = {
        "invariants_doc_id": cfg["doc_titles"]["invariants"],
        "decision_log_doc_id": cfg["doc_titles"]["decisions"],
        "change_log_doc_id": cfg["doc_titles"]["changes"],
    }

    for key, title in mapping.items():
        doc_id = cfg["docs"].get(key) or ""
        if doc_id:
            continue
        existing = find_doc_in_folder(folder_id, title)
        if existing:
            cfg["docs"][key] = existing
            continue
        new_id = create_doc(title)
        move_to_folder(new_id, folder_id)
        cfg["docs"][key] = new_id

    save_config(cfg_path, cfg)
    return cfg


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_init = sub.add_parser("init")
    ap_init.add_argument("--config", required=True)

    ap_app = sub.add_parser("append")
    ap_app.add_argument("--config", required=True)
    ap_app.add_argument("--doc", choices=["invariants", "decisions", "changes"], required=True)
    ap_app.add_argument("--text", required=True)

    sub.add_parser("get-config-path")

    args = ap.parse_args()

    if args.cmd == "get-config-path":
        # Default per-skill config location in workspace (not inside skill folder)
        print("/root/.openclaw/workspace-nero/config/longterm_memory_ledger.json")
        return

    if args.cmd == "init":
        cfg = init_docs(args.config)
        print(json.dumps(cfg["docs"], ensure_ascii=False))
        return

    if args.cmd == "append":
        cfg = init_docs(args.config)
        doc_map = {
            "invariants": cfg["docs"]["invariants_doc_id"],
            "decisions": cfg["docs"]["decision_log_doc_id"],
            "changes": cfg["docs"]["change_log_doc_id"],
        }
        doc_id = doc_map[args.doc]
        append_text(doc_id, args.text)
        print(doc_id)
        return


if __name__ == "__main__":
    main()
