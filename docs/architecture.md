# CodeMemory Architecture

> **Architecture thesis**
> 三层结构：**Adapters 接入，Core 实现机制，Importer 负责迁移**。
> Core 实现 PRD 的 11 个 canonical 概念和确定性的 Personal Profile 机制；agent 不在系统内——agent 是运行时，经 adapter 调用系统。
> 本文档是契约级参考：字段表、状态机、管线分解、收敛路径是后续 sprint 的直接依据，sprint 不再做架构决策。
> 冲突裁决顺序：`docs/prd.md`（概念）> 本文档（结构与契约）> 代码现状。

**最后更新**：2026-07-23
**状态**：canonical / 契约级
**上游**：`docs/prd.md`（memory-as-code + Personal Profile）、`docs/personal-memory-profile.md`（实例文件合同）；设计依据 `docs/superpowers/specs/2026-06-10-architecture-rebuild-design.md`

---

## 1. 总体分层

```text
┌──────────────────────────────────────────────────┐
│                    Adapters                       │
│  cli.py / tools.py / mcp_server.py /              │
│  integrations.py / evaluation/ / backend / UI     │
│  只做参数解析与传输格式，零业务逻辑                  │
├──────────────────────────────────────────────────┤
│                 Core（机制层）                     │
│  表示：models.py  core.py  index.py               │
│  操作：build  search  check  test(仅契约)          │
│  变更：create  update  merge  log  changelog      │
│  Profile：capture  personal_index  maintenance    │
│  资产：sources.py    维护：orphans suggest_deps    │
├──────────────────────────────────────────────────┤
│               Importer（迁移层）                   │
│  import_cmd / skeletonize/ / compiler/            │
│  产出一律是 proposal，经 review 晋升               │
└──────────────────────────────────────────────────┘
```

旧体系的 Layer Profiles 层仍保持删除：Personal Profile 是**实例文件与操作纪律**，不是召回概率、性格或“什么值得记”的算法层。语义判断属于 Codex Skill；Core 只实现可验证机制。

### 1.1 Adapters（接入层）

- 成员：`cli.py`、`tools.py`、`mcp_server.py`、`integrations.py`、`evaluation/`（显式 eval runner）、`backend/`（REST）、`frontend/`（Operator UI）。
- 职责：参数解析、传输格式、呈现，以及显式外部 runner 的调用编排与安全报告。
- 禁区：不得私自实现 canonical 装配、过滤或排序；不得扩展记忆语义。eval runner 可以组合既有 build/test 契约与 provider client，但不能改变任何 Atom、index 或 imports 规则。

### 1.2 Core（机制层）

- 表示：`models.py`（Pydantic v2 契约）、`core.py`（frontmatter 解析 / hash / root 解析）、`index.py`。
- 操作：build（装配）、search（入口检索）、check（校验，CLI 名 `validate`）、test（仅契约，零 LLM 依赖）。
- 变更：`create.py`、`update.py`（含 merge/reject 操作）、`log.py`、`changelog.py`。
- 资产：`sources.py`。维护：`orphans.py`、`suggest_deps.py`、`diff.py`。
- Personal Profile 目标模块：`profile.py`（manifest）、`capture.py`（原子追加）、`personal_index.py`（Capture / Topic 索引）、`maintenance.py`（changeset 与 run 状态）。
- **`handlers.py` 是 Core 的唯一门面**，所有 adapter 经它调用。
- 禁区：不依赖任何 LLM provider；不依赖 harnesslib / llm_gateway；不决定"什么值得记"。

### 1.3 Importer（迁移层）

- 成员：`import_cmd.py`、`skeletonize/`、`compiler/`。
- 职责：外部材料 → asset 登记 + atom proposals。
- 铁律：产出一律是 proposal，经 review 晋升；LLM 只 propose，不写 canonical truth；原始材料默认保留。

Markdown compiler 的阶段边界：

