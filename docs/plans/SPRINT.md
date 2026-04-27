# Sprint 6 — 代码质量 + 功能深化

> **起始日期**：2026-04-27
> **前置条件**：Sprint 5 完成（Phase 2 全闭环可交付）
> **目标**：消灭已知技术债务（handler 去重、Pydantic 迁移、logging）；补齐功能深化缺口（changelog、wander 加权、snapshot 统一、示例修复）

---

## 一、现状评估

| 问题 | 严重程度 | 影响 |
|------|----------|------|
| cli.py + tools.py handler 重复 | 高 | 每次新增命令要改两处，Sprint 1-5 每次 Generator 都复制相同逻辑 |
| 核心数据用裸 dict | 高 | CLAUDE.md 硬约束要求 Pydantic v2 但从未落；`MemoryEntry`、`IndexData` 无类型安全 |
| print() 混用 stdout/stderr | 中 | notice/warning/error 全部走 `print(file=sys.stderr)`，无法按级别过滤 |
| 示例 summary_hash 过时 | 中 | 8 个样例文件 `summary_hash: placeholder`，overview stale 检测对全部 8 个误报 |
| 无 changelog 查看命令 | 低 | `change_log` 数据在磁盘，但没有 `changelog` 命令来查看 |
| wander 1/3 硬切 | 低 | 权重生硬，access_count=0 和 access_count=1 在同一个池等概率 |
| snapshot 两条路径 | 低 | `--target` vs `--from-dag` 逻辑重叠 |

---

## 二、Sprint Backlog

### 任务 1：handler 去重 — 提取共享命令逻辑 ✅

**新建 `src/codememory/handlers.py`，将所有命令的业务逻辑从 cli.py 和 tools.py 中提取出来，三处委托同一份实现。**

| # | 子任务 | 说明 |
|---|--------|------|
| 1.1 | 提取 handler 函数 | `handle_create(root, args)` `handle_resolve(root, args)` 等 10 个同步函数，参数为 root + dataclass/namedtuple |
| 1.2 | cli.py 改为薄壳 | 每个子命令 handler 变为 `result = handle_xxx(root, args); print(result)` |
| 1.3 | tools.py handler 委托 | 每个 async handler 变为 `loop.run_in_executor(handle_xxx, ...)` 或直接调用同步版 |
| 1.4 | 行数验证 | cli.py 从 300+ 行降到 150 行以内 |

**产出**：新增 `src/codememory/handlers.py`，修改 `cli.py`、`tools.py`

**验收**：
```bash
# 功能完全等价
codememory --root examples/investment reindex && codememory --root examples/investment validate
codememory --root examples/investment resolve user/investment/context | head -5
codememory --root examples/investment search --type atom | head -3
codememory --root examples/investment orphans | head -3
codememory --root examples/investment wander --inject
codememory --root examples/investment overview
codememory --root examples/investment focus user/investment/risk-tolerance --level summary

# cli.py 行数
wc -l src/codememory/cli.py  # < 200
```

---

### 任务 2：Pydantic v2 数据模型 ✅

**所有模块间 API 边界从裸 dict 切换为 Pydantic v2 BaseModel。**

| # | 子任务 | 说明 |
|---|--------|------|
| 2.1 | `src/codememory/models.py` | `MemoryEntry`（type/id/summary/status/tags/intensity/version/path/access_count/last_access/imports/schema/summary_hash/protected）、`IndexData`（version/updated/memories: dict[str, MemoryEntry]）、`ImportRef`（id/pin/reason） |
| 2.2 | index.py 适配 | `load_index()` 返回 `IndexData`；`save_index()` 接收 `IndexData`；`reindex()` 构建 `IndexData.model_validate()` |
| 2.3 | resolve.py 适配 | `build_dag()` / `resolve()` 参数从 `dict` 改为 `IndexData` |
| 2.4 | 其余模块适配 | search/validate/create/update/orphans 全部使用 `MemoryEntry` 和 `IndexData` |
| 2.5 | `__init__.py` 导出 | `from codememory.models import MemoryEntry, IndexData, ImportRef` |

**产出**：新增 `src/codememory/models.py`，修改 index/resolve/search/validate/create/update/orphans/__init__

