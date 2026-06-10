# CodeMemory Current Sprint

> **Status:** Active — **阶段 A：写入纪律**
> **依据：** `docs/architecture.md` 第 6 章（收敛路径）；概念见 `docs/prd.md` 第 4 / 6 章。
> 实现若需偏离本合同或 architecture.md 契约：先改文档（经 owner 确认），再写代码。

---

## Sprint Goal

落地 proposal（新增类）写入纪律：没把握的新增不再直写 canonical 图，owner merge 后才生效；protected 与 intensity 彻底解耦；atom 可经 CLI 绑定 asset。

---

## Scope（交付项）

### 1. `status: proposed`（新增类载体）

- `codememory create --propose ...` 生成 `status: proposed` 的 atom；
- models / index / reindex 接受并保留 proposed 状态。

### 2. merge / reject 命令

- `codememory merge <id>`：proposed → active + log；
- `codememory reject <id>`：proposed → archived + log；
- 对非 proposed 的 atom 执行时报错退出；
- 实现于 `update.py`，`handle_merge` / `handle_reject` 进 handlers.py，cli.py 只做薄壳。

### 3. 过滤语义

- resolve 与 context-pack（现状两条路径都要生效，阶段 B 合并管线后自然统一）：closure 跳过 proposed / archived / superseded 节点并发 notice；
- search：**默认仅返回 active / draft**（行为变更，金测试固化）；`--status proposed` 等显式过滤可见任意状态。

### 4. check 新增项（validate.py）

- proposed 积压提醒：proposed 状态超过 14 天 → warning；
- proposed / archived / superseded 被 active atom import → warning。

### 5. protected 解耦

- 移除 `create` 中 intensity >= 8 自动设置 protected 的挂钩（intensity 字段本身保留，阶段 C 才删）；
- protected 仅由 owner 手动设置（直接编辑 frontmatter）；agent 侧不提供设置路径。

### 6. `update --source-ref <artifact_id>`

- 向 atom frontmatter 追加 source_refs 条目（artifact_id 必填，summary 可选参数）；
- artifact 不存在时沿用既有 `SOURCE-REF-WARN` 语义（validate 警告，不阻断写入）。

### 7. 文档同步（合同内完成，不另开 sprint）

- `docs/agent-memory-guide.md` 第 0 / 6 节：proposal 过渡做法更新为实际命令用法；
- `.claude/CLAUDE.md` CLI 速查：新增 `--propose` / `merge` / `reject` / `--source-ref`。

---

## Out of Scope

- `build` 命令、两遍式 trim、search 词法排序 → 阶段 B；
- 修改类 proposal patch 队列、intensity 字段删除、focus/overview/wander 删除、models 瘦身 → 阶段 C。

---

## Acceptance Signals（对应 architecture.md §6 阶段 A）

1. `create --propose` 产出的 atom：search 默认不可见；resolve / context-pack 不装配且有 notice；
2. `merge` 后可见、可装配；`reject` 后 status=archived；两者都留 log 记录；
3. `validate` 能报 proposed 积压与"非 active 被 import"警告（fixture 验证）；
4. `create --intensity 8` 不再自动产生 `protected: true`；
5. `update --source-ref` 后 reindex，source_refs 进入 index 并被 context-pack 渲染；
6. 全部既有测试不回归，新行为有单测覆盖。

---

## Verification Commands

```bash
PYTHONPATH=src python -m pytest tests/unit -q          # 全绿
# CLI 冒烟（依次执行）：
codememory create --propose --id user/facts/demo-proposed --tags "demo"
codememory search --query demo-proposed                 # 默认不可见
codememory search --query demo-proposed --status proposed   # 可见
codememory resolve user/facts/demo-proposed             # 不装配/notice 行为按契约
codememory merge user/facts/demo-proposed
codememory search --query demo-proposed                 # 可见
codememory validate                                     # 含积压 fixture 时输出提醒
```

---

## Constraints

- TDD：先写失败测试，再实现（红-绿循环）；
- 业务逻辑只进 handlers.py / 核心模块；cli.py、tools.py 保持薄壳；
- 禁止新增第三方依赖；不碰 `src/harnesslib/`、`src/llm_gateway/`；
- 注意 `docs/plan/pitfalls.md`（路径约定、examples 测试副作用、decay 警告对 fixture 的干扰）。

---

## References

- `docs/architecture.md` §3.2 / §3.3（状态机与载体）、§4.3 / §4.4（check 与变更操作）、§6（验收信号）
- `docs/prd.md` §6（写入纪律）
- `docs/plan/pitfalls.md`
