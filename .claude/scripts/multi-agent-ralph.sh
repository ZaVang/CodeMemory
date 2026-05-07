#!/usr/bin/env bash
# scripts/multi-agent-ralph.sh
#
# 三 Agent Ralph Loop：Planner → Generator → Evaluator
# 每个 Agent 是独立 claude -p 进程，通过文件通信，上下文互不污染。
#
# 文件协议：
#   docs/orch/plan.md        ← Planner 写，Generator 读
#   docs/orch/gen_status.md  ← Generator 写，Evaluator 读
#   docs/orch/eval.md        ← Evaluator 写，Orchestrator 读（也是下轮 Planner 的输入）
#
# Usage:
#   bash scripts/multi-agent-ralph.sh [OPTIONS]
#
# Options:
#   --max-iter N     最大迭代次数（默认 10）
#   --model MODEL    模型别名（默认 sonnet）
#   --sprint FILE    Sprint 合同路径（默认 docs/plans/SPRINT.md）
#
# Example:
#   bash scripts/multi-agent-ralph.sh --max-iter 5 --model sonnet

set -euo pipefail

# ── 解除嵌套限制（允许在 Claude Code 会话内调用）────────────────────────────
unset CLAUDECODE 2>/dev/null || true

# ── 参数解析 ──────────────────────────────────────────────────────────────────

MAX_ITER=2
MODEL="sonnet"
SPRINT_FILE="docs/plans/SPRINT.md"

while [[ $# -gt 0 ]]; do
  case $1 in
    --max-iter) MAX_ITER="$2"; shift 2 ;;
    --model)    MODEL="$2";    shift 2 ;;
    --sprint)   SPRINT_FILE="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── 文件路径 ──────────────────────────────────────────────────────────────────

PITFALLS_FILE="docs/plans/pitfalls.md"
CLAUDE_MD=".claude/CLAUDE.md"
ORCH_DIR="docs/orch"
PLAN_FILE="$ORCH_DIR/plan.md"
GEN_STATUS_FILE="$ORCH_DIR/gen_status.md"
EVAL_FILE="$ORCH_DIR/eval.md"

mkdir -p "$ORCH_DIR"

# ── Agent 调用（各自独立 claude -p 进程）─────────────────────────────────────

run_agent() {
  local role="$1"
  local system_prompt="$2"
  local user_prompt="$3"
  local allowed_tools="${4:-default}"

  echo "  ▶ [$role] 启动..."
  claude -p \
    --dangerously-skip-permissions \
    --model "$MODEL" \
    --system-prompt "$system_prompt" \
    --tools "$allowed_tools" \
    "$user_prompt" 2>/dev/null
}

# ── 主循环 ────────────────────────────────────────────────────────────────────

echo ""
echo "🚀 Multi-Agent Ralph Loop"
echo "   Sprint:    $SPRINT_FILE"
echo "   Model:     $MODEL"
echo "   Max iters: $MAX_ITER"
echo ""

for ITER in $(seq 1 "$MAX_ITER"); do
  echo "══════════════════════════════════════"
  echo "  Iteration $ITER / $MAX_ITER"
  echo "══════════════════════════════════════"

  # 检查上轮 Evaluator 反馈（跨迭代记忆）
  PREV_EVAL=""
  if [[ -f "$EVAL_FILE" ]]; then
    PREV_EVAL="上一轮 Evaluator 反馈（请重点关注失败原因）：
$(cat "$EVAL_FILE")"
  fi

  # ── Phase 1: Planner ────────────────────────────────────────────────────────
  # 职责：读 SPRINT.md + pitfalls.md + 上轮 eval → 写 plan.md
  # 工具：只需 Read + Write（不执行代码）
  run_agent "Planner" \
"你是 Sprint Planner，为本项目的 Code Generator 制定实现计划。
你的唯一输出是写入 $PLAN_FILE 文件。不要写代码，只写计划。

核心规则：
1. 读取 $SPRINT_FILE 找出所有 [ ] 未完成任务
2. 读取 $PITFALLS_FILE 筛选与本次任务相关的陷阱
3. 如果存在 $EVAL_FILE（上轮评估），重点分析失败原因，调整本轮策略
4. 每个任务必须列出：需要读取的文件、需要修改的文件、实现要点
5. 将计划写入 $PLAN_FILE（覆盖写）" \
"$PREV_EVAL

请读取相关文件后，将以下结构写入 $PLAN_FILE：

# Iteration $ITER Plan

## 本次目标任务
（从 SPRINT.md 中列出 [ ] 未完成任务，按依赖顺序排列）

## 每个任务的实现指南
### 任务 1：XXX
- 需要先读取的文件：[路径列表]
- 需要修改的文件：[路径列表]
- 实现要点：[具体步骤]
- 注意事项：[来自 pitfalls.md 的相关陷阱]

## 验收命令
（从 SPRINT.md 的验收命令章节复制）

