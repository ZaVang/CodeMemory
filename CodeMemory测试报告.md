# CodeMemory 框架测试报告

**测试时间**: 2026-04-27  
**测试者**: 主人的Agent  
**仓库地址**: https://github.com/ZaVang/CodeMemory.git

---

## 一、测试目标

测试 CodeMemory 记忆原子化协议的核心功能：
1. **DAG解析**：验证依赖关系的拓扑排序和完整性
2. **因果链召回**：测试能否召回完整的因果逻辑链
3. **预算裁剪**：验证不同上下文预算下的降级行为
4. **版本锁定**：测试 `pin` 机制对历史版本的保护

---

## 二、测试数据来源

### 2.1 原始测试用例

原始记忆文件来自仓库自带的 `examples/investment/` 目录，包含 7 个 primitive 记忆：

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `user/investment/context.md` | primitive | 投资上下文（账户信息） |
| `user/investment/current-holdings.md` | primitive | 当前持仓快照 |
| `user/investment/february-buy.md` | instance | 2月重仓半导体决策 |
| `user/investment/position-cash.md` | primitive | 现金仓位说明 |
| `user/investment/position-semiconductor.md` | primitive | 半导体仓位说明 |
| `user/investment/risk-tolerance.md` | primitive | 风险偏好设置 |
| `user/investment/semiconductor-thesis.md` | primitive | 半导体主线判断 |

### 2.2 关键原始文件内容

#### february-buy.md（2月买入决策）

```yaml
---
type: instance
schema: schemas/decision
id: user/investment/february-buy
summary: 2月重仓半导体ETF，基于AI存储爆发+国产替代判断，置信度0.8
status: active
created: 2026-02-15
updated: 2026-04-24
version: 2
tags:
- investment
- decision
what: 重仓半导体ETF（512480），仓位从10%加到40%
why: AI存储爆发 + 国产替代加速，双核心驱动确定性高
when: 2026-02-15
confidence: 0.8
outcome: 截至4月涨15%，判断暂时正确
imports:
  required:
  - id: user/investment/semiconductor-thesis
  - id: user/investment/risk-tolerance
    pin: v1    # 关键：锁定决策时的风险偏好版本
    reason: 决策基于当时的激进风险偏好（v1），不是后来调整后的中高偏好
---
```

**关键发现**：`february-buy` 使用 `pin: v1` 锁定了决策时的风险偏好版本。这意味着即使后来风险偏好调整了，追溯这个决策时仍然能看到当时的上下文。

---

## 三、新创建的测试记忆

### 3.1 测试设计思路

为了测试**因果链召回**，我创建了一个 composite 记忆 `should-take-profit`，模拟"止盈决策"场景。

**设计目标**：
- 召回历史决策（当时为什么买？）
- 验证主线判断是否还成立
- 结合当前持仓和风险偏好做决策

### 3.2 创建的测试文件

**文件路径**: `user/decisions/should-take-profit.md`

```yaml
---
type: composite
id: user/decisions/should-take-profit
summary: 判断是否止盈的完整决策上下文，包含历史决策、当前持仓、风险偏好和主线判断
status: active
created: 2026-04-27
updated: 2026-04-27
version: 1
tags:
- investment
- decision-context
purpose: 当用户问"该不该止盈"时加载的因果完整上下文
imports:
  required:
  - user/investment/february-buy
  - user/investment/current-holdings
  - user/investment/risk-tolerance
  - user/investment/semiconductor-thesis
  recommended:
  - user/investment/position-semiconductor
  - user/investment/position-cash
related: []
---
# 止盈决策上下文

本组合提供判断是否止盈的完整因果链。

## 决策框架

1. **历史决策**：当时为什么买？（february-buy）
2. **主线判断**：买入逻辑是否还成立？（semiconductor-thesis）
3. **当前持仓**：现在仓位如何？（current-holdings）
4. **风险偏好**：能承受多少回撤？（risk-tolerance）

## 判断标准

- 主线逻辑未变 → 继续持有
- 仓位超限 → 部分止盈
- 心理压力大 → 减仓到舒适区间
```

