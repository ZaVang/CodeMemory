# Round 17 任务计划 — 整顿

**生成日期：** 2026-05-07
**上轮评估：** Round 16 — 16/16 PASS，零回归（91/91 测试通过）。APIRouter 拆分完成、全文搜索交付、可写 MCP 工具上线。
**本轮主题：** 整顿 —— 修复 R16 遗留回归、回应体验官发现的新问题、消除技术债务警告。
**本轮定位：** 缺陷修复轮。不引入新功能，不启动大型项目。所有任务的"为何纳入"均有审计报告证据支撑。

---

## 一、本轮聚焦

Round 16 的 APIRouter 拆分引入了预料之外的回归：dataset 默认值被一个两段式的自强化循环污染（前端硬编码 initial value + 后端中间件在豁免路径上仍写 ContextVar）。体验官现场验证确认了此 bug 的完整因果链。进化策略师估算修复仅需约 30 分钟，但影响面涵盖所有首次访问和清除了 localStorage 的用户——每次浏览器会话都初始化到错误的数据集。

除 CRITICAL 回归外，体验官还发现了若干展示层问题（图节点标签尺寸、List 视图 padding），以及 R16-P2（SearchBar Resolve tooltip）交付但未在实时测试中生效的异常。Eval 报告进一步指出 `stability_source` 未在 API 响应中序列化——前端代码检查此字段但永远收不到——以及 FastAPI `on_event` 的 DeprecationWarning。

本轮策略：**全部聚焦于修复。** 不接受新功能提案、不碰 competitive gap、不启动架构迁移。唯一例外是 FastAPI lifespan 升级——它不是一个新功能，而是消除一个每次启动都触发的废弃警告。

---

## 二、任务拆解

### 第一梯队：CRITICAL 回归修复（必达，约 1 小时合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **CR1** | 修复 dataset 默认值自强化回归 | 自 R16-A1 APIRouter 拆分后，每个浏览器会话都初始化为 companion（11 条个人记忆、82% stale、极少依赖）而非服务端配置的 investment。根因两段式：(a) 前端 `api.ts` 硬编码初始值 `companion`，(b) 后端中间件在豁免路径（`/api/datasets`）上仍然从 header 写 ContextVar。结果：客户端询问"当前数据集"的行为本身就污染了服务端的答案。修复项目：服务端 `/api/datasets` 返回服务端默认值（不读 per-request ContextVar）；前端初始化为空，由服务端数据集 API 响应设置初始值；中间件对豁免路径不写 ContextVar。 | 体验官 CR1/CR2、进化策略师 TH5 |

### 第二梯队：展示层回归修复（约 30 分钟合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **UX1** | 图节点标签字号从 11px 提升至 12px | 体验官现场验证指出 Legend 中的目录名可读但图 canvas 上的节点标签在 11px 下仍难以辨认。R15 已将交互元素提升到 12px floor，但图节点标签落在此保护线之外。 | 体验官执行摘要、Phase 2.2 |
| **UX2** | List 视图水平 padding 回归 | 体验官注意到 List 视图表格缺少水平内边距，内容紧贴边缘。这是 R16 期间遗留的展示回归。 | 体验官执行摘要 |

### 第三梯队：R16 交付完整性补充（约 30 分钟合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **G1** | 确认/修复 SearchBar Resolve 按钮 tooltip 在实时环境中生效 | R16-P2 被 Generator 和 Evaluator 均标记为 PASS，但体验官现场测试报告"SearchBar Resolve 按钮无 tooltip"。可能存在编译期存在但运行时不可见的条件（CSS 层叠、title 属性被覆盖、条件渲染路径差异）。需现场验证并修复。 | 体验官执行摘要 + R16-P2 验收核对 |
| **G2** | 暴露 `stability_source` 字段到 API 响应 | Eval 报告 8.1 指出：`stability_source` 在 `MemoryEntry` 模型中已定义且后端逻辑正确检查（`resolve.py` 的 SInc 豁免），但 API 序列化输出中不包含此字段。前端 `MemoryDetail.tsx` 检查 `memory.stability_source === 'manual'` 来显示 "(manual)" 标签——此标签因字段缺失而永不渲染。后端保护正确（manual stability 不被 SInc 覆盖），但前端 UX 降级。修复方式：在 API 响应序列化中包含此字段。 | Eval 8.1 |