**验收**：
```bash
# Pydantic v2 序列化
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='test/x', summary='test', status='active',
                tags=[], intensity=5, version=1, path='test/x.md',
                access_count=0)
d = e.model_dump(mode='json')
assert d['type'] == 'atom'
print('OK: Pydantic v2 model_dump')

# 禁止 Pydantic v1 API
import pydantic
assert hasattr(pydantic, 'BaseModel')
print(f'OK: pydantic version {pydantic.__version__}')
"

# 功能回归
codememory --root examples/investment reindex && codememory --root examples/investment validate
codememory --root examples/investment resolve user/investment/context | grep "Resolved Context"
```

---

### 任务 3：print() → logging 迁移 ✅

**所有 stderr 输出统一走 `logging` 模块，stdout 正文保留 `print()`。**

| # | 子任务 | 说明 |
|---|--------|------|
| 3.1 | logging 配置 | `core.py` 中设置 `logging.basicConfig(level=logging.WARNING, format='[%(levelname)s] %(message)s')` |
| 3.2 | 替换规则 | `print(f"Error: ...", file=sys.stderr)` → `logging.error(...)`；`print(f"Warning: ...", file=sys.stderr)` → `logging.warning(...)`；`[NOTICE]` → `logging.info(...)` |
| 3.3 | resolve notice 输出 | `[NOTICE]` 行仍输出到 stderr（通过 logging.info），不掺入 resolve 正文（正文走 stdout print） |
| 3.4 | `--verbose` / `--quiet` | CLI 全局参数：`-v` 设置 `logging.getLogger().setLevel(logging.INFO)`；`-q` 设 `ERROR` |

**产出**：修改 `core.py`、`resolve.py`、`validate.py`、`index.py`、`create.py`、`update.py`、`cli.py`（加全局 --verbose/--quiet）

**验收**：
```bash
# --quiet 抑制 warnings
codememory --root examples/investment validate -q 2>&1 | wc -l  # 应 < 5 行

# --verbose 显示 info
codememory --root examples/investment resolve user/investment/context -v 2>&1 | grep -i "notice\|loaded"

# 默认级别（WARNING+）
codememory --root examples/investment validate 2>&1  # 含 [DECAY-WARN]，不含 INFO
```

---

### 任务 4：示例记忆 summary_hash 修复 ✅

**更新全部 8 个样例文件 + index.json，使 `summary_hash` 与实际 body 一致。**

| # | 子任务 | 说明 |
|---|--------|------|
| 4.1 | 批量计算脚本 | 遍历 `examples/investment/` 下所有 .md 文件，计算 body hash → 更新 frontmatter 中的 `summary_hash` |
| 4.2 | index.json 同步 | reindex 后确认 index 中的条目不受影响（reindex 不存储 summary_hash，只存 path 等） |
| 4.3 | 验证 stale 清零 | `overview` 对 8 个样例不再输出 `[stale]` |

**产出**：修改 8 个样例文件的 frontmatter

**验收**：
```bash
# overview 无 stale 误报
codememory --root examples/investment reindex
codememory --root examples/investment overview | grep -c "stale"  # 应为 0

# 各文件 hash 匹配
PYTHONPATH=src python -c "
from pathlib import Path
from codememory.core import parse_frontmatter, compute_body_hash
root = Path('examples/investment')
for f in sorted(root.rglob('*.md')):
    meta, body = parse_frontmatter(f)
    if not meta or 'summary_hash' not in meta:
        continue
    expected = compute_body_hash(body)
    assert meta['summary_hash'] == expected, f'{f}: {meta[\"summary_hash\"]} != {expected}'
    print(f'OK: {f.relative_to(root)}')
print('ALL HASHES VALID')
"
```

---

### 任务 5：changelog 命令 ✅

**新增 `codememory changelog <id>` 命令，展示记忆的变更历史。**

| # | 子任务 | 说明 |
|---|--------|------|
| 5.1 | `src/codememory/changelog.py` | 读取记忆的 `change_log` 列表，按时间倒序格式化输出 |
| 5.2 | 输出格式 | `v3 (2026-04-27): <change_note>` 缩进列表 |
| 5.3 | CLI 注册 + tools.py | `changelog` 子命令 + `changelog` Sandbox tool |

**产出**：新增 `changelog.py`，修改 `cli.py`、`tools.py`

