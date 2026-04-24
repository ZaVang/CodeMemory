# Sprint 2 — Agent 自主维护记忆

> **起始日期**：2026-04-24
> **前置条件**：Sprint 1 完成（`src/codememory/` package 可导入、`pip install -e .` 可用、数据与框架分离）
> **目标**：Agent 可在对话中自主创建/更新记忆、正确声明依赖与强度；瞬态记忆 DAG 可被 resolve 但不落盘，snapshot 显式持久化

---

## 一、Sprint Backlog

### 任务 1：agent-memory-guide.md — Agent 决策树

**一份 Agent 可直接嵌入 system prompt 的记忆操作指南。**

| # | 子任务 | 说明 |
|---|--------|------|
| 1.1 | 编写原语选择规则 | 何时用 atom（单一事实）/ instance（依附 schema 的决策）/ composite（组合包）的判断标准，含反例 |
| 1.2 | 编写依赖声明规则 | 如何判断 A 是 B 的 required vs recommended vs related；"理解 B 必须先读 A" = required |
| 1.3 | 编写 intensity 评估规则 | 1-3=临时信息 4-6=常规记忆 7-9=关键判断 10=终生不忘；含典型场景举例 |
| 1.4 | 编写 summary 写作规则 | 一句话概括核心内容，不超过 80 字；summary 在 token 裁剪时代替正文，必须独立可理解 |
| 1.5 | 编写完整示例 | 3 个对话场景：a) 用户分享偏好 b) 做出重大决策 c) 日常信息记录，展示 Agent 如���选择原语+写 frontmatter |

**产出**：`docs/agent-memory-guide.md`

**验收**：
```bash
# 检查文档结构完整
grep -c "## " docs/agent-memory-guide.md  # 至少 5 个标题
# 对照 3 个场景手动验证 Agent 选择正确原语
```

---

### 任务 2：create 增强 — protected + dry-run

**完善 create 命令，新增 protected 自动标记和 dry-run 预览。**

| # | 子任务 | 说明 |
|---|--------|------|
| 2.1 | `protected` 自动标记 | `intensity >= 8` → frontmatter 写入 `protected: true` |
| 2.2 | `--dry-run` 参数 | `create --dry-run` 输出完整 frontmatter + body 预览到 stdout，不写文件不更新索引 |
| 2.3 | `--tags` 参数 | `create --tags "investment,thesis"` 替代默认的 `["untagged"]` |
| 2.4 | 更新 tools.py | `create_memory` tool 支持 `dry_run` 和 `tags` 参数 |

**验收**：
```bash
# protected 自动标记
codememory --root examples/investment create --type atom --id user/ideas/high-intensity --intensity 9
python -c "
import yaml
with open('examples/investment/user/ideas/high-intensity.md') as f:
    content = f.read()
fm = yaml.safe_load(content.split('---')[1])
assert fm['protected'] == True
assert fm['intensity'] == 9
print('OK: protected+intensity')
"

# dry-run 不写文件
codememory --root examples/investment create --type atom --id user/ideas/dry-run-test --dry-run
ls examples/investment/user/ideas/dry-run-test.md 2>/dev/null && echo "FAIL: file created" || echo "OK: no file"

# tags 参数
codememory --root examples/investment create --type atom --id user/ideas/tagged --tags "test,experiment"
python -c "
import json; idx = json.load(open('examples/investment/.codememory/index.json'))
tags = idx['memories']['user/ideas/tagged']['tags']
assert 'test' in tags and 'experiment' in tags
print('OK: tags')
"
```

---

### 任务 3：update 命令

**新增 `update` 子命令，实现版本控制与变更追踪。**

| # | 子任务 | 说明 |
|---|--------|------|
| 3.1 | `src/codememory/update.py` | `update(root, memory_id, body, summary, change_note, status)` 函数 |
| 3.2 | 版本递增 | `version` 自动 +1；修改 frontmatter 的 `updated` 为当天日期 |
| 3.3 | change_note 强制 | `--change-note` 必填（不填则拒绝执行），写入 `change_log` 列表 |
| 3.4 | summary_hash 自动更新 | 如果 body 被修改，基于新 body 重新计算 `summary_hash` |
| 3.5 | status 变更 | 支持 `--status active|archived|superseded|draft` |
| 3.6 | imports 更新 | 支持 `--import-required` `--import-recommended` `--import-related` 增删依赖 |
| 3.7 | CLI 注册 + tools.py handler | `codememory update` 子命令 + `update_memory` Sandbox tool |

