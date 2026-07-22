# CodeMemory User Guide

> **最后更新**：2026-05-19
> 本文是日常使用入口。产品定义见 `docs/prd.md`，架构契约见 `docs/architecture.md`。

> **术语提示（2026-06-10）**：本文成文于 memory-as-code 重建之前，概念叙述
> （Source Artifact / ContextPack / disclosure 等）以新版 `docs/prd.md` 与
> `docs/architecture.md` 为准（对照表见 prd 附录 A）。文中的 CLI 命令与当前实现
> 一致、仍可照用；全文随收敛阶段完成后统一更新。

---

## 1. CodeMemory 是什么

CodeMemory 是一个给单 owner 和多个 agent 共享的工作记忆底座。

它的核心不是“搜索更多内容”，而是：

- 用 atom 保存长期可复用的事实、决策、约束、流程和上下文入口；
- 用 imports DAG 表达记忆之间的依赖；
- 用 ContextPack 把上下文稳定交给 agent；
- 用 Source Artifact / source_refs 追溯长文档和原始资料。

当前已实现的主线是 atom graph、resolve、ContextPack、compiler review flow，以及 Source Artifact Registry / source_refs / explicit source expansion 基础能力。

---

## 2. 快速启动

```powershell
cd D:\work\CodeMemory
.\start.ps1
```

或：

```powershell
python bin/codememory.py dev
```

默认启动：

- backend: `http://127.0.0.1:8765`
- frontend: `http://127.0.0.1:5300`

---

## 3. 基础记忆格式

每条 canonical memory 是一个 Markdown 文件：

```yaml
---
type: atom
id: user/project/context
summary: Project context entrypoint
tags: [project, context]
status: active
imports:
  required: []
  recommended: []
  related: []
---

# Memory body

长期有用、可独立引用的工作记忆正文。
```

目前稳定类型：

| 类型 | 用途 |
|---|---|
| `atom` | 通用语义记忆：事实、决策、约束、流程、上下文入口 |
| `schema` | 结构模板，不是业务记忆本体 |

`source_refs` 已经可以作为 atom metadata，用于引用 Source Artifact。

---

## 4. Imports DAG

`imports` 表示 atom 与 atom 之间的理解依赖。

```yaml
imports:
  required:
    - user/project/core-constraint
  recommended:
    - user/project/design-decision
  related:
    - user/project/old-note
```

| 强度 | 含义 |
|---|---|
| `required` | 缺少它会误解当前记忆 |
| `recommended` | 有助于理解，但不是硬前提 |
| `related` | 主题相关，用于探索或补充 |

注意：`imports` 不是 source provenance。长文档来源应走 Source Artifact / source_refs，而不是塞进 imports。

示例：

```yaml
source_refs:
  - artifact_id: src/design-md
    summary: Design source
    disclosure_hint: anchor
```

---

## 5. Source Artifact Registry

Source Artifact Registry 保存长文档、代码文件、PDF、URL 等原始材料的引用和 hash。它不把原文变成 atom。

当前 registry 存储位置：

```text
.codememory/sources/index.json
```

基础命令：

```powershell
codememory source add docs/design.md --id src/design-md --kind markdown --summary "Design source"
codememory source list
codememory source get src/design-md
codememory source check src/design-md
codememory source expand src/design-md --max-chars 2000
codememory validate
```

字段：

| 字段 | 说明 |
|---|---|
| `id` | 稳定 Source Artifact ID，例如 `src/design-md` |
| `kind` | `markdown` / `code` / `text` / `pdf` / `url` / `external` |
| `uri` | 本地相对路径、绝对路径或外部 URI |
| `sha256` | 本地文件内容 hash |
| `summary` | 简短说明 |
| `status` | `active` / `archived` / `missing` / `stale` |

`source check` 和 `validate` 可以发现本地 source 文件 missing / stale。`validate` 也会检查 atom 的 `source_refs` 是否指向已登记的 Source Artifact。

`source expand` 是显式展开 source body 的入口，默认返回 JSON。它支持本地 `markdown` / `text` / `code` source：

```powershell
codememory source expand src/design-md
codememory source expand src/design-md --start 120 --end 360
codememory source expand src/design-md --max-chars 1200
```

