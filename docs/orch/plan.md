# Iteration 12 Plan

**Date:** 2026-05-07
**Previous Round Eval:** 12/13 PASSED -- single failure: R11-P4 (MCP readOnlyHint, ~10 lines)

## 本轮任务

### Tier 1 -- Critical 修复（必须完成）

1. **R12-B1**: 修复 Validate 模态在 Wander 关闭后偶发性打不开的异步竞态问题
   - 目标：Validate 模态始终可靠打开，不受异步 fetch 生命周期影响
   - 依赖：无
   - 验收：多次重复"打开 Wander → 关闭 → 点击 Validate"，Validate 模态每次都出现；反之亦然；两个模态的 close/open 完全独立
   - 来源：体验官 Critical #1

2. **R12-B2**: 修复 List 视图 TruncatedCell tooltip 不显示（R11 回归）
   - 目标：截断的 Summary 列在 hover 时正确显示完整文本 tooltip
   - 依赖：无
   - 验收：含省略号的单元格 hover 后显示 tooltip；未截断时不显示；中文混合文本检测准确
   - 来源：体验官 Critical #2

3. **R12-B3**: 清除用户修正输入后的表单校验错误
   - 目标：用户修正输入后错误 banner 自动消失
   - 依赖：无
   - 验收：提交空表单后错误在输入有效 ID 后消失；按钮状态与错误状态一致；无闪烁
   - 来源：体验官 Important #7（升级为 Critical——错误 persist 是混淆性 UX bug）

4. **R12-B4**: 完成 R11-P4 -- MCP server 工具 readOnlyHint 注解（上轮遗留）
   - 目标：5 个 MCP 工具定义中添加 readOnlyHint 属性
   - 依赖：无
   - 验收：tools/list 响应中每个工具含 readOnlyHint；工具调用行为不变；57+24 测试通过
   - 来源：上轮遗留 + 进化策略师 I9 + 研究员 R4（三方一致）

### Tier 2 -- 高价值改进（尽量完成）

5. **R12-UX1**: 提升全局最小交互字号从 10-11px 到 12-13px
   - 目标：所有按钮、标签、badge 和控件文字 >= 12px；微标签 >= 11px
   - 依赖：无（CSS 变量/全局样式变更）
   - 验收：全应用交互文字 >= 12px；微标签 >= 11px；布局不破损；深色模式适用
   - 来源：体验官 Important #3

6. **R12-UX2**: 为 Settings、Help、MemoryForm 面板和 Wander/Validate 模态添加入场/退场动画
   - 目标：所有滑出面板和模态使用与 MemoryDetail 一致的动画模式
   - 依赖：无（纯 CSS/transition 变更）
   - 验收：Settings/Help/MemoryForm 面板滑入动画（250ms ease）；Wander/Validate 模态 fade-in + scale；退场动画正确；动画时长和缓动函数统一
   - 来源：体验官 Important #4 + #5

7. **R12-UX3**: 为 Validate 模态添加 "Validate Again" 按钮
   - 目标：Validate 模态内提供 re-run 入口，匹配 Wander 的 "Wander Again"
   - 依赖：无
   - 验收："Validate Again" 按钮出现并触发重新 validate；按钮样式和位置一致；加载态反馈
   - 来源：体验官 Important #6

8. **R12-UX4**: 为归档操作添加确认对话框
   - 目标：归档前弹出确认对话框，含被引用警告
   - 依赖：需要后端提供被引用计数（已在 MemoryDetail backlinks 数据中可用）
   - 验收：归档触发确认；含 "N memories import this" 警告；确认后执行；取消无操作；Escape 可关闭
   - 来源：进化策略师 C5

9. **R12-UX5**: 为 overview 添加时间衰减激活计算
   - 目标：heat 计算公式从线性改为时间衰减逻辑，改善 session-start 上下文注入质量
   - 依赖：无（`handle_overview` 内部公式变更）
   - 验收：最近访问的记忆 heat 高于久远的高频记忆；zero-access 降级正确；输出格式不变；57+24 测试通过
   - 来源：研究员 R1（Red / High-Impact Low-Effort）

### Tier 3 -- 打磨（至少完成四项）

10. **R12-P1**: 替换 onboarding 文字图标为 SVG 几何图标
    - 目标：5 步 onboarding 的原始文字字符替换为一致的 SVG 图标集
    - 依赖：无
    - 验收：每步为 SVG 图形（圆形/箭头/加号/对勾/星形）；风格一致；颜色与 gold accent 协调
    - 来源：体验官 Nice-to-have #8

11. **R12-P2**: 统一三个视图的空状态组件
    - 目标：Graph/List/Dashboard 零记忆和零过滤结果使用统一 EmptyState 组件
    - 依赖：无
    - 验收：三个视图空状态视觉一致；零记忆 vs 零过滤文案/图标区分；操作按钮统一
    - 来源：体验官 Nice-to-have #9

12. **R12-P3**: 统一操作标签 -- "Create Memory" / "+ New" / "+ NEW" 选一统一
    - 目标：全应用主操作标签一致；"+ NEW" 按钮与视图切换器视觉可区分
    - 依赖：无
    - 验收：所有创建入口同一文案；主操作按钮与视图切换器视觉可区分
    - 来源：体验官 Nice-to-have #9 补充

