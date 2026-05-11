# Skeletonize: 结构化批量导入记忆

日期：2026-05-11 | 状态：approved

## 动机

CodeMemory 当前缺少批量导入结构化记忆的手段。`import_cmd.py` 只能按段落盲切纯文本，不理解文档结构（标题层级、代码块、节边界）。需要一个能解析文档结构、按重要性标注裁剪、直接写入记忆目录的预处理模块。

## 设计概览

```
codememory skeletonize ./my-notes/ --min-intensity 5
                         │
                         ▼
              ┌─────────────────────┐
              │   markdown.py       │  按 ## 标题拆节，解析 @intensity 标注
              │   (Phase 1)         │  输出: Section 对象列表
              └────────┬────────────┘
                       │
              ┌────────▼────────────┐
              │   common.py         │  共享: intensity 解析、截断工具
              └────────┬────────────┘
                       │
              ┌────────▼────────────┐
              │   handlers.py       │  生成 frontmatter、写 .md 文件
              │   (handle_          │  调用 reindex()
              │    skeletonize)     │
              └─────────────────────┘
```

## 模块结构

```
src/codememory/
├── skeletonize/              # 新子包
│   ├── __init__.py           # 公开 skeletonize_markdown
│   ├── markdown.py           # Phase 1：Markdown 骨架化
│   ├── common.py             # 共享：intensity 解析、truncate 工具
│   └── code.py               # Phase 3：代码骨架化（stub）
├── handlers.py               # 新增 handle_skeletonize()
├── cli.py                    # 新增 skeletonize 子命令
```

## 标注机制

唯一标注方式：注释标记。Markdown 用 HTML 注释，代码用 `#` 或 `//`：

```markdown
<!-- @intensity:7 -->
## 核心数据流
完整保留...

<!-- @intensity:2 -->
## 部署环境
第一句保留。其余截断。
```

- 解析正则: `<!--\s*@intensity:\s*(\d+)\s*-->`
- 无标注节默认 `intensity=5`
- 节标题继承所在节的 intensity
- 文件级默认：首个 `<!-- @intensity:N -->` 之前无标注的节用此值
- intensity 取值 1-10（对应 CodeMemory frontmatter 的现有字段）

## Markdown 骨架化规则

操作单元 = **节**（`#` 或 `##` 标题开始，到下一个同级或更高级标题结束）。

| 条件 | 行为 |
|------|------|
| intensity >= min_intensity | 保留全文 |
| intensity < min_intensity | 保留标题 + 首句 + `<!-- truncated: N chars, ~M tokens -->` |

- 代码块、列表、表格等 block 元素整体保留或整体丢弃，不切碎内部
- 首句定义：第一个以 `。` `.` `！` `?` `\n` 结束的完整句子，最多 200 字符

## CLI 接口

```bash
# 扫描目录 → 骨架化 → 写入记忆
codememory skeletonize <source> --min-intensity 5

# 预览模式
codememory skeletonize <source> --dry-run

# 指定标签
codememory skeletonize <source> --tags "architecture,design"
```

参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| source | Path (positional) | 必填 | .md 文件或包含 .md 的目录 |
| --min-intensity | int | 5 | 低于此值的节被截断 |
| --dry-run | flag | False | 预览不写文件 |
| --tags | str | "" | 逗号分隔，写入生成记忆的 tags |
| --root | Path | CODEMEMORY_ROOT | 记忆目录 |

## 输出逻辑

1. 每个输入 .md 的每个节 → 一个独立 CodeMemory 记忆
2. 自动生成 frontmatter：
   - `type: atom`
   - `id`: 从文件路径 + 节标题 slug 派生（如 `user/notes/architecture-核心数据流`）
   - `intensity`: 从注释标注提取
   - `tags`: 从 CLI --tags + 源文件路径推断
   - `maturity: draft`
   - `summary`: 首句（最多 100 字符）
3. 同一文件内相邻节：前一节的 `imports` 包含后一节 ID（保持文档原始顺序的 DAG 边）
4. 写入 `--root` 下按 ID 路径组织的 .md 文件
5. 写入完成后自动运行 `reindex()`

## 与现有代码的关系

- `handlers.py` 新增 `handle_skeletonize()` — 参数走 Pydantic model
- `cli.py` 新增 `skeletonize` 子命令 — 薄壳 delegate
- 复用：`core.py` 的 `compute_body_hash()` / `get_memory_path()`
- 复用：`index.py` 的 `reindex()`
- 复用：`log.py` 的 `append_log()`
- **不引入新依赖**（Markdown 标题解析用正则，不引入 mistune）

## 非目标（Phase 1 不做）

- 代码文件骨架化（Python/JS/Go 等，留给 Phase 3 的 `code.py`）
- 多文件交叉依赖推断（留给 `suggest-deps` 扩展）
- YAML/TOML 配置文件处理
- 图片/二进制文件处理

## 测试策略

- 单元测试：`tests/unit/test_skeletonize.py`
  - intensity 注释解析（有/无/畸形）
  - 节拆分（平级标题、嵌套标题、无标题文档）
  - 截断逻辑（短节、空节、纯代码块节）
  - 首句提取（中英文、多标点、无标点）
- 集成测试：`tests/integration_test.py` 新增场景
  - 端到端：单文件 → skeletonize → 验证 .md 输出 + frontmatter
  - 端到端：目录扫描 → 验证 reindex 后 resolve 可检索
  - dry-run 模式不产生文件

## 验收标准

```bash
# 创建测试数据
mkdir -p /tmp/test-notes
cat > /tmp/test-notes/design.md << 'EOF'
# 系统设计

前言说明文字。

<!-- @intensity:8 -->
## 核心架构
这是关键的架构决策，应该完整保留。

## 辅助模块
<!-- @intensity:2 -->
这是不太重要的实现细节，有一大段很长的文字描述。
EOF

# 运行
codememory skeletonize /tmp/test-notes/ --root /tmp/test-memories --min-intensity 5

# 验证：核心架构节完整，辅助模块节被截断
codememory resolve user/notes/design-核心架构 --root /tmp/test-memories
codememory resolve user/notes/design-辅助模块 --root /tmp/test-memories  # 应含 truncated 标记
```
