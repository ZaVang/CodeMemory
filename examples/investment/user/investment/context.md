---
type: atom
id: user/investment/context
summary: 投资决策完整上下文——从主线判断→市场事实→风险约束→历史决策→当前持仓，一键加载因果链
status: active
created: 2026-04-24
version: 1
tags:
- investment
- context
- entry-point
protected: true
purpose: 讨论投资话题时加载的完整因果上下文
imports:
  required:
    - user/investment/semiconductor-thesis
    - user/investment/risk-tolerance
    - user/preferences/no-leverage
    - user/investment/february-buy
    - user/investment/current-holdings
  recommended:
    - user/facts/nvidia-earnings
    - user/facts/soxl-composition
    - user/observations/soxl-drop-march
summary_hash: fbd6e11
---
# 投资决策上下文

本组合提供讨论投资问题所需的完整因果上下文。

## 为什么需要这个入口

当你需要评估"该不该调仓、止盈还是加仓"时，你需要同时知道：
1. **为什么买**（主线判断）
2. **能不能承受波动**（风险偏好 + 硬约束）
3. **当时怎么想的**（历史决策）
4. **现在有多少**（当前持仓）
5. **外部发生了什么**（市场事件）

单独检索任何一条都会遗漏关键信息——这就是为什么需要 DAG。

## 加载顺序（拓扑排序自动处理）

因果关系从底层到顶层：市场事实 → 分析判断 → 个人约束 → 具体决策 → 当前状态。
