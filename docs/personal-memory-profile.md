# Personal Memory Profile Contract

> **状态**：canonical / Phase 0 contract
> **最后更新**：2026-07-22
> **上游**：`docs/prd.md`、`docs/architecture.md`

本文定义 CodeMemory 的 Personal Profile 实例格式。它约束外部数据仓库（例如 `D:\work\MyMemory`），不允许 CodeMemory 程序仓库绑定或保存具体个人数据。

---

## 1. 设计目标与不变量

Personal Profile 服务一个 owner 和其授权的 Agent。目标是低摩擦 Capture、异步维护、集中孵化、少量 canonical memory。

必须始终成立：

1. Capture 成功返回前，原文已落盘；维护、Git、网络失败不影响 Capture。
2. Capture 对 Agent 是 append-only；Agent 不自动改写或删除。owner 可明确手动清理。
3. 每条 Capture 有稳定 ID 和独立内容 hash；引用不依赖行号。
4. Incubator Topic 有稳定 topic ID 和段落级 provenance。
5. Incubator 可长期未审阅、继续更新并参与检索；未审阅不阻塞维护。
6. Agent 从 Incubator 提升新的 Canonical Atom 默认需要 owner 确认。
7. Capture / Incubator 不进入 canonical build；只有 Atom 通过 imports DAG 装配。
8. maintenance run、敏感扫描、commit、push 可重试且幂等。
9. missed-run catch-up 必须处理所有尚未被成功 applied run 消费的 Capture。
10. 所有 owner 数据是普通 Markdown / Git 文件；`.codememory/` 只保存可检查的协议元数据、索引和操作状态。

---

## 2. 实例目录

```text
MyMemory/
├─ README.md
├─ .gitignore
├─ journal/
│  └─ 2026/
│     └─ 07/
│        └─ 2026-07-22.md
├─ incubator/
│  └─ 2026-07.md
├─ memory/
│  ├─ ideas/
│  ├─ work/
│  ├─ life/
│  └─ people/
├─ reviews/
├─ private-local/
└─ .codememory/
   ├─ profile.yaml
   ├─ index.json
   ├─ sources/
   │  └─ index.json
   ├─ maintenance/
   │  ├─ state.json
   │  ├─ runs.jsonl
   │  └─ pending/
   └─ log.md
```

目录语义：

| 路径 | 是否 canonical | 规则 |
|---|---:|---|
| `journal/` | 否 | 一天最多一个 Markdown；Capture block 只追加 |
| `incubator/` | 否 | 一月一个 Markdown；多个 Topic 以段落组织 |
| `memory/` | 是 | 一个 Atom 一个 Markdown；沿用 atom frontmatter / imports / build |
| `reviews/` | 否 | 只有 owner 明确要求持久化的周期回顾；临时查询默认不写文件 |
| `private-local/` | 否 | 必须默认 Git ignore；Core 和 Agent 不自动搬运内容进入或离开该目录 |
| `.codememory/` | 否 | profile、索引、维护状态、日志；不得混入 journal 正文 |

`archive/` 不作为 Phase 1 必需目录。Canonical Atom 使用既有 lifecycle/status 与 Git history；未来若引入 archive，必须先定义与 archived status 的唯一关系。

---

## 3. Profile Manifest

`.codememory/profile.yaml` 是实例能力声明，不保存秘密：

```yaml
format_version: 1
profile: personal
owner: owner
timezone: Asia/Hong_Kong

paths:
  journal: journal
  incubator: incubator
  canonical: memory
  reviews: reviews
  private_local: private-local

capture:
  append_only_for_agents: true
  hash: sha256

maintenance:
  auto_commit: false
  auto_push: false
  remote: origin
  branch: main
  sensitive_scan: required

discovery:
  lexical: true
  temporal: true
  tags: true
  semantic:
    enabled: false
    external_embeddings: false
```

规则：

