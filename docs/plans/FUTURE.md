# CodeMemory 后续路线图

> 从 Phase 1 原型 → 可嵌入任意 Agent 的通用记忆后端 → 知识治理与协作
>
> 设计哲学参见 [`docs/plans/IDEA.md`](IDEA.md)
> Layer 0 认知接口原理参见 [`docs/layer0-cognitive-interface.md`](../layer0-cognitive-interface.md)

---

## 零、系统全景：四层架构

```
┌──────────────────────────────────────────────────┐
│          Layer 0：认知接口层（Agent 视角）           │
│  扫视 overview  │ 注视 focus  │ 残留 snapshot      │
│  重构 resolve   │ 触景生情 wander                  │
│  所有操作对 Agent 暴露为 bash 子命令                 │
├──────────────────────────────────────────────────┤
│            harnesslib（编排层）                     │
│  Harness: Effect 循环，yield 意图 → 基础设施执行     │
│  Sandbox: 工具注册/执行，所有工具统一 execute() 接口  │
├──────────────────────────────────────────────────┤
│            llm_gateway（LLM 接入层）                 │
│  LLMBridge: 统一入口，一行 chat() 调用任意模型       │
│  Router: API key 轮转 + 指数退避重试 + 动态 fallback │
├──────────────────────────────────────────────────┤
│            codememory（记忆层）                      │
│  resolve: DAG → 拓扑排序 → token 裁剪 → 输出        │
│  create: 生成记忆模板 + 自动索引                     │
│  validate: 循环检测 + 断链 + schema 合规 + 衰减建议   │
│  overview / focus / wander / snapshot / search ...  │
└──────────────────────────────────────────────────┘
```

### Layer 0：五个认知基础操作

| 认知行为 | 命令 | 触发方式 | 说明 |
|----------|------|----------|------|
| **扫视** glance | `codememory overview` | 会话启动自动运行 | top 5 高 heat 记忆摘要注入 system prompt |
| **注视** focus | `codememory focus <id> --level full\|summary` | Agent 主动调用 | 动态 zoom-in/out，切换记忆分辨率 |
| **残留** persist | `codememory snapshot <id>` | 会话中维护，snapshot 显式触发 | TransientDAG → 持久化 composite .md |
| **重构** reconstruct | `codememory resolve <id> --depth ... --budget ...` | Agent 主动调用 | DAG 拓扑拼装 + token 裁剪输出因果完整上下文 |
| **触景生情** recall | `codememory wander` | Agent 主动或系统偶尔自动 | 随机激活冷记忆，打破思维定势 |

### Agent 视角：只有 Bash

Agent 不调用 Python API，不 import codememory，不直接读写 .md 文件。所有记忆操作都是 bash 子命令。底层用 Python 实现复杂算法，但 Agent 只看到 bash——与 Claude Code 的 `file edit` 和 `bash` 工具模式一致。

---

## 一、已完成：Phase 1-2（历史记录）

### Phase 1：原型验证
- 单文件 `bin/codememory.py`，CLI 入口
- 四种记忆原语（atom/instance/composite/schema）
- resolve（DAG 拓扑拼装）、validate（循环检测 + 断链）、reindex
- `examples/investment/` 12 条示例记忆

### Phase 2A：框架化 + 数据分离
- 从单文件提取为 `src/codememory/` package（8 个模块）
- `pyproject.toml` + `pip install -e .`
- 记忆数据迁出框架根目录 → `examples/investment/`
- codememory 注册为 harnesslib Sandbox tool

### Phase 2B：Agent 自主维护记忆
- `agent-memory-guide.md` — Agent 决策树
- `create` 增强：intensity、protected（≥8）、dry-run、tags
- `update` 命令：版本递增 + change_log + summary_hash 重算
- `TransientDAG`：会话推理链（内存中，进程退出自动清除）
- `snapshot` 命令：瞬态 DAG → 持久化 composite .md

### Phase 2C：智能检索与自然遗忘
- `search` 增强：--query、--tags、--type、--status
- `access_count` + `last_access` 追踪
- `orphans` 命令：入度为 0 的孤立记忆发现
- `wander` 命令：偏置冷记忆的随机漫步
- `validate` 衰减建议：protected 跳过 → 热记忆跳过 → 被引用跳过 → 建议衰减
- protected 机制贯通全部模块