1. ingest 只读扫描原文，以 resolved URI 生成不随正文变化的 artifact ID，并记录当前 hash；
2. compiler 幂等 upsert Source Artifact，随后为每份文档生成一个 anchor、为每个非空段落生成一个 derived candidate；
3. anchor / derived 都携带 `source_refs`；derived 另带 paragraph ID、hash 与精确行范围；
4. review 的 accept/reject 只决定是否 materialize，写出的 atom 仍为 `status: proposed`；只有 owner merge 后才进入 canonical graph；
5. 确定性路径不生成 imports，保持默认且不加载任何 provider；显式 `--proposer llm` 路径以 paragraph ID + body 和有界 existing-Atom inventory 请求 typed structured output；
6. provider-neutral 的 prompt / provenance / stable-ID 逻辑位于 `compiler/llm_proposer.py`；`compiler/gateway_adapter.py` 只在显式 LLM 路径惰性加载 `llm_gateway` 和 provider SDK；
7. CodeMemory 丢弃未知 provenance、未知 imports target 与 model 控制的 path/status/frontmatter。semantic review materialize 前对整个 accepted batch 做 source refs、路径、覆盖、imports 可解析性与同批环检测，任一错误即零写入；
8. review 记录安全的 prompt version、requested/response model、provider 与 token usage，不保存 config 路径/正文、credential、raw thinking 或 prompt source text。

### 1.4 agent 在哪里

agent 不是系统组件。agent 是消费 build 产物、按写入纪律提交变更的运行时，永远经 adapter（CLI bash 命令 / MCP / toolkit）调用系统，不 import codememory、不直接读写记忆库的 .md 文件。

### 1.5 Personal Profile 的四方职责

| 责任方 | 负责 | 不负责 |
|---|---|---|
| **Core** | profile 校验、Capture 原子追加、稳定 ID/hash、对象解析与索引、词法/时间/标签过滤、provenance 校验、幂等 changeset、maintenance 状态、敏感扫描结果合同 | 内容分类、追问、聚类判断、生成综合、调用 embedding、Git 网络操作 |
| **Codex Skill** | 判断是否只记录或追问、主动阅读历史、聚类/upsert Topic、综合与推断、生成带 provenance 的 changeset、形成临时回答 | 直接绕过 Core 改 journal、无确认提升 canonical、commit/push |
| **Automation** | 定时唤醒、missed-run 启动、调用 Skill、驱动 scan/commit/push、按 run 状态重试、发送摘要通知 | 改写内容语义、把失败当作 Capture 失败、重新生成已 applied 的 changeset |
| **MyMemory 实例** | owner 数据、profile、journal、incubator、canonical atoms、运行 ledger；可选 Git history/remote 目标 | CodeMemory 程序实现、跨实例全局状态、凭据 |

Git credential、GitHub 访问控制和通知通道属于运行环境，不写入 profile 或仓库正文。

---

## 2. 概念 → 模块映射（目标态）

| 概念 | 目标模块 | 现状 → 目标动作 | 阶段 |
|---|---|---|---|
| repo | `core.py` + `index.py` + `.codememory/` | 不变 | — |
| atom / schema | `models.py` + `create.py` / `update.py` | 已完成：4 个 heat 字段移除（第 3.1 节） | C ✅ |
| imports + build | **`build.py`** | 已完成：build.py 为唯一管线（两遍式裁剪）；resolve.py 为薄别名，context_pack.py shim 已删除（阶段 C） | B ✅ / C ✅ |
| asset | `sources.py` | 已完成：`update --source-ref` 写入路径 | A ✅ |
| check | `validate.py` | 已完成：proposed/queue 校验、golden_questions 格式校验 | A ✅ / C ✅ |
| search | `search.py` | 已完成：词法排序（字段加权 + OR 语义），零新依赖 | B ✅ |
| test | **`test_contract.py`** + `evaluation/` | 题集导出/report + 三臂显式 provider eval 已完成，Core 仍零 LLM | C ✅ / Eval ✅ |
| proposal | `models.py`（status）+ `proposals.py`（patch 队列）+ `update.py`（merge/reject 分发） | 已完成（修改类落为独立小模块 `proposals.py`，复用 update 应用 patch） | A ✅ / C ✅ |
| log | `log.py` / `changelog.py` | 不变 | — |
| importer | `compiler/` + `sources.py` | v2A：确定性 asset + anchor + paragraph-derived；v2B：显式可选 semantic proposer + imports 建议，仍只产 proposed | Importer v2A / v2B ✅ |
| Personal Profile | `profile.py` / `capture.py` / `personal_index.py` / `maintenance.py` / `promotion.py` / `git_delivery.py` | 1A / 1B 已完成并经 owner 接受 | 1A / 1B ✅ |

### 2.1 保留与定位说明

- `snapshot.py` / `transient.py`：保留，定位为 REPL 草稿辅助工具（会话级推理链与持久化），不属于 11 概念。
- `compiler/` 的 review/materialize 机制：保留；review acceptance 与 canonical merge 是两个门，materialize 只写 proposed atom。

