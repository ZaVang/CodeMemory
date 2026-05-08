# CodeMemory 系统架构

> 最后更新：2026-05-08

## 一、设计理念

CodeMemory 的核心洞察：**AI 记忆加载的本质是依赖解析，不是语义搜索。**

传统 RAG 检索到的 chunks 之间没有依赖关系 — 可能捞到"2月买了半导体"但捞不到"为什么买"的前置判断。CodeMemory 通过显式依赖图（DAG）解决这个问题。

## 二、三层架构

```
┌─────────────────────────────────────────────────────┐
│  frontend/          React + Vite (port 5300)         │
│  Web UI: Graph / List / Dashboard / Detail / Form    │
├─────────────────────────────────────────────────────┤
│  backend/           FastAPI (port 8000)              │
│  REST API: CRUD / search / resolve / stats / touch   │
│  routers/  ← APIRouter split (memories/search/stats) │
├─────────────────────────────────────────────────────┤
│  src/codememory/    核心引擎（纯 Python 库）          │
│  CLI / MCP Server / DAG / decay / validate           │
└─────────────────────────────────────────────────────┘
```

## 三、记忆原语

### Atom（通用记忆）
- 所有记忆都是 atom
- 可选的 `imports`：显式依赖声明（required/recommended/related）
- 可选的 `schema`：声明依附的元模板

### Schema（元模板）
- 定义记忆的结构模板
- atom 通过 `schema` 字段引用

## 四、Layer 0 认知接口

Agent 与记忆系统之间的五个认知基础操作：

| 认知行为 | 命令 | 说明 |
|----------|------|------|
| **扫视** | `overview` | 启动时自动注入 top 5 相关记忆摘要 |
| **注视** | `focus <id>` | 动态切换记忆分辨率（full / summary） |
| **残留** | TransientDAG + `snapshot` | 会话推理链持久化 |
| **重构** | `resolve <id>` | DAG 拓扑拼装 + token 裁剪输出 |
| **触景生情** | `wander` | 随机激活冷记忆（按衰减加权） |

## 五、时间衰减模型

```
R = max(0.5^(days/stability), 0.1 / (1 + days / (10 * stability)))

- stability: 每记忆半衰期（默认 14.0 天，支持 domain-differentiated）
- access 时 SInc 自适应增长（FSRS 启发，Gaussian 峰值 R≈0.78）
- stale 检测时 stability 下调（0.90 乘数）
- 长期保留底线防止 90 天静默知识丢失
```

## 六、目录布局

```
CodeMemory/
├── bin/                          # 命令行入口
│   ├── codememory                # bash wrapper → python -m codememory.cli
│   ├── codememory.py             # Python thin launcher
│   └── dev                       # 一键启动（Backend + Frontend）
├── src/codememory/               # 核心引擎（19 模块）
│   ├── models.py                 # Pydantic v2 数据模型
│   ├── core.py                   # frontmatter 解析, body hash, 衰减公式
│   ├── handlers.py               # 统一命令分发（CLI + MCP + API 共享）
│   ├── index.py                  # Index 加载/保存/reindex
│   ├── resolve.py                # DAG + 拓扑排序 + token 裁剪 + SInc
│   ├── validate.py               # 循环/断链/schema/衰减检测
│   ├── create.py / update.py     # 记忆 CRUD + domain stability 默认值
│   ├── search.py                 # 全文搜索（ID/summary/tag/body）
│   ├── orphans.py                # 孤立记忆发现
│   ├── suggest_deps.py           # 自动依赖推断
│   ├── changelog.py / log.py     # 变更历史 / 审计日志
│   ├── transient.py / snapshot.py # 会话级 TransientDAG / 持久化
│   ├── import_cmd.py             # 冷启动文本导入
│   ├── cli.py                    # argparse 薄壳（< 250 行）
│   ├── tools.py                  # harnesslib Sandbox 工具注册
│   ├── integrations.py           # OpenAI/Anthropic/Gemini toolkit
│   └── mcp_server.py             # MCP server（5 readOnly + 2 write 工具）
├── backend/                      # FastAPI Web 服务层
│   ├── server.py                 # app 创建 + 中间件 + lifespan（~140 行）
│   ├── shared.py                 # 共享模型、ContextVar、辅助函数
│   └── routers/
│       ├── memories.py           # CRUD + touch + import（8 端点）
│       ├── search.py             # search + resolve + graph（3 端点）
│       └── stats.py              # stats + wander + validate + datasets（6 端点）
├── frontend/                     # React + Vite 浏览器 UI
│   └── src/components/
│       ├── GraphCanvas.tsx       # Cytoscape DAG 可视化
│       ├── MemoryList.tsx        # 表格式记忆列表（含 Health 列）
│       ├── Dashboard.tsx         # 统计 + stale + wander + validate
│       ├── MemoryDetail.tsx      # 记忆详情 + stability 滑块 + Touch + Copy-as-Context
│       ├── MemoryForm.tsx        # 创建/编辑表单 + 校验 + 标签自动补全
│       ├── SearchBar.tsx         # 全局搜索 + match quality + Resolve 动作
│       ├── HelpPanel.tsx         # 快捷键参考 + 使用指南
│       ├── Onboarding.tsx        # 首次使用引导（dataset-aware）
│       ├── Settings.tsx          # 用户设置面板
│       └── Legend.tsx            # 目录颜色图例（动态派生 + 点击高亮）
├── examples/                     # 4 个示例数据集
│   ├── companion/                # 个人日记（11 条，21 edges）
│   ├── investment/               # 投资知识（10 条）
│   ├── software-architecture/    # 架构决策（11 条）
│   └── quant_operators/          # API 文档（62 条）
├── tests/
│   ├── unit/                     # 57 个单元测试
│   ├── integration_test.py       # 24 个集成测试
│   └── test_api.py               # 5 个 API 冒烟测试
└── pyproject.toml
```