### Phase 2D：Layer 0 认知接口完善
- `overview`：heat 排序 + status 标签 + stale 检测 + --format inject
- `focus` --content 免磁盘模式 + --resolve 依赖注入
- `resolve` 被动提醒（stale + pin）+ recommended 降级策略
- `wander` --inject 模式 + weighted 随机采样

### Phase 2E：集成与发布
- `INTEGRATION.md`：10 分钟上手集成指南
- `example_agent.py`：~150 行 mock LLM 完整闭环
- `CodememoryToolkit`：OpenAI format export + Sandbox 注册
- 集成测试：5 场景 24 断言

### Phase 3A：代码质量
- handlers.py 统一命令处理（cli.py + tools.py 委托）
- Pydantic v2 数据模型（MemoryEntry、IndexData、ImportRef、ChangeLogEntry）
- print(stderr) → logging 迁移

### Phase 3B：功能深化
- 示例记忆 hash 修复
- `changelog` 命令
- `wander` 加权概率：weight = 1 / (access_count + 1)
- `snapshot` --target 统一（内部委托 resolve 逻辑）
- `--format json` 全局支持

---

## 二、Phase 3C：测试体系（待完成）

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 3C.1 | resolve.py 单元测试 | `tests/unit/test_resolve.py`：DAG 构建、拓扑排序、循环检测、token 裁剪 | 10+ 纯函数测试，不依赖文件系统 |
| 3C.2 | validate.py 单元测试 | `tests/unit/test_validate.py`：断链检测、schema 合规、衰减建议规则 | 覆盖衰减规则的边界 |
| 3C.3 | create/update 集成测试 | `tests/unit/test_create_update.py`：protected 自动标记、version 递增、summary_hash | 临时目录隔离 |
| 3C.4 | 边界测试 | 空记忆库、循环依赖、超大/零 budget、缺失 imports | 所有边界不抛异常，输出合理错误信息 |

---

## 三、Phase 3D：独立发布（待完成）

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 3D.1 | harnesslib 独立 pip 包 | 独立 `pyproject.toml`、`README.md` | `pip install harnesslib` 可在其他项目使用 |
| 3D.2 | llm_gateway 独立 pip 包 | 独立 `pyproject.toml`、`README.md` | `pip install llm-gateway` 可在其他项目使用 |
| 3D.3 | codememory 0.2.0 发布 | `pyproject.toml` 版本号、changelog | `pip install codememory && codememory --root my-memories reindex` |
| 3D.4 | LangChain/Anthropic tool 适配 | `get_tools_for_anthropic()`、`get_tools_for_langchain()` | 三个主流 Agent 框架各一行代码集成 |

---

## 四、Phase 4A：知识治理（maturity + 审计日志 + 溯源）

> 设计讨论：2026-04-27，受外部团队知识库方案启发
>
> 核心理念：记忆的"可信度"应该靠使用验证（不是作者自评），变更历史应该全局可审计

### 4A.1 maturity 字段——记忆成熟度

**动机：** 当前 `intensity`（1-10）是作者自评，"我觉得这条记忆有多重要"。maturity 是靠使用验证，"这条记忆被多少人/多少次验证过是对的"。

**规则：**

```
maturity 三级：
  draft       — 新创建，未经任何验证（默认值）
  verified    — 被 resolve ≥ 3 次（不同会话），Agent 未曾反驳
  proven      — 被 resolve ≥ 10 次 + dependents > 0（被其他记忆引用）

升级：resolve 时自动检查阈值，满足条件自动升级
降级：proven 12 个月无 resolve → validate 建议复核（仅建议，不自动降级）
推翻：update --status superseded → maturity = superseded（被验证为错）
```

**LLM 负担：** 零。maturity 基于 access_count 和 last_access 自动计算。LLM 创建记忆时不需传 maturity 参数（默认 draft），只有导入外部已验证知识时才手动传 `--maturity verified`。

**新增 CLI 支持：**

```bash
codememory search --maturity proven                    # 筛选成熟度
codememory overview --min-maturity verified            # 扫视只看验证过的
codememory validate --check-maturity                   # 检查 maturity 升降建议
```

### 4A.2 全局追加日志 log.md