### 2.2 删除清单（阶段 C 已执行，汇总见附录）

- `handle_focus` / `handle_overview` / `handle_wander` 及其 cli / tools / mcp 绑定（约 300 行）；
- `core.py` 的 `compute_retrieval_probability`（召回概率公式，专为 wander/overview 服务）；
- `models.py` 字段：`intensity`、`stability`、`stability_source`、`days_since_last_access`。

---

## 3. 数据契约

### 3.1 atom frontmatter（目标态权威字段表）

| 字段 | 判决 | 理由 / 现状注记 |
|---|---|---|
| type / id / summary / tags / path / version / created / updated | 保留 | 接口核心 |
| status | 保留，枚举扩为 `active / proposed / archived / superseded / draft` | proposal 载体（阶段 A 落地） |
| imports | 保留（required / recommended / related） | 理解性依赖 |
| schema | 保留 | 结构契约引用 |
| summary_hash | 保留 | stale 检测（基于 body hash，frontmatter 修改不触发） |
| source_refs | 保留 | asset 引用，不进依赖图；CLI 写入：`update --source-ref`（阶段 A 落地） |
| protected | 保留，**语义重定义**：仅 owner 手动设置（直接编辑 frontmatter），"动它必须走 proposal" | 阶段 A 解耦、阶段 C 移除 intensity 本体 |
| **golden_questions** | **已新增**（可选 list，入口 atom 用） | test 契约（阶段 C 落地） |
| access_count / last_access | 保留 | 维护循环 telemetry（orphans / diff 使用） |
| cache_stable / lifecycle | 保留 | build 内部优化提示；`ephemeral` 自动归档已实现 |
| maturity / evidence | 保留为**惰性元数据**：不参与 build / search / check 的任何机制 | 审计有用，不进概念层 |
| change_note / change_log | 保留 | log 的原料 |
| **intensity** | **已删除**（阶段 C 完成；deprecated 别名仅存于 skeletonize 的 --min-intensity 与 @intensity） | 重要性 = 被依赖数 |
| **stability / stability_source / days_since_last_access** | **已删除**（阶段 C 完成，连同 decay 公式） | 专为已砍的拟人召回服务 |

### 3.2 status 状态机与过滤语义

```text
create ──────────────▶ active ──update──▶ archived / superseded
create --propose ────▶ proposed ──merge──▶ active
                            └────reject──▶ archived
（draft：owner 手工标记的未完成内容，不属于 proposal 流程）
```

| status | build 装配 | search 默认返回 | check |
|---|---|---|---|
| active | ✓ | ✓ | 常规校验 |
| draft | ✓ | ✓ | 常规校验 |
| proposed | ✗（closure 跳过 + notice） | ✗（`--status proposed` 显式可见） | 积压提醒（超 14 天）；"被 active atom import"警告 |
| archived / superseded | ✗（closure 跳过 + notice） | ✗（显式 status 过滤可见） | "被 active atom import"警告 |

### 3.3 proposal：一个概念，两种载体

**新增类（阶段 A）**：一个 `status: proposed` 的普通 .md 文件，owner 直接可读。

- 创建：`codememory create --propose ...`——agent 对内容没把握、或内容涉及 protected 邻域时选用；importer 产出默认 proposed。
- `merge <id>`：status → active + log；`reject <id>`：status → archived + log。

**修改类（阶段 C 已落地）**：同一个 .md 不能同时存两个版本，变更落为 `.codememory/proposals/<seq>-<target-id>.json` patch 记录（target_id、字段新值、reason、created_by、created_at）。

- 入队：`codememory propose <id> --reason "..."`（字段级 patch，目标 atom 不被触碰）；`proposals` 查看队列；
- `merge <proposal_id>`：经 update 应用 patch（version++ + change_log）+ 清队列；`reject <proposal_id>`：丢弃记录 + log；
- merge / reject 统一分发：先查 patch 队列，再走新增类（proposed atom）路径。

### 3.4 golden_questions 契约

```yaml
golden_questions:
  - q: "缓存层用什么失效策略，为什么？"
    expect: "写穿透 + 5min TTL；因为读写比 9:1"   # 期望要点，判分参考，可选
```

- `codememory test <entry>`：输出 `{ format_version, entry, context: <build 产物>, questions: [...] }` 结构化 JSON，由 agent / CI 答题判分；题集为空时退出码 0 + notice（无题不是错误）。
- `codememory test report <entry> --results <file>`：校验 `{q, answer, pass}` 格式后写回 log。
- Core 全程零 LLM 依赖——代码类比：pytest 独立于编译器。`test` 的 runner 可以是外部 agent/CI；内置 `eval` 也只在显式 Adapter 路径调用 provider。

