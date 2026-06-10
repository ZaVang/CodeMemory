# CodeMemory PRD 重建设计：memory-as-code 公理化

**日期**：2026-06-10
**状态**：已确认（owner 逐节批准）
**产出**：本设计指导重写 `docs/prd.md`、`docs/agent-memory-guide.md`，并同步 `.claude/CLAUDE.md` 术语。

---

## 1. 背景与动机

项目文档存在两代世界观共存的混乱：原始公理时代（CLAUDE.md：Layer 0 五个认知操作、记忆原子化协议）与 2026-05 pivot 时代（prd/architecture：Source Artifact Registry、ContextPack、Work/Companion Layer、Memory Compiler）。概念靠叠加补丁引入，三处文档互相漂移。

本次重建回到唯一公理，白纸推导概念集，再对照现状决定旧概念去向。

## 2. 已确认的关键决策

| 决策点 | 结论 |
|---|---|
| 概念处理原则 | 白纸重推，再对照现状（不是叙事重组，不是逐个审计旧概念） |
| 主场景 | 跨项目个人工作记忆：库独立于任何代码 repo，单 owner，多 agent 消费 |
| 写入纪律 | 分级：低风险直写，高风险走 proposal/review |
| PRD 结构方案 | 全工作流：按开发者循环推导完整概念集，概念模型一次定型，v1 实现可分期 |

## 3. 公理

> **记忆按代码的方式组织——原子化、显式依赖、按需装配。**
> 一个记忆库就是一个仓库，agent 是它的运行时。

三推论：原子化（一个文件一个语义单元）、显式依赖（imports 声明，不靠相似度猜测）、按需装配（入口 + 依赖闭包 + 预算裁剪，不是全文检索）。

## 4. 概念模型（三组 11 概念）

### 静态结构

| 概念 | 代码对应物 | 定义 | 实现状态 |
|---|---|---|---|
| repo（记忆库） | git 仓库 | 一个目录树 = 一个库；`.codememory/` = `.git/` | 已实现 |
| atom（记忆单元） | 模块/函数 | 一个 .md 文件；frontmatter = 接口，body = 实现；summary = 签名 + docstring，必须独立可读 | 已实现 |
| imports（依赖） | import 语句 | "理解此记忆需先理解什么"；required/recommended/related | 已实现 |
| schema（结构契约） | 接口/类型定义 | 某类 atom 的字段约定 | 已实现 |
| asset（资产） | repo 里的 data/、vendored 文件 | 原始材料（长文档/会议记录/PDF/代码）：登记（路径+hash+摘要）、可被 atom 引用、可按需展开；不是 atom，不进依赖图 | 已实现（现名 Source Artifact，`sources.py`） |

### 动态操作

| 概念 | 代码对应物 | 定义 | 实现状态 |
|---|---|---|---|
| build（装配） | 构建/链接 + tree-shaking | 入口 atom → imports 闭包 → 拓扑排序 → 预算内裁剪（超预算按 target > required > recommended > related 降级 summary）→ 结构化上下文 | 已实现（现名 resolve + context_pack，待动词收敛） |
| check（校验） | 类型检查 + linter | 断链、循环、schema 违约、stale asset、孤儿 | 已实现（现名 validate） |
| search（检索） | 符号搜索/LSP | 只负责找入口，找到后一切走 build；词法排序，不做语义装配 | 部分实现（现为子串匹配） |
| test（验证） | 测试/CI | 入口 atom 可附黄金问题：装配出的上下文应能让 agent 回答 X；最小形态 = 题集 + LLM judge | 未实现（概念本次定型） |

### 变更管理

| 概念 | 代码对应物 | 定义 | 实现状态 |
|---|---|---|---|
| proposal（提案） | Pull Request | 高风险变更落为 `status: proposed`，不进默认 build，owner merge 后生效 | 未实现（概念本次定型） |
| log（日志） | git log | 变更审计轨迹（change_note / log.md） | 已实现 |

## 5. 命名决策

1. 保留已立住的名字：atom / imports / schema / validate（CLI 命令名不强制改）。
2. 新立动词用 code 词汇：build / propose / merge / test / asset。
3. `resolve` 与 `context_pack` 双动词收敛为 `build`，旧名作兼容别名；"ContextPack" 不再作为独立概念，就是 build 的产物。
4. **intensity（1-10）砍掉**：重要性由图结构（被依赖数）表达。
5. **protected 重定义**：从"intensity≥8 自动加锁"改为分级写入纪律的判据——动 protected atom 必须走 proposal。

## 6. 核心循环

**读路径（agent 接活）：**
任务 → search 找入口 → build（含预算）→ 需要原文时 asset expand → 干活。

**写路径（agent 沉淀，分级纪律落地处）：**
形成新判断 → 按 guide 判断值不值得记/记成什么/依赖谁 → 分级：
- **低风险，直写**：新增 atom（可声明自己的 imports），不修改任何已有文件；
- **高风险，propose**：修改已有 atom（正文或其 imports）、或变更涉及 protected atom；
→ owner 异步 review → merge/reject/edit → 写入后 check 守门。

