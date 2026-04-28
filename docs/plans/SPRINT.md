# Sprint 8 — 知识治理 + 知识组织

> **起始日期**：2026-04-27
> **前置条件**：Sprint 7 完成（Phase 3C + 3D：测试体系 57/57 PASS + 多 provider 适配）
> **目标**：Phase 4A 知识治理（maturity + log.md + evidence）+ Phase 4B 知识组织（semantic_type + resolve --focus + 冷启动 import）

---

## 一、Phase 4A：知识治理

### 任务 1：maturity 字段 + 自动升降 ✅

**新增 `maturity` 字段到 MemoryEntry，resolve 时自动升降，LLM 零负担。**

| # | 子任务 | 说明 |
|---|--------|------|
| 1.1 | models.py | MemoryEntry 加 `maturity: str = "draft"`（draft/verified/proven/superseded） |
| 1.2 | resolve.py | access_count 递增后加 maturity 升降：resolve ≥ 3 次 → verified；resolve ≥ 10 次 + dependents > 0 → proven |
| 1.3 | create.py | 新记忆默认 maturity=draft；支持 `--maturity verified` 覆盖 |
| 1.4 | update.py | `--status superseded` 时 maturity 自动设为 superseded |
| 1.5 | search.py | 加 `--maturity` 过滤参数 |
| 1.6 | validate.py | 加 `_check_maturity_stale()`：proven 12 个月无 resolve → 建议复核（不自动降级） |

**产出**：修改 models.py、resolve.py、create.py、update.py、search.py、validate.py

**验收**：
```bash
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='t/x', summary='s', status='active', tags=[], intensity=5, version=1, path='t/x.md', access_count=0)
assert e.maturity == 'draft'
print('OK: maturity default')
"

codememory --root examples/investment search --maturity draft | head -3
```

---

### 任务 2：全局追加日志 log.md ✅

**新增 `.codememory/log.md`，create/update/snapshot/maturity 升级时自动追加。`codememory log` 命令查看。**

| # | 子任务 | 说明 |
|---|--------|------|
| 2.1 | `log.py` | `append_log(root, action, detail)` 追加一行；`show_log(root, limit)` 查看最近 N 条 |
| 2.2 | create.py 集成 | create 后自动调 append_log |
| 2.3 | update.py 集成 | update 后自动调 append_log |
| 2.4 | snapshot.py 集成 | snapshot 后自动调 append_log |
| 2.5 | resolve.py 集成 | maturity 自动升级时追加日志 |
| 2.6 | cli.py | `log` 子命令 + `--limit N` |
| 2.7 | tools.py | `log` Sandbox tool |

**产出**：新增 log.py，修改 create.py、update.py、snapshot.py、resolve.py、cli.py、tools.py

**验收**：
```bash
codememory --root examples/investment create --type atom --id user/test/logtest --tags "test" --summary "log test"
cat examples/investment/.codememory/log.md | grep "logtest"
codememory --root examples/investment log --limit 5
rm -f examples/investment/user/test/logtest.md
codememory --root examples/investment reindex
```

---

### 任务 3：evidence 溯源字段 ✅

**MemoryEntry 加 `evidence` 字段，create 时自动记录 session 信息。**

| # | 子任务 | 说明 |
|---|--------|------|
| 3.1 | models.py | MemoryEntry 加 `evidence: dict | None = None`（contributors, sessions, verified_in） |
| 3.2 | create.py | create 时自动写入 evidence.contributors、evidence.sessions |
| 3.3 | resolve.py | maturity 升级时自动追加 evidence.verified_in |

**产出**：修改 models.py、create.py、resolve.py

**验收**：
```bash
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='t/x', summary='s', evidence={'contributors':['agent'], 'sessions':['#test']})
assert e.model_dump(mode='json')['evidence']['contributors'] == ['agent']
print('OK: evidence')
"
```

---

## 二、Phase 4B：知识组织

### 任务 4：semantic_type 语义分类 ✅

**通过 tags 支持 semantic_type（model/decision/guideline/pitfall/process），search 和 overview 支持过滤。**

| # | 子任务 | 说明 |
|---|--------|------|
| 4.1 | search.py | `--semantic-type` 参数，内部过滤 tags |
| 4.2 | cli.py | search 子命令加 `--semantic-type` |

**产出**：修改 search.py、cli.py

**验收**：
```bash
codememory --root examples/investment create --type atom --id user/test/semtest --tags "decision,test" --summary "sem test"
codememory --root examples/investment search --semantic-type decision
rm -f examples/investment/user/test/semtest.md
codememory --root examples/investment reindex
```

---

### 任务 5：resolve --focus 按语义类型过滤 ✅

**resolve 时通过 `--focus` 参数匹配节点保持正文，不匹配的降级为 summary。**

