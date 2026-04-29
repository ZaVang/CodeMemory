# CodeMemory 后续路线图

> 设计哲学：记忆加载是依赖解析问题，不是搜索问题
> Layer 0 认知接口：`docs/layer0-cognitive-interface.md`

---

## 一、已完成

Phase 1-6 全部完成（10 个 Sprint）：

- **Phase 1-2**：原型验证 + 框架化 + Agent 自主维护 + 智能检索 + Layer 0 认知接口 + 集成发布
- **Phase 3**：代码质量 + 功能深化 + 测试体系（57+24）+ 多 provider 适配
- **Phase 4**：知识治理（maturity + log.md + evidence）+ 知识组织（semantic_type + resolve --focus + import）
- **Phase 5**：自动依赖推断（suggest-deps：三层过滤 + 双向推断）
- **Phase 6**：类型体系简化（atom/schema 两种，instance/composite 删除）

当前状态：15 个 CLI 命令，12 个 Sandbox 工具。

---

## 二、Phase 6：类型体系简化

> 核心问题：atom/instance/composite 三种类型结构几乎相同——
> instance = atom + schema + imports，composite = atom + imports（三种强度）。
> 区别不在文件结构，在 DAG 里的角色。而角色是网络位置决定的，不应该写死在 type 字段里。

### 2.1 设计理念：来自 Engram 的启发

```
Engram（companion-agent）           CodeMemory（新设计）
─────────────────────────          ─────────────────────
NeuronCell（基本单元）      ←→     atom（.md 文件，一个事实/决策/组合入口）
连接（A→B, B→A）           ←→     imports（显式声明依赖）
Engram（一组神经元+连接）   ←→     resolve 的输出（不是文件，是一次计算结果）
```

**关键是 engram 没有文件类型——它是激活扩散的结果。** resolve 已经在做同样的事：从一个入口 atom 出发，沿 imports 递归扩散，拓扑排序输出完整的因果上下文。

### 2.2 新类型体系

```
只保留两种：

  schema   — 模板。定义字段结构，不是记忆。
  atom     — 记忆。所有记忆的基础类型。

atom 的可选属性：
  schema      可选   — 有 = 遵守某个模板结构
  imports     可选   — 有 = 可以作为 resolve 入口
  intensity   必选   — 1-10，>=8 自动 protected
  maturity    自动   — draft/verified/proven
  tags        可选   — 包括语义类型（decision/guideline/pitfall/...）

删除的类型：
  instance    — 等价于 atom + schema + imports
  composite   — 等价于 atom + imports（三种强度）
```

创建时 LLM 只需写 `type: atom`。schema 和 imports 都是可选的、可后加的。

### 2.3 角色由数据决定，不由 type 决定

| 旧概念 | 旧定义 | 新定义 |
|--------|--------|--------|
| atom（原料） | `type: atom`，无 imports | 出度=0 的 atom |
| instance（菜品） | `type: instance`，有 schema + required imports | 有 schema 的 atom |
| composite（套餐入口） | `type: composite`，三种 imports 强度 | 有 imports 的 atom（尤其是被 snapshot 的） |
| "高层记忆" | 无 | user/snapshots/ 下的 atom，imports 记录了某次 resolve 的 DAG |

查找方式不依赖 type：

```bash
# 找到"原料"（无 imports 的记忆）
codememory orphans              # 入度为0 = 不被任何记忆引用

# 找到"入口"（有 imports 的记忆）
codememory search --has-imports

# 找到"高层记忆"（被 snapshot 固化的）
codememory search --tags snapshot
ls user/snapshots/

# 找到遵守模板的
codememory search --has-schema
```

### 2.4 完整的记忆生命周期

```
1. 散落的 atom（无 imports）
   user/facts/a.md    user/facts/b.md    user/facts/c.md
   像孤立的神经元

2. suggest-deps 发现连接
   → b imports a（a 解释了 b）
   → c imports a, b（c 依赖 a 和 b）
   建立了出向连接

3. resolve c
   → DAG：c → a → b（拓扑排序）
   这是一次临时的 engram——算出来的，不落盘

4. snapshot 固化
   → user/snapshots/2026-04-28-xxx.md
   这是一个 atom，它的 imports 记录了这次 resolve 的 DAG
   下次 resolve 这个 snapshot 就能复现整个上下文
```

