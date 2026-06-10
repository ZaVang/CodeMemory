# CodeMemory Current Sprint

> **Status:** Active — **阶段 B：读路径收敛**
> **依据：** `docs/architecture.md` §4.1（build 管线）、§4.2（search 排序）、§6（验收信号）。
> 实现若需偏离本合同或 architecture.md 契约：先改文档（经 owner 确认），再写代码。

---

## Sprint Goal

三个装配命令收敛为一条管线（新模块 `build.py`），裁剪从"拓扑序贪心"升级为"两遍式按价值分配"，search 获得词法排序。读路径从此只有一个实现。

---

## Scope（交付项）

### 1. `build.py`（新模块，管线唯一实现）

- 迁移 `context_pack.py` 的 ContextPack 模型 / builder / renderers 与 `resolve.py` 的 DAG 工具（`build_dag` / `_get_imports` / `topological_sort` / `find_cycle_participants`）到 `build.py`；
- `resolve.py` / `context_pack.py` 保留为薄兼容 shim（re-export），不破坏现有 import 路径；shim 的去留随阶段 C 处置。

### 2. 两遍式 trim（architecture §4.1 第 4 段）

- 第一遍按角色分配预算：target → required → recommended → related 依序拿全文；某一级放不下时，级内按（被依赖数 desc → access_count desc）排序，靠后的降级 summary；target / required 最低降到 summary，永不 skipped；related 可 skipped；
- 第二遍按拓扑序渲染——阅读顺序与预算分配解耦；
- 金测试：required 叶子的大正文不再挤占 target 的预算。

### 3. resolve / context-pack 变薄别名

- `resolve(id, ...)` = `render(build_context_pack(...), "plain-markdown")`；管线异常映射为 `Error: ...` 字符串（保持 CLI 返回行为）；
- 装配副作用收敛为管线统一实现：保留 access_count / last_access 更新与 stale notice；**移除旧 resolve 实现中的 maturity 自动升级与 stability SInc 增长**——依据 architecture §5.1：maturity/evidence 是惰性元数据，不参与 build 机制；stability 属阶段 C 删除对象，不再喂养；
- 旧格式/旧副作用的既有测试断言随契约迁移（在金测试中固化新行为）。

### 4. `codememory build` 命令

- `build <id> [--depth required|recommended|full] [--budget N] [--focus tag] [--task-goal "..."] [--format xml-markdown|markdown|plain-markdown|json]`，默认 format=xml-markdown；
- `handle_build` 进 handlers.py，cli.py 薄壳。

### 5. 三命令一致性（验收核心）

- 同参数下：`build --format plain-markdown` 输出 ≡ `resolve`；`build --format xml-markdown` 输出 ≡ `context-pack`（逐字符一致，金测试固化）。

### 6. search 词法排序（architecture §4.2）

- 分词：空白 + 标点切分；每个 token 对字段做大小写不敏感子串匹配；
- `score = Σ(field_weight × 该字段命中 token 数 / 总 token 数)`，权重 id=4 / summary=3 / tags=2 / body=1；
- 全部 token 零命中才淘汰（OR 语义）；单 token query = 现状子串匹配的加权版；
- 排序：score desc → 被依赖数 desc → access_count desc → id asc；
- 金测试：多 token query 下，多字段命中者排在单字段弱命中者之前。

### 7. 文档同步（合同内完成）

- guide §0 对照表：build 为主命令，resolve / context-pack 标注为别名；
- CLAUDE.md：CLI 速查加 build，概念对照更新（build 已收敛）；
- prd.md §4.2：build / search 行的实现状态注记更新；
- architecture.md §2 映射表：build / search 行现状注记更新。

---

## Out of Scope

- intensity 全链路移除、focus/overview/wander 删除、test 契约、修改类 proposal patch 队列 → 阶段 C；
- 语义/向量检索 → 非目标（prd §8）。

---

## Acceptance Signals（对应 architecture.md §6 阶段 B）

1. 三命令一致性金测试通过（逐字符相等）；
2. 裁剪金测试：预算不足时 target 全文保留，低价值 required 叶子降级 summary；related 在预算外被 skipped；
3. 排序金测试通过；单 token 行为与现状兼容；
4. 装配不再写 maturity / stability（金测试固化惰性元数据契约）；
5. 全套既有测试在断言迁移后全绿，集成测试通过；
6. `codememory build` CLI 冒烟通过，与 resolve 输出 diff 为空。

---

## Verification Commands

```bash
PYTHONPATH=src python -m pytest tests/unit -q
PYTHONPATH=src python tests/integration_test.py
# CLI 冒烟：
codememory build <entry> --format plain-markdown > a.txt
codememory resolve <entry> > b.txt && diff a.txt b.txt   # 为空
codememory search --query "多 词 查询"                    # 观察排序
```

---

## Constraints

- TDD：先写失败测试再实现；纯代码搬移（shim 化）以全套测试保持绿色为准；
- 业务逻辑只进 handlers.py / 核心模块；cli.py、tools.py 薄壳；
- 禁止新增第三方依赖；不碰 `src/harnesslib/`、`src/llm_gateway/`；
- 提交前恢复 examples 生成文件（pitfalls）。

---

## References

- `docs/architecture.md` §2（模块映射）、§4.1 / §4.2（管线与排序契约）、§6（验收）
- `docs/plan/HISTORY.md` 阶段 A 记录（过滤语义已在管线两条路径生效，合并后自然统一）
- `docs/plan/pitfalls.md`
