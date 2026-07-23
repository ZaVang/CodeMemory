# CodeMemory Project Structure

> 本文是仓库地图：记录每个主要文件负责什么、应该改哪里、不要把逻辑塞到哪里。
> 产品判断读 `docs/prd.md`；架构边界读 `docs/architecture.md`；接入方法读 `docs/INTEGRATION.md`。

> **最后校准**：2026-07-23。本文映射当前 memory-as-code、Personal Profile、Importer v2、共享 Agent tools 与 Operator UI 文件职责。

不记录生成物和本地缓存：`__pycache__/`、`.pytest_cache/`、`frontend/node_modules/`、`frontend/dist/`、Playwright 报告、临时 review 目录等。

---

## 1. 阅读顺序

1. `docs/prd.md` — 产品公理、11 个 canonical 概念与 Personal Profile 产品边界。
2. `docs/architecture.md` — Core / Adapters / Importer、两条读取路径、Personal Profile 机制与运行时边界。
3. `docs/personal-memory-profile.md` — 外部个人实例的权威文件、provenance、维护状态与 Git 安全合同。
4. `docs/project_structure.md` — 当前仓库文件职责和落点规则。
5. `docs/INTEGRATION.md` — CLI、Python、MCP、主流 agent harness 的接入方式。
6. `docs/USER_GUIDE.md` — 面向使用者的日常操作手册。
7. `docs/agent-memory-guide.md` — canonical atom 的 agent 贡献规范。
8. `docs/plan/` — 当前 sprint 和长期 backlog。
9. `docs/reference/` — idea 来源、历史审计和非默认方向，仅作追溯。

---

## 2. 结构原则

| 原则 | 含义 |
|---|---|
| Core 不知道产品人格 | `src/codememory/` 负责 atom、schema、imports、index、build、validate；不直接决定“陪伴感”。 |
| Profile 只扩展实例能力 | Personal Profile 在 canonical Core 外增加 Capture / Incubator / maintenance；普通 root 不继承这些能力。 |
| Source Artifact 不是 Atom | 长文档、代码、PDF、URL 等原始材料应进入 source registry；atom 只表达可复用语义或 anchor。 |
| Build 产出 ContextPack | `build.py` 是唯一装配管线；source body 仍通过显式 expand 获取。 |
| Memory Compiler 不直接污染 canonical memory | Markdown 迁移先登记 asset、生成 review set；`materialize-review` 只写 proposed atom，owner merge 后才 canonical。 |
| Backend 是 adapter | `backend/` 可以做 API 编排和序列化，但不应重新实现 core 语义。 |
| Frontend 是 operator UI | `frontend/src/` 展示、编辑、Build、Review、golden questions 与 graph，不应定义 canonical memory contract。 |
| Harness / LLM Gateway 是可选接入层 | `src/harnesslib/` 和 `src/llm_gateway/` 支撑 agent 编排，但 CodeMemory core 不能依赖某个 provider。 |
| Docs 只保留 canonical、使用文档与主动计划 | 审阅报告、设计草稿、agent 执行日志不留在 `docs/` 主干；当前路线图和 sprint 只放 `docs/plan/`。 |

---

## 3. 快速导航

| 我要做什么 | 主要入口 | 配套测试 |
|---|---|---|
| 改 memory 数据模型 / schema 规则 | `src/codememory/models.py`, `src/codememory/validate.py` | `tests/unit/test_validate.py`, `tests/unit/test_edge_cases.py` |
| 改 create / update / build 行为 | `src/codememory/create.py`, `src/codememory/update.py`, `src/codememory/build.py`, `src/codememory/resolve.py`, `src/codememory/handlers.py` | `tests/unit/test_create_update.py`, `tests/unit/test_build_pipeline.py`, `tests/unit/test_context_pack.py` |
| 新增 Source Artifact / source_refs | `src/codememory/sources.py`, `src/codememory/models.py`, `src/codememory/build.py` | `tests/unit/test_sources.py`, `tests/unit/test_source_refs.py`, `tests/unit/test_source_expand.py` |
| 改 Markdown 迁移流程 | `src/codememory/compiler/` | `tests/unit/test_memory_compiler.py` |
| 改 golden-question 三臂评测 | `src/codememory/evaluation/`, `src/codememory/test_contract.py` | `tests/unit/test_eval_harness.py`, `tests/unit/test_golden_questions.py` |
| 改 REST API | `backend/server.py`, `backend/routers/*.py`, `backend/shared.py` | `tests/test_api.py` |
| 改可视化 UI | `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/App.tsx` | `frontend/tests/smoke.spec.ts`, `npm run build` |
| 改 Agent tool 接入 | `src/codememory/agent_tools.py`, `src/codememory/tools.py`, `src/codememory/integrations.py`, `src/codememory/mcp_server.py` | `tests/unit/test_agent_tool_alignment.py` |
| 改文档定位 | `docs/prd.md`, `docs/architecture.md`, `docs/project_structure.md` | `rg` 检查断链 |
| 改长期 backlog / 当前 sprint | `docs/plan/FUTURE.md`, `docs/plan/SPRINT.md` | `rg` 检查断链 |

