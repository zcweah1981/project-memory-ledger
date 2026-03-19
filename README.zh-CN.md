# Project Memory Ledger（OpenClaw Skill）

面向 AI/Agent 的工程项目总账：长效记忆 + 证据链（不变量/决策/变更）+ 回滚 + 可追溯。支持本地 Markdown 与 Google Drive 双写。

**关键词：** 项目总账、工程总账、变更记录、决策记录、不变量、可追溯、回滚、证据链、长效记忆、LLM/Agent 记忆、OpenClaw、Google Drive、Markdown

用于工程项目的“长效记忆 + 证据链 + 回滚”的低污染总账。

本 skill 维护三本总账（心智模型在 local/drive/both 下保持一致）：
- **Invariants（不变量）**：硬规则 / 稳定事实
- **Decisions（决策）**：取舍与原因
- **Changes（变更）**：改了什么 + 为什么 + 证据 + 影响 + 回滚

支持多种存储后端：
- **local**：只写本地 markdown（100% 可用）
- **drive**：写 Google Docs（需要 Drive 访问能力）
- **both**：本地 + Drive 双写

> v1 Drive 实现使用 `gws` CLI。Drive 不可用时请切换 `backend=local`。

---

## 文件结构

- skill 目录：`skills/project-memory-ledger/`
- 主脚本：`skills/project-memory-ledger/scripts/ledger.py`
- 模板：`skills/project-memory-ledger/references/ledger_templates.md`
- 默认配置模板：`skills/project-memory-ledger/references/default_config.json`

本地输出目录（默认）：
- `/root/.openclaw/workspace-nero/ledgers/`
  - `INVARIANTS.md`
  - `DECISIONS.md`
  - `CHANGES.md`
  - `PROJECTS.md`（立项注册时写入）

---

## 快速开始

### 1）创建配置文件

推荐路径：
- `/root/.openclaw/workspace-nero/config/project_memory_ledger.json`

最小配置（local-only）：
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

Drive/both 配置（增加 `shared_folder_id`）：
```json
{
  "language": "zh",
  "backend": "both",
  "default_project": "project-memory-ledger",
  "local_dir": "/root/.openclaw/workspace-nero/ledgers",
  "shared_folder_id": "<Shared/ 的 Drive folder id>",
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

### 2）初始化

```bash
python3 skills/project-memory-ledger/scripts/ledger.py init \
  --config /root/.openclaw/workspace-nero/config/project_memory_ledger.json
```

- `local`：创建本地三本总账文件
- `drive/both`：同时创建/绑定 Shared/ 下的三份 Google Docs

### 3）写入条目（append）

```bash
python3 skills/project-memory-ledger/scripts/ledger.py append \
  --config /root/.openclaw/workspace-nero/config/project_memory_ledger.json \
  --doc changes \
  --project "Keyword Engine" \
  --text "- **Interfaces**: hunter-system ↔ keyword-engine\n- **Change**: ...\n- **Why**: ...\n- **Evidence**: ...\n- **Rollback**: ...\n"
```

### 4）立项登记（可选）

```bash
python3 skills/project-memory-ledger/scripts/ledger.py register-project \
  --config /root/.openclaw/workspace-nero/config/project_memory_ledger.json \
  --name "My New Project" \
  --purpose "Why it exists + success criteria" \
  --interfaces "hunter-system ↔ keyword-engine" \
  --notes "optional"
```

---

## 约定

### Project 标记
Project 值大小写不敏感，写入前会归一化成 slug。

推荐取值：
- `hunter-system`
- `keyword-engine`
- `common`（跨项目通用规则/方法论，但不进 AGENTS/MEMORY）

禁用 `shared`。跨项目勾稽统一用显式字段：
- `Interfaces: A ↔ B`

### 默认 Project
如果不传 `--project`，脚本会注入：
- `Project: project-memory-ledger`

用于记录“对本 skill 本身的需求/bug/改动”。

---

## Drive backend options（说明）
Drive 模式是可插拔 backend：
- Option 1（默认 / v1 已实现）：`gws` CLI（安装并完成认证）
- Option 2：Google API / service account（适合服务器/CI）
- Option 3：第三方 Drive 工具（用户自选）

Drive 不可用时，使用 `backend=local` 不阻塞。