**验收**：
```bash
# 基础 update
codememory --root examples/investment update user/investment/risk-tolerance \
  --change-note "Sprint 2 测试：验证 update 命令"

# 版本递增
python -c "
import yaml
with open('examples/investment/user/investment/risk-tolerance.md') as f:
    fm = yaml.safe_load(f.read().split('---')[1])
assert fm['version'] >= 3  # was v2, now >= v3
assert 'change_log' in fm
print(f'OK: version={fm[\"version\"]}, change_log={fm[\"change_log\"]}')
"

# summary_hash 更新
codememory --root examples/investment update user/investment/risk-tolerance \
  --body "更新后的正文内容用于测试 hash" --change-note "测试 body 更新"
python -c "
import yaml, hashlib
with open('examples/investment/user/investment/risk-tolerance.md') as f:
    parts = f.read().split('---', 2)
    fm = yaml.safe_load(parts[1])
    body = parts[2].strip()
expected_hash = hashlib.sha256(body.encode()).hexdigest()[:7]
assert fm['summary_hash'] == expected_hash
print(f'OK: summary_hash={fm[\"summary_hash\"]}')
"

# Sandbox tool 注册
PYTHONPATH=src python -c "
import asyncio
from harnesslib.sandbox import Sandbox
from codememory.tools import register_all
async def t():
    s = Sandbox()
    await register_all(s)
    names = [d.name for d in s.list_tools()]
    assert 'update_memory' in names
    print(f'OK: {len(names)} tools including update_memory')
asyncio.run(t())
"
```

---

### 任务 4：瞬态记忆 DAG

**在内存中维护会话级推理链，可 resolve 但不落盘。**

| # | 子任务 | 说明 |
|---|--------|------|
| 4.1 | `src/codememory/transient.py` | `TransientNode`（id, type, summary, body, imports, intensity）+ `TransientDAG`（add, remove, resolve） |
| 4.2 | TransientDAG.add() | 添加临时节点：`dag.add(id, type, summary, body, imports)` |
| 4.3 | TransientDAG.resolve() | 拓扑排序 + 融合持久化记忆（持久化记忆通过 index 加载，瞬态节点从内存读取）；先查瞬态，再查 index |
| 4.4 | TransientDAG.remove() | 按 id 移除瞬态节点 |
| 4.5 | 会话生命周期 | TransientDAG 实例绑定到当前进程；进程退出 = 自动清除 |

**验收**：
```bash
PYTHONPATH=src python -c "
from pathlib import Path
from codememory.transient import TransientDAG

dag = TransientDAG()

# 添加瞬态节点
dag.add('session/step1', type='atom', summary='用户偏好：长期持有',
        body='用户明确表示偏好长期持有策略，不频繁交易。', intensity=6)
dag.add('session/step2', type='atom', summary='当前市场：高波动',
        body='三大指数日内振幅均超2%，恐慌指数VIX升至28。', intensity=7)
dag.add('session/conclusion', type='instance', summary='建议：维持持仓',
        body='基于用户偏好和市场状况，维持当前仓位不变。',
        imports={'required': ['session/step1', 'session/step2']})

# resolve：拓扑排序
result = dag.resolve(root=Path('examples/investment'))
# session/step1 和 session/step2 应在 conclusion 之前出现
pos_1 = result.find('session/step1')
pos_2 = result.find('session/step2')
pos_c = result.find('session/conclusion')
assert pos_1 < pos_c and pos_2 < pos_c, 'Dependencies must appear before dependents'
print(f'OK: resolved {len(result)} chars, topology correct')
print(result[:500])
"

# 进程退出后瞬态记忆消失
python -c "
from pathlib import Path
from codememory.transient import TransientDAG
dag = TransientDAG()
# 新进程，dag 应为空
assert len(dag._nodes) == 0
print('OK: transient DAG cleared on new process')
"
```

---

### 任务 5：snapshot 命令 — 瞬态持久化

**将 TransientDAG 中的节点导出为持久化的 composite .md 文件，替换当前占位实现。**

| # | 子任务 | 说明 |
|---|--------|------|
| 5.1 | 实现 `snapshot` 函数 | 接收 TransientDAG + target_id → 生成 composite .md，包含所有瞬态节点的 body + 依赖声明 |
| 5.2 | 自动生成 composite frontmatter | type=composite, id 从参数传入，imports.required 自动从瞬态 DAG 边推导 |
| 5.3 | 落盘到 user/snapshots/ | `user/snapshots/{date}-{id}.md` |
| 5.4 | CLI 集成 | `codememory snapshot <id>` 命令接收 TransientDAG 引用（通过 pickle 或 JSON 临时文件传递） |
| 5.5 | tools.py handler | `snapshot` Sandbox tool |

