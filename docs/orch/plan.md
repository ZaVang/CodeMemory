# Iteration 11 Plan

**Date:** 2026-05-06
**Previous Round Eval:** 18/18 PASSED -- no regressions, no failures

## 本轮任务（按依赖顺序）

### Tier 1 -- Critical Bug Fix + Key UX（必须完成）

1. **R11-B1**: 修复数据集切换时 List 和 Dashboard 视图数据不更新的竞态问题
   - 目标：切换到新数据集后，List 和 Dashboard 的数据更新为正确数据集的内容
   - 依赖：无
   - 验收：List 视图切换后数据匹配新数据集；Dashboard 统计数据匹配新数据集；Graph 切换不退化
   - 来源：体验官 Critical #1

2. **R11-B2**: 防止模态叠加
   - 目标：同一时间只显示一个模态
   - 依赖：无
   - 验收：已有模态打开时触发另一模态会先关闭前者；两模态关闭逻辑独立
   - 来源：体验官 Critical #2

3. **R11-UX1**: 修复 Ctrl+K 键盘快捷键失效
   - 目标：Ctrl+K 正确聚焦搜索输入框
   - 依赖：无
   - 验收：按下 Ctrl+K 后搜索框获得焦点；Help 面板快捷键列表正确
   - 来源：体验官 Important #5

4. **R11-UX2**: 为 REINDEX 操作添加完成反馈
   - 目标：Reindex 完成后显示可见的成功/失败提示
   - 依赖：无
   - 验收：成功时显示 "Reindexed N memories" toast；失败时显示错误 toast；提示自动消失
   - 来源：体验官 Important #4

5. **R11-UX3**: 使搜索过滤 Graph 视图节点
   - 目标：搜索操作能使 Graph 中匹配节点高亮、非匹配节点变暗
   - 依赖：无
   - 验收：搜索后非匹配节点 dimmed；匹配节点高亮；清除搜索恢复所有节点；搜索结果与图节点联动
   - 来源：体验官 Important #3

### Tier 2 -- 高价值改进（尽量完成）

6. **R11-UX4**: 为 Graph 视图添加加载骨架屏
   - 目标：Cytoscape 初始化期间显示带 shimmer 动画的骨架屏
   - 依赖：无（独立组件添加）
   - 验收：图加载前显示骨架（节点圆圈 + 边线）；使用现有 shimmer 动画；数据到达后替换为真实图
   - 来源：体验官 Important #6（I9/I10 遗留项）

7. **R11-UX5**: 表单校验失败时禁用 CREATE 按钮
   - 目标：校验失败后按钮不可点击，防止重复提交
   - 依赖：无
   - 验收：空表单提交失败后按钮 disabled；修正错误后恢复可点击
   - 来源：体验官 Important #7

8. **R11-UX6**: 为 List 视图截断的摘要列添加 hover tooltip
   - 目标：悬浮截断文本时显示完整摘要
   - 依赖：无
   - 验收：截断单元格 hover 显示完整内容；未截断时不显示 tooltip
   - 来源：体验官 Nice-to-have #8

9. **R11-UX7**: 改进关键操作的错误消息用户体验
   - 目标：错误消息人类可读，添加 Retry 按钮，替代原始 HTTP 状态码文本
   - 依赖：无（复用现有 error toast 基础设施）
   - 验收：网络错误含 Retry 按钮；错误措辞人类可读；CRUD 失败有可操作指引
   - 来源：进化策略师 Critical C3（部分采纳——本轮聚焦于错误措辞和重试机制，完整错误分类系统延后）

### Tier 3 -- 打磨（至少完成三项）

10. **R11-P1**: 移除 header 中的 "Stats, validation, and reindex apply to the selected dataset" 声明文字
    - 目标：将 10px 声明从 header 移除，信息移至 dataset 下拉 tooltip
    - 依赖：无
    - 验收：Header 不再显示该声明；dataset 下拉有 tooltip 说明范围
    - 来源：体验官 Nice-to-have #9 / 进化策略师 Phase 4 "删除清单"

