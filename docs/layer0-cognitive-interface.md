# Layer 0 认知接口设计原理

## 为什么不是 CRUD

主流记忆方案把记忆当成**需要管理的数据**——创建、读取、更新、删除。CRUD 是数据视角。

CodeMemory 把记忆当成**大脑皮层需要操作的认知对象**。这就像 CPU 不会直接操作硬盘扇区——它通过指令集（load/store/jump）操作寄存器和内存。Layer 0 就是 AI 记忆系统的**指令集**。

| 数据视角 (CRUD) | 认知视角 (Layer 0) |
|-----------------|-------------------|
| 列出所有记忆 | **扫视**——会话启动时自动感知"我应该知道什么" |
| 读取某条记忆 | **注视**——聚焦一个记忆，动态切换分辨率 |
| 搜索相关记忆 | **重构**——从目标出发，递归构建完整的因果上下文 |
| 保存记忆 | **残留**——会话推理链持久化，防止有价值的东西随进程消失 |
| （无对应） | **触景生情**——随机激活冷记忆中可能被遗忘的信息 |

CRUD 缺了两个关键认知行为：**重构**（不靠搜索靠依赖解析构建因果关系）和**触景生情**（主动打破思维定势）。而这恰好是 Layer 0 最核心的两个操作。

---

## 五个认知操作

### 1. 扫视 (overview) — 会话启动的透明感知

**解决什么问题：** Agent 启动一个新会话时，面对空白的 context，它"不知道它知道什么"。它不能每次都 search——它不知道要搜什么。

**类比人类：** 你早上坐到办公桌前，扫一眼桌上的便签、昨天留下的文档、打开的浏览器标签页。你不是在"搜索"，你是在**感知环境**——让大脑自动注意到高度激活的信息。

**原理：**

```
heat = dependents × 10 + access_count
```

heat 衡量一条记忆的"热度"——被多少其他记忆依赖（dependents）+ 被访问过多少次（access_count）。高 heat 的记忆是"大家都需要它"或"最近频繁用到它"的记忆。

会话启动时，overview 输出 top N 高 heat 记忆的摘要，注入 system prompt。Agent 不需要主动搜索——它自动就知道：
- 这个用户的偏好是什么
- 最近在做哪些事
- 哪些约束必须遵守

**如果不这样做：** Agent 要么盲目操作（不知道用户偏好），要么每次都要用户重复上下文（"我之前告诉过你..."，用户很烦）。

**CLI 使用：**

```bash
codememory overview --limit 5 --tags "investment" --format inject
```

输出格式 `inject` 可直接拼入 system prompt。`--with-recall` 追加一条随机冷记忆（结合触景生情）。

---

### 2. 注视 (focus) — 注意力分辨率切换

**解决什么问题：** 人不会把所有记忆都以同等分辨率放在脑子里。99% 的记忆处于"只知道大概"（summary），当前在用的那条才加载全文（full）。否则 token 预算瞬间耗尽。

**类比人类：** 你记得"上周二午餐吃了沙拉"——但只是摘要，不记得每一口。如果有人追问"沙拉里有什么"，你会切换到全文模式："生菜、鸡胸肉、凯撒酱"。focus 就是这个切换动作。

**原理：**

```
focus <id> --level summary   # zoom-out：只保留摘要
focus <id> --level full      # zoom-in ：加载完整正文
```

Agent 在对话中按需切换——resolve 已经加载了因果上下文（但可能为了省 token 部分记忆只给了 summary），需要深入了解某个具体记忆时才 focus full。

`--content` 模式允许不走磁盘直接对内存内容切换分辨率——适用于 resolve 输出中嵌入了完整正文但 Agent 想临时 zoom-out 的场景。

**如果不这样做：** 所有记忆都加载全文 → token 预算爆炸。或者全部只给摘要 → Agent 在需要细节时盲操作。

**CLI 使用：**

```bash
codememory focus user/investment/risk-tolerance --level full
codememory focus some-id --content "body text..." --summary "sum" --level summary
```

---

### 3. 重构 (resolve) — DAG 编译，不是搜索

**解决什么问题：** 当 Agent 需要做决策时，它需要的不是"语义相似的几条记忆"，而是**因果完整的背景知识**。理解"为什么 4 月清仓了 SOXL"需要知道"半导体主线判断"+"风险偏好"+"当时的持仓"——这些记忆语义上完全不相似，但因果上有硬依赖。

**类比人类：** 你要做一个重大决定，你不会去"搜索脑海中跟这个决定语义相似的想法"——你会**从决定往回追溯**：这个决定依赖哪些前提？这些前提又依赖哪些更基础的判断？这就是因果闭包。

