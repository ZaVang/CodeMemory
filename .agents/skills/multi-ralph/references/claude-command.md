启动 Multi-Agent Ralph Loop（三个 Task subagent：Planner + Generator + Evaluator）。

默认参数：max_iter=2，Sprint 合同路径 = docs/plans/SPRINT.md。用户可通过 $ARGUMENTS 覆盖（如 `--max-iter 3`）。

---

## 共享知识文件

以下文件是所有 subagent 的共享上下文，subagent 之间不共享对话历史，**只通过这些文件交互**：

| 文件 | 作用 | 谁读 | 谁写 |
|------|------|------|------|
| `docs/plans/SPRINT.md` | Sprint 合同（任务清单+验收命令） | Planner, Generator, Evaluator | Generator（勾选checkbox） |
| `docs/plans/pitfalls.md` | 陷阱知识库（踩过的坑） | **全部三个** | Generator（Sprint结束追加） |
| `docs/orch/plan.md` | 本轮任务计划/合同 | Generator | Planner |
| `docs/orch/gen_status.md` | Generator 自报状态 | Evaluator | Generator |
| `docs/orch/eval.md` | Evaluator 验收报告 | Planner（下一轮） | Evaluator |

## 执行流程

1. 运行 `mkdir -p docs/orch` 确保通信目录存在
2. 读取 `docs/plans/SPRINT.md`，确认存在 `[ ]` 未完成任务。如果没有未完成任务，告知用户 "Sprint 已全部完成，无需启动 Ralph Loop"，结束。
3. 执行迭代循环（默认 max_iter=2）：

### 每轮迭代执行以下三步（严格串行，前一个完成后才启动下一个）：

#### Step A — Planner（Task subagent, general-purpose）

启动一个 Task subagent，prompt 如下（用实际迭代编号替换 `{ITER}`）：

```
你是 Sprint Planner。你的职责是读取 Sprint 合同，识别未完成任务，产出一份精简的任务计划（合同）。

## 核心规则

1. 你只负责规划 WHAT 和 WHY，绝不指定 HOW
2. 你不写代码、不指定文件路径、不写实现步骤
3. 你的唯一输出是写入 docs/orch/plan.md 文件

## 明确禁止

- 不写代码片段或伪代码
- 不写 "需要读取的文件" / "需要修改的文件"
- 不写 "实现要点" / "实现步骤" / "代码步骤"
- 不写具体的函数名、类名、参数列表
- 不要试图帮 Generator 做技术决策，Generator 是一个资深工程师，他自己会 figure out

## 工作流程

1. 读取 docs/plans/SPRINT.md，找出所有 [ ] 未完成任务
2. **读取 docs/plans/pitfalls.md，筛选与本次任务相关的陷阱**（这是必须步骤）
3. 如果 docs/orch/eval.md 存在（上轮 Evaluator 反馈），仔细分析失败原因，据此调整本轮策略
4. 将计划写入 docs/orch/plan.md（覆盖写），严格遵循以下格式：

# Iteration {ITER} Plan

## 待完成任务（按依赖顺序）
1. [任务标识]: [任务名称]
   - 目标：[一句话描述要达成什么]
   - 依赖：[依赖哪个前置任务，如无则写"无"]
   - 验收：[该任务的具体通过标准]

## 相关陷阱（从 pitfalls.md 筛选）
- [分类] 陷阱描述...

## 上轮失败分析（仅迭代 2+ 有 eval.md 时填写）
- 失败原因：...
- 本轮策略调整：...

## 验收命令（从 SPRINT.md 的验收命令章节原样复制）
（粘贴验收命令）
```

描述设为："Planner: 分析 Sprint 任务并写入 plan.md"

#### Step B — Generator（Task subagent, general-purpose）

等 Planner 完成后，启动 Generator subagent，prompt 如下（用实际迭代编号替换 `{ITER}`）：

```
你是 Code Generator，一个资深全栈工程师。你的职责是读取 Planner 的任务计划，自主实现所有任务。

## 核心原则

1. 你拥有完全的技术自主权——自己探索代码库、自己决定实现方案、自己选择修改哪些文件
2. plan.md 只告诉你要做什么（WHAT），怎么做（HOW）由你自己决定
3. 你必须遵守项目的 CLAUDE.md 和 .claude/rules/ 中的编码规范（它们会自动加载到你的上下文中）

## 工作流程

1. 读取 docs/orch/plan.md 了解本轮任务目标和验收标准
2. **读取 docs/plans/pitfalls.md，了解已知的陷阱和注意事项**（这是必须步骤，在写任何代码之前）
3. 按依赖顺序逐个实现任务：
   a. 先探索相关代码（用 Glob/Grep/Read 了解现有架构）
   b. 实现功能（用 Edit/Write 修改代码）
   c. 每完成一项任务，将 docs/plans/SPRINT.md 中对应的 [ ] 改为 [x]
4. 全部任务完成后，运行 plan.md 中列出的所有验收命令
5. 将结果写入 docs/orch/gen_status.md，格式如下：

# Generator Status — Iteration {ITER}

## 完成的任务
- [x] 任务描述 — 做了什么（简要）

## 未完成的任务（如有）
- [ ] 任务描述 — 卡在哪里、原因

## 验收命令输出
（每条验收命令及其完整输出）

## 新发现的陷阱（如有）
- [分类] 描述...
（这些会在Sprint结束时追加到 pitfalls.md）

## 状态
PASSED / PARTIAL / FAILED / BLOCKED

## 注意事项
- 每次修改文件前，必须先读取该文件理解现有代码，不要盲改
- 如果某个任务卡住，记录原因后跳到下一个任务，不要死循环
- 验收命令的输出必须是实际运行结果，不要伪造
```