#### 3.4.1 三臂 eval harness

Eval harness 属于显式接入层，不属于 canonical build Core。`test_contract.py` 继续只负责题集和 ContextPack；`evaluation/` 负责冻结实验输入、调用可选 provider adapter、盲判和生成报告。

**冻结输入：**

| arm | context 定义 |
|---|---|
| `context_pack` | `build_context_pack(..., track_access=False)` 的同次 canonical XML-Markdown render |
| `full_memory` | index 中所有 status 不属于 `proposed / archived / superseded` 的 Atom/Schema；每项只渲染稳定 ID、summary、authored body，按 ID 排序 |
| `no_memory` | 空字符串 |

`full_memory` 不读取 Source Artifact body、Capture、Incubator、`.codememory/` runtime 文件，也不复制原始 frontmatter。特别是 `golden_questions` 与 `expect` 不得进入 answer context。索引中的每个 path 在读取前必须 resolve 并验证仍位于 bound root 内。

三条 context 在第一次 provider call 前同时生成并计算 SHA-256。full-memory dataset digest 覆盖每个 included ID、summary 和 body；相同输入的顺序和 digest 必须稳定，任一 included summary/body 变化都会改变 digest。

**答题与盲判：**

1. 只选择 `expect` 为非空字符串的问题；缺失 expect 的问题保留为 skipped notice，若没有可评分问题则在 client 构造/provider call 前失败；
2. 每个 `arm × question` 是独立 answer call，使用同一 requested answer model、system prompt、temperature 0 和 token 上限；answer prompt 只有 question + 当前 arm context；
3. judge call 使用固定 requested judge model，只接收 question + expect + candidate answer，不接收 arm、context 或其他 verdict；
4. answer/judge 都请求 typed structured output，不启用 tools/Web，不保留 raw response/thinking；
5. 单次失败只记录 `phase + exception type` 并继续。eligible denominator 不变，失败保守地不计 passed。

**报告 `memory-eval/v1`：**

- run/entry/settings、dataset/context hashes、context chars/estimated tokens；
- safe requested/response provider-model metadata、usage、latency；
- question/expect/answer、judge pass 与短 reason；
- 每 arm eligible/judged/passed/errors/pass rate；
- ContextPack-vs-full pass delta/retention、两条 memory arm 对 no-memory uplift、context 与 answer-input token savings。

报告禁止写入 root/config 绝对路径、context、prompt、credentials、raw provider payload 或 raw thinking。默认 stdout；显式 `--output` 才在最终完成后 atomic write，已有路径须 `--overwrite`，且不会隐式写入 memory root。首版只开放 trusted owner/CI CLI 与 Python handler；REST/UI、MCP/Toolkit/Agent tool、调度与远端存储均不开放。

`evaluation/gateway_adapter.py` 只能在显式 eval handler 内惰性 import `llm_gateway`。普通 `import codememory`、test export、build、search、Agent catalog 和 Web read-only golden-question endpoint 不得加载 provider dependency。

### 3.5 asset 契约（沿用现实现）

```yaml
id: src/rfc-001-cache
kind: markdown                  # markdown | code | text | pdf | url | external
uri: docs/rfc-001.md
sha256: "..."
summary: "RFC-001: 缓存层设计"
status: active                  # active | archived | missing | stale
```

- 存储：`.codememory/sources/index.json`（实现类 `SourceArtifact` / `SourceRegistry`，CLI 命令组现名 `source`）；原始文件留在原路径。
- 展开：`expand_source(artifact_id, start, end, max_chars)` → 结构化 `SourceExpansion`（含 hash 比对、stale/missing 状态、截断标记）。
- 引用边界（与 imports 的分界是本架构最重要的不变量之一）：

| 关系 | 含义 | 进 imports DAG |
|---|---|---|
| imports.required / recommended | 理解性依赖 | 是 |
| imports.related | 弱关联 | depth=full 时 |
| source_refs（asset 引用） | 出处 / 可展开原文 | **否** |

### 3.6 Personal Profile 对象边界

权威文件合同见 `docs/personal-memory-profile.md`。Core 必须把三类对象作为判别联合处理：

