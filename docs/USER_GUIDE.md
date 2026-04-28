# CodeMemory 用户指南：构建你的 AI 长期记忆库

## 为什么需要这个？

### 问题：AI 总是"健忘"

你有没有经历过：

- 问 AI "上次我们讨论的方案是什么？"，它说不知道
- AI 给出的建议和你之前的决策冲突
- 每次新对话都要重新解释背景
- AI 的回答前后不一致，没有连续性

**根本原因**：AI 没有长期记忆，每次对话都是"第一次见面"。

### 解决方案：把记忆变成代码

CodeMemory 把你的记忆变成一个 **Git 项目**：

```
your-memory/
├── .codememory/
│   ├── index.json    # 记忆索引
│   └── log.md        # 变更日志
├── preferences/      # 你的偏好
│   └── coding-style.md
├── decisions/        # 你的决策
│   └── tech-stack.md
├── projects/         # 项目记忆
│   └── my-app.md
└── knowledge/        # 知识积累
    └── best-practices.md
```

**核心思想**：
- 记忆是 **版本控制的**（可以回溯）
- 记忆是 **结构化的**（不是随意文本）
- 记忆是 **有因果链的**（决策依赖上下文）

---

## 它能做什么？

### 1. 记住你的偏好

```yaml
---
type: atom
id: preferences/coding-style
summary: 编码偏好：函数式优先，测试驱动
tags: [coding, preference]
intensity: 8
---
# 编码风格偏好

- 函数式编程优先，避免可变状态
- 测试先行，覆盖率 > 80%
- 变量命名：snake_case，函数：camelCase
```

下次 AI 写代码时，自动参考这个偏好。

### 2. 追溯决策因果

```yaml
---
type: instance
id: decisions/tech-stack
summary: 选择 React + TypeScript 作为前端技术栈
tags: [decision, frontend]
imports:
  required:
    - preferences/coding-style
    - context/team-skill
---
# 技术选型：React + TypeScript

## 决策
选择 React + TypeScript 作为前端技术栈。

## 理由
1. 团队熟悉 React（见 team-skill）
2. TypeScript 符合类型安全偏好（见 coding-style）
3. 生态成熟，问题容易解决

## 结论
2026-01-15 决定，暂不重新评估。
```

**关键**：`imports` 字段让 AI 知道"为什么这样决策"。

### 3. 自动推断依赖

```bash
# 创建新记忆时，系统自动建议相关记忆
codememory suggest-deps decisions/new-choice

# 输出：
# Score  Class        ID
# ─────  ───────────  ─────────────────────
#     8  required     preferences/coding-style
#     6  recommended  decisions/tech-stack
#     4  related      context/team-skill
```

### 4. 智能检索

```bash
# 召回完整因果链
codememory resolve decisions/tech-stack

# 输出会自动包含：
# 1. tech-stack 本身
# 2. coding-style（被引用的偏好）
# 3. team-skill（被引用的上下文）
```

---

## 快速开始

### 第一步：安装

```bash
git clone https://github.com/ZaVang/CodeMemory.git
cd CodeMemory
pip install -e .
```

### 第二步：创建你的记忆库

```bash
# 创建记忆目录
mkdir -p my-memory/preferences
mkdir -p my-memory/decisions
mkdir -p my-memory/projects

# 初始化
codememory --root my-memory reindex
```

### 第三步：写第一条记忆

```bash
# 创建偏好文件
cat > my-memory/preferences/coding-style.md << 'YAML'
---
type: atom
id: preferences/coding-style
summary: 我的编码偏好
tags: [coding, preference]
intensity: 8
---
# 编码风格

- 使用 Python，偏好函数式风格
- 测试驱动开发
- 文档先行
YAML

# 重新索引
codememory --root my-memory reindex
```

### 第四步：验证

```bash
# 查看记忆概览
codememory --root my-memory overview

# 验证结构
codememory --root my-memory validate
```

---

## 核心概念

### 四种记忆类型

| 类型 | 用途 | 示例 |
|------|------|------|
| **atom** | 原子事实 | 偏好、知识、约束 |
| **instance** | 具体实例 | 决策、事件、经验 |
| **composite** | 组合上下文 | 项目背景、问题域 |
| **schema** | 模板定义 | 决策模板、分析框架 |

### 字段说明

