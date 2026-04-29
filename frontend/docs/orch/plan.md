# Iteration 1 Plan

## 待完成任务（按依赖顺序）
1. [1.1]: POST /api/resolve 端点
   - 目标：新增后端端点，接收 resolve 请求参数并返回拓扑排序后的节点列表及裁剪级别
   - 依赖：无
   - 验收：curl POST 请求返回正确的 JSON，包含拓扑排序节点和每个节点的裁剪级别（full/summary）

2. [2.1]: 选中节点上的 Resolve 按钮
   - 目标：在图上选中节点的操作入口添加"从此节点 resolve"的交互控件
   - 依赖：1.1
   - 验收：选中节点后可看到 Resolve 操作入口，点击后能向后端发起请求

3. [2.2]: 拓扑动画
   - 目标：resolve 返回的节点按拓扑顺序依次高亮（金色 #B8860B），每步间隔 300ms
   - 依赖：1.1, 2.1
   - 验收：触发 resolve 后节点依次亮起金色，间隔约 300ms，亮起后保持但颜色渐弱

4. [2.3]: Token budget 滑块
   - 目标：添加范围 200-5000 的滑块控件，拖动时重新请求 resolve 并更新图面状态
   - 依赖：1.1, 2.1
   - 验收：滑块默认 2000，拖动至不同值后图面节点裁剪状态更新

5. [2.4]: 节点裁剪可视化
   - 目标：被裁剪节点（summary 级别）显示为半透明 + 虚线边框 + 缩小，与完整节点（full）形成视觉区分
   - 依赖：1.1, 2.2
   - 验收：小 budget 值下被裁剪节点呈现半透明/虚线/缩小样式，大 budget 下所有节点恢复正常

## 相关陷阱（从 pitfalls.md 筛选）
- [Sprint 11] Backend 需要正确设置 CODEMORY_ROOT — 新增后端端点时需确保 resolve 逻辑能找到 index.json 和 .md 文件
- [Sprint 11] Vite 端口可能被占用 — 前端验收时使用固定端口避免不确定性
- [Sprint 6] YAML date 对象与 Pydantic str 字段冲突 — resolve 返回的节点数据可能包含 YAML 解析出的日期字段，需注意序列化兼容

## 上轮失败分析（仅迭代 2+ 有 eval.md 时填写）
无。当前为 Sprint 12 首次迭代，上一轮 eval.md 属于 Sprint 11（全部通过，无失败项）。

## 验收命令（从 SPRINT.md 的验收命令章节原样复制）

```bash
# Backend resolve 端点
curl -X POST http://localhost:8000/api/resolve \
  -H "Content-Type: application/json" \
  -d '{"id":"user/investment/context","depth":"required","budget":2000}' \
  | python -m json.tool

# budget=200（极限裁剪）
curl -X POST http://localhost:8000/api/resolve \
  -H "Content-Type: application/json" \
  -d '{"id":"user/investment/context","depth":"required","budget":200}' \
  | python -m json.tool

# Frontend TypeScript 类型检查
cd frontend && npx tsc --noEmit

# 全量回归（确保现有功能不受影响）
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
```