---

## 4. 顶层文件

| 文件 / 目录 | 职责 |
|---|---|
| `.gitignore` | 忽略 Python、Node、测试、构建和本地运行产物。 |
| `.claude/` | 早期 Claude Code 本地工作流配置；不是产品 runtime，后续应只保留仍被实际使用的脚本。 |
| `LICENSE` | MIT 许可证。 |
| `pyproject.toml` | Python 包元数据、依赖、entry points、setuptools package discovery。 |
| `requirements.txt` | 最小 Python runtime 依赖，偏向快速本地安装。 |
| `README.md` | 项目入口说明、快速命令、文档导航。 |
| `start.ps1` | Windows / PowerShell 友好的完整应用启动脚本；检查依赖后调用 `bin/codememory.py dev`。 |
| `bin/` | 单文件本地 launcher。 |
| `src/` | Python source root。 |
| `backend/` | FastAPI REST adapter。 |
| `frontend/` | Vite + React operator UI。 |
| `examples/` | 示例 memory roots 和最小 agent 示例。 |
| `tests/` | Python 单元 / API / 集成测试。 |

---

## 5. `src/codememory/` — Memory Core

这一层是产品核心。它应该能在 CLI、MCP、backend、agent harness 中复用。

| 文件 | 职责 |
|---|---|
| `src/codememory/__init__.py` | Python public API 聚合入口。新增公共函数时在这里显式导出。 |
| `src/codememory/core.py` | frontmatter 解析、body hash、root 发现与严格 memory ID/path containment。 |
| `src/codememory/profile.py` | Personal Profile manifest、非覆盖初始化、独立 profile/Git capability validation。 |
| `src/codememory/capture.py` | append-only Capture、ULID、独立 SHA-256、实例锁、fsync 与完整 block 解析。 |
| `src/codememory/personal_index.py` | Capture / Incubator Topic / inline Claim typed index、词法筛选和稳定 ID read；Claim 保持在 Topic 文件内。 |
| `src/codememory/semantic_index.py` | Personal Profile provider-neutral 派生语义索引：typed 输入、atomic persistence、stale/idempotency 与候选排序；canonical build 不读取。 |
| `src/codememory/semantic_local.py` | 惰性 `sentence-transformers` 本地 adapter；只从已有 private-local 模型目录加载并禁止下载/remote code。 |
| `src/codememory/personal_web.py` | Personal owner workspace 的 provider-neutral overview/Capture/Topic/Claim/timeline typed read models；只生成安全相对 locator。 |
| `src/codememory/periodic_review.py` | Personal 月度/年度确定性 evidence bundle、digest/no-clobber 输出与 owner-only 派生 review 保存。 |
| `src/codememory/maintenance.py` | Personal maintenance run ledger、稳定 input digest、pending changeset、Topic/Claim 渲染、幂等 apply 与恢复。 |
| `src/codememory/promotion.py` | owner-gated Topic promotion 与 promote/merge/delete batch review。 |
| `src/codememory/git_delivery.py` | Profile 路径白名单、staged diff 敏感扫描、run trailer commit 与同 commit push retry。 |
| `src/codememory/models.py` | Pydantic v2 数据模型：memory entry、index、imports、source_refs 等 contract。 |
| `src/codememory/index.py` | `.codememory/index.json` 的加载、保存、重建。 |
| `src/codememory/create.py` | 新 memory 文件模板生成和初始 metadata 写入。 |
| `src/codememory/update.py` | 已有 memory 的正文、summary、tags、imports、maturity 等更新。 |
| `src/codememory/build.py` | 唯一 canonical build 管线：imports DAG、拓扑顺序、两遍式 budget trim、ContextPack 模型与全部 renderer。 |
| `src/codememory/resolve.py` | `build.py` 的 plain-Markdown 兼容薄别名与 DAG helper 导出。 |
| `src/codememory/test_contract.py` | provider-free golden-question/TestBundle 导出与外部结果日志合同。 |
| `src/codememory/sources.py` | Source Artifact Registry：`.codememory/sources/index.json` 的模型、load/save、add/list/get、stale/missing 检查、explicit source expansion。 |
| `src/codememory/validate.py` | 完整性检查：断链、循环、schema 合规、hash stale、source stale/missing、source_refs 与 proposal/status 边界。 |
| `src/codememory/search.py` | CLI / library 搜索逻辑。 |
| `src/codememory/orphans.py` | 孤立 memory 检测。 |
| `src/codememory/suggest_deps.py` | 依赖建议：基于时间、目录、tags、文本信号推断 imports。 |
| `src/codememory/diff.py` | 对比当前 index 与 snapshot，检查 memory root 变化。 |
| `src/codememory/changelog.py` | 查看单个 memory 的变更历史。 |
| `src/codememory/log.py` | 读取全局追加式审计日志。 |
| `src/codememory/transient.py` | 会话内临时推理 DAG，不直接持久化为 canonical memory。 |
| `src/codememory/snapshot.py` | 将 transient context 固化为 `.md` memory。 |
| `src/codememory/import_cmd.py` | 旧版冷启动文本导入入口；更复杂迁移应走 compiler。 |
| `src/codememory/handlers.py` | CLI、Sandbox tools、backend 共享的命令处理 facade；显式 eval 在这里完成冻结输入后才惰性构造 provider client。 |
| `src/codememory/cli.py` | `codememory` argparse CLI 壳，参数解析后委托 handlers / compiler；`eval` 是 trusted owner/CI 命令，不进入 Agent catalog。 |
| `src/codememory/agent_tools.py` | MCP / Toolkit 共用的 root-aware tool catalog 与 dispatcher；只委托 handlers，并固化 create/propose 写门。 |
| `src/codememory/tools.py` | 将共享 catalog 绑定到一个 root 后注册进 Sandbox，不再维护独立 schema/业务分发。 |
| `src/codememory/integrations.py` | `CodememoryToolkit`，把 root 对应的共享 catalog 机械转换为 OpenAI / Anthropic / Gemini 格式。 |
| `src/codememory/mcp_server.py` | 显式 `CODEMEMORY_ROOT` 绑定的 MCP stdio adapter；tools/list 与 tools/call 复用共享 catalog/dispatcher。 |

