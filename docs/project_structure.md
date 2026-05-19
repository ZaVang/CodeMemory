# CodeMemory Project Structure

> 本文是仓库地图：记录每个主要文件负责什么、应该改哪里、不要把逻辑塞到哪里。  
> 产品判断读 `docs/prd.md`；架构边界读 `docs/architecture.md`；接入方法读 `docs/INTEGRATION.md`。

不记录生成物和本地缓存：`__pycache__/`、`.pytest_cache/`、`frontend/node_modules/`、`frontend/dist/`、Playwright 报告、临时 review 目录等。

---

## 1. 阅读顺序

1. `docs/prd.md` — 产品模式：CodeMemory v1 是可靠的 work-memory substrate，不是默认拟人陪伴产品。
2. `docs/architecture.md` — Core / Layer Profile / Memory Compiler / Adapter 的正式边界。
3. `docs/project_structure.md` — 当前仓库文件职责和落点规则。
4. `docs/INTEGRATION.md` — CLI、Python、MCP、主流 agent harness 的接入方式。
5. `docs/USER_GUIDE.md` — 面向使用者的日常操作手册。
6. `docs/agent-memory-guide.md` — Work Layer 的 agent 使用规则草案。
7. `docs/companion-mode.md` — Companion Layer 的未来探索，不代表 v1 默认行为。

---

## 2. 结构原则

| 原则 | 含义 |
|---|---|
| Core 不知道产品人格 | `src/codememory/` 负责 atom、schema、imports、index、resolve、validate；不直接决定“陪伴感”。 |
| Layer Profile 才定义场景策略 | Work / Companion / Team 这类策略应表现为目录、schema、tags、召回规则和写入规则。 |
| Memory Compiler 不直接污染 canonical memory | Markdown 迁移必须先生成 review set，再由 `materialize-review` 写入正式 memory root。 |
| Backend 是 adapter | `backend/` 可以做 API 编排和序列化，但不应重新实现 core 语义。 |
| Frontend 是 operator UI | `frontend/src/` 展示、编辑、resolve、graph，不应定义 canonical memory contract。 |
| Harness / LLM Gateway 是可选接入层 | `src/harnesslib/` 和 `src/llm_gateway/` 支撑 agent 编排，但 CodeMemory core 不能依赖某个 provider。 |
| Docs 只保留 canonical 与使用文档 | 审阅报告、阶段计划、设计草稿不再留在 `docs/` 主干。 |

---

## 3. 快速导航

| 我要做什么 | 主要入口 | 配套测试 |
|---|---|---|
| 改 memory 数据模型 / schema 规则 | `src/codememory/models.py`, `src/codememory/validate.py` | `tests/unit/test_validate.py`, `tests/unit/test_edge_cases.py` |
| 改 create / update / resolve / context-pack 行为 | `src/codememory/create.py`, `src/codememory/update.py`, `src/codememory/resolve.py`, `src/codememory/context_pack.py`, `src/codememory/handlers.py` | `tests/unit/test_create_update.py`, `tests/unit/test_resolve.py`, `tests/unit/test_context_pack.py` |
| 改 Markdown 迁移流程 | `src/codememory/compiler/` | `tests/unit/test_memory_compiler.py` |
| 改 REST API | `backend/server.py`, `backend/routers/*.py`, `backend/shared.py` | `tests/test_api.py` |
| 改可视化 UI | `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/App.tsx` | `frontend/tests/smoke.spec.ts`, `npm run build` |
| 改 agent harness 接入 | `src/harnesslib/`, `src/llm_gateway/`, `src/codememory/integrations.py` | 新增对应 unit/integration tests |
| 改文档定位 | `docs/prd.md`, `docs/architecture.md`, `docs/project_structure.md` | `rg` 检查断链 |

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
| `src/codememory/core.py` | frontmatter 解析、body hash、root 发现、检索概率/衰减基础函数。 |
| `src/codememory/models.py` | Pydantic v2 数据模型：memory entry、index、imports 等 contract。 |
| `src/codememory/index.py` | `.codememory/index.json` 的加载、保存、重建。 |
| `src/codememory/create.py` | 新 memory 文件模板生成和初始 metadata 写入。 |
| `src/codememory/update.py` | 已有 memory 的正文、summary、tags、imports、maturity 等更新。 |
| `src/codememory/resolve.py` | 依赖 DAG 解析、拓扑排序、budget 裁剪、上下文拼装。 |
| `src/codememory/context_pack.py` | 结构化 agent handoff 上下文包；Core JSON/Pydantic contract + markdown / xml-markdown / json renderers。 |
| `src/codememory/validate.py` | 完整性检查：断链、循环、schema 合规、hash stale、decay warning。 |
| `src/codememory/search.py` | CLI / library 搜索逻辑。 |
| `src/codememory/orphans.py` | 孤立 memory 检测。 |
| `src/codememory/suggest_deps.py` | 依赖建议：基于时间、目录、tags、文本信号推断 imports。 |
| `src/codememory/diff.py` | 对比当前 index 与 snapshot，检查 memory root 变化。 |
| `src/codememory/changelog.py` | 查看单个 memory 的变更历史。 |
| `src/codememory/log.py` | 读取全局追加式审计日志。 |
| `src/codememory/transient.py` | 会话内临时推理 DAG，不直接持久化为 canonical memory。 |
| `src/codememory/snapshot.py` | 将 transient context 固化为 `.md` memory。 |
| `src/codememory/import_cmd.py` | 旧版冷启动文本导入入口；更复杂迁移应走 compiler。 |
| `src/codememory/handlers.py` | CLI、Sandbox tools、backend 共享的命令处理 facade；防止 adapter 重复实现 core。 |
| `src/codememory/cli.py` | `codememory` argparse CLI 壳，参数解析后委托 handlers / compiler。 |
| `src/codememory/tools.py` | Sandbox tool 注册，把 core 能力暴露给 agent harness。 |
| `src/codememory/integrations.py` | `CodememoryToolkit`，生成 OpenAI / Anthropic / Gemini 风格 tool definition。 |
| `src/codememory/mcp_server.py` | MCP server entry point，让外部 MCP client 访问 CodeMemory 工具。 |