返回结果包含 artifact id、kind、uri/path、registry hash、current hash、status、content、range 和 message。missing / stale / unsupported 都会以结构化 status 返回，而不是让 adapter 猜错误类型。

---

## 6. ContextPack

ContextPack 是给 agent 的主要上下文交接格式。

```powershell
codememory context-pack user/investment/context --format xml-markdown --budget 2000
codememory context-pack user/investment/context --format json
```

它比普通 resolve 更适合 agent，因为它保留结构：

- target；
- nodes；
- summaries；
- body；
- dependency order；
- budget notices；
- render format。

ContextPack 会渲染 memory node 的 `source_refs`，但不会自动展开 source body。需要原文时，使用 `source expand` 显式进入下一层 disclosure：

```text
L0 index card
L1 atom / anchor
L2 focused source excerpt
L3 full source artifact
```

默认应该停在 L1，不自动展开长文档全文。

---

## 7. Personal Profile（Phase 1A + 1B）

Personal Profile 可以初始化在普通目录、没有 remote 的 Git repo 或完整 Git repo 中。Git delivery 默认关闭；缺少 Git/remote 只显示为 `unavailable`，不会让 init 或 Capture 失败。

```powershell
# 初始化；不会隐式 git init，也不会创建 remote
codememory init D:\memory\MyMemory --profile personal

# Capture 可从参数或 stdin 输入，返回稳定 cap_<ULID>、SHA-256 和文件位置
codememory --root D:\memory\MyMemory capture "今天重新确认了 canonical 边界"
Get-Content note.md | codememory --root D:\memory\MyMemory capture --stdin

# Capture 不等待 reindex；需要检索时显式重建索引
codememory --root D:\memory\MyMemory reindex
codememory --root D:\memory\MyMemory search --kind capture incubator_topic atom --query "canonical"
codememory --root D:\memory\MyMemory read cap_01...
```

读取边界固定为：Capture / Incubator Topic / inline Claim 使用 `read`；Canonical Atom 使用 `build`。对前三者执行 `build` 会明确拒绝。Topic 内的 `codememory:claim` block 不拆文件；Phase 1B 将它作为 `incubator_claim` typed object 按稳定 `claim_id` 索引、读取和按 claim_status 过滤。

安全边界：`private-local/` 和本机 runtime 状态默认忽略；private GitHub 不等于加密存储，原始记录一旦进入 Git 历史，即使从工作区删除也可能仍然存在。

### 7.1 日常维护

```powershell
# 查看 active run 和所有未消费的完整 Capture
codememory --root D:\work\MyMemory maintenance status

# 由 Personal Memory Skill 生成 changeset 后执行
codememory --root D:\work\MyMemory maintenance run --changeset changeset.json

# 进程中断或 owner 修复敏感扫描问题后，恢复同一 run
codememory --root D:\work\MyMemory maintenance resume

# 集中处理 promote / merge / delete
codememory --root D:\work\MyMemory review-batch --file decisions.json
```

`maintenance run` 必须接收 Personal Memory Skill 生成的 changeset；Core 不会按标题替 Agent 猜测主题。它会按时间和稳定 ID 消费全部未处理且 hash-valid 的 Capture，因此电脑关机或漏跑某日任务后不需要补造日期任务。相同输入返回已有 applied run；pending changeset 保存目标文件 before/after hash，进程中断后不会重新生成 Topic。

仓库内 `.agents/skills/personal-memory/SKILL.md` 定义语义工作流：纯记录不追问；只有 owner 明确要求继续提问，或关键歧义阻塞结果时才进入访谈。Topic 可以长期留在 incubator；日常更新不产生逐条审核任务。

### 7.2 Git delivery 与安全阻塞

`auto_commit` / `auto_push` 默认都是 `false`，只通过 Profile 显式启用。delivery 只暂存 Profile 声明的 journal、incubator、canonical、reviews 和 tracked ledger；未知目录改动会阻塞自动提交，`private_local`、index、pending、state 和 lock 永不暂存。

提交前扫描 staged diff。命中时进入单一 `scan_blocked` run，只返回 rule、path 和 locator，不回显匹配值，也不 commit/push。Capture 仍可追加；owner 清理后执行 `maintenance resume` 恢复同一 run，阻塞期新增 Capture 在下一 run 自动 catch up。每个 delivery commit 恰有一个 `CodeMemory-Run: <run_id>` trailer；push 失败重试同一个 commit。