### 5.1 `src/codememory/evaluation/` — Explicit Eval Harness

该目录负责 golden-question 三臂实验。provider-neutral runner 先冻结 ContextPack、full-memory、no-memory 与 hashes，再通过显式惰性 adapter 答题/盲判；报告不复制 context、prompt、config path 或 raw thinking。

| 文件 | 职责 |
|---|---|
| `src/codememory/evaluation/models.py` | `memory-eval/v1` report、arm/sample/call/metric/comparison typed contract。 |
| `src/codememory/evaluation/runner.py` | full-memory 安全构造、三臂冻结、盲判调用、保守失败统计与对比指标；不 import provider。 |
| `src/codememory/evaluation/gateway_adapter.py` | 仅在显式 eval handler 中惰性加载 `llm_gateway`；answer/judge structured output、无 tools/Web。 |
| `src/codememory/evaluation/report_io.py` | 显式 output 的 no-clobber preflight 与完整报告 atomic publish。 |
| `src/codememory/evaluation/__init__.py` | provider-neutral public exports；不导入 gateway adapter。 |

### 5.2 `src/codememory/compiler/` — Markdown Memory Compiler

该目录负责“把已有 Markdown 记忆迁移成 CodeMemory graph”。核心约束：先登记 asset；默认生成 anchor / paragraph-derived proposal，或由显式可选 LLM proposer 生成 anchor / semantic-derived proposal；两条路径都经 review 选择、只 materialize 为 proposed atom，最后由 owner merge。

