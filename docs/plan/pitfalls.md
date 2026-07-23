# CodeMemory Sprint Pitfalls

Recurring implementation notes for future sprints.

---

## Path convention

The local `sprint` skill still references the older `docs/plans/` path. This repository now uses singular `docs/plan/`.

Use:

- `docs/plan/FUTURE.md`
- `docs/plan/SPRINT.md`
- `docs/plan/HISTORY.md`
- `docs/plan/pitfalls.md`

Do not recreate `docs/plans/`.

---

## Test side effects

Some API tests can rewrite example dataset generated files, especially:

- `examples/companion/.codememory/index.json`
- `examples/companion/.codememory/log.md`

If those files change only because tests reindexed or logged operations, restore them before finalizing unless the sprint intentionally changes example data.

If a sprint intentionally changes example Markdown metadata, the checked-in index is part of that contract. After regression tests touch runtime counters/logs, restore the affected index/log from `HEAD`, then reindex once from the cleaned Markdown. This preserves the pre-test runtime baseline while retaining the intentional schema/metadata update; simply restoring the index would reintroduce stale published fields.

---

## build 不自动展开 asset 原文

实现 asset 相关功能时，不要让 build 产物（resolve / context-pack 输出）自动内联 asset 的原文正文。

build 产物默认只携带 asset 引用（source_refs）；原文获取必须走显式的 `source expand`。这保证长文档不会未经请求就进入 agent 的 handoff 上下文。（概念边界见 `docs/architecture.md` §3.5。）

---

## Importer provenance 必须锚定原始字节和真实正文位置

- Source Artifact registry 使用文件字节 SHA-256；compiler review 也必须复用同一字节 hash。不要对 `read_text()` 的换行归一化结果再 hash，否则 Windows CRLF 文件会在 registry 与 proposal provenance 之间产生两个 hash。
- Markdown section 的正文定位必须从 heading 行之后开始。直接对整个 raw section 使用 `find(section.body)`，在 heading 文本与正文首段相同时会误命中 heading，产生错误行号。
- 同一 `review_id` 重试只可忽略 `created_at` 与 decision 差异；相同输入保留已有 review 字节和 decisions，不同输入必须在 registry/review 写入前拒绝。

---

## Personal Profile capability 与 validity 分离

普通目录和缺少 remote 的 Git repo 都是合法 Personal Profile。`profile_valid` 只判断实例合同；Git/remote 只产生独立 capability 状态。Capture 不得因为 `git_delivery=unavailable` 失败，也不要在 init 中隐式执行 `git init` 或创建 remote。

凡是 Profile 允许配置的路径，ignore、tracked 检查、安全提示和扫描都必须从实际 Profile 值派生；不能用默认目录名代替合同值。

---

## Dedicated adapter 必须绑定 root

`CodememoryToolkit` 与 MCP 是实例边界，不是任意文件浏览器。导出给模型的 schema 不包含 `root`；Sandbox 即使收到调用方伪造的 `root` 也必须用构造时绑定的 root。CLI 的 operator `--root` 仍是可信本地入口。

root 绑定还必须覆盖 caller-controlled ID。不能用 `replace("..", "")` 之类字符串清洗代替路径验证；memory/proposal ID 应拒绝绝对路径、反斜杠、盘符、空段和 `.` / `..`，并在写入前对 resolve 后的目标执行相对于 bound root 的 containment 检查。create、propose、update、merge/reject 和 promotion 必须复用同一边界。

---

## MCP 与 Toolkit 不能各自维护工具合同

- agent tool 的名称、JSON Schema、read-only hint 和 dispatcher 必须来自一个共享 catalog；MCP / OpenAI / Anthropic / Gemini 只做机械格式转换。
- tool profile 由绑定 root 决定：普通实例是精确最小集，Personal Profile 只追加已定义扩展。不要用 import-time cwd 推断运行时 profile。
- `propose` 的判据是 owner merge 前 target bytes 不变。写入 canonical Atom 后再加 `[PROPOSED]` 日志不构成 proposal；修改类必须进入 patch queue。
- agent create 若需要完整 summary/body/imports，应在一次 Core create 中落盘，不能由 adapter 先建半成品再 direct update；Personal Profile agent create 必须强制 proposed。

---

## Topic 内 Claim 的 Phase 1A 解析边界

月度 incubator 文件按 `##` Topic section 解析；`###` Claim block 属于 Topic body，Phase 1A 原样保留但不拆文件、不独立索引。Topic 可以 `origin: mixed`，但不能继承其中各 Claim 的 `claim_status`。

---

## 扫描 warning 不等于记录仍然有效

Capture 出现不完整 block 或 payload hash mismatch 时，validate 必须报告；扫描器不能在 warning 后继续把该记录加入有效结果。typed index、stable-ID read 和未来 maintenance 必须共享同一个“只返回完整且 hash 有效记录”的边界。

---

## Git delivery 恢复与安全输入边界

- `scan_passed` 不等于 delivery 已完成。公开 `maintenance resume` 必须重新进入 delivery，并从 `CodeMemory-Run` trailer 找回“commit 已创建但本机 state 未落盘”的 commit；push 失败只重试同一 commit。
- 不要解析 Git 面向人的 quoted porcelain 输出并把显示字符串传回 pathspec。涉及任意 Unicode 文件名时使用 `-z` 的 NUL-delimited 输出；diff locator 使用未 quote 的 UTF-8 path。
- 敏感扫描不能只依赖已知 token 前缀。还要检测可疑高熵候选，同时排除普通 hex content hash；finding 只能暴露 rule/path/locator。
- merge/delete 等复合写操作必须在第一次写入前完成自引用、目标存在性和路径约束校验。尤其 self-merge 必须无副作用失败，不能写后再依赖旧 revision 查找。

---

## Eval baseline 不能泄漏标准答案或动态 metadata

- full-memory 对照不能直接拼接原始 Atom 文件。frontmatter 内含 `golden_questions.expect`，原样发送会把标准答案泄漏给 answer model。只渲染可装配 Atom/Schema 的稳定 ID、summary 和 authored body。
- ContextPack render 含动态 `generated_at`。评测冻结时必须替换为固定值，否则相同 dataset/options 的 context hash 和实际 prompt 每次都变化。
- answer model 只看 question + arm context；judge 只看 question + expect + answer。arm/context 不能进入 judge，expect 不能进入 answer。
- 报告可保留 answer / expect / verdict 供审计，但不得复制 context、prompt、config path、credential、raw provider response 或 thinking。

---

## Semantic discovery 是 private derived index，不是第二条 build 图

- 语义索引输入必须复用 typed index 的有效对象边界；损坏 Capture、不可装配 Atom 不能因为 embedding 扫文件而重新进入候选。
- containment 必须逐级验证：先证明 resolved `paths.private_local` 仍在 bound root 内，再证明 resolved model/index path 位于该 private root 内。只做第二级检查会让 junction/symlink 把信任锚整体搬到实例外。
- 本地 adapter 固定 `local_files_only=True`，不能隐式下载或 network fallback。
- 相同 input digest + model fingerprint 重建不得调用 embedder或重写索引；内容/模型变化时 query 先报 stale，不能用旧向量“尽量返回”。
- 查询不能把 raw query 写进索引或日志。索引只保留 typed ID/hash/vector 与安全 locator，不保留绝对 root/model path。
- canonical build 永远不能 import 或读取 semantic index；候选 Atom 仍走 imports DAG，Capture/Topic/Claim 仍走稳定 ID read。
