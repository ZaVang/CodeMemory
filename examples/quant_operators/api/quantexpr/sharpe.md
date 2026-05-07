---
type: atom
id: api/quantexpr/sharpe
summary: 'QuantExpr.sharpe: 从收益率序列计算年化 Sharpe 比率'
status: active
version: 1
tags: ["api-doc", "quantexpr", "risk"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/drawdown", "api/quantexpr/max_drawdown", "api/quantexpr/max_underwater", "api/quantexpr/underwater", "api/quantexpr/sortino", "api/quantexpr/rolling_sharpe", "api/quantexpr/return_to_drawdown", "api/quantexpr/day_cumrtn_corr"]
---
# QuantExpr.sharpe

## 签名

```
QuantExpr.sharpe([annual_days, compound])
```

## 说明

从收益率序列计算年化 Sharpe 比率

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