## 七、index.json 结构

```json
{
  "version": 1,
  "updated": "2026-05-08T14:22:37",
  "memories": {
    "user/investment/semiconductor-thesis": {
      "type": "atom",
      "summary": "AI存储+AI制造双核心驱动",
      "status": "active",
      "tags": ["investment", "thesis"],
      "created": "2026-02-10",
      "version": 1,
      "path": "user/investment/semiconductor-thesis.md",
      "maturity": "proven",
      "stability": 90.0,
      "stability_source": "adaptive",
      "access_count": 12,
      "last_access": "2026-05-08",
      "days_since_last_access": 0
    }
  }
}
```

## 八、Resolve 算法

```
1. 从 index.json 读取目标记忆的 imports
2. 递归构建依赖 DAG（按 depth 过滤：required/recommended/full）
3. 循环检测（DFS 三色标记） → 跳过循环节点 + warn
4. 拓扑排序（Kahn's algorithm） → 前置知识在前
5. 按序加载文件全文
6. Token 预算裁剪：
   - 正文 fits → 输出正文
   - 正文 exceeds, is required → 输出 summary
   - 正文 exceeds, not required → 跳过
7. SInc 自适应 stability 更新（R≈0.78 峰值）
8. 输出合并后的上下文文本
```

## 九、Dashboard 和 Wander 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/datasets` | GET | 列出可用数据集 + 当前选择 |
| `/api/datasets/switch` | POST | 切换活跃数据集 |
| `/api/memories` | GET | 分页记忆列表（含 decay 字段） |
| `/api/memories/{id}` | GET | 单条记忆详情 |
| `/api/memories` | POST | 创建记忆 |
| `/api/memories/{id}` | PUT | 更新记忆 |
| `/api/memories/{id}/touch` | POST | 轻量衰减刷新 |
| `/api/search` | POST | 全文搜索（body + ID + summary + tag） |
| `/api/resolve` | POST | DAG 解析 |
| `/api/graph` | GET | 图数据（nodes + edges） |
| `/api/stats` | GET | 统计（total/maturity/stale/decay_risk） |
| `/api/validate` | POST | 运行验证 |
| `/api/wander` | POST | 随机召回冷记忆 |
| `/api/reindex` | POST | 重建索引 |
| `/docs` | GET | OpenAPI Swagger UI |

## 十、MCP Server

7 个工具暴露给 AI Agent：

| 工具 | 读写 | 说明 |
|------|------|------|
| `resolve_memory` | readOnly | DAG 解析 + token 裁剪 |
| `overview` | readOnly | Top 5 相关记忆摘要 |
| `wander` | readOnly | 随机冷记忆召回 |
| `focus` | readOnly | 记忆分辨率切换 |
| `snapshot` | write | 瞬态 DAG 持久化 |
| `propose_memory` | write | 创建 draft+proposed 记忆 |
| `propose_update` | write | 提出记忆更新 |

## 十一、错误处理

| 场景 | 行为 |
|------|------|
| 循环依赖 | `validate` warn + `resolve` 跳过循环节点 |
| 断链 | `validate` error |
| 目标记忆不存在 | `resolve` 返回 404 |
| 零预算 | required 节点降级为 summary |
| 缺少 X-Codememory-Dataset header | 返回 400（`/api/datasets` 和 `/docs` 豁免） |

## 十二、已知限制

- Token 估算用 `len(text)` 代替真实 tokenizer
- 版本锁定（`pin: v1`）未实现
- 循环检测只在 validate/resolve 时运行
- File-based index 在 > 1000 节点时可能瓶颈
- 无移动端/响应式支持
