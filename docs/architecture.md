# CodeMemory Architecture

> **Architecture thesis**
> 三层结构：**Adapters 接入，Core 实现机制，Importer 负责迁移**。
> Core 实现 PRD 的 11 概念；agent 不在系统内——agent 是运行时，经 adapter 调用系统。
> 本文档是契约级参考：字段表、状态机、管线分解、收敛路径是后续 sprint 的直接依据，sprint 不再做架构决策。
> 冲突裁决顺序：`docs/prd.md`（概念）> 本文档（结构与契约）> 代码现状。

**最后更新**：2026-06-10
**状态**：canonical / 契约级
**上游**：`docs/prd.md`（memory-as-code，11 概念）；设计依据 `docs/superpowers/specs/2026-06-10-architecture-rebuild-design.md`

---

## 1. 总体分层

```text
┌──────────────────────────────────────────────────┐
│                    Adapters                       │
│  cli.py / tools.py / mcp_server.py /              │
│  integrations.py / backend(REST) / frontend(UI)   │
│  只做参数解析与传输格式，零业务逻辑                  │
├──────────────────────────────────────────────────┤
│                 Core（机制层）                     │
│  表示：models.py  core.py  index.py               │
│  操作：build  search  check  test(仅契约)          │
│  变更：create  update  merge  log  changelog      │
│  资产：sources.py    维护：orphans suggest_deps    │
├──────────────────────────────────────────────────┤
│               Importer（迁移层）                   │
│  import_cmd / skeletonize/ / compiler/            │
│  产出一律是 proposal，经 review 晋升               │
└──────────────────────────────────────────────────┘
```

旧体系的 Layer Profiles 层已删除："什么值得记"是 `docs/agent-memory-guide.md`（CONTRIBUTING）的职责，不是代码层。

### 1.1 Adapters（接入层）

- 成员：`cli.py`、`tools.py`、`mcp_server.py`、`integrations.py`、`backend/`（REST）、`frontend/`（Operator UI）。
- 职责：参数解析、传输格式、呈现。
- 禁区：零业务逻辑；不得私自实现装配、过滤或排序；不得扩展记忆语义。

### 1.2 Core（机制层）

- 表示：`models.py`（Pydantic v2 契约）、`core.py`（frontmatter 解析 / hash / root 解析）、`index.py`。
- 操作：build（装配）、search（入口检索）、check（校验，CLI 名 `validate`）、test（仅契约，零 LLM 依赖）。
- 变更：`create.py`、`update.py`（含 merge/reject 操作）、`log.py`、`changelog.py`。
- 资产：`sources.py`。维护：`orphans.py`、`suggest_deps.py`、`diff.py`。
- **`handlers.py` 是 Core 的唯一门面**，所有 adapter 经它调用。
- 禁区：不依赖任何 LLM provider；不依赖 harnesslib / llm_gateway；不决定"什么值得记"。

### 1.3 Importer（迁移层）

- 成员：`import_cmd.py`、`skeletonize/`、`compiler/`。
- 职责：外部材料 → asset 登记 + atom proposals。
- 铁律：产出一律是 proposal，经 review 晋升；LLM 只 propose，不写 canonical truth；原始材料默认保留。

### 1.4 agent 在哪里

agent 不是系统组件。agent 是消费 build 产物、按写入纪律提交变更的运行时，永远经 adapter（CLI bash 命令 / MCP / toolkit）调用系统，不 import codememory、不直接读写记忆库的 .md 文件。

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
| test | **`test_contract.py`** | 已完成：导出题集 + 装配上下文；report 写回 log | C ✅ |
| proposal | `models.py`（status）+ `proposals.py`（patch 队列）+ `update.py`（merge/reject 分发） | 已完成（修改类落为独立小模块 `proposals.py`，复用 update 应用 patch） | A ✅ / C ✅ |
| log | `log.py` / `changelog.py` | 不变 | — |

### 2.1 保留与定位说明

- `snapshot.py` / `transient.py`：保留，定位为 REPL 草稿辅助工具（会话级推理链与持久化），不属于 11 概念。
- `compiler/` 的 review/materialize 机制：保留；阶段 C 实现修改类 proposal 前，先评审复用其底层，避免两套同构机制。

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
- Core 全程零 LLM 依赖——代码类比：pytest 独立于编译器，runner 是 agent。

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

---

## 5. Adapter Contracts

| 概念操作 | handler（目标态） | CLI | MCP / toolkit 最小集 |
|---|---|---|---|
| build | `handle_build`（现 `handle_resolve` + `handle_context_pack`） | `build` / `resolve` / `context-pack` | `build` |
| search | `handle_search` | `search` | `search` |
| check | `handle_validate` | `validate` | — |
| test | `handle_test` / `handle_test_report` | `test` / `test report` | — |
| 变更 | `handle_create` / `handle_update` / `handle_merge` / `handle_reject` | `create` / `update` / `merge` / `reject` | `create`、`propose` |
| asset | `handle_source_*` | `source add/list/get/check/expand` | `expand_source` |
| importer | `handle_import` / `handle_skeletonize` / `handle_compile_md` / `handle_materialize_review` | `import` / `skeletonize` / `compile-md` / `materialize-review` | — |

规则：

1. 每个概念操作一个 handler，CLI / REST / MCP / tools 全部委托同一 handler；
2. REST 路由随收敛阶段对齐，禁止在 backend router 或 frontend 内实现任何装配、过滤、排序逻辑；
3. MCP / toolkit 只暴露最小工具集（build / search / expand_source / create / propose），其余操作属于 owner 的 CLI 工作面。

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
