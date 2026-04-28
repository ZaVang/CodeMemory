# CodeMemory 后续路线图

> 设计哲学：记忆加载是依赖解析问题，不是搜索问题
> Layer 0 认知接口：`docs/layer0-cognitive-interface.md`

---

## 一、已完成

Phase 1-6 全部完成（10 个 Sprint）：

- **Phase 1-2**：原型验证 + 框架化 + Agent 自主维护 + 智能检索 + Layer 0 认知接口 + 集成发布
- **Phase 3**：代码质量 + 功能深化 + 测试体系（57+24）+ 多 provider 适配
- **Phase 4**：知识治理（maturity + log.md + evidence）+ 知识组织（semantic_type + resolve --focus + import）
- **Phase 5**：自动依赖推断（suggest-deps：三层过滤 + 双向推断）
- **Phase 6**：类型体系简化（atom/schema 两种，instance/composite 删除）

当前状态：15 个 CLI 命令，12 个 Sandbox 工具。

---

## 二、Phase 6：类型体系简化

> 核心问题：atom/instance/composite 三种类型结构几乎相同——
> instance = atom + schema + imports，composite = atom + imports（三种强度）。
> 区别不在文件结构，在 DAG 里的角色。而角色是网络位置决定的，不应该写死在 type 字段里。

### 2.1 设计理念：来自 Engram 的启发

```
Engram（companion-agent）           CodeMemory（新设计）
─────────────────────────          ─────────────────────
NeuronCell（基本单元）      ←→     atom（.md 文件，一个事实/决策/组合入口）
连接（A→B, B→A）           ←→     imports（显式声明依赖）
Engram（一组神经元+连接）   ←→     resolve 的输出（不是文件，是一次计算结果）
```

**关键是 engram 没有文件类型——它是激活扩散的结果。** resolve 已经在做同样的事：从一个入口 atom 出发，沿 imports 递归扩散，拓扑排序输出完整的因果上下文。

### 2.2 新类型体系

```
只保留两种：

  schema   — 模板。定义字段结构，不是记忆。
  atom     — 记忆。所有记忆的基础类型。

atom 的可选属性：
  schema      可选   — 有 = 遵守某个模板结构
  imports     可选   — 有 = 可以作为 resolve 入口
  intensity   必选   — 1-10，>=8 自动 protected
  maturity    自动   — draft/verified/proven
  tags        可选   — 包括语义类型（decision/guideline/pitfall/...）

删除的类型：
  instance    — 等价于 atom + schema + imports
  composite   — 等价于 atom + imports（三种强度）
```

创建时 LLM 只需写 `type: atom`。schema 和 imports 都是可选的、可后加的。

### 2.3 角色由数据决定，不由 type 决定

| 旧概念 | 旧定义 | 新定义 |
|--------|--------|--------|
| atom（原料） | `type: atom`，无 imports | 出度=0 的 atom |
| instance（菜品） | `type: instance`，有 schema + required imports | 有 schema 的 atom |
| composite（套餐入口） | `type: composite`，三种 imports 强度 | 有 imports 的 atom（尤其是被 snapshot 的） |
| "高层记忆" | 无 | user/snapshots/ 下的 atom，imports 记录了某次 resolve 的 DAG |

查找方式不依赖 type：

```bash
# 找到"原料"（无 imports 的记忆）
codememory orphans              # 入度为0 = 不被任何记忆引用

# 找到"入口"（有 imports 的记忆）
codememory search --has-imports

# 找到"高层记忆"（被 snapshot 固化的）
codememory search --tags snapshot
ls user/snapshots/

# 找到遵守模板的
codememory search --has-schema
```

### 2.4 完整的记忆生命周期

```
1. 散落的 atom（无 imports）
   user/facts/a.md    user/facts/b.md    user/facts/c.md
   像孤立的神经元

2. suggest-deps 发现连接
   → b imports a（a 解释了 b）
   → c imports a, b（c 依赖 a 和 b）
   建立了出向连接

3. resolve c
   → DAG：c → a → b（拓扑排序）
   这是一次临时的 engram——算出来的，不落盘

4. snapshot 固化
   → user/snapshots/2026-04-28-xxx.md
   这是一个 atom，它的 imports 记录了这次 resolve 的 DAG
   下次 resolve 这个 snapshot 就能复现整个上下文
```

**snapshot 产出的就是一个 atom——不是"composite 类型"，只是 imports 字段被填满的 atom。** 下次 resolve 它时，imports 递归展开，原样复现当时的完整上下文。

### 2.5 具体变更

| 文件 | 变更 |
|------|------|
| `models.py` | type 字段的允许值从 `atom\|instance\|composite\|schema` 改为 `atom\|schema` |
| `create.py` | 不再需要选 type（默认 atom）；不再生成 instance/composite 特有的空 imports 模板 |
| `validate.py` | 去掉"instance 必须有 schema"的检查；去掉"atom 不能有 imports"的限制 |
| `index.py` | reindex 时兼容旧数据（旧 type → 新 type 映射） |
| `resolve.py` | 去掉 `if type == "instance"` 等分支判断 |
| `search.py` | 添加 `--has-imports` / `--has-schema` 过滤器 |
| `handlers.py` | suggest-deps 对所有 atom 生效（不再检查 type） |
| `cli.py` | create 子命令去掉 `--type` 参数或默认 atom |
| `agent-memory-guide.md` | 更新原语选择规则 |
| `README.md` / `CLAUDE.md` / `architecture.md` / `INTEGRATION.md` | 同步更新 |

### 2.6 向后兼容

旧数据迁移规则：

```python
OLD_TYPE_MAP = {
    "atom":      "atom",
    "instance":  "atom",     # schema + imports 保留在文件中
    "composite": "atom",     # imports 保留在文件中
    "schema":    "schema",
}
```

reindex 时自动映射，旧 .md 文件无需修改 frontmatter（下次 update 时自然更新）。

### 2.7 验收

```bash
# type 体系
PYTHONPATH=src python -c "
from codememory.models import MemoryEntry
e = MemoryEntry(type='atom', id='t/x', summary='s')
assert e.type == 'atom'
print('OK: atom only')
"

# 旧数据兼容：instance → atom
codememory --root examples/investment reindex
codememory --root examples/investment validate
# 预期：0 errors

# --has-imports 过滤
codememory --root examples/investment search --has-imports

# suggest-deps 对所有记忆生效
codememory --root examples/investment suggest-deps user/investment/semiconductor-thesis

# 全量回归
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
```

---

## 三、时间线

```
已完成 ─── Phase 1-6 (全部 10 个 Sprint)

待开始 ─── (无)
```

---

## 四、风险与缓解

| 风险 | 缓解 |
|------|------|
| 旧数据迁移后 validate 规则变化导致误报 | 去掉 instance/composite 特有检查，validate 规则变少（更宽松），不会新增误报 |
| 现有测试依赖旧 type 值 | reindex 自动映射 `instance→atom`、`composite→atom`；测试预期同步更新 |
| LLM 在没有 type 指引时困惑 | agent-memory-guide.md 更新为"用 imports/schema/tags 表达角色，不靠 type" |
| schema 字段在旧 instance 文件中丢失 | 旧 instance 的 frontmatter 中 `schema:` 字段保持不变，reindex 正常读取 |
