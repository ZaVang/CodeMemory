# CodeMemory Frontend UX Audit

> 审计时间：2026-05-19  
> 方法：按 `.agents/skills/ux-audit/SKILL.md` 执行。先阅读 `README.md` / `docs/USER_GUIDE.md` / PRD / Architecture，再通过真实浏览器观察前端行为。  
> 约束：只记录实际观察到的行为，不基于源码猜测。

---

## 1. 审计证据

### 1.1 文档入口

用户文档把 CodeMemory 定义为：

- 可靠工作记忆底座；
- 通过显式依赖 DAG 取代普通搜索 / RAG；
- Web UI 用于浏览、创建、编辑、可视化；
- 典型入口为 `.\start.ps1` 或 `python bin/codememory.py dev`，前端地址 `http://localhost:5300`。

### 1.2 运行与页面采样

按 skill 要求，先尝试运行：

```bash
node .agents/skills/ux-audit/scripts/get_page_state.js http://127.0.0.1:5300/
```

结果失败：

```text
Cannot find module 'puppeteer'
```

因此改用项目现有 Playwright 依赖做等价页面状态采样。观察路径：

- first load / onboarding；
- Graph；
- List；
- Search；
- Search result Resolve；
- Dashboard；
- Validate；
- Wander；
- Create Memory；
- Dataset switch；
- 1280 / 1366 / 1440 / 1600 / 1920 viewport header measurement。

---

## 2. 产品理解

CodeMemory 的产品主张是成立的：它不是“又一个笔记搜索器”，而是让用户和多个 agent 共享一份可解释、可复现、可审计的工作记忆。前端承担的是 operator console：让用户看见 DAG、维护 memory、resolve context，并把结果复制给 agent。

当前前端已经有关键骨架：Graph / List / Dashboard / Search / Resolve / Create / Dataset switch 都存在。但体验还没有完全对齐 v1 的产品重心：用户最应该快速完成的动作是“选中一个上下文入口 → resolve → copy as context → 给 agent 使用”，而当前界面把 Graph 可视化、Dashboard 统计、创建表单、衰减指标、导出、设置等全部并列放在首屏，导致第一任务路径不够聚焦。

---

## 3. 启动体验

### 观察

`.\start.ps1 -SkipInstall` 启动时，当前机器已有 `8000` / `5300` 服务占用。脚本输出了目标地址，然后 backend 因端口占用失败：

```text
[Errno 10048] ... address ('0.0.0.0', 8000) ... only one usage of each socket address
```

同时实际访问 `http://127.0.0.1:8000/` 和 `http://127.0.0.1:5300/` 都是可用的。

### 判断

启动脚本对“服务已经在运行”的场景不够友好。它没有检测并复用已有服务，也没有给出“端口被占用但服务健康，可以直接访问”的提示。

分类：A. Logic is sound but awkward to use  
严重度：P2

---

## 4. First-time User Walkthrough

### 4.1 Onboarding

首次进入显示 onboarding：

- 标题：`Welcome to CodeMemory`
- 当前 dataset：`investment`
- 说明 memory atoms 和依赖图；
- 后续步骤解释 Graph、Resolve、Create、Dashboard。

Onboarding 的内容方向正确，尤其是 Resolve 示例能解释“9 nodes assembled in topological order / full-text / summarized”。这是最接近产品核心价值的部分。

问题是，onboarding 背后的完整主界面已经全部渲染并暴露交互：Create、Graph/List/Dashboard、dataset、search、zoom、budget、export、settings、help、legend 都同时出现在页面状态中。对新用户来说，这会造成注意力竞争。

分类：A. Logic is sound but awkward to use  
严重度：P2

### 4.2 初始 API 错误

首次加载时，console 多次出现：

```text
400 Bad Request
Graph load failed: X-Codememory-Dataset header is required.
```

页面最终仍显示 investment dataset，但后台错误说明首次数据初始化顺序有问题：前端在 dataset header 就绪前已经发起了需要 header 的请求。

分类：B. Logic itself is flawed  
严重度：P1

### 4.3 Graph

Onboarding 完成后，页面文本快照只包含 header 和 legend：

```text
DIRECTORIES
schemas
user/facts
user/investment
...
EDGES
Required
Recommended
Related
```

Graph 节点是 canvas 渲染，语义页面状态中没有 memory IDs / node labels。视觉用户可能能看到图，但 screen reader、自动化测试、低视力用户、以及“想快速知道该点哪里”的 first-time user 都缺少一个可读的节点入口。

分类：D. UI execution is weak  
严重度：P1

---

## 5. Feature Walkthroughs

### 5.1 List