| 文件 | 职责 |
|---|---|
| `src/codememory/compiler/__init__.py` | compiler package marker。 |
| `src/codememory/compiler/models.py` | source、segment、paragraph、anchor/derived proposal、semantic proposer metadata、review set、materialization result 的 Pydantic contract。 |
| `src/codememory/compiler/ingest.py` | 只读扫描 Markdown corpus，以 resolved URI 生成稳定 artifact id，并保留 hash/provenance。 |
| `src/codememory/compiler/segment.py` | 保留 heading context，将正文切成带稳定 ID、hash 和行范围的非空段落。 |
| `src/codememory/compiler/propose.py` | 幂等登记 Source Artifacts，生成每文档一个 anchor 与每段一个 derived proposal；确定性路径不建议 imports。 |
| `src/codememory/compiler/llm_proposer.py` | provider-neutral typed semantic draft、prompt/provenance/import 校验、稳定 proposal/path 映射与安全 metadata；不 import provider。 |
| `src/codememory/compiler/gateway_adapter.py` | 仅在显式 LLM 路径惰性加载 `llm_gateway`，请求无 tools 的 structured output。 |
| `src/codememory/compiler/review.py` | 写入 review set，保留相同输入重试的 decisions，拒绝冲突 review ID。 |
| `src/codememory/compiler/materialize.py` | 只将 accepted candidates 写为 `status: proposed` atom；semantic batch 写前整体校验 source refs/path/imports/cycle，失败零写入。 |

### 5.3 `src/codememory/skeletonize/` — 旧版结构化导入

这是 compiler 之前的批量导入能力。仍可用于轻量 markdown/code 骨架化，但不应承担正式迁移审阅流程。

| 文件 | 职责 |
|---|---|
| `src/codememory/skeletonize/__init__.py` | skeletonize public exports。 |
| `src/codememory/skeletonize/common.py` | weight annotation 解析、文本清理、通用小工具；仅为一版兼容接受旧 annotation alias。 |
| `src/codememory/skeletonize/config.py` | skeletonize 配置模型和默认值。 |
| `src/codememory/skeletonize/markdown.py` | Markdown 标题/段落拆分与 memory skeleton 生成。 |
| `src/codememory/skeletonize/code.py` | Python / JS / TS 等代码文件的结构提取；可选依赖 Tree-sitter。 |

---

## 6. `src/harnesslib/` — 通用 Agent Harness

这一层是可复用的 agent 编排库，不应该反向污染 CodeMemory core。

| 文件 | 职责 |
|---|---|
| `src/harnesslib/__init__.py` | harnesslib package marker / public exports。 |
| `src/harnesslib/event.py` | Event 模型与 SessionBase 接口；会话事件流的持久状态锚。 |
| `src/harnesslib/harness.py` | Effect-loop harness，通过 yield effect 声明工具/LLM 调用意图。 |
| `src/harnesslib/sandbox.py` | 通用 tool execution sandbox：注册工具并按 name + payload 执行。 |
| `src/harnesslib/gateway.py` | LLM gateway 抽象接口，实际 provider 能力由 `llm_gateway` 实现。 |
| `src/harnesslib/orchestration.py` | 极简调度层，确保 session 被某个 harness 处理。 |
| `src/harnesslib/prompt_engine.py` | Jinja2 prompt 模板加载、渲染、版本 hash。 |
| `src/harnesslib/resources.py` | ResourceRef / ResourceManager，让 tools 通过资源引用拿数据。 |
| `src/harnesslib/_tracing.py` | LLM / tool tracing schema，目前是可选集成 stub。 |
| `src/harnesslib/session/__init__.py` | session package marker。 |
| `src/harnesslib/session/json_session.py` | JSON 文件事件流 session 实现。 |
| `src/harnesslib/tools/__init__.py` | harness tools package marker。 |
| `src/harnesslib/tools/data_tool.py` | 数据读取/查询类 harness tool。 |
| `src/harnesslib/tools/llm_tool.py` | 将 LLM 调用包装成 harness tool。 |

---

## 7. `src/llm_gateway/` — 多 Provider LLM Gateway

这一层解决 LLM provider 差异、fallback、key rotation、tool calling。CodeMemory core 不应依赖它。

| 文件 | 职责 |
|---|---|
| `src/llm_gateway/__init__.py` | llm_gateway package marker / public exports。 |
| `src/llm_gateway/bridge.py` | `LLMBridge` 主入口；调度 provider、重试、fallback、工具调用和可选 tracing。 |
| `src/llm_gateway/models.py` | 统一响应、聊天参数、tool schema、provider config 的 Pydantic 模型。 |
| `src/llm_gateway/config.py` | YAML 配置加载与 `${ENV_VAR}` secret 解析。 |
| `src/llm_gateway/router.py` | retry、fallback、负载均衡、API key rotation。 |
| `src/llm_gateway/circuit_breaker.py` | provider/model 熔断器，避免持续打坏链路。 |
| `src/llm_gateway/skills.py` | 本地 `SKILL.md` 加载、frontmatter stripping、Jinja2 渲染。 |
| `src/llm_gateway/providers/__init__.py` | provider package marker。 |
| `src/llm_gateway/providers/base.py` | provider adapter 抽象基类。 |
| `src/llm_gateway/providers/openai_provider.py` | OpenAI provider adapter。 |
| `src/llm_gateway/providers/anthropic_provider.py` | Anthropic provider adapter。 |
| `src/llm_gateway/providers/google_provider.py` | Google / Gemini provider adapter。 |
| `src/llm_gateway/tools/__init__.py` | gateway tools package marker。 |
| `src/llm_gateway/tools/base.py` | `BridgeTool`、`ToolRegistry` 和默认 registry。 |
| `src/llm_gateway/tools/io.py` | 内置 I/O tools：fetch URL、read file、glob、search docs 等。 |

