---
type: composite
id: user/investment/current-holdings
summary: "当前持仓概览：半导体ETF 40% + 现金 30%"
status: active
created: 2026-04-20
updated: 2026-04-24
version: 1
tags: [investment, portfolio]
purpose: "查看当前持仓分布时加载"

imports:
  required:
    - user/investment/position-semiconductor
    - user/investment/position-cash
---

# 当前持仓

本组合提供当前持仓的完整视图。

## 持仓分布

| 标的 | 仓位 | 状态 |
|------|------|------|
| 半导体ETF (512480) | 40% | 浮盈 15% |
| 现金（货币基金） | 30% | 稳定 |
| 其他（未跟踪） | 30% | — |