- `external_embeddings` 默认且初始化时必须为 `false`；显式启用前不得向外部服务发送正文。
- `remote` 和 `branch` 是目标，不是凭据；认证留给 Git credential manager / SSH agent。
- `auto_commit` / `auto_push` 安全默认值均为 `false`。现有 Git 实例只能通过 init 参数或显式配置启用；`auto_push: true` 隐含要求 `auto_commit: true`。
- init 不隐式执行 `git init`、不创建 remote。普通目录、没有 remote 的 Git repo 与完整 Git repo 都是有效 Personal Profile。
- Git delivery 是可选能力：非 Git 目录报告 `unavailable:not_git_repo`；缺少目标 remote 报告 `unavailable:remote_missing`。这些诊断不得让 profile init 或 Capture 失败。
- validation 分开报告 `profile_valid` 与 `git_delivery`。显式启用但不可用时 delivery validation 非零/警告均可由 adapter 呈现，但 Capture 路径只依赖 `profile_valid`，不得被 delivery 状态阻塞。
- `init --profile personal` 必须创建或校验上述目录与 `.gitignore`，不得覆盖已有正文。
- `paths.private_local` 指向的实际目录（默认 `private-local/`）必须动态写入并校验根 `.gitignore`；若该实际路径已被 Git 跟踪，init / validate 必须报错而不是假装安全。
- `.codememory/capture.lock`、`.codememory/maintenance/state.json` 与 `.codememory/maintenance/pending/` 是本机可重建的 runtime/delivery 状态，也必须默认 Git ignore；`runs.jsonl` 和内容变更则进入每日 commit。

---

## 4. Capture 文件合同

### 4.1 Journal 文档

路径固定为 `journal/YYYY/MM/YYYY-MM-DD.md`。文件可以有日期标题；每次输入追加一个 Capture block：

```markdown
# 2026-07-22

## 21:05 — cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M
<!-- codememory:capture
id: cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M
captured_at: 2026-07-22T21:05:14+08:00
actor: owner
content_hash: sha256:52b0...
-->
我今天重新想清楚了个人记忆和项目决策之间的关系。
```

### 4.2 Capture ID 与 hash

- `id`：全实例唯一、不可复用、可按时间排序的稳定 ID；Phase 1 使用 ULID 表示并加 `cap_` 前缀。
- `content_hash`：只覆盖 owner 输入 payload，不覆盖标题或 metadata。
- hash 输入规范：将 CRLF / CR 规范为 LF，按 UTF-8 编码；不 trim、不做 Unicode 重写、不包含结构性尾随换行。
- Agent 分类、标签、摘要不得写回或改写 Capture block；它们属于生成索引或 Incubator provenance。
- owner 的纠正默认作为新 Capture，并通过 `corrects: <capture_id>` 建立关系；owner 仍可明确要求物理清理旧记录。

### 4.3 Capture 原子性

`capture` 必须：

1. 生成 ID、时间和内容 hash；
2. 在实例级 capture lock 下追加完整 block；
3. flush + fsync；
4. 释放 lock；
5. 返回 Capture ID。

返回前不得等待分类、reindex、maintenance、Git commit 或 push。若写入中断，下一次扫描必须忽略不完整 block 并由 validate 报告修复需求，不能把半段正文当成已消费 Capture。完整 block 的 payload 若与 `content_hash` 不匹配，同样必须报告并从 typed index、read 和未来 maintenance 输入中排除，直到 owner 修复。

---

## 5. Incubator Topic 文件合同

### 5.1 月度文档与段落

路径固定为 `incubator/YYYY-MM.md`。一个文件包含多个 Topic；不按想法数量创建文件。

```markdown
# 2026-07 Incubator

## 个人记忆与项目决策的连接
<!-- codememory:topic
topic_id: topic/personal-memory/project-decisions
revision_id: topic/personal-memory/project-decisions@2026-07
created_at: 2026-07-22T22:00:00+08:00
updated_at: 2026-07-22T22:00:00+08:00
created_by: agent:codex
last_edited_by: agent:codex
origin: agent_synthesis
owner_confirmed: false
content_hash: sha256:98af...
derived_from:
  - kind: capture
    id: cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M
    content_hash: sha256:52b0...
relations: []
-->

### 当前理解

……

### Agent 新联想

……

### Claim：项目决策需要引用个人记忆中的原始动机
<!-- codememory:claim
claim_id: claim/personal-memory/project-decisions/original-motivation
origin: agent_inference
claim_status: unassessed
confidence: 0.72
created_by: agent:codex
derived_from:
  - kind: capture
    id: cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M
    content_hash: sha256:52b0...
-->

这是 Agent 的独立推断，不是 owner 原话。
```

### 5.2 Topic 身份和演化