**snapshot 产出的就是一个 atom——不是"composite 类型"，只是 imports 字段被填满的 atom。** 下次 resolve 它时，imports 递归展开，原样复现当时的完整上下文。

### 2.5 具体变更

| 文件 | 变更 |
|------|------|
| `models.py` | type 字段的允许值从 `atom\|instance\|composite\|schema` 改为 `atom\|schema` |
| `create.py` | 不再需要选 type（默认 atom）；不再生成 instance/composite 特有的空 imports 模板 |
| `validate.py` | 去掉"instance 必须有 schema"的检查；去掉"atom 不能有 imports"的限制 |
| `index.py` | reindex 时兼容旧数据（旧 type → 新 type 映射） |
| `resolve.py` | 去掉 `if type == "instance"` 等分支判断 |
| `search.py` | 添加 `--has-imports` / `--has-schema` 过滤器 |
| `handlers.py` | suggest-deps 对所有 atom 生效（不再检查 type） |
| `cli.py` | create 子命令去掉 `--type` 参数或默认 atom |
| `agent-memory-guide.md` | 更新原语选择规则 |
| `README.md` / `CLAUDE.md` / `architecture.md` / `INTEGRATION.md` | 同步更新 |

### 2.6 向后兼容

旧数据迁移规则：

```python
OLD_TYPE_MAP = {
    "atom":      "atom",
    "instance":  "atom",     # schema + imports 保留在文件中
    "composite": "atom",     # imports 保留在文件中
    "schema":    "schema",
}
```

reindex 时自动映射，旧 .md 文件无需修改 frontmatter（下次 update 时自然更新）。

### 2.7 验收

```bash
# type 体系
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='t/x', summary='s')
assert e.type == 'atom'
print('OK: atom only')
"

# 旧数据兼容：instance → atom
codememory --root examples/investment reindex
codememory --root examples/investment validate
# 预期：0 errors

# --has-imports 过滤
codememory --root examples/investment search --has-imports

# suggest-deps 对所有记忆生效
codememory --root examples/investment suggest-deps user/investment/semiconductor-thesis

# 全量回归
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
```

---

## 三、Phase 7：React 前端 + Backend API

> 目标：为 CodeMemory 搭建可视化界面。DAG 图展示记忆间的依赖关系——这是语义搜索类工具做不到的。

### 3.1 架构

```
浏览器 (React SPA)
    │
    ▼
FastAPI backend (:8000)          ← 薄壳，委托给现有 handlers
    │
    ▼
src/codememory/  (不变)          ← handlers.py / resolve.py / index.py ...
    │
    ▼
文件系统 (.md + index.json)
```

- **Backend**：FastAPI（与现有 Python 技术栈一致），只做 JSON 序列化 + 委托
- **Frontend**：React + TypeScript，图形库用 cytoscape 或 react-flow
- **不修改** `src/codememory/` 内部逻辑——backend 只是现有 handlers 的 HTTP 壳

### 3.2 Tier 1：DAG 图 + 记忆详情（MVP）

**目标：** 打开页面就看到记忆依赖图，点击节点查看详情。

**Backend 端点：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/memories` | 所有记忆列表（id, type, summary, tags, intensity, maturity） |
| GET | `/api/memories/{id}` | 单条记忆完整内容（frontmatter + body markdown） |
| GET | `/api/graph` | 节点 + 边数据（nodes: id/summary/directory/tags/intensity, edges: source/target/strength） |

**前端页面：**

- **主画布**：力导向 DAG 图
  - 节点颜色按目录（facts=蓝, preferences=绿, observations=橙, investment=紫, snapshots=灰）
  - 节点大小按 intensity（越大越重要）
  - 边样式按依赖强度（实线=required, 虚线=recommended, 点线=related）
  - 边带箭头表示依赖方向
- **侧面板**：点击节点 → 渲染 markdown body + frontmatter 元数据卡片
- **顶部搜索栏**：按 tag/目录/maturity 过滤，高亮匹配节点
- **图例**：目录颜色 + 边类型说明

**文件结构：**

```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
└── src/
    ├── App.tsx
    ├── api.ts              # fetch 封装
    ├── components/
    │   ├── GraphCanvas.tsx  # DAG 主画布
    │   ├── MemoryDetail.tsx # 侧边详情面板
    │   ├── SearchBar.tsx    # 搜索/过滤
    │   └── Legend.tsx       # 图例
    └── types.ts            # TypeScript 类型定义