### 5.1 `src/codememory/compiler/` — Markdown Memory Compiler

该目录负责“把已有 Markdown 记忆迁移成 CodeMemory graph”。核心约束：先 proposal，后 review，再 materialize。

| 文件 | 职责 |
|---|---|
| `src/codememory/compiler/__init__.py` | compiler package marker。 |
| `src/codememory/compiler/models.py` | ingest source、segment、proposal、review set、materialization result 的 Pydantic contract。 |
| `src/codememory/compiler/ingest.py` | 扫描 Markdown corpus，生成稳定 source id，并保留 provenance。 |
| `src/codememory/compiler/segment.py` | 将 Markdown 切成可评审的语义片段。 |
| `src/codememory/compiler/propose.py` | 根据片段生成 draft memory proposals，包括 id、summary、body、tags、imports 候选。 |
| `src/codememory/compiler/review.py` | 写入 review set，供人或 agent 逐项 accept/reject/edit。 |
| `src/codememory/compiler/materialize.py` | 只将 accepted proposals 写入 canonical memory root，并做路径安全校验。 |

### 5.2 `src/codememory/skeletonize/` — 旧版结构化导入

这是 compiler 之前的批量导入能力。仍可用于轻量 markdown/code 骨架化，但不应承担正式迁移审阅流程。

| 文件 | 职责 |
|---|---|
| `src/codememory/skeletonize/__init__.py` | skeletonize public exports。 |
| `src/codememory/skeletonize/common.py` | intensity 解析、文本清理、通用小工具。 |
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
| `backend/shared.py` | 后端共享配置、dataset root 解析、Pydantic request models、序列化、stale/fuzzy helper。 |
| `backend/routers/__init__.py` | routers package marker。 |
| `backend/routers/memories.py` | memory CRUD、touch、rehash、import、export、backlinks。 |
| `backend/routers/search.py` | graph、resolve、context-pack、search API。 |
| `backend/routers/stats.py` | stats、wander、validate、reindex、datasets API。 |

Backend contract：

- 请求必须通过 `X-Codememory-Dataset` 选择 dataset，除 `/`, `/docs`, `/openapi.json`, `/api/datasets`, `/api/datasets/switch`。
- 读写 memory 时优先委托 `src/codememory/handlers.py` 或 core module。
- `backend/shared.py` 可以放 API request models 和序列化 helper，但不应继续膨胀成业务核心。

---

## 9. `frontend/` — Operator UI

Frontend 是本地操作台：查看 graph、resolve context、编辑 memory、运行 validate/reindex。它不定义 core contract。