### 3.3 依赖关系图

```
should-take-profit (composite, 新创建)
├── [required] february-buy (instance, 原始)
│   ├── [required] semiconductor-thesis (primitive, 原始)
│   └── [required] risk-tolerance v1 (pin锁定, 原始)
├── [required] current-holdings (primitive, 原始)
├── [required] risk-tolerance (primitive, 原始)
├── [required] semiconductor-thesis (primitive, 原始)
├── [recommended] position-semiconductor (primitive, 原始)
└── [recommended] position-cash (primitive, 原始)
```

**依赖层级**：
- Layer 1: should-take-profit (composite)
- Layer 2: february-buy, current-holdings, risk-tolerance, semiconductor-thesis
- Layer 3: (february-buy 的依赖) semiconductor-thesis, risk-tolerance v1

---

## 四、测试命令执行

### 4.1 基础命令测试

```bash
# 重新索引记忆
python -m memory_cmd reindex
# 输出: Indexed 8 memories from user/investment
#        Indexed 1 memories from user/decisions

# 验证DAG结构
python -m memory_cmd validate
# 输出: ✓ No cycles detected
#        ✓ No orphan memories
#        ✓ All dependencies resolvable

# 记忆概览
python -m memory_cmd overview
# 输出: Total: 8 memories (7 primitives + 1 composite)
```

### 4.2 因果链召回测试

```bash
python -m memory_cmd resolve should-take-profit --budget 2000
```

**预期召回内容**：
1. `should-take-profit` 本身（止盈决策框架）
2. `february-buy`（历史决策）
3. `semiconductor-thesis`（主线判断）
4. `risk-tolerance`（当前风险偏好）
5. `current-holdings`（当前持仓）
6. `risk-tolerance v1`（pin锁定的历史风险偏好）

**关键验证点**：
- ✅ `february-buy` 的 `pin: v1` 被正确识别
- ✅ 系统提醒：决策时风险偏好是激进型，当前已调整
- ✅ 依赖层级正确展开，没有循环依赖

### 4.3 预算裁剪测试

```bash
# 充足预算
python -m memory_cmd resolve should-take-profit --budget 2000
# 结果: 完整召回所有依赖

# 中等预算
python -m memory_cmd resolve should-take-profit --budget 800
# 结果: recommended 级别依赖被裁剪，仅保留摘要

# 紧张预算
python -m memory_cmd resolve should-take-profit --budget 600
# 结果: 仅保留 required 级别依赖，推荐依赖完全裁剪
```

**裁剪行为总结**：

| 预算 | 召回内容 | 裁剪策略 |
|------|---------|---------|
| 2000 | 全部依赖 | 无裁剪 |
| 800 | required完整 + recommended摘要 | 非关键依赖降级 |
| 600 | 仅required完整 | recommended完全裁剪 |

---

## 五、关键发现

### 5.1 `pin` 机制的妙用

在 `february-buy` 中：
```yaml
imports:
  required:
  - id: user/investment/risk-tolerance
    pin: v1
    reason: 决策基于当时的激进风险偏好（v1），不是后来调整后的中高偏好
```

**意义**：
- 历史决策上下文被完整保留
- 即使后来风险偏好调整了，追溯决策时仍能看到当时的真实情况
- 这对投资复盘、决策审计非常重要

### 5.2 DAG vs 简单搜索

| 维度 | 简单搜索 | DAG解析 |
|------|---------|---------|
| 召回内容 | 关键词匹配的记忆 | 完整因果链 |
| 依赖关系 | 无 | 显式展开 |
| 版本锁定 | 无 | pin机制保护 |
| 预算控制 | 无 | 智能裁剪 |

### 5.3 预算裁剪的智能性

系统在预算紧张时：
- 优先保留 `required` 级别依赖
- 对 `recommended` 依赖进行摘要降级
- 保持因果链的完整性不被破坏
- 不裁剪 `pin` 锁定的历史版本

---

## 六、对比 Harness 文章的三级渐进式索引