## 上轮失败分析（如适用）
（分析上轮为什么失败，本轮如何避免）" \
    "Read,Write,Glob,Grep" > /dev/null

  echo "  Planner ✓  → $PLAN_FILE"

  # ── Phase 2: Generator ──────────────────────────────────────────────────────
  # 职责：读 plan.md → 实现代码 → 运行验收命令 → 更新 SPRINT.md → 写 gen_status.md
  # 工具：全套（Bash/Edit/Write/Glob/Grep/Read）
  run_agent "Generator" \
"你是 Code Generator，负责按照 Planner 的计划实现代码。

工作流程：
1. 先读取 .claude/CLAUDE.md 和 .claude/rules/ 下的规则文件，了解项目编码规范
2. 读取 $PLAN_FILE 了解任务列表和实现指南
3. 对每个任务：先读取相关源文件，理解现有代码，再修改
4. 严格遵守 CLAUDE.md 中的所有强制规范
5. 每完成一项，将 $SPRINT_FILE 对应的 [ ] 改为 [x]
6. 全部完成后运行验收命令
7. 将结果写入 $GEN_STATUS_FILE" \
"首先读取 .claude/CLAUDE.md 了解项目规范，然后读取 $PLAN_FILE，按计划逐项实现。
每次修改文件前，必须先读取该文件理解现有代码。

完成后将以下内容写入 $GEN_STATUS_FILE：

# Generator Status — Iteration $ITER

## 完成的任务
- [x] 任务描述 — 修改了哪些文件、做了什么

## 未完成的任务（如有）
- [ ] 任务描述 — 卡在哪里、原因

## 验收命令输出
\`\`\`
（粘贴实际运行的命令和完整输出）
\`\`\`

## 状态
PASSED / PARTIAL / FAILED / BLOCKED" \
    "default" > /dev/null

  echo "  Generator ✓ → $GEN_STATUS_FILE"

  # ── Phase 3: Evaluator ──────────────────────────────────────────────────────
  # 职责：独立重新运行验收命令 → 写 eval.md → 输出决策到 stdout
  # 工具：Read + Bash + Write（独立验证，不信任 Generator 自报结果）
  EVAL_RAW=$(run_agent "Evaluator" \
"你是 QA Evaluator，独立验证 Sprint 是否完成。
核心原则：不信任 Generator 的自报结果，自己重新运行所有验收命令。

工作流程：
1. 读取 $SPRINT_FILE，检查所有任务的 checkbox 状态
2. 自己重新运行 SPRINT.md 中的每一条验收命令，记录实际输出
3. 对比 Generator 报告 ($GEN_STATUS_FILE) 与实际运行结果
4. 将完整评估写入 $EVAL_FILE
5. 最后在终端输出决策（详见下方格式）

决策标准：
- COMPLETE：所有 [ ] 都变成了 [x] 且所有验收命令通过
- CONTINUE：还有未完成任务，或验收命令有失败项
- BLOCKED：遇到环境问题、依赖缺失等无法通过代码修改解决的阻塞" \
"读取 $SPRINT_FILE 和 $GEN_STATUS_FILE，然后自己重新运行所有验收命令。

将完整评估写入 $EVAL_FILE，格式：

# Evaluator Report — Iteration $ITER

## Checkbox 状态
（逐项列出 [x] / [ ]）

## 验收命令重跑结果
（每条命令的实际输出）

## Generator 报告 vs 实际对比
（是否有出入）

## 失败原因分析（如有）
（具体是什么失败了、可能的修复方向，供下轮 Planner 参考）

## 决策
COMPLETE / CONTINUE / BLOCKED

---
写完 $EVAL_FILE 后，在终端输出最后一行，格式严格为：
DECISION: COMPLETE
或 DECISION: CONTINUE
或 DECISION: BLOCKED
（仅此一行，不加其他文字）" \
    "Read,Bash,Write")

  # 健壮解析：先找 DECISION: XXX 格式，再 fallback 到关键词匹配
  DECISION=$(echo "$EVAL_RAW" | grep -oP 'DECISION:\s*\K(COMPLETE|CONTINUE|BLOCKED)' | tail -1 || true)
  if [[ -z "$DECISION" ]]; then
    if echo "$EVAL_RAW" | grep -q "COMPLETE"; then
      DECISION="COMPLETE"
    elif echo "$EVAL_RAW" | grep -q "BLOCKED"; then
      DECISION="BLOCKED"
    else
      DECISION="CONTINUE"
    fi
  fi

  echo "  Evaluator ✓ → 决策: $DECISION"
  echo ""

  # ── 路由 ────────────────────────────────────────────────────────────────────
  case "$DECISION" in
    COMPLETE)
      echo "✅ Sprint Complete! (completed in $ITER iterations)"
      echo "   详见 $EVAL_FILE"
      exit 0
      ;;
    BLOCKED)
      echo "🚫 Blocked — 需要人工介入"
      echo "   详见 $EVAL_FILE"
      exit 2
      ;;
    CONTINUE)
      echo "  继续下一轮..."
      ;;
  esac
done

echo ""
echo "⏱  达到最大迭代次数 ($MAX_ITER)，Sprint 未完成"
echo "   查看 $EVAL_FILE 了解当前状态"
exit 1