backend/
├── server.py               # FastAPI app + 路由
└── requirements.txt        # fastapi, uvicorn
```

### 3.3 Tier 2：交互式 Resolve

**目标：** 在图上动态展示依赖解析过程。

**Backend 端点：**

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/resolve` | body: `{id, depth, budget}` → 返回拓扑排序后的节点列表 + 每个节点的裁剪级别 |

**前端交互：**

- 任意节点右键 / 按钮 → "从此节点 Resolve"
- 动画展示拓扑遍历顺序（节点依次高亮，显示加载顺序）
- **Token budget 滑块**：拖动时实时看到节点在 "full body" ↔ "summary only" 之间切换（裁剪的节点变灰/折叠）
- Focus 模式：选择一个决策节点，其他节点自动折叠为 summary

### 3.4 Tier 3：管理面板

**目标：** 在 UI 中完成记忆的增删改查 + 系统健康检查。

**Backend 端点：**

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/memories` | 创建新记忆 |
| PUT | `/api/memories/{id}` | 更新记忆 |
| GET | `/api/stats` | 统计（总数、maturity 分布、stale 数量、tag 分布） |
| POST | `/api/wander` | 触发 wander，返回一条冷记忆 |
| POST | `/api/validate` | 运行 validate，返回诊断结果 |

**前端页面：**

- **Dashboard 页**：统计卡片（总记忆数、stale 数、maturity 分布饼图、tag 词云）
- **创建/编辑表单**：markdown 编辑器 + frontmatter 字段表单
- **Stale 热力图**：按目录分组，高亮 stale 记忆
- **Wander 按钮**：点击随机激活一条冷记忆，展示在弹窗中

### 3.5 任务拆分

```
Phase 7 — Sprint 11: Backend API + Tier 1 MVP
  [ ] 7.1  创建 frontend/ 项目脚手架（Vite + React + TypeScript）
  [ ] 7.2  创建 backend/server.py FastAPI 应用 + CORS
  [ ] 7.3  GET /api/memories + GET /api/memories/{id}
  [ ] 7.4  GET /api/graph（从 index.json 构建节点+边）
  [ ] 7.5  GraphCanvas 组件（cytoscape/react-flow 力导向图）
  [ ] 7.6  MemoryDetail 侧面板（markdown 渲染 + 元数据卡片）
  [ ] 7.7  SearchBar + Legend 组件
  [ ] 7.8  验收：页面加载 → 看到 DAG 图 → 点击节点 → 看到详情

Phase 7 — Sprint 12: Interactive Resolve (Tier 2)
  [ ] 7.9  POST /api/resolve 端点
  [ ] 7.10 图上 resolve 交互（右键 → 拓扑动画）
  [ ] 7.11 Token budget 滑块 + 节点裁剪可视化
  [ ] 7.12 验收：拖动 budget → 节点折叠/展开

Phase 7 — Sprint 13: Management Dashboard (Tier 3)
  [ ] 7.13 POST /api/memories + PUT /api/memories/{id}
  [ ] 7.14 GET /api/stats + POST /api/wander + POST /api/validate
  [ ] 7.15 Dashboard 页面（统计卡片 + 饼图 + 词云）
  [ ] 7.16 记忆创建/编辑表单
  [ ] 7.17 Stale 记忆高亮 + Wander 按钮
  [ ] 7.18 验收：全功能可用的管理工具