**验收**：
```bash
PYTHONPATH=src python -c "
import tempfile, json, subprocess, sys
from pathlib import Path

# 1. 创建 TransientDAG 并序列化到临时文件
from codememory.transient import TransientDAG
dag = TransientDAG()
dag.add('session/a', type='atom', summary='要点A', body='内容A', intensity=5)
dag.add('session/b', type='atom', summary='要点B', body='内容B', intensity=5)
dag.add('session/sum', type='composite', summary='汇总',
        body='AB 汇总', imports={'required': ['session/a', 'session/b']})

# 2. 序列化到临时文件
tmpfile = Path(tempfile.mktemp(suffix='.json'))
tmpfile.write_text(json.dumps(dag.to_dict(), ensure_ascii=False))

# 3. 调用 snapshot CLI
result = subprocess.run([
    sys.executable, '-m', 'codememory.cli',
    '--root', 'examples/investment',
    'snapshot', 'test-session-001',
    '--from-dag', str(tmpfile),
], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr)

# 4. 验证 composite 已生成
snap_file = Path('examples/investment/user/snapshots/2026-04-24-test-session-001.md')
assert snap_file.exists(), 'Snapshot file not created'
print(f'OK: snapshot created at {snap_file}')

# 5. 验证 frontmatter 含正确的 imports
import yaml
with open(snap_file) as f:
    fm = yaml.safe_load(f.read().split('---')[1])
assert fm['type'] == 'composite'
assert 'session/a' in fm['imports']['required']
assert 'session/b' in fm['imports']['required']
print(f'OK: imports={fm[\"imports\"][\"required\"]}')
tmpfile.unlink()
print('PASS: snapshot full cycle')
"
```

---

### 任务 6：回归验证 + 清理

**确保新功能不破坏已有能力。**

| # | 验证项 | 命令 |
|---|--------|------|
| 6.1 | 模块可导入（含新模块） | `python -c "from codememory import resolve, create, update, search, validate, reindex"` |
| 6.2 | examples 可运行 | `codememory --root examples/investment reindex && codememory --root examples/investment validate` |
| 6.3 | resolve 拓扑正确 | `codememory --root examples/investment resolve user/investment/context` → 7 节点正确顺序 |
| 6.4 | Sandbox 全部 6 个 tool | `register_all()` 后 `list_tools()` 返回 resolve_context, create_memory, search_memories, validate_memories, focus_memory, update_memory |
| 6.5 | 清理测试文件 | `rm -f examples/investment/user/ideas/high-intensity.md examples/investment/user/ideas/tagged.md examples/investment/user/ideas/dry-run-test.md examples/investment/user/snapshots/*.md` |
| 6.6 | risk-tolerance 恢复原状 | `git checkout -- examples/investment/user/investment/risk-tolerance.md`（撤销 update 测试修改） |

---

## 二、文件变更总览

```
新增：
  docs/agent-memory-guide.md       # Agent 决策树文档
  src/codememory/update.py         # update 命令实现
  src/codememory/transient.py      # TransientDAG + TransientNode

修改：
  src/codememory/__init__.py       # 新增 export: update, TransientDAG
  src/codememory/create.py         # protected 自动标记 + --dry-run + --tags
  src/codememory/cli.py            # update/snapshot 子命令完善
  src/codememory/tools.py          # update_memory + snapshot tool

不修改（Sprint 1 完成的模块）：
  src/codememory/core.py
  src/codememory/index.py
  src/codememory/resolve.py
  src/codememory/validate.py
  src/codememory/search.py
```

---

## 三、验收命令汇总