```yaml
---
type: atom              # 记忆类型
id: preferences/style   # 唯一标识
summary: 一句话摘要      # 用于检索和预览
tags: [tag1, tag2]      # 标签，用于分类和推断
intensity: 7            # 重要性 1-10，越高越不容易被裁剪
status: active          # active / archived / superseded
version: 1              # 版本号，update 时自动递增
imports:                # 依赖的其他记忆
  required: [id1]       # 必须加载
  recommended: [id2]    # 预算充足时加载
  related: [id3]        # 可选参考
---
```

### 关键命令

| 命令 | 用途 |
|------|------|
| `create` | 创建新记忆 |
| `update` | 更新记忆（自动版本化） |
| `resolve` | 召回记忆 + 依赖链 |
| `search` | 搜索记忆 |
| `suggest-deps` | 推断依赖关系 |
| `validate` | 检查循环依赖、断链 |
| `overview` | 查看记忆库概况 |

---

## 为什么这个方案好？

### 1. 记忆是版本控制的

每次更新都会生成新版本，你可以：

```bash
# 查看历史版本
codememory --root my-memory focus preferences/style --versions

# 回溯到特定版本
codememory --root my-memory resolve preferences/style@v2
```

**好处**：决策可以追溯，不会丢失历史。

### 2. 记忆是有因果链的

传统笔记是孤立的，CodeMemory 的记忆有 `imports`：

```
决策（instance）
├── 依赖 → 偏好（atom）
├── 依赖 → 上下文（composite）
└── 依赖 → 之前的决策（instance）
```

**好处**：AI 回答问题时能理解完整背景，而不是只看到孤立信息。

### 3. 记忆是自动治理的

系统会：

- **自动推断依赖**：`suggest-deps` 告诉你该关联哪些记忆
- **自动升级成熟度**：高频使用的记忆从 draft → verified → proven
- **自动检测问题**：循环依赖、断链、孤立记忆

**好处**：不需要手动维护，记忆库自己会"整理"。

### 4. 记忆是可迁移的

整个记忆库就是一个 Git 仓库：

- 可以备份到 GitHub
- 可以在不同机器间同步
- 可以分享给团队

**好处**：不依赖特定平台，你的记忆永远属于你。

---

## 实际使用场景

### 场景 1：项目知识管理

```
projects/my-app/
├── context.md          # 项目背景
├── architecture.md     # 架构决策
├── api-design.md       # API 设计
└── lessons-learned.md  # 经验教训
```

每次讨论项目时，AI 自动加载完整上下文。

### 场景 2：个人知识库

```
knowledge/
├── coding/
│   ├── best-practices.md
│   └── design-patterns.md
├── productivity/
│   ├── time-management.md
│   └── note-taking.md
└── learning/
    └── language-learning.md
```

构建你自己的"第二大脑"。

### 场景 3：团队协作

团队共享一个记忆库：

```
team-memory/
├── conventions/        # 团队规范
├── decisions/          # 架构决策记录（ADR）
└── onboarding/         # 新成员入职知识
```

新成员入职时，AI 自动加载团队上下文。

---

## 与其他方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **普通笔记** | 灵活 | 孤立、无结构、AI 难以理解 |
| **知识图谱** | 关联强 | 维护成本高、学习曲线陡 |
| **RAG 文档库** | AI 可检索 | 无因果链、无版本控制 |
| **CodeMemory** | 结构化 + 因果链 + 版本控制 | 需要学习 YAML 格式 |

---

## 下一步

1. **创建你的第一个记忆库**
2. **导入现有笔记**（使用 `import` 命令）
3. **在日常对话中让 AI 参考**
4. **定期 `validate` 和 `reindex`**

---

## 常见问题

### Q: 我需要写很多 YAML 吗？

A: 核心字段只有 `type`、`id`、`summary`，其他都是可选的。熟练后 1 分钟就能写一条记忆。

### Q: 记忆库会不会太大？

A: 系统会自动裁剪。`resolve --budget 1000` 只召回最重要的记忆，预算不足时自动降级。

### Q: 如何让 AI 使用记忆库？

A: 在对话开始时运行 `codememory resolve <id>`，把输出交给 AI 作为上下文。或者集成到你的 Agent 工具中。

### Q: 记忆会冲突吗？

A: 系统会检测循环依赖和断链。冲突的记忆会标记为 `stale`，提示你更新。

---

**开始构建你的 AI 长期记忆库吧！** 🚀

记住：好的记忆 = 好的 AI 助手。