**验收**：
```bash
# 先制造变更历史
codememory --root examples/investment update user/investment/risk-tolerance --change-note "Sprint 6 测试 changelog"
codememory --root examples/investment update user/investment/risk-tolerance --summary "updated summary" --change-note "更新摘要"
codememory --root examples/investment changelog user/investment/risk-tolerance
# 应输出 2 条以上变更记录
git checkout -- examples/investment/user/investment/risk-tolerance.md
codememory --root examples/investment reindex
```

---

### 任务 6：wander 加权概率 ✅

**wander cool 模式从"最低 1/3 等概率"改为加权随机。**

| # | 子任务 | 说明 |
|---|--------|------|
| 6.1 | 权重公式 | `weight = 1.0 / (access_count + 1)`，排除 protected（intensity >= 8） |
| 6.2 | `random.choices(k=1, weights=...)` | 替换当前 `candidates[:len(candidates)//3]` 硬切逻辑 |
| 6.3 | 保留 `--mode random` | 等概率模式不受影响 |

**产出**：修改 `cli.py` wander handler

**验收**：
```bash
# 多次 wander 结果有变化但冷记忆更频繁出现
for i in $(seq 1 5); do
  codememory --root examples/investment wander --inject
done
# 观察输出，低 access_count 的记忆（冷测试文件）应更频繁出现
```

---

### 任务 7：snapshot 统一 ✅

**`snapshot --target <id>` 内部自动构建临时 DAG，消除与 `--from-dag` 的两条路径。**

| # | 子任务 | 说明 |
|---|--------|------|
| 7.1 | snapshot.py 重构 | `snapshot(root, snapshot_id, target=None, dag=None)`：无 dag 时从 index 构建临时 DAG → resolve → 落盘 composite |
| 7.2 | `--target` 和 `--from-dag` 互斥 | 只能传其中一个，内部走统一落盘逻辑 |
| 7.3 | cli.py handler 简化 | 委托 `handlers.py` 的 handler |

**产出**：修改 `snapshot.py`、`cli.py`

**验收**：
```bash
# --target 模式（自动构建临时 DAG）
codememory --root examples/investment snapshot test-target-snap --target user/investment/context
ls examples/investment/user/snapshots/*test-target-snap.md 2>/dev/null && echo "OK: snapshot created"
rm -f examples/investment/user/snapshots/*test-target-snap.md

# --from-dag 模式（原有路径不受影响）
PYTHONPATH=src python -c "
import tempfile, json, subprocess, sys
from pathlib import Path
from codememory.transient import TransientDAG
dag = TransientDAG()
dag.add('s/x', type='atom', summary='X', body='X', intensity=5)
tf = Path(tempfile.mktemp(suffix='.json'))
tf.write_text(json.dumps(dag.to_dict(), ensure_ascii=False))
r = subprocess.run([sys.executable, '-m', 'codememory.cli', '--root', 'examples/investment',
    'snapshot', 'test-from-dag', '--from-dag', str(tf)], capture_output=True, text=True)
print(r.stdout or r.stderr)
snap = list(Path('examples/investment/user/snapshots').glob('*test-from-dag*'))[0]
assert snap.exists()
print(f'OK: {snap.name}')
snap.unlink()
tf.unlink()
"
```

---

### 任务 8：回归验证 + 清理 ✅

**确保 Sprint 6 重构不破坏已有能力。**

| # | 验证项 |
|---|--------|
| 8.1 | 10 个 CLI 命令全部可用：create/resolve/reindex/validate/search/orphans/wander/snapshot/overview/focus/changelog |
| 8.2 | `pip install -e .` + codememory 全局 CLI |
| 8.3 | CodememoryToolkit 9+1 tools（+changelog） |
| 8.4 | `tests/integration_test.py` 24/24 PASS |
| 8.5 | Sprint 1-5 验收脚本不退化 |
| 8.6 | 清理测试文件 + `git checkout -- risk-tolerance.md` |

---

## 三、文件变更总览