**原理：**

```
resolve user/investment/context
    │
    ├── 1. 读取 imports（显式依赖声明）
    ├── 2. 递归构建 DAG
    ├── 3. 循环检测（DFS 三色标记）
    ├── 4. 拓扑排序（被依赖的在前）
    ├── 5. token 预算裁剪（超预算时降级）
    │     降级优先级：required=full > recommended=full
    │                  > required=summary > recommended=summary
    │                  > related=full
    └── 6. 输出合并上下文
```

关键差异：
- **搜索**说："找到跟 query 最像的 top-5"
- **编译**说："从入口模块出发，递归解析所有 import，按依赖顺序排列"

搜索可能漏掉因果相关但语义不相似的记忆。编译不会——依赖是显式声明的合约。

**被动提醒：** resolve 在输出末尾附加 `## Notices` 节：
- `summary may be stale` — body 被改了但 summary_hash 没更新，Agent 看到的是过时摘要
- `pinned version v1 is behind current v3` — 锁定的版本不是最新的

这两个提醒不用 Agent 主动检查——resolve 时被动告知，降低 Agent 的认知负荷。

**CLI 使用：**

```bash
codememory resolve user/investment/context
codememory resolve user/investment/context --depth full --budget 3000
```

---

### 4. 残留 (snapshot) — 会话推理链持久化

**解决什么问题：** Agent 在一个会话中可能完成复杂的推理链——"读了 A 和 B，发现矛盾，跟用户确认，修正了 B，得出结论 C"。这个推理链存在内存中（TransientDAG），进程退出即消失。如果没有持久化机制，下一次会话从零开始，丢失了宝贵的推理过程。

**类比人类：** 你开了一个长会，讨论了很多东西，达成了一些结论。会后你**做笔记**——把核心讨论点和结论写下来。不写的话，明天早上基本忘光。

**原理：**

```
TransientDAG（内存）
    │
    ├── add(node)     — 添加推理节点
    ├── remove(id)    — 移除错误节点
    ├── resolve()     — 在内存中构建 DAG 查看当前推理状态
    │
    └── snapshot_dag("session-001")  → user/snapshots/2026-04-27-session-001.md
                                       （落盘为 atom 类型的 .md 文件）
```

`--target` 模式：不是快照 TransientDAG，而是对 index 中的某个记忆执行 DAG 解析后落盘——"把这个记忆的完整因果上下文拍个快照，存档"。

**如果不这样做：** 有价值的推理链每次会话结束就消失。Agent 永远在"重新发现"已知的结论。

**CLI 使用：**

```bash
codememory snapshot "session-001"                        # 快照当前 TransientDAG
codememory snapshot "ctx-snapshot" --target user/investment/context  # 快照记忆上下文
codememory snapshot "from-file" --from-dag /tmp/dag.json              # 快照序列化 DAG
```

---

### 5. 触景生情 (wander) — 随机激活冷记忆

**解决什么问题：** 确定性检索（search/resolve）只会返回"你明确想找的东西"。但人脑有一个至关重要的能力：**偶然想起一件很久没想的事，发现它跟当前问题有关。** 这是创造力和灵感的重要来源。

**类比人类：** 你在思考一个技术选型问题时，突然想起三年前看过的一篇关于类似问题的文章——你当时没有刻意"搜索"它，是某个细节触发了联想。wander 模拟这个过程。

**原理：**

```
cool 模式权重：weight = 1 / (access_count + 1)
排除：protected 记忆（intensity >= 8，太重要不需要随机激活）
```

访问次数越少的记忆被选中的概率越大（冷记忆优先）。但不是一直推送冷记忆——`overview --with-recall` 在输出末尾只追加一条。

这防止了 Agent 的"思维定势"——总是访问那几条高 heat 的活跃记忆，忽略了角落里可能相关的信息。

**如果不这样做：** 记忆系统变成"你需要什么就搜什么"的数据库。冷记忆永远冷下去，虽然 validate 会提示衰减，但没有主动激活机制。

**CLI 使用：**

```bash
codememory wander                          # cool 模式：偏置冷记忆
codememory wander --mode random           # 纯随机（所有记忆等权）
codememory wander --inject                # 输出可直接注入 system prompt 的格式
```

---

## 五个操作的协作流

一次典型的 Agent 会话中，Layer 0 五个操作不是孤立的，而是按认知节奏协作：

