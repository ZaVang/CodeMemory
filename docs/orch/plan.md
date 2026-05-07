# Round 19 任务计划 — 最终轮：卫生与收尾

**生成日期：** 2026-05-07
**上轮评估：** Round 18 — 8/8 PASS，86/86 测试通过，零回归。体验官审计 9.0/10（首次 9+ 级别，零 Critical）。8 of 9 R17 建议已关闭（89%）。
**本轮主题：** 最终轮 —— 轻量卫生与收尾。关闭最后未关闭审计建议，确保 CI/构建卫生，清理最后的技术欠账。
**本轮定位：** 产品循环 3/3 最终轮。不接受大型功能。此前延期至此的 Import UI（3 天）、AI 辅助创建（2 天）、Imports 自动补全（1 天）不再纳入——产品已无阻塞性问题且体验官评分 9.0/10，大型功能投资的边际收益递减。

---

## 一、本轮聚焦

Round 18 将产品评分从 8.5 提升至 9.0，关闭了 89% 的 R17 审计建议。剩余的改进方向集中在三个领域：

1. **最后未关闭的审计建议。** 唯一未关闭的 R17 建议是 N4（暗色模式图节点填充可见性），在 R18 审计中重新确认为 N1。此外 R18 审计的 I2（Onboarding Resolve 交互演示）是第 2 个未关闭的高信号建议。

2. **构建卫生。** Playwright 测试的跨目录执行脆弱性在多轮 Eval 中被反复提及。R16-F3 修复了路径解析但 CI 执行路径仍不完整。

3. **部署健壮性。** "Copy as Context" 特征的发现性（R18 N2）和快捷键（R18 N3）在新功能推出后尚未完善；HTTP 环境下的剪贴板回退（R18 N5）是最后一道部署防线。

本轮策略：**5 个轻量任务，全部可在 1 小时内单独完成。** 不启动大型功能、不碰架构迁移、不引入新依赖。

---

## 二、任务拆解

### 第一梯队：关闭最后未关闭的审计建议（必达，< 1 小时合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **C1** | 暗色模式图节点填充可见性 | R17 唯一未关闭建议（89% 关闭率 → 目标 100%）。将 `DIRECTORY_TINTS_DARK` 各值整体上移 5-10% 亮度，使暗色模式下节点 fill 更易感知。修改范围：`colors.ts` 一处文件的多行数值调整。 | 体验官 R17 N4 + R18 N1 |
| **C2** | Onboarding Resolve 交互演示步骤 | R18 I2（Important）。Onboarding 告知用户 Resolve 是什么，但没有"show, don't tell"。在 Resolve 说明步骤后自动对默认数据集入口记忆触发 resolve，在 onboarding overlay 内展示结果摘要。不可达时优雅降级为纯文本。 | 体验官 R18 I2 |

### 第二梯队：构建卫生与健壮性（应达，< 1 小时合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **C3** | Playwright 跨目录执行兼容性 + CI 脚本 | 多轮 Eval 均提及。`playwright.config.ts` 的 `testDir` 相对路径使从项目根目录运行依赖手动 `cd frontend`。添加绝对路径支持 + `test:e2e:ci` 脚本。 | 多轮 Eval 卫生建议（R15-R18） |
| **C4** | "Copy as Context" 发现性 + 快捷键 | R18 N2 + N3 合并。R18 交付的差异化功能缺少发现途径和 power-user 快捷键。Help 面板条目 + Ctrl+Shift+C 快捷键。 | 体验官 R18 N2 + N3 |
| **C5** | "Copy as Context" HTTP 剪贴板回退 | R18 N5。`navigator.clipboard` 在非安全上下文不可用。添加 `execCommand('copy')` 回退确保所有部署场景下功能完整。 | 体验官 R18 N5 |

---

## 三、本轮排除项目（不接受、不实现、不讨论）

本轮定位为最终轮卫生与收尾。以下项目明确排除：

