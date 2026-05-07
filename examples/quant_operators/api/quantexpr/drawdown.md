---
type: atom
id: api/quantexpr/drawdown
summary: 'QuantExpr.drawdown: 从收益率序列计算回撤序列'
status: active
version: 1
tags: ["api-doc", "quantexpr", "risk"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/max_drawdown", "api/quantexpr/max_underwater", "api/quantexpr/underwater", "api/quantexpr/sharpe", "api/quantexpr/sortino", "api/quantexpr/rolling_sharpe", "api/quantexpr/return_to_drawdown", "api/quantexpr/day_cumrtn_corr"]
---
# QuantExpr.drawdown

## 签名

```
QuantExpr.drawdown([compound])
```

## 说明

从收益率序列计算回撤序列

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