11. **R11-P2**: 移除 Dashboard stale 区域中重复的 memId 显示
    - 目标：每条 stale 记忆的 ID 仅显示一次
    - 依赖：无
    - 验收：不再出现同一 ID 渲染两次的情况
    - 来源：体验官 Nice-to-have #11

12. **R11-P3**: 添加搜索"无结果"空状态反馈
    - 目标：零结果搜索显示可见提示，而非下拉菜单静默消失
    - 依赖：无
    - 验收：无结果时显示 "No memories found matching 'xyz'" 提示含建议
    - 来源：进化策略师 Critical C4（部分采纳——聚焦搜索空状态，其他空状态延后）

13. **R11-P4**: 为 MCP server 工具添加读写注解
    - 目标：MCP tools/list 响应中标记只读/写入操作
    - 依赖：无
    - 验收：tools/list 返回每个工具的读写属性；现有工具调用不变；57+24 测试通过
    - 来源：研究员建议 #4（High-Impact, Low-Effort）

## 来自 Reviewer 的改进项（采纳的）

- **修复数据集切换竞态** -- 本轮行动：R11-B1
- **防止模态叠加** -- 本轮行动：R11-B2
- **修复 Ctrl+K 快捷键** -- 本轮行动：R11-UX1
- **REINDEX 完成反馈** -- 本轮行动：R11-UX2
- **搜索过滤 Graph 节点** -- 本轮行动：R11-UX3
- **Graph 加载骨架屏** -- 本轮行动：R11-UX4
- **表单校验后禁用 CREATE** -- 本轮行动：R11-UX5
- **List 摘要 hover tooltip** -- 本轮行动：R11-UX6
- **错误消息用户体验改进** -- 本轮行动：R11-UX7
- **移除 header 声明文字** -- 本轮行动：R11-P1
- **移除重复 memId 显示** -- 本轮行动：R11-P2
- **搜索"无结果"空状态** -- 本轮行动：R11-P3
- **MCP 工具读写注解** -- 本轮行动：R11-P4

## 相关陷阱（从 pitfalls.md 筛选）

- **异步操作竞态**（隐含陷阱，非显式记录）：数据集切换涉及多个 useEffect 和异步 API 调用的执行顺序，是 R11-B1 的核心风险。Generator 应确保数据集标识在子组件数据拉取之前已同步更新。
- **Budget no-op 检查仅对增加方向有效**（SPRINT.md 记录）：与 R11-UX3（搜索过滤 Graph）无直接关系，但若修改 Graph 刷新逻辑需留意。

## 上轮失败分析

R10 eval.md 显示 18/18 PASSED，全部任务通过验证，零回归。本轮无需特殊策略调整，直接推进新任务。

## 验收命令（从 SPRINT.md 的验收命令章节原样复制）

```bash
# Backend 统计端点
curl http://localhost:8000/api/stats | python -m json.tool

# Backend wander
curl -X POST http://localhost:8000/api/wander | python -m json.tool

# Backend validate
curl -X POST http://localhost:8000/api/validate | python -m json.tool

# Backend 创建 + 清理
curl -X POST http://localhost:8000/api/memories \
  -H "Content-Type: application/json" \
  -d '{"id":"user/test/sprint13-test","summary":"Sprint 13 test memory","tags":["test"],"intensity":5,"body":"Test body content."}'
curl http://localhost:8000/api/memories/user/test/sprint13-test | python -m json.tool
curl -X PUT http://localhost:8000/api/memories/user/test/sprint13-test \
  -H "Content-Type: application/json" \
  -d '{"change_note":"update summary","summary":"Updated test summary"}'
# Clean up: manually delete the test file + reindex

# Frontend TypeScript 类型检查
cd frontend && npx tsc --noEmit

# Frontend 构建
cd frontend && npx vite build

# 全量回归
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
```