```
会话启动
    │
    ├── overview（扫视）
    │   └── top 5 高 heat 记忆摘要注入 system prompt
    │   └── --with-recall 追加一条冷记忆（触景生情）
    │
    ├── 用户提出需求
    │   │
    │   ├── resolve（重构）
    │   │   └── 从相关记忆出发构建因果闭包
    │   │   └── ## Notices 被动告知 stale/pin 问题
    │   │
    │   ├── focus（注视）
    │   │   └── 对上下文中的关键记忆切换 full 分辨率
    │   │   └── 对不需要细节的记忆保持 summary
    │   │
    │   └── wander（触景生情）
    │       └── 对话中间歇激活边缘记忆
    │       └── 打破思维定势
    │
    └── 会话结束
        │
        └── snapshot（残留）
            └── 推理链中有价值的部分持久化
            └── 下次会话 overview 会扫视到它
```

这不是一个线性流程，而是一个**认知循环**——扫视建立态势感知，重构构建因果上下文，注视聚焦关键节点，残留把产物写回记忆系统，触景生情在循环中随机注入新鲜信息。下一次会话的扫视会感知到上一次残留的内容。

---

## 与主流方案的认知覆盖对比

| 认知操作 | 人类行为 | Claude Code Memory | ChatGPT Memory | CodeMemory |
|---------|---------|-------------------|----------------|------------|
| 扫视 | 看桌上便签 | ✓ (MEMORY.md 启动加载) | ~ (隐式注入，用户不可控) | ✓ overview |
| 注视 | 聚焦一个想法 | ✗ | ✗ | ✓ focus |
| 重构 | 追溯因果关系 | ✗ | ✗ | ✓ resolve (DAG) |
| 残留 | 做笔记 | ✗ (会话结束=消失) | ✓ (隐式提取持久) | ✓ snapshot |
| 触景生情 | 偶然想起旧事 | ✗ | ✗ | ✓ wander |

Claude Code 的 MEMORY.md 方案做了"扫视"——启动时加载相关记忆到 context。但它没有"重构"（你不能声明记忆 A 依赖记忆 B，加载 A 时自动带入 B）、没有"注视"（你不能对某条记忆说"给我全文"vs"只看摘要"）、没有"触景生情"（冷记忆永远冷，直到被遗忘）。

ChatGPT Memory 做了"残留"——自动从对话中提取信息持久化——但它是隐式的、黑盒的。用户不知道系统记住了什么、这些记忆之间有什么关系。

CodeMemory 的五个操作覆盖了全部五种认知行为，且全部是**显式的、可审计的、确定性的**。

---

## 设计原则总结

1. **Agent 不搜索，Agent 感知** — overview 是被动注入，Agent 不需要知道"要搜什么"
2. **记忆之间是显式依赖，不是隐式相似** — resolve 编译依赖图，不靠 embedding 猜
3. **分辨率是动态的，不是二元的** — focus 允许 summary/full 切换，节省 token 预算
4. **推理链是重要的，不能随会话丢弃** — snapshot 持久化 TransientDAG
5. **遗忘不是删除，是冷却** — protected 记忆不衰减，冷记忆靠 wander 激活，系统只建议不删除
6. **不把记忆当文档管理，当下一次思考的起点** — 存储是为了将来的重构，不是为了归档

---

## Bash 是接口，CLI 是加速器

CodeMemory 遵循 Claude Code 的设计原则：**给 LLM 的工具越少越好，最好只有 bash。**

### 一切操作都有 bash 等效

记忆以 `.md` + YAML frontmatter 存储在文件系统上。`index.json` 是标准 JSON。任何 LLM 只要能用 `cat`、`echo`、`grep`，就能操作 CodeMemory 的记忆库——**不安装 codememory 也能用**。

下面逐条给出每个命令对应的 bash 等效操作。

---

#### create — 创建记忆

```bash
# codememory create --type atom --id user/ideas/my-thesis --tags "ai" --intensity 5
cat > user/ideas/my-thesis.md << 'EOF'
---
type: atom
id: user/ideas/my-thesis
summary: "AI 基础设施投资主线"
tags: ["ai", "investment"]
intensity: 5
---
# 正文
EOF
codememory reindex   # 更新 index.json（LLM 也可手动更新 index.json，但极易出错）
```

**封装了什么：** 自动补全 YAML 模板字段（version、created、summary_hash），自动 reindex。

---

#### update — 更新记忆（版本控制）

