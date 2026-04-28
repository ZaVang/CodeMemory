# CodeMemory 后续路线图

> 设计哲学：记忆加载是依赖解析问题，不是搜索问题
> Layer 0 认知接口：`docs/layer0-cognitive-interface.md`

---

## 一、已完成

Phase 1-4 全部完成（8 个 Sprint）：

- **Phase 1**：原型验证（四种原语 + resolve + validate）
- **Phase 2A-E**：框架化 + Agent 自主维护 + 智能检索 + Layer 0 认知接口 + 集成发布
- **Phase 3A-B**：代码质量（handlers 去重 + Pydantic v2 + logging）+ 功能深化（changelog + wander 加权 + snapshot 统一）
- **Phase 3C-D**：测试体系（57 单元 + 24 集成）+ OpenAI/Anthropic/Gemini 工具适配
- **Phase 4A**：知识治理（maturity 自动升降 + 全局 log.md + evidence 溯源）
- **Phase 4B**：知识组织（semantic_type + resolve --focus + 冷启动 import）
- **Phase 4C**：文档体系（architecture.md / INTEGRATION.md / layer0-cognitive-interface.md / interop-with-team-knowledge.md / agent-memory-guide.md）

当前状态：14 个 CLI 命令，12 个 Sandbox 工具，57+24 测试覆盖。

---

## 二、Phase 5：自动依赖推断（suggest-deps）

> 核心问题：`create` 生成空 `imports` 模板，全靠人/LLM 手动填。记忆少时没问题，500 条时 LLM 无法全量分析。
>
> 设计目标：依赖推断命令，输入新记忆 ID，输出候选依赖列表。不做向量/embedding（零新依赖）。

### 2.1 三层过滤算法

```
codememory suggest-deps user/ideas/new-memory

Layer 1: 标签交集评分（成本≈0）
  新记忆 tags: ["investment", "decision", "risk"]
  扫描 index 中所有记忆，计算标签交集数
  交集 >= 1 → 进入候选池
  预期：500 → ~40-60

Layer 2: Schema 结构模式（成本≈0）
  如果新记忆 type=instance + schema=schemas/decision：
    找所有同 schema 的 instance，统计它们最常 import 哪些记忆
    高频被引用的记忆 → 加权加分
    例：85% 的 decision instance 都 import 了 risk-tolerance
  如果新记忆 type=composite：
    找所有 composite，统计常见依赖模式

Layer 3: 热度加权排序
  候选池按以下公式排序：
    score = tag_overlap × 3 + schema_pattern_score × 5 + dependents
  dependents 高的记忆是"大家都需要它"，很可能新记忆也需要
```

### 2.2 双向推断

正向是新→旧（"理解 B 需要先读 A"），但实践中也常见反向——**旧的果，新的因**：

> 1 月观察到 SOXL 暴跌（A），当时不知道为什么。3 月发现 NVIDIA 延迟出货（B），B 完美解释了 A。B 创建时，A 的 imports 应该补上 B。

```
codememory suggest-deps user/facts/nvidia-delay

====================
This memory should IMPORT:
====================
  [REQUIRED] user/facts/nvidia-earnings-q4    score:8  tags:2
  [RELATED]  user/industry/semicon-trends      score:4  tags:1

====================
These may need to IMPORT this (retroactive):
====================
  [REQUIRED] user/observations/soxl-drop-jan   score:11 tags:3 | missing same-domain deps
  [RELATED]  user/investment/buy-feb            score:6  tags:2 | partial explanation
```

反向推断的启发式：候选记忆 C 的 imports 里缺少同标签领域的依赖（说明 C 当时是"孤立的果"），而新记忆 B 的标签恰好覆盖这个缺口。反向建议标为 `retroactive`，不会自动 apply。

### 2.3 CLI 设计

```bash
codememory suggest-deps <id>                     # 基础：标签 + schema 模式
codememory suggest-deps <id> --min-score 5        # 只输出高分建议
codememory suggest-deps <id> --dry-run            # 仅输出建议（默认行为）
codememory suggest-deps <id> --forward-only       # 只做正向推断
codememory suggest-deps <id> --retroactive-only   # 只做反向推断
```

默认 `--dry-run`，需要手动确认后通过 `update` 写入 imports。不自动修改任何文件。

### 2.4 不做什么

- 不引入 embedding/向量——零新依赖
- 不做在 `create` 里——suggest-deps 是独立操作
- 不自动写入——默认 `--dry-run`
- 不强依赖 LLM——前两层纯统计算法；未来可选加 `--llm` 做最终精排
- 不做反向自动 apply——反向建议需要人工判断因果方向

### 2.5 文件变更

```
新增：
  src/codememory/suggest_deps.py    # 依赖推断逻辑（~120 行）

修改：
  src/codememory/cli.py             # + suggest-deps 子命令
  src/codememory/handlers.py        # + handle_suggest_deps
```

### 2.6 验收

```bash
# 标签交集过滤
codememory --root examples/investment suggest-deps user/investment/new-buy-decision
# 预期：输出正向 + 反向候选列表，按 score 降序

# --min-score
codememory suggest-deps user/investment/new-buy-decision --min-score 5

# --forward-only
codememory suggest-deps user/investment/new-buy-decision --forward-only
```

---

## 三、时间线

```
已完成 ─── Phase 1-4 (全部 8 个 Sprint)

待开始 ─── Phase 5 (suggest-deps)    约 0.5 周
```

---

## 四、风险与缓解

| 风险 | 缓解 |
|------|------|
| suggest-deps 标签交集噪声（无关记忆因标签巧合被推荐） | 三层评分叠加：标签权重低（×3），schema 模式权重高（×5），最终靠 score 排序过滤 |
| 反向推断误判（B 并不真的解释 A） | 反向建议标注 `retroactive`，需人工确认；默认不自动 apply |
| 大规模记忆库标签交集计算慢 | 标签交集计算是 O(n) 字典查找，500 条记忆在毫秒级；可在 index.json 中预建标签倒排索引加速 |