13. **R12-P4**: 添加视图切换键盘快捷键（1/2/3 对应 Graph/List/Dashboard）
    - 目标：数字键 1/2/3 切换视图；Help 面板记录
    - 依赖：无
    - 验收：按键切换视图；输入框聚焦时不触发；Help 面板列出快捷键
    - 来源：体验官 Nice-to-have #12 + 进化策略师 I3

14. **R12-P5**: 为 List 视图表格行添加 hover 效果
    - 目标：表行悬浮时有微妙背景色过渡（~100ms）
    - 依赖：无
    - 验收：hover 时背景色平滑过渡；深色模式适用；与其它视图交互风格一致
    - 来源：体验官 Nice-to-have #13

15. **R12-P6**: 为 List 视图添加容器横向 padding
    - 目标：表格不拉伸到边缘，与 Dashboard padding 一致
    - 依赖：无
    - 验收：表格有可见横向 padding；深色模式 padding 背景色一致；列宽正确自适应
    - 来源：体验官 Phase 2.3

---

## 来自 Reviewer 的改进项（采纳的）

### 体验官采纳
- **Validate 模态异步竞态** -- 本轮行动：R12-B1
- **List 视图 tooltip 回归** -- 本轮行动：R12-B2
- **表单错误清除** -- 本轮行动：R12-B3
- **全局字号提升** -- 本轮行动：R12-UX1
- **面板/模态入场动画** -- 本轮行动：R12-UX2
- **Validate Again 按钮** -- 本轮行动：R12-UX3
- **Onboarding SVG 图标** -- 本轮行动：R12-P1
- **统一空状态组件** -- 本轮行动：R12-P2
- **统一操作标签** -- 本轮行动：R12-P3
- **视图切换快捷键** -- 本轮行动：R12-P4
- **List 行 hover 效果** -- 本轮行动：R12-P5
- **List 横向 padding** -- 本轮行动：R12-P6

### 进化策略师采纳
- **归档确认对话框** -- 本轮行动：R12-UX4
- **MCP readOnlyHint** -- 本轮行动：R12-B4（三方一致）

### 研究员采纳
- **时间衰减激活** -- 本轮行动：R12-UX5
- **MCP readOnlyHint** -- 本轮行动：R12-B4

---

## 相关陷阱（从 pitfalls.md 筛选）

- **异步操作竞态**：R12-B1 的核心风险。Validate 模态的打开依赖异步 fetch 结果——Generator 需确保模态打开逻辑不耦合于 promise 解析时机。一个可靠的模式是：fetch 完成后无条件设置 validate 数据并打开模态（不依赖前一个模态的关闭 promise），模态关闭逻辑独立。

- **TruncatedCell text-overflow 检测**：R12-B2 涉及 CSS overflow 与 DOM 尺寸检测的交互。父元素 `overflow: hidden` 会导致 `scrollWidth` 始终等于 `clientWidth`。Generator 需打破这个 CSS 限制——无论是绕过溢出检测、在更外层元素测量、还是采用其他截断判定策略。

- **字体变更的布局影响**：R12-UX1 涉及全局字号变更。10-11px → 12-13px 的增加可能压破紧凑元素的布局——如 view switcher 按钮组、header 区域、badge 标签。Generator 应进行跨视图的视觉回归检查。

- **动画与 React 生命周期**：R12-UX2 的退场动画需要面板/模态在卸载前播放动画。React 的 conditional rendering 模式下，状态变为 false 后组件立即卸载——需要延迟卸载或使用动画库来处理退场过渡。

---

## 上轮失败分析

### R11-P4: MCP tool read/write annotations — NOT IMPLEMENTED

**根因**：R11 共 13 项任务，Generator 完成了前 12 项后遗漏了最后一项。eval.md 确认 12/13 PASSED，`mcp_server.py` 的 TOOLS 列表中 5 个工具均无 `readOnlyHint` 属性。

**修复方向**：在 `mcp_server.py` 的 TOOLS 列表中添加 `readOnlyHint` 属性——4 个只读工具设为 `true`，1 个写入工具（snapshot）设为 `false`。约 10 行改动，零风险。

**本轮策略**：作为 R12-B4 直接纳入 Tier 1，优先于所有新任务完成。

---

## 验收命令

```bash
# Backend 端点回归
curl -s -H "X-Codememory-Dataset: companion" http://localhost:8000/api/stats | python -m json.tool
curl -s -X POST -H "X-Codememory-Dataset: companion" http://localhost:8000/api/wander | python -m json.tool
curl -s -X POST -H "X-Codememory-Dataset: companion" http://localhost:8000/api/validate | python -m json.tool

# MCP readOnlyHint 验证
PYTHONPATH=src python -c "
from codememory.mcp_server import TOOLS
for t in TOOLS:
    has = 'readOnlyHint' in t
    print(f'{t[\"name\"]}: readOnlyHint={\"present\" if has else \"MISSING\"}')
" | grep -c "MISSING" | xargs -I{} sh -c '[ {} -eq 0 ] && echo "PASS: all tools have readOnlyHint" || echo "FAIL: {} tools missing readOnlyHint"'

# Frontend TypeScript 类型检查
cd frontend && npx tsc --noEmit

# Frontend 构建
cd frontend && npx vite build

# 全量回归
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short
```