```bash
# codememory update user/ideas/my-thesis --change-note "修改正文" --body "新内容"
# 等效于：
# 1. 读取原文件 frontmatter
# 2. 递增 version
# 3. 追加 change_log 条目
# 4. 重算 summary_hash（如果 --summary 也改了）
# 5. 写回文件
# 6. 重新计算 body hash
# 7. codememory reindex
```

**封装了什么：** 版本递增 + change_log 追加 + hash 重算——三步必须原子一致，LLM 手动操作容易忘掉其中一步。

---

#### reindex — 重建索引

```bash
# codememory reindex
# 等效于：扫描 user/ self/ schemas/ 下所有 .md，解析 YAML frontmatter，
# 写入 .codememory/index.json
```

**封装了什么：** 遍历目录 → 解析 YAML → 提取字段 → 保留已有 access_count/last_access → 写 JSON。LLM 每条 .md 读一遍做这件事太贵。

---

#### validate — 完整性校验

```bash
# codememory validate
# 等效于：
# 1. 读 index.json
# 2. 对每个 memory 的 imports 做存在性检查（断链检测）
# 3. 对有 schema 字段的记忆做 schema 字段合规检查
# 4. 对 imports 图做 DFS 三色标记循环检测
# 5. 对孤立 + 冷记忆做衰减判断（access_count=0 + 无引用 + intensity<8）
```

**封装了什么：** 四项检查（断链/schema 合规/循环依赖/衰减建议）——LLM 理论上能做，但 DFS 循环检测在自然语言推理中极易出错。

---

#### resolve — DAG 拓扑拼装

```bash
# codememory resolve user/investment/context --depth full --budget 3000
# 等效于：
# 1. 读 index.json 找到目标记忆的 imports
# 2. 递归读取每个依赖记忆的 imports（构建 DAG）
# 3. 对 DAG 做 DFS 循环检测，跳过循环节点
# 4. Kahn's algorithm 拓扑排序（被依赖的在前）
# 5. 按 depth 过滤节点（required/recommended/related）
# 6. 按序读取每个节点的 .md 文件
# 7. 累加 token 计数，超 budget 时降级（required=full > recommended=full
#    > required=summary > recommended=summary > related=full）
# 8. 对比每条记忆的 summary_hash vs 实际 body hash（stale 检测）
# 9. 检查 pin 版本是否落后于当前版本
# 10. 合并输出 + ## Notices 节
```

**封装了什么：** 10 步流程，LLM 手动做的话，光是递归追踪依赖读完所有文件 context 就满了，更别说拓扑排序和降级裁剪。

---

#### search — 检索记忆

```bash
# codememory search --query "risk" --tags "investment" --type atom --status active
grep -rl "risk" user/ self/ schemas/ | while read f; do
    # 检查 frontmatter 的 tags/type/status 是否匹配
done
# 然后按 (被引用数, access_count) 降序排列
```

**封装了什么：** 多条件过滤 + 排序。LLM 用 grep + 手动翻文件也能做，但封装后一行搞定。

---

#### orphans — 孤立记忆发现

```bash
# codememory orphans --type atom --min-intensity 5
# 等效于：
# 1. 读 index.json
# 2. 遍历所有记忆的 imports，计算每个 ID 的 in-degree
# 3. 输出 in-degree=0 的记忆
# 4. 标注 [protected]（intensity>=8）或 [decay-risk]
```

**封装了什么：** 入度计算——LLM 手动做需要在 context 里同时持有所有 imports 关系，记忆数量多时不可行。

---

#### overview — 扫视

```bash
# codememory overview --limit 5 --tags "investment" --format inject --with-recall
# 等效于：
# 1. 读 index.json
# 2. 对每个记忆计算 heat = dependents * 10 + access_count
# 3. 按 heat 降序，取 top N
# 4. 检查 stale（summary_hash vs body hash）
# 5. --with-recall：从冷记忆中随机抽一条
#    weight = 1 / (access_count + 1)，排除 protected
```

**封装了什么：** heat 公式 + stale 检测 + 冷记忆加权随机——全是算术和排序，LLM 能做但浪费 token。

---

#### focus — 注视

```bash
# codememory focus user/investment/risk-tolerance --level full
cat user/investment/risk-tolerance.md        # level=full：读全文

# codememory focus user/investment/risk-tolerance --level summary
# 提取 frontmatter 中的 summary 字段输出    # level=summary：只读摘要
```

**封装了什么：** 几乎没封装。`focus --level full` 本质上就是 `cat`。`--level summary` 只是帮你从 frontmatter 里取 summary 字段。这是最薄的一层包装。

---

#### wander — 触景生情