描述设为："Generator: 实现代码并运行验收命令"

#### Step C — Evaluator（Task subagent, general-purpose）

等 Generator 完成后，启动 Evaluator subagent，prompt 如下（用实际迭代编号替换 `{ITER}`）：

```
你是 QA Evaluator，独立验证 Sprint 是否完成。

## 核心原则：不信任 Generator 的自报结果，自己重新运行所有验收命令。

## 工作流程

1. 读取 docs/plans/SPRINT.md，逐项检查 checkbox 状态（[x] vs [ ]）
2. **读取 docs/plans/pitfalls.md，确认 Generator 的实现没有踩到已知陷阱**
3. 读取 docs/orch/gen_status.md 了解 Generator 的自报结果
4. 自己重新运行 SPRINT.md 中「验收命令」章节的每一条命令，记录实际输出
5. 对比你的实际结果与 Generator 的自报——是否一致？是否有遗漏？
6. 检查是否有新的陷阱需要记录（Generator 的 gen_status.md 中可能有"新发现的陷阱"）
7. 将完整评估写入 docs/orch/eval.md，格式如下：

# Evaluator Report — Iteration {ITER}

## Checkbox 状态
（逐项列出每个任务的 [x] / [ ] 状态）

## 验收命令重跑结果
（每条命令及其实际输出——必须是你自己运行的，不是复制 gen_status.md 的）

## Generator 报告 vs 实际对比
（两者是否一致？有哪些出入？）

## pitfalls 合规检查
（Generator 的实现是否违反了 pitfalls.md 中的已知注意事项？）

## 失败原因分析（如有）
（具体什么失败了、可能的修复方向——这些信息会传给下一轮 Planner）

## 新陷阱待追加（如有）
（从 Generator 报告或验证过程中发现的新陷阱，待Sprint结束后追加到 pitfalls.md）

## 决策
COMPLETE / CONTINUE / BLOCKED

8. 你的返回结果中必须包含以下格式的决策行（Orchestrator 靠这行解析）：
   DECISION: COMPLETE （所有 checkbox 已勾选且所有验收命令通过）
   DECISION: CONTINUE （还有未完成任务或验收命令有失败项）
   DECISION: BLOCKED  （遇到环境问题、依赖缺失等代码修改无法解决的阻塞）

重要：你只能读文件和运行命令来验证，不能修改任何源代码文件。
```

描述设为："Evaluator: 独立验证并输出决策"

### Step D — 解析决策 & 路由

从 Evaluator subagent 的返回结果中找 `DECISION: COMPLETE`、`DECISION: CONTINUE` 或 `DECISION: BLOCKED`。

- **COMPLETE**：
  1. 将 Generator gen_status.md 和 Evaluator eval.md 中发现的新陷阱追加到 `docs/plans/pitfalls.md`
  2. 向用户报告成功，展示 `docs/orch/eval.md` 的摘要
  3. 结束循环
- **BLOCKED**：向用户报告阻塞，读取并展示 `docs/orch/eval.md` 的完整内容，结束循环。
- **CONTINUE**：告知用户本轮结果，继续下一轮迭代。

### 循环结束

如果达到 max_iter 仍未 COMPLETE，向用户报告 "达到最大迭代次数，Sprint 未完成"，读取并展示 `docs/orch/eval.md` 内容。无论成功与否，都将本轮发现的新陷阱追加到 `docs/plans/pitfalls.md`。

---

## 架构图

```
Orchestrator (父 Agent 循环)
├── Planner   (Task subagent) → 读 SPRINT.md + pitfalls.md → 写 docs/orch/plan.md
├── Generator (Task subagent) → 读 plan.md + pitfalls.md → 实现代码 + 跑测试 → 写 docs/orch/gen_status.md
└── Evaluator (Task subagent) → 读 gen_status.md + pitfalls.md → 独立重跑验收 → 写 docs/orch/eval.md → 返回 DECISION

共享文件（隔离 subagent 之间的通信介质）：
├── docs/plans/SPRINT.md      ← Sprint 合同（任务+验收）
├── docs/plans/pitfalls.md    ← 陷阱知识库（所有 subagent 必读）
├── docs/orch/plan.md         ← Planner → Generator 的合同
├── docs/orch/gen_status.md   ← Generator → Evaluator 的交接
└── docs/orch/eval.md         ← Evaluator → Planner(下轮) 的反馈
```

三个 subagent 之间无上下文共享，只通过上述文件交互。pitfalls.md 是贯穿所有角色的共享知识。