---

## 8. `backend/` — REST Adapter

Backend 的职责是把 core 能力变成 HTTP API，并处理 dataset header、序列化、错误码。不要在这里定义新的 memory 语义。

| 文件 | 职责 |
|---|---|
| `backend/requirements.txt` | 后端运行依赖。 |
| `backend/server.py` | FastAPI app 创建、CORS、中间件、lifespan reindex、router mounting、health endpoint。 |
| `backend/shared.py` | 后端共享配置、dataset alias/root containment、Pydantic request models、序列化与 stale helper。 |
| `backend/routers/__init__.py` | routers package marker。 |
| `backend/routers/memories.py` | memory CRUD、rehash、import、export、backlinks；create/update 委托 Core。 |
| `backend/routers/search.py` | graph、build、兼容 assembly aliases、search API；所有装配走统一 Core build pipeline。 |
| `backend/routers/reviews.py` | proposed Atom / modification patch review 队列、kind-specific merge/reject、只读 TestBundle API。 |
| `backend/routers/sources.py` | Source Artifact REST adapter；当前提供 explicit source expansion，并委托 core `expand_source_artifact`。 |
| `backend/routers/stats.py` | stats、validate、reindex、datasets API。 |
| `backend/routers/personal.py` | Personal-only overview/capture/topic/timeline REST 与一次 batch review 的薄 adapter。 |

Backend contract：

- 请求必须通过 `X-Codememory-Dataset` 选择 dataset，除 `/`, `/docs`, `/openapi.json`, `/api/datasets`, `/api/datasets/switch`。外部 Personal root 只来自 `CODEMEMORY_INSTANCE_REGISTRY`，公开 metadata 不含 path。
- 读写 memory 时优先委托 `src/codememory/handlers.py` 或 core module。
- `backend/shared.py` 可以放 API request models 和序列化 helper，但不应继续膨胀成业务核心。

---

## 9. `frontend/` — Operator UI

Frontend 是本地操作台：查看 graph、Build canonical context、编辑 memory、处理 owner review、查看 golden questions、运行 validate/reindex，以及在 Personal dataset 中浏览 Capture/Topic 并确认集中审阅。它不定义 core contract。

| 文件 | 职责 |
|---|---|
| `frontend/package.json` | Node scripts 和 frontend dependencies。 |
| `frontend/package-lock.json` | npm 锁文件。 |
| `frontend/index.html` | Vite HTML entry。 |
| `frontend/vite.config.ts` | Vite 配置。 |
| `frontend/eslint.config.js` | ESLint 配置。 |
| `frontend/playwright.config.ts` | Playwright e2e 配置，默认验证 `http://127.0.0.1:5300`。 |
| `frontend/tsconfig.json` | TypeScript project references。 |
| `frontend/tsconfig.app.json` | App TS 编译配置。 |
| `frontend/tsconfig.node.json` | Node-side TS 编译配置。 |
| `frontend/.gitignore` | frontend 局部忽略规则。 |
| `frontend/README.md` | Operator UI 本地启动、视图边界与验证命令。 |
| `frontend/public/favicon.svg` | 浏览器 favicon。 |
| `frontend/public/icons.svg` | UI 使用的 SVG icon sprite。 |
| `frontend/tests/smoke.spec.ts` | Playwright smoke test。 |

### 9.1 `frontend/src/`

| 文件 | 职责 |
|---|---|
| `frontend/src/main.tsx` | React root bootstrap。 |
| `frontend/src/App.tsx` | UI 状态中枢和页面编排：dataset、selection、Build、panels、settings、undo 等；不要继续堆页面 JSX。 |
| `frontend/src/api.ts` | REST client；统一处理 dataset header、network error event、API response。 |
| `frontend/src/types.ts` | 前端 API/graph/memory TypeScript 类型。 |
| `frontend/src/colors.ts` | GraphCanvas 和 Legend 共享的目录颜色表。 |
| `frontend/src/index.css` | 全局 CSS、Tailwind v4 `@theme`、设计 token、动画。 |
| `frontend/src/useExitAnimation.ts` | 通用退出动画 hook。 |