List 能正确显示 10 条 investment memories，包括 ID、summary、type、maturity、status、tags、health。它是当前最清晰、最可靠的入口。

观察到的问题：

- 表格信息密度很高；
- 中英文混排可接受，但视觉层次偏重；
- `Health` 百分比有用，但新用户还不一定理解其含义；
- Graph 是默认视图，但 List 反而更适合 first-time user 找入口。

分类：A. Logic is sound but awkward to use  
严重度：P2

### 5.2 Search

搜索 `risk` 后，出现 1 个结果：

- `user/investment/risk-tolerance`
- 有 `RESOLVE →`
- 显示 match 字段、snippet、R probability。

这条路径有效，且很接近产品价值。但结果层和底下 List 同时存在，页面文本变成“搜索结果 + 全表格”混合，用户不容易判断搜索是否过滤了 List，还是打开了一个 overlay。

分类：C. Purpose or operation is unclear  
严重度：P2

### 5.3 Resolve

从搜索结果点击 `RESOLVE →` 后，右侧详情面板显示：

- `All 1 nodes fit within budget`
- memory metadata；
- referenced by；
- `RESOLVE — 1 NODES · budget 2000 · depth recommended`
- `COPY AS CONTEXT`

这是目前最有价值的流程。问题是它不够突出：`COPY AS CONTEXT` 应该是核心 CTA，但在视觉结构里只是面板中的一个小按钮。另一个问题是 metadata 有明显空值：

```text
Intensity: /10
```

分类：A. Logic is sound but awkward to use / B. Logic itself is flawed  
严重度：P2

### 5.4 Dashboard

Dashboard 能显示总数、stale、proven、draft、maturity distribution、top tags、status distribution。

点击 `VALIDATE` 后，整个 React 应用变成空白。浏览器 page error：

```text
Cannot read properties of undefined (reading 'length')
at Dashboard (.../Dashboard.tsx:1406:29)
```

直接调用 API 观察到：

```json
{
  "value": [0, 0],
  "Count": 2
}
```

这说明 Validate 的前后端响应契约和 Dashboard 渲染预期不一致，并且缺少 Error Boundary，导致单个功能错误摧毁整个应用。

分类：B. Logic itself is flawed  
严重度：P0

### 5.5 Wander

点击 `WANDER` 后出现弹窗：

```text
Wander Recall
WHY THIS MEMORY?
Access Count:
Intensity: /10
Last Access: never
Memory ID
Summary
VIEW DETAILS
WANDER AGAIN
CLOSE
```

Memory ID 和 Summary 为空，Intensity 也为空。直接调用 API 观察到 `/api/wander` 返回的是一个字符串型 `result`，不是结构化对象。前端没有把可读字段解析出来，用户看到的是一个空的推荐卡片。

分类：B. Logic itself is flawed  
严重度：P1

### 5.6 Create Memory

点击 `CREATE MEMORY` 后，右侧打开 New Memory 面板。字段包括 ID、summary、tags、imports、intensity、maturity、body。

优点：

- 字段覆盖 memory contract；
- placeholder 给了 ID/import 示例；
- 可直接写 Markdown body。

问题：

- 对 first-time user 来说，“ID / imports / intensity / maturity”全部同时出现，认知负担较大；
- imports 只能手写 comma-separated IDs，没有 picker；
- 表单位于右侧，背景 Dashboard 仍在语义页面状态中，像 side panel，不像明确的 creation flow；
- 底部 `CANCEL / CREATE` 在 1000px 高 viewport 下接近底边。

分类：A. Logic is sound but awkward to use  
严重度：P2

### 5.7 Dataset Switch

切换到 `software-architecture` 后，目录 legend 正确更新为：

```text
schemas
user/beliefs
user/decisions
user/facts
user/observations
user/preferences
```

该功能基本可用。但切换后没有明确的 loaded confirmation，也没有“当前 dataset 的推荐入口 memory”。用户仍然需要猜应该从哪个节点开始。

分类：C. Purpose or operation is unclear  
严重度：P3

---

## 6. Responsive / Layout Findings

在 Graph 视图下，header 控件横向溢出。实际测量：

| Viewport | 被裁切控件 |
|---:|---|
| 1280 | Budget input、theme、PNG、Export、Settings、Help |
| 1366 | Budget input、theme、PNG、Export、Settings、Help |
| 1440 | theme、PNG、Export、Settings、Help |
| 1600 | Export、Settings、Help |
| 1920 | 无裁切 |

这意味着常见 13/14 寸笔记本宽度下，右上角帮助、设置、导出等功能不可见或不可达。尤其 onboarding 最后一页说“Help button (top-right) has full reference documentation”，但 1440 viewport 下 Help 的 x 坐标在 1764，已经在视口外。