- **大型功能**（Import UI ~3 天、AI 辅助创建 ~2 天、Imports 自动补全 ~1 天、Review Queue ~1.5 天、Proposed 审核队列 ~1 天、Markdown 预览 ~0.5 天）—— 产品已达 9.0/10 评分，大型功能投资的边际收益递减。留给未来 Sprint。
- **架构迁移**（App.tsx 状态管理、CSS 现代化、SQLite 索引后端）—— 技术健康项，非用户可见改进。当前 1-2 人团队可管理。
- **复合目标 Export-as-Context**（R18 N4）—— 需 resolve 引擎变更 + merge DAG 逻辑 + 新 UI 流程，约 2 天。
- **响应式工具栏**（R18 N6）—— 约 1-2 天，当前目标用户（桌面开发者）不受影响。

---

## 四、验收概要

### C1 — 暗色模式节点填充
1. 暗色模式下所有目录节点 fill 比当前更亮（肉眼可感）
2. 不同目录 dark tint 仍可相互区分
3. 亮色模式不受影响
4. Legend 暗色模式下颜色同步正确

### C2 — Onboarding Resolve 演示
1. 首次访问 investment 时 onboarding 包含真实 resolve 演示
2. 演示显示结果摘要（节点数 + 结构简述）
3. API 不可达时优雅降级为纯文本步骤
4. Onboarding 可正常跳过和关闭

### C3 — Playwright CI 就绪
1. `npx playwright test --config frontend/playwright.config.ts` 从根目录 5/5 通过
2. `npm run test:e2e:ci` 正确执行
3. 原有 `cd frontend && npx playwright test` 行为不变

### C4 — Copy as Context 发现性
1. Help Panel 包含 "Copy as Context" 条目
2. Help Panel 快捷键列表包含 Ctrl+Shift+C
3. Ctrl+Shift+C 在 Resolve 结果可见时触发复制（等效于点击按钮）
4. 不与 Ctrl+K（搜索聚焦）冲突

### C5 — HTTP 剪贴板回退
1. localhost 下 `navigator.clipboard.writeText()` 仍为首选
2. clipboard API 不可用时 execCommand 回退成功
3. 两种路径使用相同的成功/失败视觉反馈

### 全量回归
1. `cd frontend && npx tsc --noEmit` — 零错误
2. `cd frontend && npx vite build` — 构建成功
3. `PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short` — 57/57
4. `PYTHONPATH=src python tests/integration_test.py` — 24/24
5. `PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short` — 5/5
6. `cd frontend && npx playwright test` — 5/5
7. 全部 86 可执行测试零回归

---

## 五、陷阱提示

- **[C1] DIRECTORY_TINTS_DARK 修改后需逐对验证区分度。** teal vs green 的 dark tint 当前仅 2 点亮度差（#153D38 vs #153520），同时提升后仍需保持足够距离。建议修改前截图记录当前状态，修改后对比。
- **[C2] Resolve 演示依赖后端。** 后端不可达时必须优雅降级——静默回退到纯文本步骤，不显示技术错误。用户在 onboarding 中不应看到 "Resolve failed"。
- **[C3] `__dirname` 在 ESM 模式下不可用。** 若 tsconfig 使用 ESM module，需使用 `import.meta.url` 替代或保持相对路径 + CI 脚本中显式 `cd`。
- **[C4] Ctrl+Shift+C 与浏览器 DevTools 冲突。** Chrome/Firefox 使用此组合键打开元素选择器。仅在 MemoryDetail 面板可见且有 Resolve 结果时拦截，其他情况让浏览器原生行为通过。备选：Ctrl+Shift+X。
- **[C5] execCommand 需同步调用栈。** 如果在异步回调（await 之后）中调用 execCommand，浏览器将拒绝。`buildPromptContent()` 是同步函数，此风险较低——但实现时需确认点击处理器中无异步操作在 execCommand 之前。
