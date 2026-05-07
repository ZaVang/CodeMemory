# Generator Status — Iteration 16 (Final)

## 完成的任务 (16/16)

### 第一梯队：必达 — 承诺兑现 + 已知缺陷 (F1-F5)

- [x] **R16-F1: 修复端点缺失的 decay 字段** — POST/PUT 端点在 reindex 后重新加载索引，确保 `days_since_last_access`、`stability`、`access_count` 出现在响应中。`get_memory` 端点调整 dict 构建顺序：`**meta` 在前，显式 decay 字段在后覆盖，防止 frontmatter 覆盖索引数据。

- [x] **R16-F2: 修复过时注释** — 修正 Badges.tsx 中 "List view uses 10px" 为 "List view also uses 12px"。

- [x] **R16-F3: 修复 Playwright 配置** — 添加 `import path from 'path'` 和 `import { fileURLToPath } from 'url'`，计算 `__dirname`。`testDir` 改为 `path.resolve(__dirname, './tests')`。webServer 添加 `cwd: __dirname`。`package.json` 添加 `test:e2e:root` 脚本。

- [x] **R16-F4: R-probability 三档着色** — MemoryDetail 的 Access Freshness 区域使用绿色(R>50%)、琥珀色(10-50%)、红色(R<10%) 着色 R 值。

- [x] **R16-F5: 陈旧检测时降低 stability** — `resolve.py` 在 SInc 之前检测陈旧记忆，对它们的 stability 应用 0.90 衰减因子（下限 14.0）。`MemoryEntry` 添加 `stability_source` 字段追踪来源。

### 第二梯队：特性 — 全文搜索 + stability UI (C1-C2)

- [x] **R16-C1: 全文 body 搜索** — 搜索端点加载 `.md` 文件 body 内容并参与模糊匹配。匹配优先级：ID > summary > tag > body。搜索结果包含高亮 snippet（`<mark>` 标签封装匹配关键词）。

- [x] **R16-C2: 单条记忆 stability 滑块** — MemoryDetail 面板添加 stability 滑块（范围 1-365，步长 1）。拖动后设置 `stability_source: "manual"` 并持久化到 index.json。SInc 公式仅对 `stability_source != "manual"` 的记忆应用。

### 第三梯队：衰减表面 (S1-S3)

- [x] **R16-S1: Touch 端点** — 新增 `POST /api/memories/{id}/touch` 端点：更新 `last_access` 为当前时间、`days_since_last_access` 设为 0、若 stability_source 非 manual 则用 SInc 重算 stability。前端添加 Touch 按钮，点击后显示 ~600ms 对勾动画，"Last accessed" 变为 "just now"，R 值更新并着色为绿色。

- [x] **R16-S2: 搜索结果中显示访问新鲜度** — SearchBar 搜索结果条目内联显示 "X days ago" / "never" 和 R-probability 百分比（三档着色）。数据来自搜索 API 响应中的 `days_since_last_access` 和 `stability` 字段。

- [x] **R16-S3: List 视图健康列** — MemoryList 表格新增 "Health" 列：每行显示彩色水平条形（绿/琥珀/红）和 R 百分比数值。Health 列可排序（按 R 值降序——最有风险的排在最前）。点击健康指示器打开 MemoryDetail 面板。

### 第四梯队：批量 Polish (P1-P3)

- [x] **R16-P1: 移除 Wander 模式切换** — HelpPanel 移除 "cool" / "random" 模式切换 UI 和对应状态管理。默认使用 "cool" 模式。

- [x] **R16-P2: Resolve 按钮 tooltip** — SearchBar 搜索结果中的 "Resolve ->" 按钮添加 title 属性 "Resolve this memory's dependency graph into a structured context"。

- [x] **R16-P3: 上下文菜单快捷键提示** — App.tsx 的 ContextMenuItem 组件添加可选的 `shortcut` prop，右键菜单项显示快捷键提示（"Ctrl+D"、"Ctrl+R"、"Ctrl+E"、"Del"）。

### 第五梯队：延伸目标 (M1, A1)

- [x] **R16-M1: 可写 MCP 工具** — `mcp_server.py` 添加 `propose_memory` 和 `propose_update` 工具定义。`propose_memory` 创建 `maturity: draft` + `status: proposed` 的记忆；`propose_update` 以 `[PROPOSED]` 前缀提出更新。两个工具均非 readOnly。

- [x] **R16-A1: APIRouter 拆分** — `server.py` 从 ~1419 行缩减至 ~180 行（仅 app 创建、中间件、router 挂载和启动逻辑）。端点按业务域拆分为 3 个 router 模块：
  - `routers/memories.py`：8 个端点（GET list/by id/backlinks、POST create/update/import、DELETE、POST touch）
  - `routers/search.py`：3 个端点（GET graph、POST resolve、POST search）
  - `routers/stats.py`：6 个端点（GET stats、POST wander/validate/reindex、GET datasets、POST datasets/switch）
  - 共享代码提取至 `backend/shared.py`（helpers、Pydantic models、配置常量）