- `topic_id` 表示跨月稳定的逻辑主题；标题变化、段落移动或合并不得改变它。
- `revision_id` 标识主题在某个月度文档中的版本；跨月延续使用同一 `topic_id`、新的 `revision_id`，并通过 relation 指向上个 revision。
- Topic `content_hash` 覆盖该 Topic 的 Markdown body，排除标题和 `codememory:topic` metadata；换行规范与 Capture 相同。Canonical provenance 引用 Topic 时保存该 revision 当时的 content hash。
- Topic 级 `origin` 允许 `human_explicit / agent_synthesis / agent_inference / mixed`。当一个 Topic 同时含 owner 信息、Agent synthesis 与独立 inference 时必须为 `mixed`。
- `claim_status` 不属于整个 Topic。只有可单独判断真伪或支持度的具体主张才拥有 claim_status。
- 同一月内不得出现重复 `topic_id`；维护重复运行必须更新同一段落而不是再创建一段。
- 合并 Topic 时保留目标 `topic_id`，在 provenance 中记录 `merged_from`；源段落可以由 owner 批量审阅后删除，或标为已合并。
- 未审阅 Topic 不过期、不形成提醒积压指标，也不阻塞后续检索、关联和维护。

### 5.3 Claim block

- Agent 的独立推断必须写成 Topic 内部的 claim block，不拆成独立 Markdown 文件。
- `claim_id` 在实例内稳定且唯一；标题、位置或 claim_status 改变不生成新 ID。
- claim block 至少包含 `claim_id`、`origin: agent_inference`、`claim_status`、`created_by` 与 `derived_from`；可选 `confidence`。
- synthesis 正文不因包含多条来源而自动变成 claim；只有独立可反驳的主张才需要 claim block。
- Phase 1A 只要求 Topic parser 能完整保留/跳过嵌套 claim block而不误切 Topic；claim block 的独立索引、筛选和关系演化属于 Phase 1B。

### 5.4 自动写入边界

Agent 可以自动：

- 新建 Topic 段落；
- 向已有 Topic 增加来源、更新综合和关系；
- 合并语义重复的 Incubator Topic；
- 将推断标为 contested / refuted，而不删除其历史来源。

Agent 不可以自动：

- 改写或删除 Capture；
- 把 Topic 提升为 active Canonical Atom；
- 删除 owner-confirmed canonical 内容；
- 把 Incubator 文本写进 imports DAG。

---

## 6. Canonical Atom 合同

Canonical 文件存放于 `memory/`，继续遵守一个文件一个语义单元、显式 imports、按需 build。Personal Profile 增加以下 provenance 字段：

```yaml
type: atom
id: memory/ideas/personal-memory-project-decisions
summary: 个人记忆与项目决策需要通过可追溯关系连接
status: proposed
origin: agent_synthesis
claim_status: supported
created_by: agent:codex
last_edited_by: agent:codex
reviewed_by: null
owner_confirmed: false
derived_from:
  - kind: incubator_topic
    id: topic/personal-memory/project-decisions@2026-07
    content_hash: sha256:98af...
imports:
  required: []
```

提升规则：

1. Agent 自主判断“已成熟”只能生成 `status: proposed` 的 Atom。
2. owner 明确说“新建正式 idea”“提升这个主题”等等价指令时，本次指令视为确认；Atom 可直接为 `active`，并写入 `reviewed_by: owner`、`owner_confirmed: true` 和确认时间/来源。
3. 集中审阅支持批量 promote / merge / delete；整个批次只需一次 owner 明确确认。
4. 修改已有 Atom 正文或 imports、修改 protected Atom，继续走 proposal。
5. `status` 是生命周期；不得写 `status: refuted`。

---

## 7. Provenance 与认识状态

### 7.1 字段

| 字段 | 值 / 语义 |
|---|---|
| `created_by` | `owner` 或 `agent:<name>` |
| `last_edited_by` | 最后修改该衍生内容的主体 |
| `reviewed_by` | owner 确认者；未确认时为 null |
| `owner_confirmed` | 是否已得到提升或高风险变更确认 |
| `origin` | Topic 可为 `human_explicit` / `agent_synthesis` / `agent_inference` / `mixed`；Claim/Atom 使用前三类 |
| `derived_from` | 稳定对象 ID + 当时内容 hash；不得使用行号作为身份 |
| `relations` | `supports` / `contradicts` / `corrects` / `evolves_from` / `merged_from` / `related` |
| `confidence` | 仅 Agent synthesis / inference 可选；0..1，不替代来源 |
| `claim_status` | 具体 Claim 或单一主张型 Atom 的 `unassessed` / `supported` / `contested` / `refuted`；不属于整个 Topic |