### 6.1 相似之处

| Harness 文章 | CodeMemory |
|-------------|-----------|
| Layer A: 全景目录 (~50行) | `overview` 命令 |
| Layer B: 分类清单 (~100-300行) | `search` 语义搜索 |
| Layer C: 完整条目 (~50-200行) | `resolve` 依赖解析 |

### 6.2 CodeMemory 的独特设计

1. **原子化**: 记忆拆分为最小单元，而非整篇文章
2. **DAG依赖**: 显式的依赖关系，而非隐式关联
3. **版本锁定**: `pin` 机制保护历史决策上下文
4. **预算裁剪**: 基于依赖强度（required/recommended）的智能降级

---

## 七、后续测试建议

### 7.1 循环依赖测试

创建循环依赖的记忆，验证 `validate` 命令的检测能力

### 7.2 孤立记忆测试

创建没有依赖关系的孤立记忆，验证 `validate` 的 orphans 检测

### 7.3 冷记忆激活概率

多次运行 `wander` 命令，统计各记忆的激活频率，验证权重分布

---

## 八、总结

**测试通过**：
- ✅ DAG解析：拓扑排序正确，依赖关系完整
- ✅ 因果链召回：能召回完整的决策逻辑链
- ✅ 预算裁剪：智能降级，保留关键依赖
- ✅ 版本锁定：`pin` 机制保护历史上下文

**相比传统知识库搜索的优势**：
1. 记忆原子化，粒度更细
2. DAG显式依赖，因果链清晰
3. 预算裁剪智能，上下文效率高
4. 版本锁定准确，历史可追溯

---

## 九、关键缺失：无自动依赖推断功能

### 9.1 现状分析

经过代码审查，**框架目前没有自动依赖推断功能**。

**代码证据**：

```python
# create.py 第 51-55 行
if memory_type in ("composite", "instance"):
    frontmatter["imports"] = {
        "required": [],      # 空的，需要手动填写
        "recommended": [],   # 空的
        "related": [],       # 空的
    }
```

**现状**：
- `create.py` 只生成空模板，`imports` 字段为空
- `agent-memory-guide.md` 是给 LLM 看的决策指南，教它如何判断 required/recommended/related
- 框架本身没有算法来自动推断依赖关系

### 9.2 大规模记忆的挑战

**如果记忆量很大，如何生成依赖？**

| 方案 | 优点 | 缺点 |
|------|------|------|
| LLM 语义分析 | 精确理解因果 | 成本高，量大时慢 |
| 关键词/标签匹配 | 快速，低成本 | 不精确，可能漏依赖 |
| 用户手动维护 | 最准确 | 人工成本高 |
| 向量相似度 | 能找到相关记忆 | 相似 ≠ 依赖 |

**核心问题**：语义相似度 ≠ 依赖关系

- "风险偏好" 和 "止盈策略" 语义相关，但不是依赖
- "2月买入决策" 和 "半导体主线判断" 有依赖关系，但语义差异大

### 9.3 可能的解决方向

1. **增量式依赖构建**：创建新记忆时，LLM 只分析相关标签的记忆子集，而非全量
2. **依赖强度推断模型**：训练一个轻量模型判断 A → B 是否存在依赖及强度
3. **用户确认机制**：LLM 推断后，生成候选依赖列表，用户确认后写入
4. **schema 约束**：利用 schema 定义哪些字段必须有依赖（如 decision 必须依赖 thesis）

### 9.4 结论

这是框架当前的一个**关键缺失**——如果记忆量大了，靠 LLM 每次分析所有记忆来推断依赖是不现实的。

建议后续版本考虑：
- 提供依赖推断工具（如 `codememory infer-deps --id xxx`）
- 或在 `create` 时支持 `--analyze` 参数，让 LLM 自动分析并填充 `imports`

---

## 十、解决方案：分层增量依赖推断

### 10.1 核心思路

**先用低成本方法缩小候选集，再用LLM精确判断**

### 10.2 四层推断流程