```

### 3.6 技术选型

| 层 | 选择 | 理由 |
|----|------|------|
| 图可视化 | cytoscape + dagre | 学术级图算法，支持分层/力导向切换 |
| Markdown 渲染 | react-markdown + remark-gfm | 轻量，支持 GFM |
| 图表 | recharts | React-native，简单够用 |
| 构建 | Vite | 快 |
| Backend | FastAPI + uvicorn | 与现有 Python 栈一致 |
| CSS | Tailwind CSS | 原子类，组件不多时最快 |
| 设计系统 | Claude（docs/design/claude-DESIGN.md） | 书卷感、温暖知性，契合记忆管理工具 |

### 3.6.1 设计系统映射

基于 Claude 设计系统，CodeMemory 专属配色映射：

**目录 → 节点颜色（图节点）：**

| 目录 | 色值 | 理由 |
|------|------|------|
| `facts/` | `#141413` 近黑 | 事实是基石，最重 |
| `preferences/` | `#c96442` 赤陶 | 偏好有温度 |
| `observations/` | `#d97757` 珊瑚 | 观察是流动的 |
| `investment/` | `#3898ec` 专注蓝 | 决策需冷静，唯一冷色 |
| `snapshots/` | `#87867f` 灰 | 快照是凝固的时间 |
| 其他域 | `#e8e6dc` 暖沙 | 默认中性 |

**依赖边样式：**

| 强度 | 样式 | 颜色 |
|------|------|------|
| required | 实线 2px | `#141413` |
| recommended | 虚线 1.5px | `#87867f` |
| related | 点线 1px | `#e8e6dc` |

**节点大小（按 intensity）：**

| intensity | 大小 | 效果 |
|-----------|------|------|
| 1-3 | 小 (24px) | 临时信息 |
| 4-6 | 中 (32px) | 常规记忆 |
| 7-9 | 大 (40px) | 重要判断 |
| 10 | 最大 (48px) | ring shadow 光环 |

**状态徽章：**

| maturity | 样式 |
|----------|------|
| draft | Sand 底 + `#87867f` 字 |
| verified | `#3898ec/15%` 底 + `#3898ec` 字 |
| proven | `#22c55e/15%` 底 + `#22c55e` 字 |
| stale | `#b53333/15%` 底 + `#b53333` 字 |

**图布局切换：**
- 默认：Dagre 分层布局（自上而下，展示依赖方向）
- 可切换：力导向布局（探索性浏览）
- 切换按钮在画布工具栏

**字体：** Georgia（标题）、Inter（正文）、SF Mono（代码）

**底色：** `#f5f4ed` Parchment（页面）、`#faf9f5` Ivory（卡片/侧面板）

### 3.7 验收命令

```bash
# Backend 启动
cd backend && uvicorn server:app --reload

# Frontend 启动
cd frontend && npm run dev

# 集成验证
curl http://localhost:8000/api/memories | jq 'length'
curl http://localhost:8000/api/graph | jq '.nodes | length'
curl -X POST http://localhost:8000/api/resolve \
  -H "Content-Type: application/json" \
  -d '{"id":"user/investment/context","depth":"required","budget":2000}'
```

---

## 四、时间线

```
已完成 ─── Phase 1-6 (全部 10 个 Sprint)

当前     ─── Phase 7: React 前端 + Backend API (Sprint 11-13)
            ├── Sprint 11: Backend API + Tier 1 DAG 图 + 详情
            ├── Sprint 12: 交互式 Resolve
            └── Sprint 13: 管理面板

待开始   ─── Phase 8+: (待定)
```

---

## 五、风险与缓解

| 风险 | 缓解 |
|------|------|
| 旧数据迁移后 validate 规则变化导致误报 | 去掉 instance/composite 特有检查，validate 规则变少（更宽松），不会新增误报 |
| 现有测试依赖旧 type 值 | reindex 自动映射 `instance→atom`、`composite→atom`；测试预期同步更新 |
| LLM 在没有 type 指引时困惑 | agent-memory-guide.md 更新为"用 imports/schema/tags 表达角色，不靠 type" |
| schema 字段在旧 instance 文件中丢失 | 旧 instance 的 frontmatter 中 `schema:` 字段保持不变，reindex 正常读取 |
| Frontend 引入新语言栈（TypeScript）增加维护面 | Backend 只做薄壳委托，核心逻辑仍在 Python；前端不碰记忆引擎 |
| 图可视化在大数据量下性能下降 | 默认只展示 required 边，分页加载 recommended/related；节点数 < 500 时不会有问题 |
| backend 直接读文件系统可能有并发写风险 | FastAPI 单线程 async，所有写操作走现有 handlers（已有文件锁保护） |