### 第四梯队：技术债务消除（约 30 分钟合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **T1** | FastAPI `on_event` → lifespan 迁移 | `server.py` 使用已废弃的 `@app.on_event("startup")`，每次启动触发 `DeprecationWarning`。迁移到 `@app.router.on_event` 或 lifespan context manager。非阻塞 bug 但每次开发/验收启动都可见，消除以避免 CI 日志噪音和未来 FastAPI 升级中断。 | Eval 8.3、进化策略师 |

---

## 三、本轮排除项目（不接受、不实现、不讨论）

本轮定位为纯修复轮。以下项目明确排除：

- **新功能提案**（Review Queue、Dataset Comparison、Memory Timeline、Dependency Health Score、Export-as-Context）—— 留待未来 Sprint
- **竞争差距**（导入 UI、AI 辅助创建、语义搜索、移动端适配）—— 留待未来 Sprint
- **架构迁移**（App.tsx 状态管理重构、CSS 现代化、SQLite 索引后端）—— 留待未来 Sprint
- **companion 数据集维护**（依赖丰富、内容清洗）—— 数据集回归修复后 investment 将成为默认值，此问题的紧迫性自然下降。留待未来 Sprint。
- **Dashboard stale ID 可点击** —— 体验官 Nice-to-have。本轮容量已用于更紧急的回归修复。留待未来 Sprint。
- **图节点 hover tooltip 丰富** —— 体验官 Nice-to-have。留待未来 Sprint。
- **暗色模式图节点填充可见性** —— 体验官 Nice-to-have。留待未来 Sprint。
- **响应式工具栏** —— 体验官 Nice-to-have。留待未来 Sprint。
- **Playwright 测试需后端运行** —— Eval 8.2。CI 就绪改进。非代码缺陷。留待未来 Sprint。
- **搜索精确/模糊结果分组** —— 体验官 Important。功能改进非缺陷。留待未来 Sprint。

---

## 四、验收概要

本轮共计 6 个任务。核心验收标准：

1. `curl http://localhost:8000/api/datasets` 返回 `"current": "investment"`（服务端默认值）
2. `curl -H "X-Codememory-Dataset: companion" http://localhost:8000/api/datasets` 返回 `"current": "investment"`（不被 header 污染）
3. 浏览器首次访问（无 localStorage）初始化为 investment 数据集
4. 图节点标签至少 12px，肉眼可读
5. List 视图表格有合理的水平 padding
6. SearchBar Resolve 按钮 hover 时显示 tooltip
7. `GET /api/memories/{id}` 响应包含 `stability_source` 字段
8. `uvicorn backend.server:app` 启动无 DeprecationWarning
9. 全部 91 测试无回归（57 unit + 24 integration + 5 API + 5 Playwright）

---

## 五、陷阱提示

- **[CR1] 两段式修复的原子性。** 前端和后端必须同时修复。如果只修复后端（中间件豁免但前端仍硬编码 companion），前端首次 fetchDatasets 调用会发送空 header、服务端正确返回 investment、前端拿到正确值覆盖硬编码——但若只修复前端（初始化空值但后端仍被 header 污染），浏览器首次请求不带 header，服务端返回正确值，看起来也正常。但一旦用户切换过数据集，服务端 ContextVar 已被前一个切换请求污染，后续无 header 的 datasets 调用也会被残留的 ContextVar 污染（如果 ContextVar 是跨请求共享的——需要验证 FastAPI ContextVar 的生命周期语义：在 ASGI 中间件中设置的 ContextVar 是否跨请求？如果是的话，仅豁免中间件写入不够，还需在豁免路径上主动清除 ContextVar，或改用 header → 独立的请求级状态）。
- **[G1] tooltip 可能已存在于源码但未在实时环境渲染。** R16-P2 验收通过证明源码存在。若实时测试中不可见，根因可能是 CSS z-index 被下拉菜单叠层、title 属性被 CSS content 覆盖、或条件渲染路径在特定 dataset 组合下跳过了 tooltip 宿主元素。需在实时环境中用浏览器的元素检查器核实 DOM 中 title 属性是否存在，而非仅检查源码。
- **[G2] 序列化字段暴露可能影响现有 API 消费者。** 在 API 响应中新增 `stability_source` 字段是纯加法，不应破坏任何现有消费者（未知字段被忽略）。但仍需确认所有 API 测试通过。
- **[T1] lifespan 迁移后确保 startup 逻辑执行时机不变。** `@app.on_event("startup")` 和 lifespan 的 `yield` 之前逻辑执行时机相同（均在 app 启动后、首次请求前），但异步上下文切换行为可能不同。需确认 CORS 中间件添加和 router 挂载仍在 lifespan 启动阶段执行。