分类：D. UI execution is weak  
严重度：P0

---

## 7. Issue Register

| ID | 分类 | 严重度 | 观察 | 影响 |
|---|---|---:|---|---|
| UX-01 | B | P0 | Dashboard 点击 Validate 后应用空白，React page error | 维护功能不可用，且无 Error Boundary |
| UX-02 | D | P0 | Graph header 在 1280/1366/1440/1600 下裁切关键按钮 | 常见屏幕无法访问 Help/Settings/Export |
| UX-03 | B | P1 | 首次加载多次 400：缺少 `X-Codememory-Dataset` header | 初始化时序错误，污染用户/开发者信任 |
| UX-04 | B | P1 | Wander 弹窗 Memory ID / Summary / Intensity 为空 | 召回功能看起来坏了 |
| UX-05 | D | P1 | Graph 节点不出现在语义页面状态中 | 可访问性差，用户难以从文本路径理解图 |
| UX-06 | C | P2 | Search 结果和 List 同时显示，关系不清楚 | 用户不知道搜索是在过滤还是 overlay |
| UX-07 | A | P2 | Copy as Context 是核心价值，但不是主 CTA | 产品最强动作不够突出 |
| UX-08 | A | P2 | Create 表单一次暴露过多底层字段 | 新用户创建第一条 memory 的门槛偏高 |
| UX-09 | A | P2 | 启动脚本遇到已运行服务时失败提示粗糙 | 本地开发/使用体验不稳 |
| UX-10 | C | P3 | Dataset switch 后没有推荐入口或 loaded confirmation | 用户仍需猜从哪里开始 |

---

## 8. Scores

| 维度 | 分数 | 说明 |
|---|---:|---|
| 产品概念表达 | 7/10 | Onboarding 和 docs 能解释 DAG/Resolve，但 UI 首屏不够聚焦。 |
| 启动体验 | 6/10 | 启动入口清楚；端口占用场景不友好。 |
| First-time onboarding | 6/10 | 内容方向对；背景界面太吵，且 Help 在常见宽度不可见。 |
| Graph UX | 5/10 | 视觉核心存在；响应式和可访问性弱。 |
| List/Search UX | 7/10 | 当前最可用；搜索层级关系需澄清。 |
| Resolve UX | 7/10 | 核心流程有效；Copy as Context 应更突出。 |
| Dashboard UX | 3/10 | Validate 崩溃，Wander 空字段。 |
| Create/Edit UX | 5/10 | 功能完整；面向新用户的引导不足。 |
| Overall | 5.5/10 | 技术 owner 可用，但 first-time user 还会被 P0/P1 问题打断。 |

---

## 9. Continued-use Verdict

如果我是熟悉项目动机的 technical owner，我会继续用它，因为 List/Search/Resolve 已经能体现 CodeMemory 的核心价值。

如果我是第一次接触 CodeMemory 的用户，我会在两个地方失去信任：

1. 常见屏幕宽度下 Help / Settings / Export 被裁切；
2. Dashboard 的 Validate 直接让应用白屏，Wander 又显示空内容。

所以当前前端还不适合作为“让陌生用户第一次理解并愿意继续使用”的版本。它更像一个功能已经铺开的 operator prototype，需要先修 P0/P1，再重排首屏任务路径。

---

## 10. Top Three Recommendations

### 1. 先修前后端契约与错误边界

优先级最高：

- 修复 `/api/validate` 与 Dashboard 的响应 contract；
- 修复 `/api/wander` 或前端 parser，让 Wander 卡片显示 memory id / summary / intensity；
- 前端初始化时等 dataset header 就绪后再请求 graph/stats/search；
- 加 React Error Boundary，任何 panel 崩溃都不能让整页白屏。

### 2. 重做 Graph header 响应式布局

把 Graph-only 控件从全局 header 中拆出来：

- 左侧：产品名 + primary CTA；
- 中间：Graph/List/Dashboard + dataset；
- 右侧：Help/Settings；
- Graph canvas 内部或二级 toolbar：Zoom / Budget / PNG；
- 小屏时折叠为 overflow menu。

验收标准：1366px 下 Help、Settings、dataset、Search、主 CTA 都必须可见。

### 3. 把 first-time path 改成“Resolve-first”

首屏应该引导用户完成一个明确闭环：

```text
Choose dataset → Select recommended entry memory → Resolve → Copy as Context
```

具体建议：

- 默认给每个 dataset 一个 “Start here” memory；
- onboarding 结束后高亮该入口；
- Resolve 面板把 `Copy as Context` 提升为主按钮；
- Graph 旁边提供一个可访问的 node list，避免 canvas-only。

