# CodeMemory 架构重建设计：契约级 architecture.md

**日期**：2026-06-10
**状态**：已确认（owner 逐节批准）
**上游**：`docs/prd.md`（memory-as-code，11 概念）、`docs/superpowers/specs/2026-06-10-memory-as-code-prd-rebuild-design.md`
**产出**：本设计指导重写 `docs/architecture.md`，并同步 `docs/plan/FUTURE.md` 的 roadmap 区。

---

## 1. 背景与定位

PRD 已按 memory-as-code 公理重建；architecture.md 还停留在 2026-05 体系（Source Artifact Registry / ContextPack / Layer Profiles 四层）。新 architecture.md 是**指导后续代码撰写与代码结构组织的最关键参考**，因此采用契约级形态：字段表、状态机、管线分解、收敛阶段全部写实，后续 sprint 不再做架构决策。

## 2. 已确认的关键决策

| 决策点 | 结论 |
|---|---|
| 收敛策略 | 目标态 + 分阶段：文档定义目标模块结构，同时定义三个独立可合并的收敛阶段 |
| test 架构位置 | Core 存契约（golden_questions frontmatter + 题集导出），agent 是 runner；Core 零 LLM 依赖 |
| 文档形态 | 契约级（~350-450 行），不是原则级 |
| proposal 载体 | 一个概念、两种载体、分阶段：新增类 = `status: proposed` 的 .md（阶段 A）；修改类 = `.codememory/proposals/` patch 队列（阶段 C） |

## 3. 分层模型（四层减为三层）

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

- Layer Profiles 层删除："什么值得记"是 guide（CONTRIBUTING）的职责，不是代码层。
- `handlers.py` 是 Core 的唯一门面，所有 adapter 经它调用。
- agent 不在系统内——agent 是运行时，经 adapter 调用系统。

## 4. 概念 → 目标模块映射

| 概念 | 目标模块 | 现状 → 目标动作 |
|---|---|---|
| repo | core.py + index.py + `.codememory/` | 不变 |
| atom / schema | models.py + create.py / update.py | 字段瘦身（第 5 节） |
| imports + build | **build.py（新）** | resolve.py + context_pack.py 合并；ContextPack 类保留为 build 产物模型 |
| asset | sources.py | 不变；补 update 的 source_refs 写入路径 |
| check | validate.py | 新增 proposed 校验、golden_questions 格式校验 |
| search | search.py | 加词法排序，零新依赖 |
| test | **test_contract.py（新，最小）** | 导出题集 + 装配上下文；report 写回 log |
| proposal | models.py（status）+ update.py（merge/reject 操作） | 不需要新模块 |
| log | log.py / changelog.py | 不变 |

**删除清单（阶段 C 终点）**：

- `handle_focus` / `handle_overview` / `handle_wander`（约 300 行）及 cli / tools / mcp 绑定；
- core.py 的 `compute_retrieval_probability`（召回概率公式）；
- models.py 字段：`intensity`、`stability`、`stability_source`、`days_since_last_access`。

**保留**：snapshot.py / transient.py（REPL 草稿，辅助工具定位）。

## 5. 数据契约

### 5.1 MemoryEntry 目标态字段表

| 字段 | 判决 | 理由 |
|---|---|---|
| type / id / summary / tags / path / version / created / updated | 保留 | 接口核心 |
| status | 保留，枚举扩为 `active / proposed / archived / superseded / draft` | proposal 载体 |
| imports / schema / summary_hash / source_refs | 保留 | 依赖、契约、stale 检测、asset 引用 |
| protected | 保留，语义重定义：仅 owner 手动设置，"动它必须走 proposal"，与 intensity 彻底解耦 | 写入纪律判据 |
| golden_questions | **新增**（可选 list，入口 atom 用） | test 契约 |
| access_count / last_access | 保留 | 维护循环 telemetry（orphans / diff） |
| cache_stable / lifecycle | 保留 | build 内部优化提示；ephemeral 自动归档已实现 |
| maturity / evidence | 保留为惰性元数据：不参与 build/search/check 任何机制 | 审计有用，不进概念层 |
| change_note / change_log | 保留 | log 原料 |
| intensity | **删除** | 重要性 = 被依赖数 |
| stability / stability_source / days_since_last_access | **删除**（连同 decay 公式） | 专为已砍的拟人召回服务 |

### 5.2 proposal 状态机（一个概念、两种载体、分阶段）

- **新增类**（阶段 A）：`status: proposed` 的普通 .md 文件，owner 直接可读。创建方式：`codememory create --propose ...`（agent 对内容没把握、或内容涉及 protected 邻域时选用；importer 产出默认 proposed）。`merge` = status → active + log；`reject` = status → archived + log。
- **修改类**（阶段 C）：`.codememory/proposals/<seq>-<target-id>.json` patch 记录（target_id、字段新值、reason、created_by、created_at）。`merge` = 应用 patch + version++ + change_log；`reject` = 丢弃记录 + log。落地前沿用 guide 的过渡做法（会话内征得 owner 同意）。
- **过滤语义（阶段 A 一并落地）**：build 永不装配 proposed（被 imports 指到时跳过并出 notice）；search 默认不返回 proposed（`--status proposed` 显式可见）；check 新增 proposed 积压提醒（超 14 天）与"proposed 被 active atom import"警告。
- 实现注记：阶段 C 实现 patch 队列前，先评审能否复用 compiler 的 review/materialize 底层，避免两套同构机制。

### 5.3 golden_questions 契约

```yaml
golden_questions:
  - q: "缓存层用什么失效策略，为什么？"
    expect: "写穿透 + 5min TTL；因为读写比 9:1"   # 期望要点，判分参考，可选
```

