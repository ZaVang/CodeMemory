# Sprint 11 — Backend API + DAG 图前端 MVP

> **起始日期**：2026-04-29
> **前置条件**：Sprint 10 完成（类型体系简化）
> **目标**：搭建 FastAPI backend + React 前端，实现 DAG 依赖图可视化 + 记忆详情面板

---

## 一、任务

### 任务 1：项目脚手架

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 1.1 | 创建 `frontend/` 项目 | Vite + React + TypeScript + Tailwind CSS | [x] |
| 1.2 | 安装依赖 | cytoscape, dagre, react-markdown, remark-gfm | [x] |
| 1.3 | 创建 `backend/` | FastAPI + uvicorn + CORS | [x] |
| 1.4 | Tailwind 配置 | 按 Claude 设计系统的颜色/字体/间距 | [x] |

**产出**：两个可启动的空项目骨架

---

### 任务 2：Backend API 端点

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 2.1 | `GET /api/memories` | 返回所有记忆列表（id, type, summary, tags, intensity, maturity, directory） | [x] |
| 2.2 | `GET /api/memories/{id}` | 返回单条记忆完整内容（frontmatter 所有字段 + body markdown） | [x] |
| 2.3 | `GET /api/graph` | 从 index.json 构建 cytoscape 格式的节点+边数据 | [x] |

**产出**：3 个 REST 端点，通过 curl 可验证

---

### 任务 3：DAG 图可视化

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 3.1 | `api.ts` | fetch 封装层，对接 backend 三个端点 | [x] |
| 3.2 | `GraphCanvas.tsx` | cytoscape 力导向图组件，节点颜色按目录、大小按 intensity、边样式按依赖强度 | [x] |
| 3.3 | `Legend.tsx` | 图例：目录颜色 + 边类型说明 | [x] |
| 3.4 | 布局切换 | 默认 Dagre 分层布局，工具栏按钮切换力导向 | [x] |

**产出**：页面加载 → 看到 DAG 依赖图

---

### 任务 4：记忆详情 + 搜索

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 4.1 | `MemoryDetail.tsx` | 侧边面板：点击节点 → 渲染 markdown body + frontmatter 元数据卡片（Claude 风格卡片，whisper shadow） | [x] |
| 4.2 | `SearchBar.tsx` | 顶部搜索栏：按 tag/目录/maturity 过滤，高亮匹配节点 | [x] |
| 4.3 | `App.tsx` | 主布局：左侧画布 + 右侧详情面板 + 顶部搜索栏 | [x] |

**产出**：完整的 MVP 交互流

---

## 二、技术约束

- 后端只读 `index.json` 和 `.md` 文件，不修改 `src/codememory/` 内部逻辑
- 设计系统：`docs/design/claude-DESIGN.md`（Parchment 底色、Georgia/Inter 字体、whisper shadow、ring shadow）
- 配色映射：facts→#141413, preferences→#c96442, observations→#d97757, investment→#3898ec, snapshots→#87867f
- 边样式：required=实线2px #141413, recommended=虚线1.5px #87867f, related=点线1px #e8e6dc
- 一切按 Claude 设计系统的 Do's and Don'ts（无纯黑 #000、无纯白 #fff 底色、少用赤陶主色、serif 标题）
- 状态徽章按 Claude 设计系统：draft=Sand底+灰字, verified=蓝底+蓝字, proven=绿底+绿字, stale=红底+红字

---

## 三、文件结构

```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── index.html
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── index.css
    ├── api.ts
    ├── types.ts
    └── components/
        ├── GraphCanvas.tsx
        ├── MemoryDetail.tsx
        ├── SearchBar.tsx
        └── Legend.tsx

backend/
├── server.py
└── requirements.txt
```

---

## 四、验收命令汇总

```bash
# Backend 启动
cd backend && pip install -r requirements.txt && uvicorn server:app --reload

# 端点验证
curl http://localhost:8000/api/memories | python -m json.tool
curl http://localhost:8000/api/memories/user/investment/context | python -m json.tool
curl http://localhost:8000/api/graph | python -m json.tool

# Frontend 启动
cd frontend && npm install && npm run dev

# TypeScript 类型检查
cd frontend && npx tsc --noEmit

# 全量回归（确保现有功能不受影响）
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
```

---

## 五、完成定义

1. `backend/server.py` 启动，3 个端点返回正确 JSON
2. `frontend/` 启动，页面加载后显示 DAG 依赖图
3. 节点颜色按目录区分、大小按 intensity、边样式按依赖强度
4. 点击节点 → 侧面板显示 markdown body + frontmatter 元数据
5. 搜索栏可按 tag 过滤，高亮匹配节点
6. 布局可在 Dagre 分层 / 力导向之间切换
7. 配色/字体/阴影遵循 Claude 设计系统
8. 现有 57+24 测试不退化