```bash
# ── 模块导入 ──
python -c "from codememory import resolve, create, update, search, validate, reindex"
PYTHONPATH=src python -c "from codememory.transient import TransientDAG; print('OK')"

# ── agent-memory-guide.md 存在 ──
test -f docs/agent-memory-guide.md && echo "OK" || echo "FAIL"

# ── create: protected + dry-run + tags ──
codememory --root examples/investment create --type atom --id user/ideas/test-protected --intensity 9
python -c "import yaml; fm=yaml.safe_load(open('examples/investment/user/ideas/test-protected.md').read().split('---')[1]); assert fm['protected']==True; print('protected OK')"
codememory --root examples/investment create --type atom --id user/ideas/test-dryrun --dry-run
ls examples/investment/user/ideas/test-dryrun.md 2>/dev/null && echo "FAIL: dry-run wrote file" || echo "OK: dry-run"
codememory --root examples/investment create --type atom --id user/ideas/test-tags --tags "a,b"
python -c "import json; idx=json.load(open('examples/investment/.codememory/index.json')); t=idx['memories']['user/ideas/test-tags']['tags']; assert 'a' in t; print('tags OK')"

# ── update: version + change_note + summary_hash ──
codememory --root examples/investment update user/investment/risk-tolerance --change-note "Sprint2 验证"
python -c "import yaml; fm=yaml.safe_load(open('examples/investment/user/investment/risk-tolerance.md').read().split('---')[1]); assert fm['version']>=3; assert 'change_log' in fm; print('update OK')"

# ── update: body 修改触发 summary_hash 更新 ──
codememory --root examples/investment update user/investment/risk-tolerance --body "新正文测试hash" --change-note "测试body"
python -c "
import yaml, hashlib
with open('examples/investment/user/investment/risk-tolerance.md') as f:
    parts = f.read().split('---', 2)
    fm = yaml.safe_load(parts[1])
    body = parts[2].strip()
assert fm['summary_hash'] == hashlib.sha256(body.encode()).hexdigest()[:7]
print('summary_hash OK')
"

# ── 瞬态 DAG：resolve 拓扑正确 ──
PYTHONPATH=src python -c "
from pathlib import Path
from codememory.transient import TransientDAG
dag = TransientDAG()
dag.add('s/a', type='atom', summary='A', body='A', intensity=5)
dag.add('s/b', type='atom', summary='B', body='B', intensity=5)
dag.add('s/c', type='composite', summary='C', body='C', imports={'required': ['s/a', 's/b']})
r = dag.resolve(root=Path('examples/investment'))
assert r.find('s/a') < r.find('s/c')
assert r.find('s/b') < r.find('s/c')
print('transient DAG OK')
"

# ── snapshot：瞬态 → 持久化 ──
PYTHONPATH=src python -c "
import tempfile, json, subprocess, sys
from pathlib import Path
from codememory.transient import TransientDAG
dag = TransientDAG()
dag.add('s/x', type='atom', summary='X', body='X', intensity=5)
dag.add('s/y', type='atom', summary='Y', body='Y', intensity=5)
dag.add('s/z', type='composite', summary='Z', body='Z', imports={'required': ['s/x', 's/y']})
tf = Path(tempfile.mktemp(suffix='.json'))
tf.write_text(json.dumps(dag.to_dict(), ensure_ascii=False))
r = subprocess.run([sys.executable, '-m', 'codememory.cli', '--root', 'examples/investment', 'snapshot', 'test-sprint2', '--from-dag', str(tf)], capture_output=True, text=True)
print(r.stdout or r.stderr)
snap = Path('examples/investment/user/snapshots/2026-04-24-test-sprint2.md')
assert snap.exists()
import yaml
fm = yaml.safe_load(snap.read_text().split('---')[1])
assert 's/x' in fm['imports']['required']
tf.unlink()
print('snapshot OK')
"

# ── Sandbox 6 tools ──
PYTHONPATH=src python -c "
import asyncio
from harnesslib.sandbox import Sandbox
from codememory.tools import register_all
async def t():
    s = Sandbox()
    await register_all(s)
    names = [d.name for d in s.list_tools()]
    assert len(names) == 6, f'Expected 6 tools, got {len(names)}: {names}'
    print(f'OK: {names}')
asyncio.run(t())
"

# ── Phase 1 回归 ──
codememory --root examples/investment reindex
codememory --root examples/investment validate
codememory --root examples/investment resolve user/investment/context

# ── 清理 ──
rm -f examples/investment/user/ideas/test-protected.md
rm -f examples/investment/user/ideas/test-tags.md
rm -f examples/investment/user/ideas/sprint1-test.md
rm -f examples/investment/user/snapshots/*.md
git checkout -- examples/investment/user/investment/risk-tolerance.md
codememory --root examples/investment reindex
```

---

## 四、风险

| 风险 | 缓解 |
|------|------|
| update 修改 risk-tolerance 后影响其他测试 | 验收后 `git checkout` 恢复原状 |
| TransientDAG 与 resolve.py 的 DAG 算法重复 | TransientDAG 内部复用 `resolve.py` 的 `topological_sort`，不重写 |
| snapshot 需要跨进程传递 TransientDAG | 使用 JSON 临时文件序列化（`dag.to_dict()` / `dag.from_dict()`） |
| `--dry-run` 输出格式不直观 | 输出完整 YAML frontmatter + body，Agent 可直接读取 |

---

## 五、完成定义

1. `docs/agent-memory-guide.md` 可嵌入 Agent system prompt，覆盖原语选择 + 依赖声明 + intensity 评估 + summary 写作
2. `create --intensity 9` 自动标记 `protected: true`，`--dry-run` 预览不写文件，`--tags` 自定义标签
3. `update` 命令实现版本递增、change_note 强制、summary_hash 自动更新、status 变更
4. `TransientDAG` 支持 add/remove/resolve，拓扑顺序正确，进程退出自动清除
5. `snapshot` 将 TransientDAG 导出为 persistent composite .md
6. Sprint 1 的 3 个回归测试（reindex + validate + resolve context）全部通过
