# CodeMemory 用户指南

> 最后更新：2026-05-08

## 一、这是什么？

CodeMemory 是一个 **AI 记忆管理系统**——帮你和 AI Agent 建立共用的结构化长期记忆。

核心理念：**记忆加载是依赖解析问题，不是搜索问题。** 传统搜索可能找到相关片段但丢失因果链；CodeMemory 通过显式依赖图（DAG）保证上下文完整。

### 两种使用方式

| 方式 | 适用场景 | 入口 |
|------|---------|------|
| **Web UI** | 浏览、创建、编辑、可视化 | `./bin/dev` → http://localhost:5300 |
| **CLI** | 脚本、Agent 集成、批量操作 | `codememory <command>` |
| **MCP Server** | AI Agent 直接调用 | 配置到 Claude Code / Cursor 等 |

---

## 二、快速开始

### 1. 启动

```bash
git clone https://github.com/ZaVang/CodeMemory.git
cd CodeMemory
pip install -e .

# 一键启动
./bin/dev
```

浏览器打开 http://localhost:5300 ，首次访问会看到 Onboarding 引导。

### 2. 界面概览

三个主视图，按 `1` `2` `3` 切换：

| 视图 | 快捷键 | 用途 |
|------|--------|------|
| **Graph** | `1` | DAG 可视化，节点颜色按目录区分，右键可 Edit/Resolve/Delete |
| **List** | `2` | 表格式浏览，按列排序，Health 列显示衰减风险 |
| **Dashboard** | `3` | 统计卡片、stale 检测、Wander 漫游、Validate 验证 |

### 3. 核心操作

| 操作 | 方式 |
|------|------|
| 创建记忆 | 点击 `+ Create Memory` 或 `Ctrl+N` |
| 编辑记忆 | 右键节点 → Edit，或 List 中点击 |
| 解析依赖 | 选中记忆 → Resolve，或右键 → Resolve |
| 搜索 | `Ctrl+K` 聚焦搜索栏 |
| 切换数据集 | 顶部下拉框选择 |

---

## 三、记忆格式

每条记忆是一个 Markdown 文件，以 YAML frontmatter 开头：

```yaml
---
type: atom                          # atom 或 schema
id: user/investment/my-thesis       # 全局唯一 ID，"/" 分隔层级
summary: AI存储+AI制造双核心驱动     # 用于检索预览和 token 裁剪降级
tags: [investment, thesis]          # 标签
intensity: 7                        # 1-10，影响图节点大小和裁剪优先级
status: active                      # active / archived / draft
maturity: proven                    # draft / verified / proven / superseded
stability: 90.0                     # 半衰期（天），默认 14.0，decision 类型默认 90
imports:                            # 显式依赖声明
  required: [user/investment/context]
  recommended: [user/investment/risk-tolerance]
  related: []
---
# Memory body（Markdown 正文）
```

### 核心字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | 是 | `atom`（通用记忆）或 `schema`（元模板） |
| `id` | 是 | 全局唯一 ID，含 "/" 分隔符，如 `user/investment/context` |
| `summary` | 是 | 一句话摘要，token 预算不足时替代 body |
| `imports` | 否 | 依赖图的核心——显式声明"这条记忆依赖哪些其他记忆" |

---

## 四、依赖图（DAG）

CodeMemory 区别于其他记忆系统的核心能力：

```
user/investment/semiconductor-thesis (atom)
├── required → user/investment/context       ← 必须加载
├── required → user/facts/semiconductor      ← 必须加载
├── recommended → user/investment/risk-tolerance  ← 预算充足时加载
└── related → user/observations/market-event      ← 可选参考
```

### import 强度

| 强度 | Resolve 行为 |
|------|-------------|
| `required` | 始终加载 |
| `recommended` | `--depth recommended` 时加载 |
| `related` | `--depth full` 时加载 |

---

## 五、时间衰减

系统自动追踪每条记忆的访问时间并计算检索概率：

```
R = max(0.5^(days/stability), long_term_floor)
```

- **stability**：每记忆可调，默认 14 天，可通过 UI 滑块或 API 修改
- **自适应增长**：Resolve 访问时 stability 自动增加（间隔效应）
- **长期保留底线**：90 天后的知识不会静默消失
- **Touch**：轻量衰减刷新（不触发 DAG 加载）
- **R-probability 着色**：MemoryDetail 和 List 视图中绿色(>50%) / 琥珀(10-50%) / 红色(<10%)

---

## 六、CLI 命令

```bash
# 一键启动
./bin/dev

# 扫视 — 启动时自动注入 top 5 相关记忆
codememory overview --tags "investment"

# 重构 — DAG 拓扑拼装 + token 裁剪
codememory resolve user/investment/context --budget 2000

# 注视 — 动态切换记忆分辨率
codememory focus risk-tolerance --level full

# 触景生情 — 随机激活冷记忆
codememory wander

# 创建 / 更新
codememory create --id user/ideas/new-idea --summary "..."
codememory update user/ideas/new-idea --body "..."

# 索引 / 验证 / 搜索
codememory reindex
codememory validate
codememory search --query "semiconductor"

# 导入
codememory import --file notes.txt --extract preferences
codememory skeletonize ./my-notes/ --min-intensity 5   # 从 Markdown 文件批量导入

# 依赖推断
codememory suggest-deps user/investment/context
```

---

## 七、MCP Server

在 Claude Code 或其他 MCP 客户端中配置：

```json
{
  "codememory": {
    "command": "python",
    "args": ["-m", "codememory.mcp_server"]
  }
}
```

7 个工具：`resolve_memory` / `overview` / `wander` / `focus` / `snapshot` / `propose_memory` / `propose_update`

---

## 八、与其他方案对比

| 方案 | 检索方式 | 因果完整性 | 版本控制 | 衰减管理 |
|------|---------|-----------|---------|---------|
| 普通笔记 | 全文搜索 | 无 | Git | 无 |
| RAG | 语义相似度 | 无保证 | 无 | 无 |
| 知识图谱 | 图遍历 | 有 | 无 | 无 |
| **CodeMemory** | **DAG 拓扑** | **有** | **Git + version** | **stability + SInc** |

---

## 九、提示与快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+K` | 搜索 |
| `Ctrl+N` | 新建记忆 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Shift+D` | 切换亮色/暗色模式 |
| `Ctrl+Shift+C` | Copy as Context（Resolve 后可用） |
| `1` / `2` / `3` | 切换 Graph / List / Dashboard |
| `?` | 快捷键参考 |
| `Esc` | 关闭面板 / 模态
