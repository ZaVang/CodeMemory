# /sync-review — 与 AririgiAgent 持续协作审查循环

单次检查-处理循环。由外部定时器（`/loop`）驱动重复执行。

## 运行方式

用户启动持续轮询：
```
/loop 10m /sync-review
```

每次 `/sync-review` 执行完整的"检查 → 实施 → 推送 → 回复"周期。

## 审查循环流程

```
[检查邮件] → 有新邮件? → YES → [读取审查] → [写入 SPRINT.md] → [/goal 实现] → [git push] → [回复邮件]
                       → NO  → 静默退出，等待下一轮
```

## 循环参数

- **审查者邮箱**：AririgiAgent@coze.email
- **Sprint 合同路径**：docs/plans/SPRINT.md
- **已处理 UID**：记忆在对话上下文中（会话级别），避免重复处理

## 操作步骤

### 步骤 1：检查新邮件

使用 email-mailbox:check-email 技能：

```bash
python "<plugin_dir>/scripts/check_email.py" list --limit 10 --json
```

筛选 `from == "AririgiAgent@coze.email"` 的邮件，排除：
- subject 含 "测试" 的邮件
- UID 已在本次会话"已处理"列表中的邮件

若没有新的审查邮件 → 提示"本轮无新审查"，退出。

### 步骤 2：读取审查内容

```bash
python "<plugin_dir>/scripts/check_email.py" read <new_uid> --json
```

提取 `body`，识别审查建议列表。

### 步骤 3：写入 Sprint 合同

将审查意见按以下格式追加到 `docs/plans/SPRINT.md`：

```markdown
---
## 第 N 轮追加任务（AririgiAgent 审查，<日期>）

| # | 任务 | 说明 | 状态 |
|---|------|------|------|
| 1 | <建议摘要> | <详细说明> | [ ] |

---
```

### 步骤 4：实施审查建议

对每个 `[ ]` 任务：
1. 使用 `superpowers:receiving-code-review` 技能验证建议的适用性
2. 逐项实现，每完成一项将 `[ ]` 改为 `[x]`
3. 运行测试确认零回归：
   ```bash
   PYTHONPATH=src python -m pytest tests/unit/ -q --tb=short
   PYTHONPATH=src python tests/integration_test.py
   ```

### 步骤 5：推送代码

```bash
git add <changed_files> && git commit -m "feat: <审查轮次> from AririgiAgent review" && git push origin main
```

### 步骤 6：回复邮件

使用 email-mailbox:send-email 技能回复 AririgiAgent@coze.email：
- 标题：`Re: <原邮件标题>`
- 正文：已实施项 / 暂不实施项及原因 / 测试结果 / Commit SHA

### 步骤 7：标记完成

将处理完的邮件 UID 加入"已处理"列表，等待 `/loop` 下一轮触发。

---

## 状态管理

- **已处理 UID**：会话级内存列表（不持久化），避免同一会话内重复处理
- **跨会话去重**：同一封邮件若在上一会话已实施并回复，新会话启动时会识别为"已回复"（通过检查 sent 邮件或 subject 前缀）
- **中断恢复**：若实施过程中会话中断，重启 `/loop` 后 `/sync-review` 会重新检测到未处理邮件并继续

## 验收命令

```bash
# 检查邮件拉取
python "<plugin_dir>/scripts/check_email.py" search "AririgiAgent" --json

# 验证代码质量
PYTHONPATH=src python -m pytest tests/unit/ -q --tb=short
PYTHONPATH=src python tests/integration_test.py

# 验证 Sprint 合同
codememory reindex && codememory validate
```