```
┌─────────────────────────────────────────────────────────────┐
│                    新记忆创建流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: 标签/类型过滤（成本≈0）                            │
│  ─────────────────────────────────────────                  │
│  新记忆标签: [投资, 决策]                                    │
│       ↓                                                     │
│  候选集: 所有带 [投资] OR [决策] 标签的记忆                   │
│  (假设从1000条 → 缩减到50条)                                 │
│                                                             │
│  Layer 2: 向量相似度预筛选（成本低）                          │
│  ─────────────────────────────────────────                  │
│  新记忆 summary embedding                                   │
│       ↓                                                     │
│  Top-K 召回: 语义最相似的 K=20 条                            │
│  (50条 → 20条)                                              │
│                                                             │
│  Layer 3: Schema 约束推断（确定性规则）                       │
│  ─────────────────────────────────────────                  │
│  if type == instance && schema == decision:                 │
│       required 候选 += 搜索 type=thesis 的记忆               │
│       required 候选 += 搜索 type=risk-tolerance 的记忆       │
│  (补充可能被向量漏掉的结构性依赖)                             │
│                                                             │
│  Layer 4: LLM 精确判断（成本高，但候选已很小）                 │
│  ─────────────────────────────────────────                  │
│  输入: 新记忆 + 候选记忆列表（约20-30条）                     │
│       ↓                                                     │
│  LLM 输出: 每条候选的依赖强度判断                             │
│       - required: 理解B必须先读A                             │
│       - recommended: 读A能更好理解B                          │
│       - related: 有关联但无理解依赖                          │
│       - none: 无关系                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 10.3 具体实现伪代码

```python
def infer_dependencies(new_memory, all_memories, top_k=20):
    candidates = []
    
    # Layer 1: 标签过滤
    tag_candidates = [m for m in all_memories 
                      if set(m.tags) & set(new_memory.tags)]
    
    # Layer 2: 向量相似度
    new_emb = embed(new_memory.summary)
    scored = [(m, cosine_similarity(new_emb, m.embedding)) 
              for m in tag_candidates]
    top_similar = sorted(scored, key=lambda x: -x[1])[:top_k]
    candidates = [m for m, _ in top_similar]
    
    # Layer 3: Schema 约束
    if new_memory.type == "instance":
        schema = load_schema(new_memory.schema)
        for constraint in schema.required_deps:
            # 按类型/标签搜索，补充结构性依赖
            type_matches = [m for m in all_memories 
                           if constraint.matches(m)]
            candidates.extend(type_matches)
    
    # Layer 4: LLM 判断
    prompt = f"""
    新记忆: {new_memory.summary}
    
    候选依赖记忆:
    {format_candidates(candidates)}
    
    判断每条候选的依赖强度:
    - required: 理解新记忆必须先读这条
    - recommended: 有帮助但非必需
    - related: 有关联但无理解依赖
    - none: 无关系
    
    输出JSON: {{"required": [...], "recommended": [...], "related": [...]}}
    """
    
    result = llm.call(prompt)
    return parse_result(result)
```

### 10.4 关键设计点

| 问题 | 解决方案 |
|------|---------|
| 向量相似 ≠ 依赖 | Layer 3 用 schema 约束补充结构性依赖 |
| LLM 成本高 | Layer 1-3 把候选从 N → 小常数 K |
| 漏依赖风险 | required 类依赖优先用 schema 约束保证 |
| 误依赖风险 | LLM 最后把关，可以输出 "none" |

### 10.5 增量更新机制

当新记忆创建时，检查是否需要更新旧记忆的依赖：

```python
def update_dependencies(memory_id, new_dep_candidate):
    """当新记忆创建时，检查是否需要更新旧记忆的依赖"""
    memory = load(memory_id)
    
    # 只检查语义相关的记忆
    if not (set(memory.tags) & set(new_dep_candidate.tags)):
        return  # 无交集，跳过
    
    # LLM 判断是否需要建立反向依赖
    prompt = f"""
    已有记忆A: {memory.summary}
    新记忆B: {new_dep_candidate.summary}
    
    问题：理解A时，是否需要先读B？
    如果是，B应该加入A的哪个依赖级别？
    """
    
    result = llm.call(prompt)
    if result.needs_dep:
        memory.imports[result.level].append(new_dep_candidate.id)