**动机：** 当前 change_log 按条目分散存储（每个 .md 的 frontmatter 里）。无法回答"这个知识库上周发生了什么"——必须翻几十个文件。全局日志提供**时间线审计**。

**格式约定：**

```markdown
## [2026-04-27] create | [agent] | 新增风险偏好约束 | +1 atom | #session-a3f8
- 新增 user/preferences/position-limit: 单只股票不超过20%

## [2026-04-27] update | [user] | 重新评估加密资产立场 | user/preferences/crypto-stance v2→v3 | #session-b1e4
- change_note: 开始接受小额比特币，不超过5%

## [2026-04-28] verify | [auto] | maturity 自动升级 | draft→verified | #session-c5f0
- user/investment/semiconductor-thesis: resolve 3 次验证通过
```

**实现：** `.codememory/log.md`，只追加不修改。`create`/`update`/`snapshot` 操作完自动追加一行。`codememory log` 命令查看最近 N 条。

### 4A.3 evidence 溯源字段

**动机：** 记录"谁、何时、在哪个会话"贡献了这条记忆。对团队场景是审计，对个人场景是"我什么时候想的这个"。

**新增字段（可选，不强制 LLM 填写）：**

```yaml
---
evidence:
  contributors: ["agent"]            # agent | user | 用户名
  sessions: ["#a3f8c2"]              # 首次创建的会话哈希
  verified_in:                        # maturity 升级时追加
    - session: "#c5f0e2"
      date: "2026-04-28"
---
```

`contributors` 和 `sessions` 由 `create` 自动记录当前会话信息。`verified_in` 由 resolve 自动追加。LLM 不需要手动填写。

### 4A.4 文件变更

| 文件 | 变更 |
|------|------|
| `models.py` | MemoryEntry 加 `maturity: str = "draft"`、`evidence: dict \| None` |
| `resolve.py` | access_count 递增后加 maturity 升降判断（~15 行） |
| `create.py` | 自动写入 evidence（session hash + contributor） |
| `search.py` | 加 `--maturity` 过滤、`--min-maturity` |
| `validate.py` | 加 `_check_maturity_stale()`：proven 长期无访问 → 复核建议 |
| 新增 `log.py` | 全局追加日志：追加函数 + `log` CLI 子命令 |
| `update.py` | 变更时自动追加 log.md |

---

## 五、Phase 4B：知识组织（五层目录 + 语义分类）

> 设计讨论：2026-04-27
>
> 核心理念：目录结构回答"知识放哪"，frontmatter 回答"怎么加载"

### 4B.1 五层目录约定

**动机：** 当前只有 `user/`、`self/`、`schemas/`。无法区分个人偏好、团队约定、技术知识和业务知识。引入可选层级目录，所有文件格式不变。

```
<memory-root>/
├── user/                # Layer 0-P：个人偏好（纯本地，不进 Git）
│   ├── preferences/     #   偏好、习惯、约束
│   └── {domain}/        #   个人对某领域的理解
├── team/                # Layer 0-T：团队约定（Git 共享）
│   └── conventions/     #   编码规范、分支策略、review 流程
├── tech/                # Layer 1：技术知识（跨项目共享）
│   └── wiki/            #   架构决策、技术选型、反模式
├── biz/                 # Layer 2：业务知识（按领域）
│   └── {domain}/        #   业务模型、流程、规则
├── schemas/             # 元模板（不变）
└── .codememory/
    ├── index.json
    └── log.md
```

**imports 可以跨层引用：**

```yaml
# team/conventions/code-review.md（Layer 0-T）
imports:
  required:
    - tech/wiki/git-workflow       # 引用 Layer 1
```

DAG 不关心目录层级——只跟 id 和 imports 打交道。

### 4B.2 semantic_type 语义分类

**动机：** 四种原语（atom/instance/composite/schema）描述**结构角色**（有没有 imports？能不能被引用？）。semantic_type 描述**语义内容**（这段知识是什么性质的？）。

| semantic_type | 定义 | 示例 |
|---------------|------|------|
| `model` | 实体定义、数据结构、关系 | "广告计划包含预算/出价/投放时段" |
| `decision` | 技术选型、架构决策及理由 | "选择事件驱动而非 RPC 同步" |
| `guideline` | 推荐做法（recommend）或禁止做法（avoid） | "公共模块变更后跑兼容性检查" |
| `pitfall` | 已知风险、故障模式 | "广告预算扣减在高并发下会超扣" |
| `process` | 业务流程、状态机 | "广告审核：提交→机审→人审→上线" |