### 9.2 `frontend/src/pages/`

页面层只做“页面组合”：把 App 状态传给可复用组件，不直接实现 API contract 或大块业务逻辑。

| 文件 | 职责 |
|---|---|
| `DashboardPage.tsx` | Dashboard 页面包装层，连接 stats/validate/reindex 面板与 App 回调。 |
| `GraphPage.tsx` | Graph 页面包装层，组合 GraphCanvas、Legend、MemoryDetail 和 Build 状态提示。 |
| `ListPage.tsx` | List 页面包装层，组合 MemoryList 和列表筛选入口。 |
| `PersonalPage.tsx` | Personal-only overview、Capture feed、Topic/Claim inspection、显式 timeline 与 batch preview/confirm。 |
| `ReviewPage.tsx` | owner review 页面：分别读取 proposed Atom 与 patch proposal，确认后调用 kind-specific merge/reject。 |

### 9.3 `frontend/src/components/`

| 文件 | 职责 |
|---|---|
| `AppHeader.tsx` | 顶部导航、dataset switcher、search、graph controls、export/settings/help；负责响应式换行，避免 App 内联 header。 |
| `Badges.tsx` | status / maturity badge 组件。 |
| `Dashboard.tsx` | stats、validate、reindex 的仪表盘。 |
| `EmptyState.tsx` | Graph/List/Dashboard 共享空状态。 |
| `ErrorBoundary.tsx` | 页面级渲染错误隔离，避免单个 panel 崩溃导致整页白屏。 |
| `GraphCanvas.tsx` | Cytoscape + dagre graph 渲染、节点交互、高亮、缩放。 |
| `HelpPanel.tsx` | CLI / UI 帮助面板。 |
| `Legend.tsx` | graph 颜色和边类型图例。 |
| `MemoryDetail.tsx` | memory 详情、markdown 渲染、canonical Build 输出复制、golden questions 与 rehash。 |
| `MemoryForm.tsx` | create/edit/archive 表单。 |
| `MemoryList.tsx` | memory 列表、分页、排序、过滤。 |
| `Onboarding.tsx` | 首次进入数据集选择和 Build demo。 |
| `SearchBar.tsx` | 搜索输入、结果展示、match highlighting。 |
| `Settings.tsx` | 用户设置：默认 dataset、budget、theme。 |

---

## 10. `examples/` — 示例 Memory Roots

这些目录是演示数据和回归样本。它们可以被 backend/frontend 直接加载，但不应包含产品逻辑。

| 文件 / 目录 | 职责 |
|---|---|
| `examples/example_agent.py` | 使用 CodeMemory tool 的最小 mock agent 示例。 |
| `examples/.codememory/index.json` | examples 根级 index；主要用于兼容旧示例。 |
| `examples/investment/` | 投资决策 canonical Atom/Schema 示例 root。 |
| `examples/investment/schemas/decision.md` | 投资决策 schema 示例。 |
| `examples/investment/user/**.md` | 投资事实、偏好、观察、当前持仓、风险承受等 memory atoms。 |
| `examples/companion/` | 个人生活语境演示 root；目录名为兼容 dataset alias，不代表独立 canonical Layer。 |
| `examples/companion/user/context.md` | 个人生活语境数据集的 build 入口。 |
| `examples/companion/user/**.md` | 情绪、人物、偏好、belief、moment 等 canonical 示例 atoms。 |
| `examples/software-architecture/` | 软件架构决策 canonical Atom/Schema 示例 root。 |
| `examples/software-architecture/schemas/architectural-decision.md` | 架构决策 schema 示例。 |
| `examples/software-architecture/user/**.md` | 架构事实、偏好、观察、决策等 atoms。 |
| `examples/*/.codememory/index.json` | 每个 dataset 的索引；由 `codememory reindex` 重建。 |
| `examples/*/.codememory/log.md` | 每个 dataset 的追加式操作日志。 |

---

## 11. `bin/` — 本地 Launcher

| 文件 | 职责 |
|---|---|
| `bin/codememory.py` | 唯一本地 launcher。默认转发到 `codememory.cli`；`dev` 子命令跨平台启动 backend + frontend。 |

---

## 12. `tests/` — 测试边界