| kind | 身份 | 可变性 | 默认读取动作 | 进入 build |
|---|---|---|---|---:|
| `capture` | `capture.id` | Agent append-only | `read_object(id)` | 否 |
| `incubator_topic` | `topic_id + revision_id` | Agent 可 upsert / merge | `read_object(revision_id)` | 否 |
| `atom` | frontmatter `id` | 受 proposal 纪律约束 | `build(id)` | 是 |

索引结果必须返回 `kind` 和 `read_action`；调用方不能仅凭路径猜测是否可 build。Capture / Topic 的 locator 由稳定 block ID 解析，行号只能作为展示提示，不能作为引用身份。

### 3.7 provenance 合同

Personal Profile 对象使用：

- 作者字段：`created_by`、`last_edited_by`、`reviewed_by`、`owner_confirmed`；
- 来源字段：`origin = human_explicit | agent_synthesis | agent_inference`；
- 内部衍生：`derived_from[] = {kind, id, content_hash}`；
- 外部材料：继续使用 `source_refs` / asset registry；
- 显式关系：`supports / contradicts / corrects / evolves_from / merged_from / related`；
- 认识状态：`claim_status = unassessed | supported | contested | refuted`。

Topic 可以包含多种来源，Topic 级 `origin` 因而允许 `mixed`。Topic 本身不带 `claim_status`；独立可反驳的 Agent inference 使用 Topic 内嵌 `codememory:claim` block、稳定 `claim_id` 和自己的 claim_status。Phase 1A 只解析 Topic 边界并保留 claim block；Phase 1B 将内嵌 block 作为 `incubator_claim` typed object 索引和读取，但仍不拆分 Markdown 文件。

`status`、`claim_status`、`freshness` 是三个正交维度：

- `status` 决定生命周期和 build 可见性；
- `claim_status` 表达具体 claim block 或单一主张型 Atom 的认识支持度；
- `freshness` 由引用 hash 计算，不作为 owner 真相持久化。

### 3.8 Canonical 提升门

```text
Incubator Topic
  ├─ Agent 自主认为成熟 → create proposed atom → owner merge
  ├─ owner 明确“新建正式 idea / 提升” → create active atom + confirmation provenance
  └─ 集中审阅批次 → owner 一次确认 → batch promote / merge / delete
```

Skill 必须把 owner 原始指令或 review batch ID 写入确认 provenance。日常整理结果不走逐条 proposal；确认门只位于 canonical 提升和既有高风险变更。

---

## 4. 操作管线契约

### 4.1 build 管线（目标态 `build.py`，单一管线服务所有出口）

```text
entry → closure → order → trim → render
```

1. **entry**：入口 id 校验，不存在即报错。
2. **closure**：按 depth（required / recommended / full）收集 imports 闭包；跳过 proposed / archived / superseded 节点并发 notice。
3. **order**：拓扑排序；检测到环时将环上节点降权处理并发 notice（沿用现实现）。
4. **trim（两遍式）**：
   - 第一遍按角色分配预算：target → required → recommended → related 依序拿全文；某一级放不下时，级内按（被依赖数 desc → access_count desc）排序，靠后的降级为 summary；target / required 永不 skipped（最低降到 summary）；related 可 skipped。
   - 第二遍按拓扑序渲染——**阅读顺序与预算分配解耦**，修正现状"拓扑序先到先得"导致低价值叶子吃掉 target 预算的缺陷。
   - 预算单位：字符（`len(text)` 近似，沿用）。
5. **render**：xml-markdown / markdown / json；`ContextPack` 是管线的中间产物模型，渲染只是输出格式。

命令关系：`build` = 新主命令；`resolve` = 管线 + plain-markdown 的薄别名；`context-pack` = 管线 + 指定格式的薄别名。三命令一个管线，输出必须一致。

### 4.2 search（词法排序，零新依赖）

- 保留现有过滤器（tags / type / status / maturity / has-imports / has-schema）。
- query 分词：按空白与标点切分；每个 token 对字段做大小写不敏感子串匹配。
- 计分：`score = Σ(field_weight × 命中 token 数 / 总 token 数)`，字段权重 id=4 / summary=3 / tags=2 / body=1。
- 淘汰规则：全部 token 零命中才淘汰（OR 语义）；单 token query 行为 = 现状子串匹配的加权版。
- tie-break：被依赖数 desc → access_count desc → id asc（沿用现状）。

### 4.3 check（CLI 名 `validate`）

现有项：断链（error）、循环依赖、schema 违约、stale asset、孤儿、source-ref 缺失（warning）。

新增项：proposed 积压提醒（超 14 天，阶段 A）、"proposed / archived 被 active atom import"警告（阶段 A）、golden_questions 格式校验（阶段 C）。