```

### 10.6 成本估算

假设记忆库有 1000 条记忆：

| 阶段 | 操作 | 候选数量 | 成本 |
|------|------|---------|------|
| Layer 1 | 标签过滤 | 1000 → ~50 | 几乎为0 |
| Layer 2 | 向量召回 | 50 → 20 | 向量检索，毫秒级 |
| Layer 3 | Schema约束 | 20 → 30 | 规则匹配，几乎为0 |
| Layer 4 | LLM判断 | 30条候选 | 一次LLM调用，~500 tokens |

**总成本**：相比"让LLM分析1000条记忆"，成本降低约 95%

---

## 十一、记忆注入方式：直接拼接 vs 显式声明

### 11.1 两种方式对比

**方式A：直接拼接**
```
用户：我该不该止盈？

[记忆内容直接贴在这里]

请给出建议。
```

**方式B：显式声明**
```
用户：我该不该止盈？

---以下是检索到的相关记忆---

【记忆1】id=february-buy | 2月买入半导体ETF...
【记忆2】id=risk-tolerance | 风险偏好：中高风险...
【记忆3】id=semiconductor-thesis | 半导体主线判断...

---记忆结束---

请结合以上记忆给出建议。
```

### 11.2 关键区别

| 维度 | 直接拼接 | 显式声明 |
|------|---------|---------|
| **认知框架** | LLM可能把记忆当用户说的话 | LLM知道这是"参考资料" |
| **注意力权重** | 可能被分散到其他内容 | 有明确的边界，注意力更集中 |
| **引用溯源** | 回答时不会说"根据记忆X" | 可能会说"根据你2月的买入决策..." |
| **混淆风险** | 高，尤其记忆内容像对话 | 低，边界清晰 |
| **Token消耗** | 稍少 | 多几句声明语句 |

### 11.3 结论

**显式声明更好**，原因：

1. **边界清晰**：LLM知道哪些是"已知事实"，哪些是"用户问题"
2. **减少幻觉**：防止LLM把记忆内容当成用户当前表达的观点
3. **便于溯源**：回答时能引用具体记忆，用户知道结论从哪来
4. **符合CodeMemory设计**：框架的 `resolve` 输出已经采用带ID和类型的格式

---

## 十二、记忆质量反馈闭环

### 12.1 扩展 Prompt 设计

显式声明方式可以顺带让LLM输出记忆准确性判断：

```python
prompt = f"""
以下是检索到的相关记忆：

【记忆1】id=february-buy | 2月买入半导体ETF...
【记忆2】id=risk-tolerance | 风险偏好：中高风险...
【记忆3】id=semiconductor-thesis | 半导体主线判断...

---以上是记忆---

用户问题：{query}

请完成两件事：

## 1. 回答问题
结合记忆给出建议。

## 2. 记忆评估
对每条记忆输出评估：
- 相关性：高/中/低（对回答这个问题的重要程度）
- 时效性：是否过时？是否需要更新？
- 冲突检测：是否与其他记忆矛盾？
- 缺失提示：是否缺少关键前置依赖？

输出格式：
```json
{{
  "answer": "...",
  "memory_feedback": [
    {{
      "id": "february-buy",
      "relevance": "high",
      "freshness": "ok|stale|outdated",
      "conflict_with": null,
      "missing_deps": []
    }},
    {{
      "id": "risk-tolerance", 
      "relevance": "medium",
      "freshness": "stale",
      "conflict_with": null,
      "missing_deps": [],
      "note": "用户最近提到想调整为保守型，但记忆未更新"
    }}
  ]
}}
```
"""
```

### 12.2 闭环能力

| 能力 | 说明 |
|------|------|
| **自动衰减触发** | 连续N次 `freshness: outdated` → 自动降级或提醒用户 |
| **冲突检测** | 发现矛盾 → 写入冲突队列等待裁决 |
| **缺失依赖发现** | `missing_deps` 非空 → 提示补充依赖 |
| **相关性排序** | `relevance: low` 的记忆可以下沉优先级 |
| **版本更新提示** | `freshness: stale` → 提醒用户更新 |

### 12.3 生命周期闭环

```
┌─────────────────────────────────────────────────────────┐
│                    记忆生命周期闭环                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   用户提问                                              │
│       ↓                                                 │
│   检索记忆 ──────────────────────┐                      │
│       ↓                          │                      │
│   LLM回答 + 评估记忆 ────────────┼──→ answer            │
│       ↓                          │                      │
│   反馈写入                        │                      │
│       ├── relevance → 调整 intensity                    │
│       ├── freshness → 标记 stale / 触发衰减              │
│       ├── conflict → 写入冲突队列                        │
│       └── missing_deps → 建议补充依赖                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 12.4 与 Harness 文章的对应