**实现方式：** 放在 tags 里（`tags: ["decision", "architecture"]`），或新增可选字段 `semantic_type`。推荐先用 tags——不需要改 models.py。

### 4B.3 resolve --focus 按语义类型过滤

**动机：** Agent 在"做方案设计"和"做风险排查"两个阶段需要的信息不同。`--focus` 允许 Agent 在 resolve 时只加载特定语义类型的依赖。

```bash
codememory resolve user/investment/context --focus decision     # 只看决策
codememory resolve user/investment/context --focus pitfall      # 只看坑
codememory resolve user/investment/context --focus model,process # 交叉过滤
```

**实现：** resolve 遍历 DAG 时，按节点 tags 中的 semantic_type 过滤。不在指定类型内的节点降级为 summary（仍保留在输出中，保证因果链不断）。

### 4B.4 冷启动 import 命令

**动机：** 新用户记忆库为空。ta 的历史偏好和决策散落在聊天记录、笔记、邮件里。需要一个从非结构化文本中提取初始记忆的路径。

```bash
# 从文件导入
codememory import chat-log.md --extract preferences    # 提取偏好类记忆
codememory import notes.txt --extract decisions        # 提取决策类记忆

# 从 stdin 导入（Agent 会话产物）
cat session-summary.md | codememory import --stdin
```

**LLM 辅助提取：** import 内部调 LLM 做文本分析（"这段文字里有没有偏好声明？有没有决策记录？"），生成 draft 级别的初始记忆。所有导入记忆 maturity=draft，等待后续使用验证。

**安全阀：** import 的产物都是 draft，必须经过 resolve 验证才能升级到 verified。不会因自动提取产生噪声——如果提取错了，它不会被引用，最终被衰减建议标记。

---

## 六、Phase 4C：文档与生态

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 4C.1 | 与外部方案的互操作文档 | `docs/interop-with-team-knowledge.md`：五层目录映射、semantic_type 对照、maturity 对照 | 持有那套方案的团队能直接理解差异和适配方式 |
| 4C.2 | Layer 0 认知接口原理文档 | `docs/layer0-cognitive-interface.md`（已完成） | — |
| 4C.3 | bash 等效性文档 | 同上文件的"Bash 是接口，CLI 是加速器"章节（已完成） | — |

---

## 七、时间线

```
已完成 ─── Phase 1-2 (原型 → 完整记忆闭环)
         Phase 3A-3B (代码质量 + 功能深化)

待完成 ─── Phase 3C (测试体系)  ─── 约 1 周
         Phase 3D (独立发布)    ─── 约 1 周
         Phase 4A (知识治理)    ─── 约 1.5 周
         Phase 4B (知识组织)    ─── 约 1.5 周
         Phase 4C (文档)        ─── 约 0.5 周
```

---

## 八、完成定义

1. `pip install codememory` 可独立安装，`--root` 指向任意记忆数据目录
2. Layer 0 五个认知操作全部可用：`overview` / `focus` / `resolve` / `wander` / `snapshot`
3. Agent 通过 bash CLI 使用全部记忆操作，无需 function-calling 工具列表
4. OpenAI/Anthropic/LangChain 各一行代码集成
5. maturity 自动升降，LLM 零负担
6. 全局 log.md 提供时间线审计
7. 五层目录约定可承载个人到团队的知识
8. 冷启动 import 让新用户从零开始
9. 测试覆盖核心模块 + 边界

---

## 九、风险与缓解

| 风险 | 缓解 |
|------|------|
| maturity 自动升级误判（被 resolve 不等于被验证） | 仅升级到 verified；proven 需要 dependents > 0（被其他记忆引用 = 更强的验证信号）；不自动降级 |
| 全局 log.md 随操作膨胀 | 只追加一行摘要，不是全文变更；可定期归档 |
| import 自动提取产生噪声 | 所有 import 产物 maturity=draft；未被引用的 draft 会被衰减建议标记 |
| 五层目录过度设计 | 全部层级可选——只用 user/ 也能正常工作；团队场景才用到 team/ tech/ biz/ |