### 4.4 变更操作

| 操作 | 语义 | 状态 |
|---|---|---|
| `create` | 新 atom 模板，默认 active；低风险直写路径 | 已实现 |
| `create --propose` | 新 atom，status: proposed | 已实现 |
| `update` | 修改已有 atom（高风险，纪律见 guide）；含 `--source-ref` | 已实现 |
| `merge <id>` | 新增类：proposed → active；修改类：应用 patch + version++ | 已实现 |
| `reject <id>` | 新增类归档；修改类丢弃 patch；均留 log | 已实现 |

### 4.5 Personal Discovery 管线

```text
parse query → filter kinds/time/tags/metadata → lexical rank → return typed candidates
                                                    ├─ capture/topic → read_object
                                                    └─ atom → build
```

Phase 1 排序使用确定性的词法、时间、标签和 metadata，Agent 可在候选结果上主动继续读取。Phase 2 增加可选本地 semantic discovery adapter：

- Profile 必须显式启用并指向 `private_local` 内已存在的模型；adapter 惰性 import `sentence-transformers`，以 `local_files_only=True` 加载，不下载模型。
- provider-neutral indexer 只读取有效 typed Personal objects 与可装配 Atom/Schema，保存归一化向量到 ignored `private_local/semantic/index.json`；相同输入/model fingerprint 构建幂等。
- 内容或模型改变后 query 以 stale 失败，必须显式重建；查询文本和绝对路径不持久化。
- 外部 embeddings 当前拒绝；semantic 输出只参与候选排序，不可生成 imports、自动读取命中正文或向 build 注入节点。

### 4.6 Maintenance changeset 与状态机

一次 run 的权威输入是排序后的 `(capture_id, content_hash)` 集合；input digest 相同且已有 run 达到 `applied` 时，Core 必须返回既有 run，不生成新 changeset。

`pending/<run_id>.json` 至少包含：

```json
{
  "run_id": "run_...",
  "input_digest": "sha256:...",
  "captures": [{"id": "cap_...", "content_hash": "sha256:..."}],
  "operations": [
    {
      "op": "upsert_topic",
      "topic_id": "topic/...",
      "revision_id": "topic/...@2026-07",
      "path": "incubator/2026-07.md",
      "before_hash": "sha256:...",
      "after_hash": "sha256:..."
    }
  ]
}
```

Core apply 规则：

1. 目标为 `after_hash`：视为已应用并跳过；
2. 目标为 `before_hash`：执行该操作；
3. 两者都不是：进入 conflict / `apply_failed`，禁止覆盖；
4. 所有操作达到 after hash 后才记 `applied`，此时输入 Capture 才算已消费；
5. interrupted `applying` run 在下次从同一 changeset 恢复，不重新调用 Skill；
6. 未消费集合由完整 Capture 扫描减去所有 reached-applied run 的输入集合得到，不依赖日期、mtime 或 last-run time。

并发规则：一个实例最多一个 active maintenance run；plan 在 maintenance lock 下冻结输入集合。plan 后到达的新 Capture 由独立 append lock 写入，并留给下一次 catch-up，不能改变当前 run 的 input digest。

状态机与 Git 语义：

```text
planned → applying → applied → scanning → scan_passed → committed → pushed
              │          │          │          └→ push_failed
              │          │          └→ scan_blocked
              │          └→ commit_failed
              └→ apply_failed
```

Tracked / local 边界：

- `runs.jsonl` 受 Git 跟踪，每行一个不可变 run event，只记录内容阶段到 `scan_passed`；
- `state.json` 与 `pending/` 默认 Git ignore，是可重建的本机 runtime/delivery 状态；
- `committed` 由唯一 `CodeMemory-Run: <run_id>` commit trailer 证明；
- `pushed` 由目标 remote ref 包含该 commit 证明；
- commit/push 后不得再写受跟踪状态来“记录已 push”，避免产生新的脏工作树。

Automation 执行 Git：commit 必须带 `CodeMemory-Run: <run_id>` trailer，并在创建前查重；push 失败只更新本机 delivery state，下次推同一 commit，不能回到 maintenance 或重新消费 Capture。commit 必须包含本 run 的 journal/incubator 变更与 tracked ledger events；push 成功后工作树应为 clean。

Automation 只允许 stage profile 声明的受跟踪路径；`private-local/`、ignored runtime state 和 profile 路径外未知改动不得进入自动 commit。遇到未知改动时进入 `commit_failed` 并报告，而不是扩大范围。

