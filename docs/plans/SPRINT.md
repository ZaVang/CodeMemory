## Sprint 计划：CodeMemory Phase 2

### Sprint 目标

将已跑通 Demo 的记忆子系统，升级为**具备透明接口、自主维护与自然遗忘能力的通用 Agent 记忆后端**。交付一个可嵌入任意 LLM harness 的原型，实现记忆的自动创建、智能检索、因果完整加载及基于结构的自然遗忘。

### 用户故事

1. **作为 Agent，我能通过“透明玻璃”感知相关记忆的存在，无需显式调用工具即可获得上下文轮廓。**
2. **作为 Agent，我能在对话中自动识别值得记忆的信息，判断其强度与依赖，创建结构化的记忆文件。**
3. **作为 Agent，我能通过组合视图和依赖图重建完整的推理链条，并在 token 受限时自动切换分辨率。**
4. **作为用户，记忆会因不被引用而自然衰减，但高强度的核心记忆永不丢失，像真实记忆一样“触景生情”。**

---

### Sprint Backlog

#### Epic 1：透明接口层（Layer 0）

**目标**：让 Agent 不必主动搜索就能感知记忆库，仅在需要时聚焦细节。

| 任务 | 产出 | 验证 |
|------|------|------|
| **1.1 动态上下文摘要注入** | 在 Agent 系统提示中插入一段 `memory_overview`：列出与当前对话 tags/关键词匹配的 top N 记忆的 summary + 状态，由 harness 每次会话启动时自动调用 codememory 生成 | 新会话中 Agent 直接提到“我知道你的投资主线判断是…”，无需调用 search |
| **1.2 被动提醒机制** | 在 resolve 或对话中检测到 summary_hash 过期、依赖版本冲突、记忆被 superseded 时，系统自动向 Agent 发送一条低优先级的提示消息，不打断当前交互 | 手动修改记忆正文不改 summary，下次 resolve 时 Agent 收到 stale 提醒 |
| **1.3 分辨率动态切换工具** | 实现 `focus` 工具：Agent 可对已加载的 context 中的某个记忆要求“放大”（加载完整正文）或“缩小”（仅保留 summary），不重新 resolve | Agent 浏览 summary 列表后说“把风险偏好的全文加载进来”，完成切换 |

---

#### Epic 2：Agent 自主维护记忆

**目标**：Agent 能在对话中调用工具创建、更新记忆，并自动声明依赖与强度。

| 任务 | 产出 | 验证 |
|------|------|------|
| **2.1 创建决策树文档** | 一份 `agent-memory-guide.md`，包含何时创建 atom/composite/instance、如何声明依赖、如何写 summary、如何评估 intensity 的规则，可直接嵌入 system prompt 或工具描述 | 对照 3 个对话场景测试，Agent 选择正确原语且 frontmatter 符合规范 |
| **2.2 增强 create 工具** | `create_memory` 工具：生成文件模板后允许 Agent 预览并修改 frontmatter；自动更新 index.json；支持传入 `intensity` 字段 | 创建一条高强度的车祸级记忆，检查 intensity 写入成功 |
| **2.3 update 与版本控制** | `update_memory` 工具：递增 version，强制填写 change_note，自动检查并更新 summary_hash | 更新风险偏好记忆，版本号正确递增，旧版本可通过 Git 追溯 |
| **2.4 瞬态记忆（会话级）** | 在内存中维护一个 transient DAG，存储本次对话产生的中间推理，可被 resolve 引用但不落盘；提供 `snapshot` 工具将会话 DAG 导出为 composite 持久化 | 一次投资讨论后执行 snapshot，生成 composite 记录推导过程 |

---

#### Epic 3：智能检索与自然遗忘

**目标**：记忆可通过依赖图自然变得不可达，同时系统支持强度评估与联想发现。

| 任务 | 产出 | 验证 |
|------|------|------|
| **3.1 search 实现增强** | `search` 支持 `--query`（summary 模糊匹配）、`--tags`、`--type`、`--status`，结果按拓扑位置（被依赖数）+ access_count 降序排列 | 搜索“调仓”返回 context composite 排在顶部 |
| **3.2 access_count 与热度衰减** | index.json 记录每个记忆的 access_count（每次 resolve 递增）及 last_access 时间；提供 `list --sort-by heat` 展示近期热点 | 多次 resolve 同一记忆后，access_count 增长，冷记忆排在后 |
| **3.3 孤立记忆发现** | `codememory orphans` 命令列出所有入度为 0（无任何 composite/instance 依赖）的 atom，作为自然遗忘候选 | 运行 orphans，显示某条从未被引用的旧想法 |
| **3.4 联想漫步工具** | `codememory wander`：随机选择一个低 access_count 的记忆，并显示其邻居依赖，模拟“走神”式发现 | 执行 wander，系统返回一条几乎被遗忘的记忆及关联记忆预览 |
| **3.5 记忆衰减建议** | `validate` 扩展：对长期未被访问且无入边的记忆，输出“建议压缩或重新关联”的警告，不自动删除 | 运行 validate，看到对某条记忆的衰减建议 |

---

#### Epic 4：集成与文档

**目标**：让系统可被第三方 Agent 集成，并提供完整的使用说明。

| 任务 | 产出 | 验证 |
|------|------|------|
| **4.1 Python 模块化重构** | 核心逻辑（parse/resolve/search/create）封装为 `codememory` package，CLI 调用模块接口 | 在另一个脚本中 `from codememory import resolve` 可正常使用 |
| **4.2 Harness 集成示例** | 提供一个简单的 CLI harness 或 LangChain tool 封装，演示如何绑定 create/search/resolve 为 Agent 工具 | 在本地跑起示例 harness，Agent 能通过 function calling 操作记忆 |
| **4.3 集成文档** | `INTEGRATION.md`：如何配置记忆库路径、如何注册工具、如何自定义系统提示中的记忆摘要模板 | 另一个开发者按文档操作，10 分钟内复现 demo |
| **4.4 idea.md** | 汇总本项目的哲学洞察与奇思妙想，作为设计背景文档 | 阅读 idea.md 能理解“透明玻璃”“代码即因果”等核心隐喻 |

---

### 时间线（建议 3 周）

- **第 1 周**：Epic 1（透明接口层）+ Epic 2 的 2.1、2.2
- **第 2 周**：Epic 2 剩余 + Epic 3（检索与遗忘）
- **第 3 周**：Epic 4（重构、集成、文档）+ 全场景闭环测试

---

### 完成定义

1. Agent 在无人工干预下，可根据对话创建/更新记忆并能正确评估强度与依赖
2. 新会话中 Agent 无需调用工具即能感知相关记忆轮廓，并可按需聚焦细节
3. 记忆通过依赖图自然产生孤立节点，系统可发现并提供衰减建议，高强度记忆永不自动衰减
4. 核心模块可独立导入，提供集成文档，第三方 Agent 可接入

---

### 风险与缓解

| 风险 | 缓解 |
|------|------|
| Agent 自动创建记忆依赖声明不准确 | 决策树给出明确规则，初期允许人工审核 |
| 摘要注入导致系统提示过长 | 限制 top 5，仅含 summary + id，提供“更多”按钮由 Agent 主动拉取 |
| 不同平台的 tool 调用格式差异 | 先适配 OpenAI / Claude 格式，抽象通用接口 |
| 瞬态记忆与持久记忆的边界模糊 | 严格限定瞬态记忆仅存活于当前会话，snapshot 操作需显式执行 |