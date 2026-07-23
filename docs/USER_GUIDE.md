# CodeMemory User Guide

> **最后更新**：2026-07-23
> 本文是日常使用入口。产品定义见 `docs/prd.md`，架构契约见 `docs/architecture.md`。

---

## 1. CodeMemory 是什么

CodeMemory 是一个给单 owner 和多个 agent 共享的工作记忆底座。

它的核心不是“搜索更多内容”，而是：

- 用 atom 保存长期可复用的事实、决策、约束、流程和上下文入口；
- 用 imports DAG 表达记忆之间的依赖；
- 用 canonical build 生成 ContextPack，把上下文稳定交给 agent；
- 用 Source Artifact / source_refs 追溯长文档和原始资料。

当前主线包括 atom graph、canonical build、proposal review、golden questions、显式三臂 eval harness、source-aware compiler、Source Artifact 显式展开、Personal Profile，以及本地 Operator UI。

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

- backend: `http://127.0.0.1:8000`
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

## 6. Build 与 ContextPack

`build` 是 canonical 装配入口，ContextPack 是其结构化产物。

```powershell
codememory build user/investment/context --format xml-markdown --budget 2000
codememory build user/investment/context --format json
```

它保留以下结构：

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

### 7.3 本地 semantic discovery（Personal Phase 2）

这是一条显式、可选的候选发现路径，不替代默认词法搜索，也不改变 canonical build。

先安装可选依赖，并把已下载好的 sentence-transformer 模型放在 Profile 实际 `private_local` 目录内：

```powershell
pip install -e ".[semantic]"

# profile.yaml 中显式设置 enabled/model_path/model_id 后
codememory --root D:\work\MyMemory semantic status
codememory --root D:\work\MyMemory semantic index
codememory --root D:\work\MyMemory search `
  --query "职业发展方向" `
  --semantic `
  --kind capture incubator_topic incubator_claim atom
```

CodeMemory 不下载模型，也不会切换到外部 embedding。索引在 ignored `private_local/semantic/index.json`，只保存 typed 候选所需的 ID/hash/vector/locator；raw query 不持久化。相同内容和模型的重复构建直接复用；正文或模型改变后查询会提示 stale，需重新执行 `semantic index`。

语义结果中的 Capture / Topic / Claim 仍走 `read`，Atom 仍走 `build`。命中相似对象不会自动读取正文、生成 imports、影响 maintenance，或向 ContextPack 注入节点。当前不提供 REST/Web semantic surface。

---

## 8. 常用 CLI

```powershell
# 创建 / 更新
codememory create --id user/project/new-fact --tags "project,fact" --propose
codememory update user/project/new-fact --change-note "Fill reviewed fact" --summary "..." --body "..."

# 装配 canonical context
codememory build user/project/context --budget 2000
codememory build user/project/context --format xml-markdown

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
codememory compile-md docs --review-id semantic-review --proposer llm --llm-config path\to\gateway.yaml --llm-model smart
codememory materialize-review docs-review --accept-all
```

完整命令列表：

```powershell
codememory --help
```

### 8.1 三臂 Eval Harness

带非空 `expect` 的 golden questions 可以通过显式 provider runner 做对照实验：

```powershell
codememory --root D:\memory\work eval user/project/context `
  --llm-config D:\config\llm_gateway.yaml `
  --answer-model smart `
  --judge-model smart `
  --depth recommended `
  --budget 2000 `
  --output D:\reports\context-eval.json
