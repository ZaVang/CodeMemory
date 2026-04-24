# CodeMemory — 记忆原子化协议

将 AI 记忆拆分为可依赖解析的原子单元。核心理念：**记忆加载是依赖解析问题，不是搜索问题。**

## 文件架构

```
CodeMemory/
├── bin/
│   ├── codememory.py         # Python CLI（核心实现，单文件）
│   ├── codememory             # bash wrapper
│   └── codememory.ps1         # PowerShell wrapper
├── user/                      # 用户记忆（按主题域组织）
├── self/                      # AI 内部记忆（思考、调试等）
│   └── thoughts/
├── schemas/                   # Schema 定义（template 类型记忆）
├── .codememory/
│   └── index.json             # 自动生成的索引（可重建）
├── docs/
│   ├── architecture.md        # 系统架构
│   ├── plans/                 # Sprint 计划
│   └── pitfalls.md            # 陷阱知识库
├── prd.md                     # 产品需求文档
├── README.md
└── .claude/                   # Claude Code 配置
```

## 核心概念

### 四种记忆原语

| 类型 | 含义 | 可被引用？ | 有 imports？ |
|------|------|-----------|-------------|
| **atom** | 原子事实（不可再分） | 是 | 否 |
| **instance** | 具体决策/事件（依附 schema） | 是 | 是（required） |
| **composite** | 组合包（引用其他记忆） | 是 | 是（required/recommended/related） |
| **schema** | 元模板（定义 instance 结构） | 是（instance 通过 schema 字段引用） | 否 |

### 关键设计决策

- 记忆加载是 DAG 解析问题，不是 vector search
- 每个 .md 文件 = 一个记忆单元（YAML frontmatter + Markdown body）
- 依赖通过 frontmatter 的 `imports` 显式声明，不靠语义相似度猜测
- Token 预算裁剪：超预算时 required 节点降级为 summary，非 required 节点跳过

## CLI 参考

```bash
# 创建记忆
python bin/codememory.py create --type atom --id user/investment/my-thesis

# 重建索引（新增/修改/删除记忆后）
python bin/codememory.py reindex

# 解析并输出上下文
python bin/codememory.py resolve user/investment/context --depth required

# 完整性验证
python bin/codememory.py validate
```

## 代码规范

### 技术栈
- Python 3.13+，唯一外部依赖 `pyyaml`
- 单文件实现（`bin/codememory.py`），不超过 500 行
- 原型阶段：token 估算用 `len(text)` 近似

### 编码约定
- 所有函数类型注解覆盖公共接口
- 错误输出到 `sys.stderr`，正常输出到 `sys.stdout`
- frontmatter 修改不触发 stale（基于 body hash）
- 无外部 API 调用，无需 async
- 原型阶段用 `print()` 而非 `logging`

### 修改原则
- 最小变更：只改与任务直接相关的代码
- 不引入新依赖：除非有充分理由
- 保持单文件结构：新功能优先在现有文件中实现
- 先验证再提交：改代码后运行 `validate` + `resolve` 确认

## 测试规范

- 手工验证为主：`validate` → `resolve` → 检查输出
- 边界测试：循环依赖、断链、空记忆、超大预算/零预算
- 原型阶段无自动化测试框架要求
- 验证命令：
  ```bash
  python bin/codememory.py validate
  python bin/codememory.py resolve user/investment/context
  python bin/codememory.py resolve user/investment/context --budget 500
  ```