- `codememory test <entry>`：输出 `{ context: <build 产物>, questions: [...] }` 结构化 JSON，由 agent / CI 答题判分；
- `codememory test report <entry> --results <file>`：把 `{q, answer, pass}` 写回 log；
- Core 全程零 LLM 依赖（代码类比：pytest 独立于编译器）。

## 6. 操作管线契约

### 6.1 build 管线（目标态 build.py，单一管线服务所有出口）

```text
entry → closure → order → trim → render
```

1. **entry**：入口 id 校验；
2. **closure**：按 depth 收集 imports 闭包，过滤 proposed/archived 并出 notice；
3. **order**：拓扑排序，环检测降级；
4. **trim（两遍式）**：先按角色定级（target > required > recommended > related，同级 tie-break：被依赖数 → access_count），再分配预算——修正现状"拓扑序先到先得"导致低价值叶子吃掉 target 预算的缺陷；
5. **render**：xml-markdown / markdown / json。

`resolve` = 管线 + plain-markdown；`context-pack` = 管线 + 指定格式；`build` = 新主命令。三命令一个管线。

### 6.2 search 词法排序（零新依赖）

- 保留现有过滤器（tags/type/status/maturity 等）；
- query 计分 = 字段权重（id 命中 4 / summary 3 / tags 2 / body 1）× token 重叠度；
- tie-break：被依赖数 desc → access_count desc → id asc；
- 子串匹配保底：query 无法分词时退化为现状行为。

### 6.3 check 新增项

现有（断链/循环/schema/stale asset/孤儿）基础上新增：proposed 积压提醒、proposed 被 import 警告、golden_questions 格式校验。

## 7. Adapter Contracts

- 每个概念操作一个 handler：handle_build / handle_search / handle_validate / handle_test / handle_create / handle_update / handle_merge / handle_source_* / importer 系列；
- CLI / REST / MCP / tools 全部委托同一 handler；任何 adapter 不得私自实现装配或过滤逻辑；
- MCP / toolkit 最小工具集：`build`、`search`、`expand_source`、`create`、`propose`。

## 8. 收敛三阶段（每阶段独立可合并、可验收）

| 阶段 | 内容 | 验收信号 |
|---|---|---|
| **A 写入纪律** | `status: proposed`（新增类）+ merge/reject 命令 + build/search/check 过滤语义 + protected 解耦 intensity（仅 owner 手动设置） | 高风险新增默认 proposed；merge 前不进 build；check 报积压；protected 不再随 intensity 自动出现 |
| **B 读路径收敛** | `build` 命令落地（resolve/context-pack 变薄别名调同一管线）+ 两遍式 trim + search 词法排序 | 三命令输出一致性测试；裁剪优先级金测试；排序金测试 |
| **C 清理与 test** | intensity 全链路移除（skeletonize 参数改名 `--min-weight`，旧名 deprecated 别名）+ 删 focus/overview/wander + retrieval_probability + models 瘦身（4 字段）+ test 契约落地 + 修改类 proposal patch 队列 | `grep intensity src/` 仅剩 deprecated 别名一处；全测试绿；`codememory test` 可输出题集 |

## 9. 架构守门问题（新 7 问）

1. 它在代码世界的对应物是什么？（公理筛选，过不了直接拒）
2. 它属于 Core / Importer / Adapter 哪一层？是否跨层？
3. 它改变记忆语义，还是只改呈现？
4. 它把 imports（理解依赖）和 asset 引用（出处）混淆了吗？
5. 它让 LLM 绕过 proposal 直写 canonical 了吗？
6. 它需要新依赖吗？理由写在哪？
7. 另一个 adapter 能通过同一个 handler 调到它吗？

任何一问答案不清楚：先改架构文档，再写代码。

## 10. 新 architecture.md 大纲

1. Thesis（三层一句话 + agent 是运行时）
2. 分层模型
3. 概念 → 模块映射（目标态 + 删除清单）
4. 数据契约（字段表 / proposal 状态机 / golden_questions / asset 契约沿用）
5. 操作管线契约（build / search / check / test / proposal 操作）
6. Adapter Contracts
7. 收敛路径（阶段 A/B/C + 验收信号）
8. 架构守门问题
9. 附录：删除清单

工程规约不重复——指向 `.claude/CLAUDE.md` 与 `.claude/rules/`。

## 11. 范围边界

本次实施 = 重写 `docs/architecture.md`（临时 banner 随重写消失）+ 同步 `docs/plan/FUTURE.md`（Roadmap Priority 区替换为收敛三阶段，移除临时注记）。**不动代码**；阶段 A/B/C 是后续 sprint 的内容。

CLAUDE.md 不需要本次同步（其概念速览与命令对照在 PRD 重建时已对齐，架构文档定义的是目标态，不改变现状命令）。`.claude/rules/python.md` 的陈旧表述（"16 个模块"等）留给阶段 C 的 sprint 一并更新——届时模块数量才会真正稳定。

## 12. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 契约级文档与未来实现出现偏差 | 守门问题的收尾原则（"先改架构文档，再写代码"）写入文档；每阶段 sprint 验收含"文档-实现一致"检查 |
| 修改类 proposal patch 队列与 compiler review 机制重复建设 | 阶段 C 实现前先做小评审，优先复用 compiler 的 review/materialize 底层（已写入 5.2 实现注记） |
| 两遍式 trim 改变 resolve 现有输出，可能破坏依赖旧输出的测试/调用方 | 阶段 B 的验收含三命令一致性测试；输出变化在 sprint 中以金测试显式固化 |
