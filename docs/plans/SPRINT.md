# Sprint 9 — 自动依赖推断 ✅

> **起始日期**：2026-04-28
> **前置条件**：Sprint 8 完成（Phase 4A + 4B：知识治理 + 知识组织）
> **目标**：实现 `suggest-deps` 命令——基于标签 + Schema 模式的三层过滤算法，输出正向+反向候选依赖列表，零新依赖
> **状态**：已完成

---

## 一、任务

### 任务 1：suggest-deps 命令 ✅

**新增 `suggest-deps` 命令，帮助 LLM/用户判断新记忆应该 import 哪些已有记忆。**

| # | 子任务 | 说明 |
|---|--------|------|
| 1.1 | `suggest_deps.py` ✅ | 三层过滤算法：标签交集评分 → Schema 结构模式统计 → 热度加权排序。`score = tag_overlap * 3 + schema_pattern_score * 5 + dependents` |
| 1.2 | 正向推断 ✅ | 输出"新记忆该 import 谁"的候选列表，按 required/recommended/related 分类（根据 score 阈值） |
| 1.3 | 反向推断 ✅ | 输出"谁该 import 新记忆"的候选列表。启发式：候选记忆在同标签领域缺少 imports（孤立的果），新记忆覆盖了该缺口 |
| 1.4 | CLI ✅ | `suggest-deps` 子命令：`--min-score N`（默认 3）、`--dry-run`（默认行为）、`--forward-only`、`--retroactive-only` |
| 1.5 | handlers.py ✅ | `handle_suggest_deps(root, args)` 委托 suggest_deps.py |

**产出**：新增 `suggest_deps.py`，修改 `cli.py`、`handlers.py`

**算法细节**：

```
Layer 1: 标签交集评分
  新记忆 tags 与每条已有记忆 tags 的交集数 → 交集 >= 1 进入候选池

Layer 2: Schema 结构模式
  如果新记忆 type=instance + schema=schemas/decision：
    找所有同 schema 的 instance，统计它们最常 import 哪些记忆
    高频被引用的记忆获得加分（每被一个同 schema 的 instance 引用 +1）
  如果新记忆 type=composite：
    找所有 composite，统计常见 required imports

Layer 3: 热度加权
  score = tag_overlap * 3 + schema_pattern_score * 5 + dependents
  按 score 降序输出

反向推断：
  候选记忆 C 在同标签领域缺少 imports（has_same_domain_deps == False）
  且 tag_overlap >= 2 → 标记为 retroactive 候选
```

---

## 二、文件变更总览

```
新增：
  src/codememory/suggest_deps.py    # 依赖推断逻辑（~120 行）

修改：
  src/codememory/cli.py             # + suggest-deps 子命令
  src/codememory/handlers.py        # + handle_suggest_deps

不修改：
  src/codememory/ 其余模块
  src/harnesslib/**
  src/llm_gateway/**
  tests/
```

---

## 三、验收命令汇总

```bash
# suggest-deps 基础功能
codememory --root examples/investment suggest-deps user/investment/semiconductor-thesis
# 预期：输出正向候选列表（含 score + tags 信息）

# --forward-only
codememory --root examples/investment suggest-deps user/investment/semiconductor-thesis --forward-only

# --min-score
codememory --root examples/investment suggest-deps user/investment/semiconductor-thesis --min-score 5

# 全量回归
codememory --root examples/investment reindex && codememory --root examples/investment validate
codememory --root examples/investment resolve user/investment/context | grep "Resolved"
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
```

---

## 四、风险

| 风险 | 缓解 |
|------|------|
| 标签交集噪声（无关记忆因标签巧合被推荐） | 三层评分叠加：标签权重低（×3），schema 模式权重高（×5），靠 score 排序过滤 |
| 反向推断误判 | 反向建议标 `retroactive`，不自动 apply；默认 dry-run |
| 大规模记忆库性能 | 标签交集是 O(n) 字典查找，500 条毫秒级 |

---

## 五、完成定义

1. `suggest-deps <id>` 输出正向候选依赖列表，按 score 降序
2. 输出包含反向候选（retroactive），标注缺失同领域依赖的记忆
3. `--min-score` / `--forward-only` / `--retroactive-only` 参数可用
4. 默认 dry-run，不修改任何文件
5. 57+24 测试不退化
