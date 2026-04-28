# Sprint 10 — 类型体系简化

> **起始日期**：2026-04-28
> **前置条件**：Sprint 9 完成（Phase 5：suggest-deps）
> **目标**：将 atom/instance/composite 合并为单一 `atom` 类型，保留 `schema`。角色由 imports/schema/tags/目录 表达，不靠 type 字段。

---

## 一、任务

### 任务 1：type 体系简化

**取消 instance 和 composite 类型。所有记忆统一为 `atom`。schema 保留。**

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 1.1 | `models.py` | type 字段允许值 `atom\|instance\|composite\|schema` → `atom\|schema`；`MemoryEntry` 的 type 默认值改为 `"atom"` | ✅ 完成 |
| 1.2 | `create.py` | 去掉 type 选择逻辑（默认 atom）；不再生成 instance/composite 特有的空 imports 模板；`--type` 参数保留但只接受 atom/schema，默认 atom | ✅ 完成 |
| 1.3 | `index.py` | reindex 时自动映射旧 type：`instance→atom`、`composite→atom`；不影响文件内容，只影响 index.json 中的 type 值 | ✅ 完成 |
| 1.4 | `validate.py` | 去掉"instance 必须有 schema"检查；去掉"atom 不能有 imports"限制；schema 合规检查改为"有 schema 字段时才检查" | ✅ 完成 |
| 1.5 | `resolve.py` | 去掉 `if type == "instance"` / `if type == "composite"` 等分支判断 | ✅ 完成（无需改动） |
| 1.6 | `search.py` | 添加 `--has-imports`（出度>0）、`--has-schema`（有 schema 字段）过滤器 | ✅ 完成 |
| 1.7 | `handlers.py` | suggest-deps 对所有 atom 生效，不再检查 type | ✅ 完成 |
| 1.8 | `cli.py` | `create` 子命令的 `--type` 参数 choices 改为 `["atom", "schema"]`，默认 `"atom"` | ✅ 完成 |

**产出**：修改 8 个核心模块

---

### 任务 2：文档同步

**更新项目文档反映新类型体系。**

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 2.1 | `agent-memory-guide.md` | 去掉 atom/instance/composite 的区分，改为"所有记忆都是 atom，用 imports/schema/tags 表达角色" | ✅ 完成 |
| 2.2 | `README.md` / `CLAUDE.md` | 四种原语 → 两种（atom + schema）；更新 CLI create 示例 | ✅ 完成 |
| 2.3 | `architecture.md` | 更新记忆原语章节 | ✅ 完成 |
| 2.4 | `INTEGRATION.md` | 更新 create 命令说明；更新四原语概念 | ✅ 完成 |

**产出**：修改 5 个文档文件

---

## 二、向后兼容

旧数据的第一行 frontmatter 不动。reindex 时自动映射：

```
instance  → type: atom（schema + imports 保留）
composite → type: atom（imports 保留）
atom     → type: atom（不变）
schema   → type: schema（不变）
```

旧 .md 文件在下次 `update` 时自然更新 frontmatter 中的 type 值。

---

## 三、文件变更总览

```
修改（代码）：
  src/codememory/models.py           # type 允许值
  src/codememory/create.py           # 去掉 type 选择逻辑
  src/codememory/index.py            # reindex 旧数据映射
  src/codememory/validate.py         # 去掉 instance/composite 检查
  src/codememory/resolve.py          # 去掉 type 分支
  src/codememory/search.py           # --has-imports, --has-schema
  src/codememory/handlers.py         # suggest-deps 全 atom 生效
  src/codememory/cli.py              # --type choices

修改（文档）：
  docs/agent-memory-guide.md
  README.md
  .claude/CLAUDE.md
  docs/architecture.md
  docs/INTEGRATION.md

不修改：
  src/harnesslib/**
  src/llm_gateway/**
  tests/（待更新测试预期）
```

---

## 四、验收命令汇总

```bash
# type 体系
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='t/x', summary='s')
assert e.type == 'atom'
print('OK: atom only')
"

# 旧数据兼容
codememory --root examples/investment reindex
codememory --root examples/investment validate
# 预期：0 errors

# --has-imports / --has-schema
codememory --root examples/investment search --has-imports
codememory --root examples/investment search --has-schema

# suggest-deps 对所有记忆生效
codememory --root examples/investment suggest-deps user/investment/semiconductor-thesis

# create 默认 atom
codememory --root examples/investment create --id user/test/typecheck --tags "test"
PYTHONPATH=src python -c "
from codememory.index import load_index
from pathlib import Path
idx = load_index(Path('examples/investment'))
e = idx.memories['user/test/typecheck']
assert e.type == 'atom'
print('OK: default type is atom')
"
rm -f examples/investment/user/test/typecheck.md
codememory --root examples/investment reindex

# 全量回归
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
```

---

## 五、风险

| 风险 | 缓解 |
|------|------|
| 现有代码中有对 `type == "instance"` 的硬编码分支 | grep 全局搜索 + 逐个改为检查 `schema` 字段存在性或 `imports` 存在性 |
| 旧测试断言了 `type` 值 | reindex 映射后测试预期同步更新；expert 测试数据文件不改 frontmatter |
| LLM 失去 type 指引后困惑 | agent-memory-guide 更新：用标签/imports/schema/目录来表达旧概念 |

---

## 六、完成定义

1. `type` 字段只接受 `atom` 或 `schema`
2. create 默认 type=atom，`--type` 参数可选 atom/schema
3. reindex 自动将旧 instance/composite 映射为 atom
4. validate 不再要求 instance 有 schema，不再禁止 atom 有 imports
5. search 支持 `--has-imports` 和 `--has-schema` 过滤
6. suggest-deps 对所有 atom 有效
7. 文档全部同步（agent-memory-guide、README、CLAUDE、architecture、INTEGRATION）
8. 57+24 测试不退化