## 未完成的任务

无。全部 16 项任务完成。

## A1 bug 修复记录

APIRouter 拆分过程中发现并修复了 3 个错误：
1. **resolve 端点丢失结构化响应**：新 router 返回 `{"result": text}` 而非包含 `target`、`depth`、`budget`、`nodes`、`full_text`、`notices` 的结构化响应。修复：将完整的 resolve 解析逻辑从旧 server.py 移植到 routers/search.py。
2. **stats 端点键名不匹配**：router 返回 `"types"` 而非 `"type"`、`"statuses"` 而非 `"status"`，与 API 测试预期不符。修复：对齐键名。
3. **Vite build 失败**：App.tsx 第 1666 行存在重复的 `</button>` 闭合标签（P3 上下文菜单编辑的产物）。修复：移除重复标签。

## 验收命令输出

### TypeScript
```
cd frontend && npx tsc --noEmit
```
零错误，通过。

### Vite Build
```
cd frontend && npx vite build
```
```
✓ built in 362ms
dist/index.html                     0.48 kB │ gzip:   0.32 kB
dist/assets/index-UGWmOg9z.css     14.82 kB │ gzip:   3.97 kB
dist/assets/index-DxonBvg0.js   1,005.01 kB │ gzip: 300.65 kB
```
构建成功。

### Python 单元测试
```
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
```
**57/57 passed** (0.35s)

### Python 集成测试
```
PYTHONPATH=src python tests/integration_test.py
```
**24/24 passed**

### API 测试
```
PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short
```
**5/5 passed** (0.49s)

### CLI Overview
```
PYTHONPATH=src python -m codememory.cli --root examples/companion overview --limit 5
```
正确输出 top 5 记忆摘要，含 heat 分数、status、tags。

### Backend 端点 (curl)
```
GET  /api/stats    → 200 OK (total:12, type/status/maturity/tags 统计正确)
POST /api/search   → 200 OK (全文 body 匹配有效，返回 snippet 和 decay 字段)
GET  /docs         → 200 OK (OpenAPI Swagger UI 可访问)
```

### Playwright 冒烟测试
```
cd frontend && npx playwright test
```
**5/5 passed** (28.9s) — 零失败、零重试。

## 文件变更清单

| 文件 | 任务 |
|------|------|
| `backend/server.py` | A1: APIRouter 拆分 — 从 ~1419 行缩减至 ~180 行 |
| `backend/shared.py` | A1: 共享后端模块（新增） |
| `backend/routers/__init__.py` | A1: Router 包标记（新增） |
| `backend/routers/memories.py` | A1: 记忆 CRUD 路由（新增）+ F1: decay 字段修复 |
| `backend/routers/search.py` | A1: 搜索+解析路由（新增）+ C1: 全文 body 搜索 |
| `backend/routers/stats.py` | A1: 统计+工具路由（新增） |
| `src/codememory/models.py` | F5/C2: MemoryEntry 添加 `stability_source` 字段 |
| `src/codememory/resolve.py` | F5: 陈旧记忆 stability 衰减 + C2: manual stability 排除 |
| `src/codememory/search.py` | C1: 全文 body 搜索 + snippet 提取 |
| `src/codememory/mcp_server.py` | M1: `propose_memory` + `propose_update` 工具 |
| `frontend/src/App.tsx` | P3: 上下文菜单快捷键提示 + A1 bugfix: 移除重复 </button> |
| `frontend/src/components/Badges.tsx` | F2: 注释修正 |
| `frontend/src/components/MemoryDetail.tsx` | F4: R-probability 着色 + C2: stability 滑块 + S1: Touch 按钮 |
| `frontend/src/components/SearchBar.tsx` | C1: 高亮匹配 + S2: 访问新鲜度 + P2: Resolve tooltip |
| `frontend/src/components/MemoryList.tsx` | S3: Health 列 + 排序 |
| `frontend/src/components/HelpPanel.tsx` | P1: 移除 Wander 模式切换描述 |
| `frontend/playwright.config.ts` | F3: cwd 修复 |
| `frontend/package.json` | F3: test:e2e:root 脚本 |
| `frontend/src/types.ts` | C2: stability_source / UpdateMemoryRequest stability |
| `frontend/src/api.ts` | S1: touchMemory() 函数 + C2: stability 字段 |

## 测试总计

| 测试类型 | 通过 | 总计 |
|----------|------|------|
| Python 单元测试 | 57 | 57 |
| Python 集成测试 | 24 | 24 |
| API 测试 | 5 | 5 |
| Playwright 冒烟测试 | 5 | 5 |
| TypeScript 编译 | 0 errors | — |
| Vite 构建 | success | — |
| **合计** | **91** | **91** |

## 状态

**PASSED** — 16/16 任务完成，91/91 测试通过（57 unit + 24 integration + 5 API + 5 Playwright），TypeScript 零错误，Vite 构建成功，所有 Backend 端点正常，APIRouter 拆分完成。