| 文件 | 职责 |
|---|---|
| `frontend/package.json` | Node scripts 和 frontend dependencies。 |
| `frontend/package-lock.json` | npm 锁文件。 |
| `frontend/index.html` | Vite HTML entry。 |
| `frontend/vite.config.ts` | Vite 配置。 |
| `frontend/eslint.config.js` | ESLint 配置。 |
| `frontend/playwright.config.ts` | Playwright e2e 配置，默认验证 `http://localhost:5300`。 |
| `frontend/tsconfig.json` | TypeScript project references。 |
| `frontend/tsconfig.app.json` | App TS 编译配置。 |
| `frontend/tsconfig.node.json` | Node-side TS 编译配置。 |
| `frontend/.gitignore` | frontend 局部忽略规则。 |
| `frontend/README.md` | Vite/React 默认说明和本地开发备注。 |
| `frontend/public/favicon.svg` | 浏览器 favicon。 |
| `frontend/public/icons.svg` | UI 使用的 SVG icon sprite。 |
| `frontend/tests/smoke.spec.ts` | Playwright smoke test。 |

### 9.1 `frontend/src/`

| 文件 | 职责 |
|---|---|
| `frontend/src/main.tsx` | React root bootstrap。 |
| `frontend/src/App.tsx` | UI 状态中枢和页面编排：dataset、selection、resolve、panels、settings、undo 等；不要继续堆页面 JSX。 |
| `frontend/src/api.ts` | REST client；统一处理 dataset header、network error event、API response。 |
| `frontend/src/types.ts` | 前端 API/graph/memory TypeScript 类型。 |
| `frontend/src/colors.ts` | GraphCanvas 和 Legend 共享的目录颜色表。 |
| `frontend/src/index.css` | 全局 CSS、Tailwind v4 `@theme`、设计 token、动画。 |
| `frontend/src/useExitAnimation.ts` | 通用退出动画 hook。 |

### 9.2 `frontend/src/pages/`

页面层只做“页面组合”：把 App 状态传给可复用组件，不直接实现 API contract 或大块业务逻辑。

| 文件 | 职责 |
|---|---|
| `DashboardPage.tsx` | Dashboard 页面包装层，连接 stats/wander/validate/reindex 面板与 App 回调。 |
| `GraphPage.tsx` | Graph 页面包装层，组合 GraphCanvas、Legend、MemoryDetail 和 resolve 状态提示。 |
| `ListPage.tsx` | List 页面包装层，组合 MemoryList 和列表筛选入口。 |

### 9.3 `frontend/src/components/`

| 文件 | 职责 |
|---|---|
| `AppHeader.tsx` | 顶部导航、dataset switcher、search、graph controls、export/settings/help；负责响应式换行，避免 App 内联 header。 |
| `Badges.tsx` | status / maturity badge 组件。 |
| `Dashboard.tsx` | stats、wander、validate、reindex 的仪表盘。 |
| `EmptyState.tsx` | Graph/List/Dashboard 共享空状态。 |
| `ErrorBoundary.tsx` | 页面级渲染错误隔离，避免单个 panel 崩溃导致整页白屏。 |
| `GraphCanvas.tsx` | Cytoscape + dagre graph 渲染、节点交互、高亮、缩放。 |
| `HelpPanel.tsx` | CLI / UI 帮助面板。 |
| `Legend.tsx` | graph 颜色和边类型图例。 |
| `MemoryDetail.tsx` | memory 详情、markdown 渲染、resolve context prompt 构造、touch/rehash。 |
| `MemoryForm.tsx` | create/edit/archive 表单。 |
| `MemoryList.tsx` | memory 列表、分页、排序、过滤。 |
| `Onboarding.tsx` | 首次进入数据集选择和 resolve demo。 |
| `SearchBar.tsx` | 搜索输入、结果展示、match highlighting。 |
| `Settings.tsx` | 用户设置：默认 dataset、budget、theme。 |

---

## 10. `examples/` — 示例 Memory Roots

这些目录是演示数据和回归样本。它们可以被 backend/frontend 直接加载，但不应包含产品逻辑。