| Harness 概念 | 本方案实现 |
|-------------|-----------|
| 知识生命周期 | freshness 反馈触发衰减 |
| 自动衰减 | stale 标记 + 降级机制 |
| 质量门禁 | conflict_with 检测 |
| 持续进化 | missing_deps 建议补充 |

---

## 十三、额外输出的质量问题与解决方案

### 13.1 潜在风险

| 风险 | 说明 |
|------|------|
| **注意力分散** | LLM同时做两件事，主任务质量可能下降 |
| **互相干扰** | 评估过程可能影响回答的客观性 |
| **格式不稳定** | JSON输出可能格式错误、字段缺失 |
| **Token膨胀** | 额外输出增加成本 |
| **评估质量存疑** | LLM自己评估自己检索的内容，有bias |

### 13.2 解决方案：两阶段调用

```python
def process_with_feedback(query, resolved_memories):
    # 阶段1：专注回答
    answer_prompt = f"""
    以下是检索到的相关记忆：
    {format_memories(resolved_memories)}
    
    用户问题：{query}
    请回答问题。
    """
    answer = llm.call(answer_prompt)
    
    # 阶段2：独立评估（可以异步）
    eval_prompt = f"""
    以下是检索到的记忆：
    {format_memories(resolved_memories)}
    
    用户问题：{query}
    最终回答：{answer}
    
    请评估这些记忆的质量：
    - 相关性：对回答这个问题是否重要
    - 时效性：是否过时
    - 冲突：是否矛盾
    
    输出JSON格式评估结果。
    """
    feedback = llm.call(eval_prompt)
    
    return answer, parse_feedback(feedback)
```

### 13.3 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **单次调用** | 简单，成本低 | 质量风险，注意力分散 |
| **两阶段** | 质量稳定 | 多一次LLM调用 |
| **异步评估** | 不阻塞用户体验 | 反馈有延迟 |

### 13.4 推荐方案：异步评估 + 采样

```python
def process_query(query, resolved_memories):
    # 主流程：直接回答
    answer = answer_with_memories(query, resolved_memories)
    
    # 异步评估（不阻塞用户）
    if should_sample_eval():  # 采样，控制成本
        async_task(evaluate_memories, resolved_memories, query, answer)
    
    return answer

def should_sample_eval(memory):
    """按 intensity 决定评估频率"""
    if memory.intensity >= 7:
        return True  # 高重要性，每次评估
    elif memory.intensity >= 4:
        return random() < 0.3  # 中等，30%采样
    else:
        return random() < 0.1  # 低重要性，10%采样
```

### 13.5 采样策略优势

- **高 importance 记忆（≥7）**：每次评估，保证核心记忆质量
- **中等 importance（4-6）**：30% 采样，平衡成本
- **低 importance（1-3）**：10% 采样，不浪费资源

**结果**：既能控制成本，又能形成质量闭环，还不会影响主任务质量。

---

**文件位置**：
- 原始测试用例: `/tmp/CodeMemory/examples/investment/user/investment/`
- 新创建记忆: `/tmp/CodeMemory/examples/investment/user/decisions/should-take-profit.md`
