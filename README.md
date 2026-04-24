# CodeMemory

**记忆原子化协议** — 将 AI 记忆拆分为可依赖解析的原子单元。

记忆加载是依赖解析问题，不是搜索问题。CodeMemory 用显式依赖图（DAG）替代语义相似度检索，保证加载的上下文因果完整。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 重建索引
python bin/codememory.py reindex

# 验证完整性
python bin/codememory.py validate

# 加载投资决策上下文
python bin/codememory.py resolve user/investment/context
```

## 核心概念

记忆被拆分为四种**原语**：

| 类型 | 说明 | 示例 |
|------|------|------|
| **atom** | 不可再分的原子事实 | 投资主线、风险偏好、持仓明细 |
| **instance** | 依附 schema 的决策/事件 | "2月买入半导体ETF"决策 |
| **composite** | 组合其他记忆的上下文包 | "投资决策完整上下文" |
| **schema** | 定义 instance 结构的模板 | "决策模板"（what/why/when/confidence） |

每个记忆是一个 Markdown 文件（YAML frontmatter + body），通过 `imports` 显式声明依赖关系。

## CLI 命令

```bash
# 创建新记忆
python bin/codememory.py create --type atom --id user/ideas/my-idea

# 重建索引
python bin/codememory.py reindex

# 解析上下文（拓扑排序加载）
python bin/codememory.py resolve <memory-id> [--depth required|recommended|full] [--budget N]

# 完整性检查（循环检测 + 断链 + schema 合规）
python bin/codememory.py validate
```

## 目录结构

```
user/          # 用户记忆（按主题域组织）
self/          # AI 内部记忆
schemas/       # Schema 定义
.codememory/   # 自动生成的索引（index.json）
bin/           # CLI 实现 + shell wrappers
docs/          # 架构文档 + 计划
```

## 文档

- [架构设计](docs/architecture.md)
- [产品需求文档](prd.md)

## 许可证

MIT — 详见 [LICENSE](LICENSE)