| 文件 / 目录 | 职责 |
|---|---|
| `examples/example_agent.py` | 使用 CodeMemory tool 的最小 mock agent 示例。 |
| `examples/.codememory/index.json` | examples 根级 index；主要用于兼容旧示例。 |
| `examples/investment/` | 投资决策 Work Layer 示例。 |
| `examples/investment/schemas/decision.md` | 投资决策 schema 示例。 |
| `examples/investment/user/**.md` | 投资事实、偏好、观察、当前持仓、风险承受等 memory atoms。 |
| `examples/companion/` | Companion Layer 示例数据。 |
| `examples/companion/user/context.md` | companion dataset 的上下文入口。 |
| `examples/companion/user/**.md` | 情绪、人物、偏好、belief、moment 等 future layer 示例 atoms。 |
| `examples/software-architecture/` | 软件架构决策 Work Layer 示例。 |
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
| `tests/test_api.py` | FastAPI API 级测试。 |
| `tests/unit/__init__.py` | unit test package marker。 |
| `tests/unit/test_create_update.py` | create/update 行为测试。 |
| `tests/unit/test_edge_cases.py` | 边界条件和异常路径测试。 |
| `tests/unit/test_memory_compiler.py` | Markdown compiler ingest/propose/review/materialize 测试。 |
| `tests/unit/test_resolve.py` | DAG resolve、预算裁剪、拓扑顺序测试。 |
| `tests/unit/test_context_pack.py` | 结构化 ContextPack 和 renderer 测试。 |
| `tests/unit/test_skeletonize.py` | skeletonize markdown/code 导入测试。 |
| `tests/unit/test_validate.py` | validate 断链、循环、schema、decay warning 测试。 |

建议命令：

```bash
python -m pytest -q tests/unit tests/test_api.py
python tests/integration_test.py
cd frontend && npm run build
```

---

## 13. `docs/` — Canonical Documentation

当前 `docs/` 只保留会长期指导产品和工程判断的文档。

| 文件 | 职责 |
|---|---|
| `docs/prd.md` | 产品定义：目标用户、v1 范围、非目标、产品分层、迁移体验。 |
| `docs/architecture.md` | 系统架构：Core、Layer Profile、Compiler、Adapters、integration contract。 |
| `docs/project_structure.md` | 本文：仓库文件地图和落点规则。 |
| `docs/INTEGRATION.md` | 外部接入指南：CLI、Python API、MCP、agent framework/harness。 |
| `docs/USER_GUIDE.md` | 使用者指南：安装、创建、检索、维护、迁移。 |
| `docs/agent-memory-guide.md` | Work Layer agent 操作指南草案。 |
| `docs/companion-mode.md` | Companion Layer 未来探索文档。 |

已删除的文档类型：

- 历史审阅报告：`gemini-audit-review.md`, `docs/orch/*`
- 阶段计划和执行记录：`docs/plans/*`, `docs/superpowers/*`
- 早期产品草稿：`product_spec.md`, `chronicle.md`, `interop-with-team-knowledge.md`
- 早期单点概念文档：`layer0-cognitive-interface.md`
- UI 设计探索稿：`docs/design/*`

这些内容不再作为当前判断依据；如果需要追溯，用 Git history。

---

## 14. 新代码落点规则

| 新需求 | 应放位置 | 不应放位置 |
|---|---|---|
| 新 memory 字段或 contract | `src/codememory/models.py`, `validate.py`, `architecture.md` | `frontend/src/types.ts` 单独新增 |
| 新 CLI 子命令 | `src/codememory/cli.py` + `handlers.py` 或专门 core module | backend router 内部私有实现 |
| 新迁移算法 | `src/codememory/compiler/` | `import_cmd.py` 继续堆逻辑 |
| 新 REST endpoint | `backend/routers/<domain>.py` | `backend/server.py` |
| 新 UI 页面 | `frontend/src/pages/` 组合组件，由 `App.tsx` 选择页面 | `App.tsx` 内联大量 JSX |
| 新可复用 UI 组件 | `frontend/src/components/` | `frontend/src/pages/` 中复制粘贴实现 |
| 新 agent provider | `src/llm_gateway/providers/` | `src/codememory/` |
| 新 harness tool | `src/harnesslib/tools/` 或 `src/codememory/tools.py` | 直接耦合到某个 LLM provider |
| 新产品策略 | Layer profile / schema / docs | Core 函数里硬编码场景规则 |

---

## 15. 清理规则

1. `docs/` 中新增文档前，先判断是否能合并进 `prd.md`、`architecture.md`、`project_structure.md`、`INTEGRATION.md` 或 `USER_GUIDE.md`。
2. 审阅报告、一次性计划、agent 执行日志默认不入 repo；需要保留时放 issue/PR 或 Git history。
3. `backend/shared.py` 每次新增 helper 都要问：是否其实应该进 `src/codememory/handlers.py` 或 core。
4. `frontend/src/App.tsx` 每次超过一个新交互簇，应优先抽组件或 hook。
5. compiler 任何写文件路径都必须通过路径安全校验，避免 proposal 写出 memory root。