| 文件 | 职责 |
|---|---|
| `tests/integration_test.py` | CLI / core 集成流程测试。 |
| `tests/integration_personal.py` | Phase 1A disposable external instance、root binding 与两条读取路径验收。 |
| `tests/test_api.py` | FastAPI API 级测试。 |
| `tests/personal/test_profile.py` | Personal Profile 与可选 Git capability 合同。 |
| `tests/personal/test_capture.py` | Capture ID/hash/锁/完整块合同。 |
| `tests/personal/test_discovery.py` | 三类对象、Topic/Claim 保留、typed search/read/build 边界。 |
| `tests/personal/test_maintenance.py` | missed-run、input digest、pending changeset、interrupted apply、Topic/Claim 与 Skill 交互合同。 |
| `tests/personal/test_promotion.py` | proposed/active promotion provenance 与 batch promote/merge/delete。 |
| `tests/personal/test_git_delivery.py` | staged scan、单 run block、路径白名单、commit trailer 与同 commit push retry。 |
| `tests/personal/test_periodic_review.py` | 周期窗口、baseline/claim transition、证据 digest、path/privacy、显式保存与 no-mutation 合同。 |
| `tests/unit/__init__.py` | unit test package marker。 |
| `tests/unit/test_create_update.py` | create/update 行为测试。 |
| `tests/unit/test_edge_cases.py` | 边界条件和异常路径测试。 |
| `tests/unit/test_memory_compiler.py` | Markdown compiler ingest/propose/review/materialize 测试。 |
| `tests/unit/test_importer_llm.py` | 显式 semantic proposer、lazy gateway、provenance/imports、幂等与零写入 preflight 测试（fake bridge，无真实网络）。 |
| `tests/unit/test_agent_tool_alignment.py` | 标准/Personal tool profile parity、root binding、complete create、proposal no-mutation、expand_source 与 MCP error 合同。 |
| `tests/unit/test_resolve.py` | DAG resolve、预算裁剪、拓扑顺序测试。 |
| `tests/unit/test_context_pack.py` | 结构化 ContextPack 和 renderer 测试。 |
| `tests/unit/test_source_refs.py` | source_refs metadata、reindex、validate、ContextPack 关联测试。 |
| `tests/unit/test_source_expand.py` | explicit source expansion 的模型、全文/范围、missing/stale/unsupported、handler JSON 测试。 |
| `tests/unit/test_skeletonize.py` | skeletonize markdown/code 导入测试。 |
| `tests/unit/test_validate.py` | validate 断链、循环、schema、status/proposal 与 source registry warning 测试。 |
| `tests/unit/test_docs_examples.py` | primary guide、runnable Agent 示例与 example metadata 漂移防护。 |

建议命令：

```bash
python -m pytest -q tests/unit tests/test_api.py
python tests/integration_test.py
python tests/integration_personal.py
cd frontend && npm run build
```

---

## 13. `docs/` — Canonical Documentation

当前 `docs/` 只保留会长期指导产品和工程判断的文档。

| 文件 | 职责 |
|---|---|
| `docs/prd.md` | 产品定义：memory-as-code 公理、11 个 canonical 概念、Personal Profile 三层模型与非目标。 |
| `docs/architecture.md` | 系统架构：Core / Adapters / Importer、build/discovery、Personal runtime、状态机与职责边界。 |
| `docs/personal-memory-profile.md` | Personal Profile 外部实例合同：Capture、Incubator Topic、Canonical Atom、provenance、maintenance、Git 安全。 |
| `docs/project_structure.md` | 本文：仓库文件地图和落点规则。 |
| `docs/INTEGRATION.md` | 外部接入指南：CLI、Python API、MCP、agent framework/harness。 |
| `docs/USER_GUIDE.md` | 使用者指南：安装、创建、检索、维护、迁移。 |
| `docs/agent-memory-guide.md` | canonical atom 的 Agent 贡献规范。 |
| `docs/plan/FUTURE.md` | 长期 roadmap 和 backlog；不存放一次性执行日志。 |
| `docs/plan/SPRINT.md` | 当前 active sprint；验收通过后移除已完成任务。 |
| `docs/reference/` | 历史探索、审计报告、非 v1 默认方向。用于追溯 idea 来源，不作为当前实现依据。 |

已删除的文档类型：

- 历史审阅报告：`gemini-audit-review.md`, `docs/orch/*`
- 旧的多目录阶段计划、一次性计划和 agent 执行记录
- 早期产品草稿：`product_spec.md`, `chronicle.md`, `interop-with-team-knowledge.md`
- 早期单点概念文档：`layer0-cognitive-interface.md`
- UI 设计探索稿：`docs/design/*`