```
新增：
  src/codememory/handlers.py          # 共享命令 handler
  src/codememory/models.py            # Pydantic v2 数据模型
  src/codememory/changelog.py         # changelog 命令

修改：
  src/codememory/__init__.py          # 导出新模块
  src/codememory/cli.py               # 薄壳（-200 行）+ --verbose/--quiet
  src/codememory/tools.py             # handler 委托 + changelog tool
  src/codememory/core.py              # logging 初始化
  src/codememory/index.py             # Pydantic 适配
  src/codememory/resolve.py           # Pydantic + logging
  src/codememory/validate.py          # Pydantic + logging
  src/codememory/create.py            # Pydantic + logging
  src/codememory/update.py            # Pydantic + logging
  src/codememory/search.py            # Pydantic
  src/codememory/orphans.py           # Pydantic
  src/codememory/snapshot.py          # 统一路径
  examples/investment/user/investment/*.md  # summary_hash 修复 (7 files)
  examples/investment/schemas/decision.md   # summary_hash 修复

不修改：
  src/codememory/transient.py
  src/harnesslib/**
  src/llm_gateway/**
```

---

## 四、验收命令汇总

```bash
# ── 模块导入 ──
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry, IndexData
from codememory.handlers import handle_resolve
from codememory.changelog import changelog
print('OK')
"

# ── handler 去重：cli.py < 200 行 ──
wc -l src/codememory/cli.py

# ── Pydantic v2 ──
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='t/x', summary='s', status='active',
                tags=[], intensity=5, version=1, path='t/x.md', access_count=0)
assert e.model_dump(mode='json')['type'] == 'atom'
print('Pydantic OK')
"

# ── logging: --quiet --verbose ──
codememory --root examples/investment validate -q 2>&1
codememory --root examples/investment resolve user/investment/context -v 2>&1 | head -5

# ── summary_hash 全部有效 ──
PYTHONPATH=src python -c "
from pathlib import Path
from codememory.core import parse_frontmatter, compute_body_hash
root = Path('examples/investment')
for f in sorted(root.rglob('*.md')):
    meta, body = parse_frontmatter(f)
    if not meta or 'summary_hash' not in meta: continue
    assert meta['summary_hash'] == compute_body_hash(body), f'{f}'
print('ALL HASHES VALID')
"
codememory --root examples/investment overview | grep -c "stale"  # 0

# ── changelog ──
codememory --root examples/investment update user/investment/risk-tolerance --change-note "Sprint6 changelog test"
codememory --root examples/investment changelog user/investment/risk-tolerance
git checkout -- examples/investment/user/investment/risk-tolerance.md

# ── wander 加权 ──
for i in $(seq 1 3); do codememory --root examples/investment wander --inject; done

# ── snapshot 统一 ──
codememory --root examples/investment snapshot test-unified --target user/investment/context
ls examples/investment/user/snapshots/*test-unified* && echo "OK" || echo "FAIL"
rm -f examples/investment/user/snapshots/*test-unified*

# ── 回归 ──
codememory --root examples/investment reindex
codememory --root examples/investment validate
codememory --root examples/investment resolve user/investment/context | grep "Resolved"
codememory --root examples/investment orphans | head -3
codememory --root examples/investment overview | head -3
PYTHONPATH=src python tests/integration_test.py

# ── 清理 ──
codememory --root examples/investment reindex
```

---

## 五、风险

| 风险 | 缓解 |
|------|------|
| Pydantic 迁移导致所有模块改动 | models.py 定义清晰的 `model_validate(existing_dict)` 入口；每个模块逐个迁移并验证，不一次性全改 |
| handler 去重引入行为差异 | 提取前后对比 10 个命令的输出，用 diff 验证一致性 |
| logging 改变 stderr 格式 | `--verbose`/`--quiet` 可选；默认级别保持与 print() 时代相同的信息量 |
| 示例文件批量修改出错 | 修改前 git stash 保留原状，修改后逐文件校验 hash |

---

## 六、完成定义

1. `handlers.py` 统一所有命令逻辑，cli.py < 200 行，tools.py 只做薄委托
2. `models.py` 中 `MemoryEntry`/`IndexData`/`ImportRef` 为 Pydantic v2 BaseModel；核心模块接口类型标注全覆盖
3. `--verbose`/`--quiet` 可控日志级别；resolve 正文不被日志污染
4. 8 个样例 + 所有 .md 文件 `summary_hash` 与 body 一致；overview stale 计数 = 0
5. `changelog` 命令存在并可用
6. wander `--mode cool` 加权随机，结果多样性优于硬切
7. snapshot `--target` 和 `--from-dag` 走统一落盘逻辑
8. Sprint 1-5 回归 + `tests/integration_test.py` 全部通过