```bash
# codememory wander --mode cool --inject
# 等效于：
# 1. 读 index.json
# 2. 列出所有非 protected 记忆（intensity < 8）
# 3. 按 weight = 1 / (access_count + 1) 加权随机选一条
# 4. 输出：[recall] <id> — <summary>（tags: t1,t2）
```

**封装了什么：** 加权随机采样——LLM 自己也能 `shuf`，但按 access_count 加权需要算概率分布。

---

#### changelog — 变更历史

```bash
# codememory changelog user/investment/risk-tolerance
# 等效于：
# 读 .md 文件的 YAML frontmatter，提取 change_log 列表，按时间倒序输出
```

**封装了什么：** 几乎没封装。就是 frontmatter 字段提取 + 格式化输出。存在只是为了命令完备性。

---

#### snapshot — 瞬态持久化

```bash
# codememory snapshot "session-001"
# 等效于：
# 将当前 TransientDAG（内存中的推理节点）转为 YAML frontmatter，
# 写入 user/snapshots/2026-04-27-session-001.md，然后 reindex
```

**封装了什么：** TransientDAG 是内存结构，没有文件对应——bash 操作不了。这是唯一一个 LLM 无法用纯 bash 等效的操作。但 `--target` 和 `--from-dag` 模式本质上是 resolve + 写文件，bash 可直接操作。

---

### 等效性总结

| 命令 | 封装程度 | LLM 用 bash 能做吗 |
|------|---------|-------------------|
| `focus` | 几无封装（≈ cat） | ✓ 一行 bash |
| `changelog` | 几无封装（frontmatter 提取） | ✓ 读文件即可 |
| `search` | 薄封装（grep + 过滤 + 排序） | ✓ 多行 bash |
| `create` | 中等（模板生成 + 自动 reindex） | ✓ 手写 YAML 即可 |
| `update` | 中等（版本递增 + hash 重算） | ✓ 但容易漏步骤 |
| `orphans` | 算法封装（入度计算） | ~ 需脚本辅助 |
| `overview` | 算法封装（heat 公式 + stale 检测） | ~ 需脚本辅助 |
| `wander` | 算法封装（加权随机采样） | ~ 需脚本辅助 |
| `validate` | 算法封装（DFS 循环检测） | ✗ LLM 不擅长 |
| `resolve` | 算法封装（DAG + 拓扑 + 降级） | ✗ LLM 不擅长 |
| `snapshot` | 内存操作（TransientDAG） | ✗ 内存结构无文件对应 |
| `reindex` | 批量 I/O（遍历 + 解析 + 写 JSON） | ~ 能做但极贵 |

底线：**没有一条命令是魔法。** 12 条命令里，6 条是薄到中等封装（LLM 用 bash 能做，CLI 只是省 token），4 条包装了确定性的算法逻辑（LLM 做容易出错），2 条（snapshot 的内存操作 + reindex 的批量 I/O）是 CLI 独有的。这就回到了设计的起点——以 `.md` 文件为唯一真源，CLI 只是高频操作的快捷方式。

---

## 两层接口：Agent vs 外部平台

CodeMemory 有两类使用者，对应两种接口层：

```
┌─────────────────────────────────────────┐
│  Agent（如 Claude Code 内的 Agent）       │
│  看到的接口：bash                        │
│  用法：codememory resolve <id>           │
│        codememory overview --limit 5     │
│        codememory validate               │
│                                          │
│  工具数量：1 个（bash）                   │
│  选择负担：零（不需要判断用哪个工具）       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  外部平台（OpenAI API、LangChain 等）     │
│  看到的接口：function-calling schema     │
│  用法：tools = toolkit.get_tools_for_openai() │
│        response = client.chat(..., tools=tools) │
│                                          │
│  工具数量：10 个（展开的函数列表）          │
│  原因：这些平台的工具协议是 function-calling│
│        不是 bash，需要展开才能对接          │
└─────────────────────────────────────────┘
```

**Agent 走 bash** — 这是硬约束，写在 CLAUDE.md 里。Agent 不需要知道有 10 个 Python 函数，它只看到一行 `codememory overview`。

**外部平台走 function-calling adapter** — `CodememoryToolkit.get_tools_for_openai()` 和 `register_to_sandbox()` 是给那些"只能调 function"的平台用的适配层。它们不是 CodeMemory 的原生接口，是翻译层。

这就是为什么 `cli.py`（174 行）和 `tools.py`（300 行）同时存在但都委托给同一个 `handlers.py`：同一个业务逻辑，两种外壳——一种给 bash 用，一种给 function-calling 协议用。
