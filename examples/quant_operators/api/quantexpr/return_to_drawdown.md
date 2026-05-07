---
type: atom
id: api/quantexpr/return_to_drawdown
summary: 'QuantExpr.return_to_drawdown: 计算年化收益与绝对最大回撤之比'
status: active
version: 1
tags: ["api-doc", "quantexpr", "risk"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/drawdown", "api/quantexpr/max_drawdown", "api/quantexpr/max_underwater", "api/quantexpr/underwater", "api/quantexpr/sharpe", "api/quantexpr/sortino", "api/quantexpr/rolling_sharpe", "api/quantexpr/day_cumrtn_corr"]
---
# QuantExpr.return_to_drawdown

## 签名

```
QuantExpr.return_to_drawdown([annual_days, compound])
```

## 说明

计算年化收益与绝对最大回撤之比

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