### 7.2 生命周期、claim 与 freshness 分离

- `status`：对象是否 active / proposed / archived / superseded / draft。
- `claim_status`：具体 claim block 或单一主张型 Atom 当前得到怎样的认识支持。
- `freshness`：由 `derived_from.content_hash` 或 `source_refs` hash 比对计算出的 `fresh / stale / missing / unknown`，默认不持久化为真相。

来源变化可以使衍生内容 `freshness=stale`，但不能自动把它判成 refuted。新的反证可以把 `claim_status` 更新为 contested 或 refuted；原推断仍保留在 Git history 和 provenance 中。

---

## 8. 两条读取路径

### 8.1 Personal Discovery Path

```text
query + filters
  → 搜索 Capture / Incubator Topic / Canonical Atom 的候选入口
  → Capture / Topic：按稳定 ID 直接读取目标 block
  → Agent 主动扩展时间邻域、provenance 和显式 relations
  → 临时综合回答（默认不保存 report）
```

Phase 1 filters：时间范围、全文词法、标签、对象类型、topic/project/person、origin，以及 Atom 级 claim_status。claim block 独立过滤在 Phase 1B。

Phase 2 可增加本地 semantic discovery。外部 embeddings 必须显式启用；语义结果只改变候选排序，不产生 imports 边，也不直接进入 build。

### 8.2 Canonical Build Path

```text
search 找到 Canonical Atom
  → imports closure
  → topo order
  → budget trim
  → render canonical context
```

Capture / Topic 只能作为 provenance 被显式读取；build 不得自动内联其正文。

---

## 9. Maintenance Run 合同

### 9.1 权威状态与 tracked 边界

- `.codememory/maintenance/runs.jsonl`：受 Git 跟踪的 append-only 内容处理 ledger；每行是一个不可变 run event。它记录 `planned / applying / applied / scan_passed`，同一 run 的最新 event 决定其 tracked 状态。
- `.codememory/maintenance/state.json`：被 Git ignore 的本机 delivery/status cache，可从 journal + runs ledger + Git commit trailer + remote refs 重建。
- `.codememory/maintenance/pending/<run_id>.json`：被 Git ignore 的幂等 changeset，包含输入 Capture IDs/hashes、目标文件 before/after hashes 与操作列表；达到 pushed 或明确终止后可清理。

`committed` 的权威证据是包含 `CodeMemory-Run: <run_id>` trailer 的唯一 Git commit；`pushed` 的权威证据是目标 remote/branch 已包含该 commit。commit/push 后不得再为记录 delivery 状态而修改受跟踪文件，否则会形成无限“状态 commit”。

维护状态不得写入 journal 或 incubator 正文。

### 9.2 状态机

```text
planned → applying → applied → scanning → scan_passed → committed → pushed
              │          │          │          └→ push_failed ─┐
              │          │          └→ scan_blocked             │
              │          └→ commit_failed ──────────────────────┤
              └→ apply_failed                                   │
                                                                └→ retry
```

语义：

| 状态 | 含义 |
|---|---|
| `planned` | 已冻结输入 Capture IDs/hashes 和 changeset |
| `applying` | 正在幂等应用文件变更 |
| `applied` | 所有目标文件达到 after hash；输入 Capture 已消费 |
| `scanning` | 对待提交 diff 做敏感信息扫描 |
| `scan_passed` | tracked ledger 已记录扫描通过；下一步可创建唯一 commit |
| `scan_blocked` | 发现疑似敏感信息；保留本地内容，不 commit/push，等待 owner |
| `committed` | 由 commit trailer 证明唯一 Git commit 已存在；状态可由 Git 重建 |
| `pushed` | 由 remote ref 包含该 commit 证明；状态可由 Git 重建 |
| `*_failed` | 失败阶段和安全错误信息已记录；下次从该阶段重试 |

`scan_blocked` 采用单 run 安全模型：

1. Capture 始终允许继续 append；它使用独立 capture lock。
2. 同一实例不得创建新的 maintenance run，也不得执行任何新的 Git delivery；不允许叠加多个未提交 run。
3. owner 解决敏感项后恢复**同一个 run**，重新扫描并继续 commit/push，不重新生成 changeset或重复消费输入。
4. 阻塞期间新增 Capture 不加入被阻塞 run；该 run 完成后由下一次 missed-run catch-up 消费。
5. Automation 必须发送安全阻塞通知，但它不是普通 incubator/proposal 审核积压，不计入审核数量，也不周期性催促。