`scan_blocked` 是单 active run 安全门：Capture 继续 append，但 plan/apply 新 run 与所有 Git delivery 均停止；owner 修复后恢复同一 run。阻塞期间新增 Capture 留给该 run 完成后的 catch-up。通知按安全事件发送，不进入普通审核积压。

### 4.7 敏感扫描守门

敏感扫描发生在 `applied` 之后、commit 之前，输入是待提交 diff。Core 提供结构化 scanner/result contract，Automation 负责调用和状态推进。

- 命中时进入 `scan_blocked`，不得 commit/push；
- 输出不得包含完整秘密，只含 rule、path、对象 ID 和位置提示；
- 不自动修改 Capture，也不自动搬入 `private-local/`；
- validate 必须检查 `paths.private_local` 指向的实际目录已 ignore 且未被跟踪；
- private remote 不是加密边界，相关警告属于 init 生成的实例文档合同。

---

## 5. Adapter Contracts

| 概念操作 | handler（目标态） | CLI | MCP / toolkit 最小集 |
|---|---|---|---|
| build | `handle_build`（现 `handle_resolve` + `handle_context_pack`） | `build` / `resolve` / `context-pack` | `build` |
| search | `handle_search` | `search` | `search` |
| check | `handle_validate` | `validate` | — |
| test | `handle_test` / `handle_test_report` | `test` / `test report` | — |
| 变更 | `handle_create` / `handle_propose` / `handle_update` / `handle_merge` / `handle_reject` | `create` / `propose` / `update` / `merge` / `reject` | `create_memory`、`propose_memory` |
| asset | `handle_source_*` | `source add/list/get/check/expand` | `expand_source` |
| importer | `handle_import` / `handle_skeletonize` / `handle_compile_md` / `handle_materialize_review` | `import` / `skeletonize` / `compile-md` / `materialize-review` | — |
| profile | `handle_profile_init` / `handle_profile_validate` | `init --profile personal` / `validate` | — |
| capture | `handle_capture` | `capture` | `capture` |
| typed discovery | `handle_search` / `handle_read_object` | `search` / `read` | `search` / `read` |
| maintenance | `handle_maintenance_run/resume/status` | `maintenance run/resume/status` | `maintenance_status` / `maintain_memory` / `resume_memory_maintenance` |
| batch review | `handle_review_batch` | `review-batch --file` | `review_personal_memory` |
| promotion review | `handle_promote` / batch review handlers | `promote` / `review-incubator` | `propose`（canonical 写门） |

规则：

1. 每个概念操作一个 handler，CLI / REST / MCP / tools 全部委托同一 handler；
2. REST 路由随收敛阶段对齐，禁止在 backend router 或 frontend 内实现任何装配、过滤、排序逻辑；
3. MCP / toolkit 从 `agent_tools.py` 读取同一 catalog 并走同一 root-bound dispatcher；普通实例精确暴露 `build_memory / search_memories / expand_source / create_memory / propose_memory`，其余 owner 操作只在 CLI；

Personal Profile 补充：

4. Personal Profile 在上述五项之上只追加 `capture_memory / read_memory / maintenance_status / maintain_memory / resume_memory_maintenance / review_personal_memory`；Codex Skill 不得直接编辑 journal 或 run ledger；
5. `maintain --daily` 若未来作为便利命令出现，只能编排确定性 run 阶段或启动外部 Skill，不能把 LLM provider 引入 Core；
6. CLI 继续使用 `--root` / `CODEMEMORY_ROOT`；MCP 每个进程绑定一个显式 root；toolkit 每个实例绑定一个 root；
7. Web 通过服务端 allowlist registry 将实例别名映射为绝对 root。请求只传精确命中的已知别名；middleware 在写入 request ContextVar 前校验，root resolver 再做 registry 命中与 containment 防线。禁止把任意绝对路径、未知 alias、首尾空白、路径分隔符或 `..` 交给 backend 解析；现有 `examples/` 自动发现只保留为开发/demo 兼容路径。

Operator UI 的 REST 对齐：`POST /api/build` 是主装配入口并同时返回结构化 ContextPack 与同次 build 的 rendered output；`GET /api/reviews` 分开返回 proposed Atom 与 modification patch，kind-specific merge/reject 继续委托 Core；`GET /api/tests/{memory_id}` 只读导出 TestBundle，不在 Web 内执行模型或判分。兼容路由可以保留，但不得形成第二套装配实现。