**维护循环（owner 周期性）：**
check 报 stale asset → 复核受影响 atom；orphans 报不可达 → 归档或重挂依赖；test 跑黄金问题 → 装配质量回归。

## 7. 旧概念对照表（将作为新 PRD 附录）

| 旧概念 | 去向 | 理由 |
|---|---|---|
| Source Artifact / Registry | → asset（保留实现，改名降重） | 概念正确但被包装成平行体系 |
| source_refs | → asset ref（保留） | 语义不变 |
| ContextPack | → build 的产物（保留实现） | 不再作为独立概念 |
| resolve | → build 的兼容别名 | 双动词收敛 |
| Anchor Atom / Derived Atom | → guide 里的写法模式 | 不配专有名词 |
| Memory Compiler | → importer（迁移工具，保留） | = codemod；"自动结果默认是 proposal"纪律保留 |
| intensity | → 砍 | 重要性由图结构表达 |
| Work / Companion Layer | → 砍 | 场景已锚定；目录约定进 guide；companion 文档留 docs/reference/ |
| overview / focus / wander | → 砍；focus 能力并入 build 参数 | 拟人范式残留，被 search/build/expand 覆盖 |
| TransientDAG / snapshot | → 保留为辅助工具（REPL 草稿） | 非核心概念 |
| maturity / cache_stable / heat | → 实现细节，移出概念层 | 不进 PRD |
| disclosure L0-L3 | → 不作为独立概念 | 是 build 预算 + asset expand 的自然结果 |

## 8. 新 prd.md 大纲

1. 公理（一句话 + 三推论）
2. 背景与问题（继承旧 PRD 痛点，压缩到半页）
3. 主场景（跨项目个人工作记忆；非目标场景）
4. 概念模型（三组 11 概念，含实现状态标注）
5. 核心循环（读/写/维护）
6. 写入纪律（直写条件、提案条件、protected 新语义）
7. 成功标准
8. 非目标
9. 附录：旧概念对照表
10. 术语表

## 9. 新 agent-memory-guide.md 大纲（agent 的 CONTRIBUTING.md）

1. 你在贡献什么（向一个代码式记忆库提交变更）
2. 写入门槛（三个月后还重要吗？丢了会导致错误决策吗？）
3. 记成什么：目录约定 + schema 选择（保留现有目录体系）
4. summary 规范（签名 + docstring：裁剪后只剩它）
5. imports 声明判据（required/recommended/related，好坏例子）
6. asset 引用规范（长材料登记为 asset，atom 只写语义索引）
7. 直写还是提案（分级纪律判断清单）
8. 完整场景示例（示例域从投资换成工作：记录架构决策 / 沉淀排障流程 / 登记设计文档）
9. 常见错误速查（保留，术语更新）

## 10. 成功标准（写入新 PRD 第 7 章，描述产品 v1 的成功，非本次文档重建的验收）

**产品侧：**
- 新 agent 通过 search → build 重建某项目关键上下文，并通过该入口的黄金问题测试；
- 高风险变更 100% 走 proposal（check 可验证）；
- 重要结论可追溯到 asset 或 change_log。

**工程侧：**
- 所有 adapter（CLI/MCP/REST/SDK）调同一 core handler；
- prd / architecture / CLAUDE.md 三处术语一致；
- check 全绿是任何 merge 的前置条件。

## 11. 非目标

1. 语义向量检索作为装配机制（search 只做词法入口发现）；
2. 多人协作与权限系统；
3. 拟人记忆、遗忘、陪伴体验（companion 留 docs/reference/）；
4. 把长文档塞进 atom body；
5. LLM 直写高风险路径；
6. 图的分支管理（proposal 是状态，不是分支）。

## 12. 范围边界

本次实施 = 重写 `docs/prd.md` + `docs/agent-memory-guide.md` + 同步 `.claude/CLAUDE.md` 术语，**不动代码**。

CLAUDE.md 同步原则：概念部分（核心概念、Layer 0 表格、设计哲学表述）按新术语重写；工程硬约束（Agent 只用 bash、Pydantic v2、代码规范、测试规范、端口表）保持不变——它们与概念重建正交。

代码层收敛（build 动词统一、intensity 字段移除、proposed 状态、search 词法排序、test 最小实现）属于后续 architecture.md 确认后的 sprint，不在本次范围。

## 13. 风险与缓解

| 风险 | 缓解 |
|---|---|
| PRD 含"已定义未实现"概念（test/proposal），sprint 长期不跟进会再次形成文档-现实漂移 | 概念表诚实标注实现状态；FUTURE.md 的 roadmap 优先级随新 PRD 更新 |
| 旧术语在代码注释/测试/前端文案中残留，与新文档不一致 | 本次只承诺三份文档一致；代码层术语随后续 sprint 渐进收敛 |
| examples/investment 示例数据与 guide 新工作域示例不一致 | examples 定位为"另一个记忆库的示例数据"，guide 中注明即可，不删除 |