当前归档：

- `docs/reference/companion-mode.md` — Companion Layer 早期探索；
- `docs/reference/ux-audit-report.md` — 一次性前端 UX 审计报告。

这些内容不再作为当前判断依据；如果需要追溯，用 `docs/reference/` 或 Git history。

### 13.1 Personal Profile 模块（Phase 1A / 1B / Phase 2 / Periodic Review）

Phase 1A / 1B / 2 与 Personal Web 已经 owner 接受；Personal Periodic Review 正在 active Sprint。当前 Personal Profile 落点如下：

| 目标路径 | 责任 |
|---|---|
| `src/codememory/profile.py` | Personal manifest 与目录/ignore 校验 |
| `src/codememory/capture.py` | Capture ID/hash、锁、append + fsync、block parser |
| `src/codememory/personal_index.py` | Capture / Topic / Atom typed discovery 与 read locator |
| `src/codememory/semantic_index.py` | ignored private-local typed vector index、显式 build/status/query 与 build isolation |
| `src/codememory/semantic_local.py` | 可选本地 embedding adapter；惰性 import、local-only load |
| `src/codememory/personal_web.py` | Web 所需 typed read model 与显式关系 timeline；不读取 private-local |
| `src/codememory/periodic_review.py` | 显式周期、确定性 evidence bundle 与 owner-only review persistence；不执行语义综合 |
| `src/codememory/maintenance.py` | Phase 1B changeset、run ledger 与幂等状态机 |
| `src/codememory/promotion.py` | canonical promotion 与 batch review |
| `src/codememory/git_delivery.py` | 敏感扫描和可选 Git delivery adapter |
| `backend/shared.py` / `backend/routers/personal.py` | 服务端 allowlist registry 与 Personal REST 薄 adapter |
| `frontend/src/pages/PersonalPage.tsx` | Personal owner browsing/review workspace |
| `.agents/skills/personal-memory/` | Phase 1B Codex 语义维护工作流；不属于 Core |

外部 `MyMemory` 实例的目录结构不属于本程序仓库；权威定义只在 `docs/personal-memory-profile.md`。

---

## 14. 新代码落点规则

| 新需求 | 应放位置 | 不应放位置 |
|---|---|---|
| 新 memory 字段或 contract | `src/codememory/models.py`, `validate.py`, `architecture.md` | `frontend/src/types.ts` 单独新增 |
| 新 Source Artifact 能力 | `src/codememory/sources.py` + `build.py` + `validate.py` | backend router 或 frontend 内部私有实现 |
| 新 CLI 子命令 | `src/codememory/cli.py` + `handlers.py` 或专门 core module | backend router 内部私有实现 |
| 新迁移算法 | `src/codememory/compiler/` | `import_cmd.py` 继续堆逻辑 |
| 新 REST endpoint | `backend/routers/<domain>.py` | `backend/server.py` |
| 新 UI 页面 | `frontend/src/pages/` 组合组件，由 `App.tsx` 选择页面 | `App.tsx` 内联大量 JSX |
| 新可复用 UI 组件 | `frontend/src/components/` | `frontend/src/pages/` 中复制粘贴实现 |
| 新 agent provider | `src/llm_gateway/providers/` | `src/codememory/` |
| 新 harness tool | `src/harnesslib/tools/` 或 `src/codememory/tools.py` | 直接耦合到某个 LLM provider |
| 新产品策略 | PRD / profile contract / Codex Skill | Core 函数里硬编码语义判断 |

---

## 15. 清理规则

1. `docs/` 根目录新增文档前，先判断是否能合并进 `prd.md`、`architecture.md`、`project_structure.md`、`INTEGRATION.md`、`USER_GUIDE.md` 或 `agent-memory-guide.md`。
2. 长期 backlog 和当前 active sprint 只放 `docs/plan/FUTURE.md` 与 `docs/plan/SPRINT.md`。
3. 审阅报告、一次性计划、agent 执行日志默认不入 docs 主干；确实要保留 idea 来源时放 `docs/reference/`。
4. `backend/shared.py` 每次新增 helper 都要问：是否其实应该进 `src/codememory/handlers.py` 或 core。
5. `frontend/src/App.tsx` 每次超过一个新交互簇，应优先抽组件或 hook。
6. compiler 任何写文件路径都必须通过路径安全校验，避免 proposal 写出 memory root。