```

一次 run 冻结三个条件：

- `context_pack`：入口经过 imports DAG 与 budget 裁剪后的 canonical build；
- `full_memory`：所有可装配 Atom/Schema 的 summary + 正文，按 ID 排序；
- `no_memory`：不给模型任何记忆上下文。

答题模型三路完全相同且看不到 `expect`；judge 只看到问题、期望要点和候选答案，不知道答案来自哪一路。报告给出每路 pass rate、ContextPack 相对 full-memory 的质量保留/差值、两条 memory 路径相对 no-memory 的提升，以及 context/实际输入 token 差异。

这是显式外部调用。`context_pack` 会发送装配内容，`full_memory` 可能发送整个 canonical memory；运行前应确认这些内容适合交给该 provider。报告不保存 memory context、prompt、config 路径、credential、raw response 或 thinking，但会保留问题、expect、答案和判分理由供复核。默认输出 JSON 到 stdout；`--output` 不覆盖已有文件，除非同时明确 `--overwrite`。

没有 `expect` 的问题会被跳过；若一个可评分问题都没有，命令会在加载 provider 前失败。Web、MCP 和 Agent tools 都不会触发 eval。

---

## 9. Web UI

Web UI 是 operator console，不定义 canonical memory contract。

主要用途：

- Graph：查看 imports DAG；
- List：浏览和筛选 memories；
- Dashboard：运行 validate / reindex 等维护操作；
- Review：分开审阅 proposed Atoms 与 modification patches，确认后 merge / reject；
- Create / Edit：一次提交完整 summary、body、tags、maturity 与 imports；新建时可明确选择 proposed；
- Build / Copy Build：通过 Core 的 imports DAG 装配 canonical context，并直接复制同次 build 的 rendered output；
- Golden Questions：在详情面板只读查看题目、可选期望和 notices；Web 不运行模型或判分。
- Personal：只在 Personal dataset 中出现；浏览有效 Capture、Topic/Claim、显式 provenance timeline，并准备一次确认后的 promote / merge / delete 批次。

要把外部 Personal Profile 加入本地 Web，创建服务端 registry 并在启动前设置环境变量：

```yaml
instances:
  mymemory: D:\work\MyMemory
```

```powershell
$env:CODEMEMORY_INSTANCE_REGISTRY = "D:\config\codememory-instances.yaml"
python bin/codememory.py dev
```

浏览器请求只使用 `mymemory` 这个 alias；公开 dataset 响应不会返回 root。registry root 必须是已存在且 validation 通过的 Personal Profile，server 启动不会自动 reindex 它。Personal 页面也不提供 Capture 编辑、maintenance、Git、semantic index 或 registry 控制。

当前仍未进入 Operator UI 的能力：

- source_refs 展示；
- expand source；
- migration review。
- Personal Capture/Topic 正文编辑、maintenance/Git delivery、semantic discovery 管理。

---

## 10. Markdown 迁移

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

### 10.1 显式 LLM semantic proposer

需要语义提炼时，可以安装可选 provider 依赖并显式选择 LLM proposer：

```powershell
pip install -e ".[llm]"
codememory --root path\to\memory compile-md path\to\docs `
  --review-id semantic-review-1 `
  --proposer llm `
  --llm-config path\to\llm_gateway.yaml `
  --llm-model smart
```

该模式与确定性模式的边界不同：

- Source 正文会发送到你显式配置的模型；运行前应先确认文档适合交给该 provider 处理。
- CodeMemory 不会把 gateway 配置正文或路径放入 review，也不会为 proposer 开启 tools / Web。
- 模型只返回 typed semantic drafts。CodeMemory 自己生成 ID/path/status/source_refs，并丢弃未知 paragraph provenance 或未授权 import target。
- 同一 `review-id`、相同 source/options 会直接返回已有 review，不再次调用模型；输入或模型/config 变化必须使用新的 review ID。
- materialize 仍只生成 `status: proposed` atom；需要 owner 继续审阅并执行正常 `merge` 后才进入默认 search/build。
- semantic accepted batch 会先整体预检；source ref、路径、覆盖、import 解析或同批环任一失败时，一个文件也不会写入。

不带 `--proposer llm` 时仍走 v2A 确定性路径，不读取 LLM 配置、不加载 `llm_gateway`、不发起 provider/network 调用。

---

## 11. 判断一条信息怎么存

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

## 12. 相关文档

- `docs/prd.md` — 产品定义和优先级；
- `docs/architecture.md` — 架构契约；
- `docs/INTEGRATION.md` — CLI / API / MCP / harness 接入；
- `docs/project_structure.md` — 仓库文件职责；
- `docs/agent-memory-guide.md` — canonical Atom 的 Agent 贡献规范；
- `docs/reference/` — 历史探索和审计记录。