Automation 每次只调用以下流程：`maintenance status` → 用 Skill 读取候选并生成 changeset → `maintenance run`；若存在 active run 则改为 `maintenance resume`。成功通知只包含 run ID、消费数量、Topic 变更数量和 commit/push 状态；失败通知包含 stage 与可执行修复；`scan_blocked` 使用安全通知，不计入普通审核积压。

Phase 1B 仍不包含 Web 或 semantic discovery，external embeddings 保持关闭。

---

## 8. 常用 CLI

```powershell
# 创建 / 更新
codememory create --id user/project/new-fact --summary "..."
codememory update user/project/new-fact --body "..."

# 解析上下文
codememory resolve user/project/context --budget 2000
codememory context-pack user/project/context --format xml-markdown

# Source Artifact Registry
codememory source add docs/design.md --id src/design-md --kind markdown --summary "Design source"
codememory source list
codememory source check
codememory source expand src/design-md --max-chars 2000

# 搜索 / 验证 / 重建索引
codememory search --query "architecture"
codememory validate
codememory reindex

# 依赖建议
codememory suggest-deps user/project/context

# Markdown 迁移 review flow
codememory compile-md docs --review-id docs-review
codememory materialize-review docs-review --accept-all
```

完整命令列表：

```powershell
codememory --help
```

---

## 9. Web UI

Web UI 是 operator console，不定义 canonical memory contract。

主要用途：

- Graph：查看 imports DAG；
- List：浏览和筛选 memories；
- Dashboard：运行 validate / reindex 等维护操作；
- Create / Edit：维护 atom；
- Resolve / Copy Context：把上下文交给 agent。

下一阶段 UI 应跟随后端契约增加：

- ContextPack 面板；
- source_refs 展示；
- expand source；
- migration review。

---

## 9. Markdown 迁移

当前已有 compiler review flow：

```powershell
codememory compile-md path\to\docs --review-id docs-review
codememory materialize-review docs-review --accept-all
codememory validate
```

当前 deterministic compiler 已实现 source-aware proposal / review / materialize 链路：

```text
Markdown corpus
  ↓
Source Artifacts
  ↓
Anchor Atom proposals
  ↓
Derived Atom proposals
  ↓
review set
  ↓
selected status: proposed atom files
  ↓ owner merge
canonical graph
```

迁移原则：

1. 原文不被静默改写；
2. 每份文档只有一个稳定 Source Artifact 和一个轻量 anchor；每个非空段落是 derived candidate；
3. review 只选择要落盘的候选，materialize 后仍是 `status: proposed`；
4. owner merge 后才进入 canonical memory；
5. 每条候选通过 `source_refs` 追溯到 artifact 和行范围；
6. 确定性路径不生成 imports，也不调用 LLM。

重复使用同一 `review-id` 编译相同输入会保留已有 decisions，且不会重写未变化的 registry / review 文件。若输入、tags 或 namespace 已变化，应使用新的 review ID；旧 ID 会安全拒绝覆盖。

---

## 10. 判断一条信息怎么存

| 信息类型 | 存法 |
|---|---|
| 长文档、会议记录、设计稿 | Source Artifact；再建 Anchor Atom |
| 单个长期事实 | Atom |
| 架构/产品决策 | Atom，可挂 schema |
| 操作流程 | Atom，必要时拆成流程入口 + 步骤 atoms |
| 旧文档中的多个结论 | Source Artifact + 多个 Derived Atom proposals |
| 只是临时聊天上下文 | 不一定进入 canonical memory |

核心规则：

> 能独立复用的语义进入 atom；原始材料进入 Source Artifact；二者通过 source_refs 连接。

---

## 11. 相关文档

- `docs/prd.md` — 产品定义和优先级；
- `docs/architecture.md` — 架构契约；
- `docs/INTEGRATION.md` — CLI / API / MCP / harness 接入；
- `docs/project_structure.md` — 仓库文件职责；
- `docs/agent-memory-guide.md` — Work Layer agent 写入规则草案；
- `docs/reference/` — 历史探索和审计记录。