### 9.3 missed-run catch-up

未消费集合的权威算法：

```text
all_complete_capture_blocks
  minus capture IDs listed by runs whose state reached applied or later
  equals next run inputs
```

不得只看“昨天”“最后运行时间”或文件 mtime。电脑关机数日后，下次 run 必须一次处理全部未消费 Capture；可分批时也必须保持确定顺序和不重不漏。

每个实例同一时间只允许一个 active maintenance run。plan 在锁内冻结输入集合；plan 完成后新追加的 Capture 不加入当前 changeset，留给下一个 catch-up run。Capture 使用独立 append lock，因此 maintenance 不得长时间阻塞白天记录。

### 9.4 幂等规则

- changeset 以排序后的 `(capture_id, content_hash)` 集合派生稳定 input digest。
- 若相同 input digest 已达到 `applied`，不得再次生成 Topic 或再次消费 Capture。
- apply 比对 before/after hash：目标已是 after 时跳过；既不匹配 before 也不匹配 after 时进入 conflict，不盲写。
- Topic upsert 以 `topic_id + revision_id` 为键，不以标题或相似度结果作为唯一身份。
- commit 带 trailer `CodeMemory-Run: <run_id>`；若该 commit 已存在，不重复 commit。
- push 只推送已记录的 commit；失败后重试同一 commit，不重新 maintenance。
- commit 必须同时包含 journal、incubator/canonical 变更和该 run 的 tracked ledger events；push 成功后工作树必须保持干净。
- Automation 只能 stage Personal Profile 的受跟踪路径；绝不 stage ignored runtime state 或 `private-local/`。发现 profile 路径外的未知改动时应停止并报告，不能静默扩大 commit 范围。

---

## 10. Git 与敏感信息

只有显式启用 Git delivery 时，每日维护才在 applied 后自动 commit，并按配置推送。没有 Git repo 或 remote 时 Personal Profile 与 Capture 仍完整可用，delivery 只显示 unavailable。

提交前必须扫描 staged diff：

- 私钥块、常见 API token、凭据格式；
- password / secret / token 等疑似赋值；
- 高熵疑似密钥；
- 被配置为禁止提交的路径。

扫描输出只能包含 rule、path、Capture/Topic ID 和位置提示，不得回显完整秘密。命中后进入 `scan_blocked`；Capture 仍安全保留在本地，Agent 不自动删除、改写或搬入 `private-local/`。

安全声明必须出现在 MyMemory README / 使用文档中：

1. private GitHub 限制访问，但不等于正文加密或端到端加密；
2. 一旦原始记录进入 Git history，删除工作树文件不能保证历史对象、remote、副本或备份中的内容消失；
3. 需要真正不提交的内容应存入被忽略的 `private-local/`，且用户应避免先 Capture 到 journal 再移动；
4. push 失败只影响远程同步，不能回滚本地 Capture、maintenance changes 或 commit。

---

## 11. 文档增长约束

Phase 1 必须硬性执行：

1. 每个自然日最多一个 journal Markdown。
2. 每个自然月最多一个 incubator Markdown。
3. 每次 daily run 自动创建 Canonical Atom 的数量恒为 0。
4. 新候选优先检索现有 `topic_id` 并 upsert；标题变化不创建新 Topic。
5. 临时检索和周期综合默认只回答，不保存 report。
6. promotion 只发生于 owner 明确指令或集中审阅。
7. 合并保留 `merged_from`，refuted 保留来源，不靠复制文件保存历史。
8. importer / compile-md 的“按标题一段一 proposal”策略不得直接用于 daily maintenance。

---

## 12. 实例与程序边界

| 归属 | 内容 |
|---|---|
| CodeMemory repo | 协议、模型、Core、handlers、CLI、MCP/toolkit、Web、测试、Personal Skill 模板 |
| MyMemory repo | journal、incubator、canonical memory、reviews、profile、运行状态、Git history |

CodeMemory 升级不得写入固定的 `D:\work\MyMemory`；所有实例通过显式 `--root`、`CODEMEMORY_ROOT` 或服务端实例 registry 选择。Web 客户端只能传实例别名，不能把任意绝对路径放进请求 header；服务端将别名解析为预先允许的绝对 root。