| # | 子任务 | 说明 |
|---|--------|------|
| 5.1 | resolve.py | 加 focus 参数：匹配的节点正文输出，不匹配的降级为 summary |
| 5.2 | cli.py | `resolve` 子命令加 `--focus <type>` |

**产出**：修改 resolve.py、cli.py

**验收**：
```bash
codememory --root examples/investment resolve user/investment/context --focus decision | head -10
```

---

### 任务 6：冷启动 import 命令 ✅

**新增 `import` 子命令，从文本提取初始记忆，maturity=draft 入场。**

| # | 子任务 | 说明 |
|---|--------|------|
| 6.1 | `import_cmd.py` | `import_text(root, text, extract_types)` — CLI 接口，从 stdin/文件读取文本 |
| 6.2 | import 输出 | 输出 draft maturity 的 atom 记忆，带基本 YAML frontmatter |
| 6.3 | cli.py | `import` 子命令：`--file <path>` 或 `--stdin`，`--extract <types>` |
| 6.4 | 安全阀 | 所有 import 产物 maturity=draft |

**产出**：新增 import_cmd.py，修改 cli.py

**验收**：
```bash
echo "用户偏好长期持有，不追涨杀跌。" | codememory --root examples/investment import --stdin --extract preferences 2>&1 | head -5
# 清理
rm -f examples/investment/user/test/*.md
codememory --root examples/investment reindex
```

---

## 三、文件变更总览

```
新增：
  src/codememory/log.py              # 全局追加日志
  src/codememory/import_cmd.py       # 冷启动文本导入

修改：
  src/codememory/models.py           # + maturity, + evidence
  src/codememory/resolve.py          # + maturity 升降, + --focus
  src/codememory/create.py           # + log, + evidence
  src/codememory/update.py           # + log, + maturity superseded
  src/codememory/snapshot.py         # + log
  src/codememory/search.py           # + --maturity, + --semantic-type
  src/codememory/validate.py         # + _check_maturity_stale()
  src/codememory/cli.py              # + log, + import, + --focus, + --maturity, + --semantic-type
  src/codememory/tools.py            # + log tool

不修改：
  src/harnesslib/**
  src/llm_gateway/**
  tests/
```

---

## 四、验收命令汇总

```bash
# ── Phase 4A ──

# maturity
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='t/x', summary='s', status='active', tags=[], intensity=5, version=1, path='t/x.md', access_count=0)
assert e.maturity == 'draft'
print('OK: maturity')
"

# log.md
codememory --root examples/investment create --type atom --id user/test/logtest --tags "test" --summary "log test"
cat examples/investment/.codememory/log.md | grep "logtest"
codememory --root examples/investment log --limit 5
rm -f examples/investment/user/test/logtest.md

# evidence
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='t/x', summary='s', evidence={'contributors':['agent'],'sessions':['#test']})
assert e.model_dump(mode='json')['evidence']['contributors'] == ['agent']
print('OK: evidence')
"

# --maturity
codememory --root examples/investment search --maturity draft | head -3

# ── Phase 4B ──

# --semantic-type
codememory --root examples/investment create --type atom --id user/test/semtest --tags "decision,test" --summary "sem test"
codememory --root examples/investment search --semantic-type decision
rm -f examples/investment/user/test/semtest.md

# --focus
codememory --root examples/investment resolve user/investment/context --focus decision | head -10

# import
echo "用户偏好长期持有，不追涨杀跌。" | codememory --root examples/investment import --stdin --extract preferences 2>&1 | head -5
rm -f examples/investment/user/test/*.md

# ── 全量回归 ──
codememory --root examples/investment reindex && codememory --root examples/investment validate
codememory --root examples/investment resolve user/investment/context | grep "Resolved"
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py

# ── 清理 ──
codememory --root examples/investment reindex
```

---

## 五、风险

| 风险 | 缓解 |
|------|------|
| maturity 自动升级误判 | proven 额外要求 dependents > 0；不自动降级，只建议复核 |
| log.md 膨胀 | 只追加一行摘要；`--limit` 控制输出 |
| import 自动提取噪声 | 产物 maturity=draft；衰减建议会标记未引用的 draft |
| resolve --focus 遗漏信息 | 不匹配节点降级为 summary 保留在输出中，不删除 |

---

## 六、完成定义

1. maturity 字段默认 draft，resolve 自动升级到 verified（≥3 次）和 proven（≥10 次 + dependents > 0）
2. update --status superseded 时 maturity 自动设为 superseded
3. search 支持 `--maturity` 过滤
4. validate 对 proven 长期无访问给出复核建议
5. `.codememory/log.md` 全局追加日志 + `codememory log` 命令
6. evidence 字段 create 时自动写入 session 和 contributor
7. search 支持 `--semantic-type` 过滤
8. resolve --focus 按语义类型过滤节点输出分辨率
9. import 命令从 stdin/文件提取初始记忆，maturity=draft
10. Sprint 7 测试（57/57 + 24/24）不退化
