---
type: composite
id: user/investment/context
summary: "投资决策的完整上下文包，包含主线判断、风险偏好、历史决策和当前持仓"
status: active
created: 2026-04-24
updated: 2026-04-24
version: 1
tags: [investment, context]
purpose: "讨论投资话题时加载的完整上下文"

imports:
  required:
    - user/investment/semiconductor-thesis
    - user/investment/risk-tolerance
    - user/investment/february-buy
    - user/investment/current-holdings
---

# 投资决策上下文

本组合提供完整的投资决策背景。

## 加载顺序

1. 主线判断 → `semiconductor-thesis`
2. 风险偏好 → `risk-tolerance`
3. 历史决策 → `february-buy`
4. 当前持仓 → `current-holdings`

## 使用场景

- 讨论是否要调仓
- 回顾"当时为什么买这个"
- 给其他 AI 平台提供投资上下文