Agent 写入补充：`create_memory` 一次写入完整 summary/body/imports；普通实例可显式选择 active 或 proposed，Personal Profile 强制 proposed。`propose_memory` 只表示针对已有 Atom 的 modification patch，委托 `handle_propose` 且 owner merge 前目标字节不变。历史 `update_memory / propose_update / resolve_context / resolve_memory` 等 adapter alias 不再导出，但 CLI/Core 能力不删除。

实例 registry 目标格式：

```yaml
instances:
  mymemory: D:\\work\\MyMemory
```

registry 路径由服务端环境配置提供；它不属于 MyMemory 仓库，也不得包含 Git 凭据。

Git delivery 是可选 adapter 能力：profile init 不隐式创建 Git repo/remote，`auto_commit` / `auto_push` 默认 false。非 Git root 或 remote 缺失只产生结构化 unavailable 状态，不得阻止 init、validate profile core contract 或 Capture；显式启用但不可用时 adapter 单独报告 delivery validation。

---

## 6. 收敛路径（目标态 ← 现状的三个阶段）

每阶段独立可合并、独立验收；C 依赖 A（复用 merge 机制）与 B（管线先收敛再清理）。**当前状态：A、B、C 全部验收合并——收敛路径完成。**

| 阶段 | 内容 | 验收信号 |
|---|---|---|
| **A 写入纪律** | `status: proposed`（新增类）+ `create --propose` + merge/reject 命令 + build/search/check 过滤语义 + protected 解耦 intensity（仅 owner 手动设置）+ `update --source-ref` | 高风险新增默认 proposed；merge 前不进 build；check 报积压；protected 不再随 intensity 自动出现；atom 可经 CLI 绑定 asset |
| **B 读路径收敛** | `build` 命令落地（resolve / context-pack 变薄别名调同一管线）+ 两遍式 trim + search 词法排序 | 三命令输出一致性测试通过；裁剪优先级金测试（低价值叶子不再挤占 target 预算）；排序金测试 |
| **C 清理与 test** | intensity 全链路移除（skeletonize 参数改名 `--min-weight`，旧名 deprecated 别名）+ 删 focus/overview/wander + `compute_retrieval_probability` + models 瘦身（4 字段）+ test 契约落地 + 修改类 proposal patch 队列 | `grep intensity src/` 仅剩 deprecated 别名一处；全测试绿；`codememory test` 可输出题集；patch 队列可 merge |

每阶段 sprint 的验收必须包含"文档-实现一致"检查：实现若需偏离本文契约，先改本文档（经 owner 确认），再写代码。

---

## 7. 架构守门问题

任何新功能过这 7 问：

1. 它在代码世界的对应物是什么？（公理筛选，过不了直接拒）
2. 它属于 Core / Importer / Adapter 哪一层？是否跨层？
3. 它改变记忆语义，还是只改呈现？
4. 它把 imports（理解依赖）和 asset 引用（出处）混淆了吗？
5. 它让 LLM 绕过 proposal 直写 canonical 了吗？
6. 它需要新依赖吗？理由写在哪？
7. 另一个 adapter 能通过同一个 handler 调到它吗？
8. 它是否把 Capture / Incubator 偷渡进 canonical build？
9. 它的重试是否会重复消费 Capture、重复生成 Topic、重复 commit？
10. 它是否在 owner 未确认时创建 active Canonical Atom？
11. 它是否会把正文发送给默认关闭的外部 embedding 服务？

任何一问答案不清楚：**先改架构文档，再写代码。**

---

## 附录：删除清单汇总（阶段 C 终点）

**代码符号**：

- `handlers.py`：`handle_focus`、`handle_overview`、`handle_wander`；
- `core.py`：`compute_retrieval_probability`；
- `cli.py` / `tools.py` / `mcp_server.py`：focus / overview / wander 命令与工具绑定。

**字段（models.py / frontmatter）**：`intensity`、`stability`、`stability_source`、`days_since_last_access`。

**CLI 参数**：`create --intensity`、`orphans --min-intensity`；`skeletonize --min-intensity` 改名 `--min-weight`（旧名保留为 deprecated 别名一个版本）。

**保留不删**：`snapshot` / `transient`（REPL 草稿辅助工具）、`maturity` / `evidence`（惰性元数据）、`cache_stable` / `lifecycle`（build 内部优化与归档自动化）。

---

工程规约（编码约定、测试规范、端口、禁止事项）见 `.claude/CLAUDE.md` 与 `.claude/rules/`，本文不重复。
