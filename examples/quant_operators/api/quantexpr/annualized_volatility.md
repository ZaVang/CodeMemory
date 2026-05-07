---
type: atom
id: api/quantexpr/annualized_volatility
summary: 'QuantExpr.annualized_volatility: 从收益率序列计算年化波动率'
status: active
version: 1
tags: ["api-doc", "quantexpr", "basic"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/nav", "api/quantexpr/total_return", "api/quantexpr/annualized_return", "api/quantexpr/daily_win_ratio", "api/quantexpr/active_return", "api/quantexpr/annualized_active_return", "api/quantexpr/total_active_return"]
---
# QuantExpr.annualized_volatility

## 签名

```
QuantExpr.annualized_volatility([annual_days, compound])
```

## 说明

从收益率序列计算年化波动率

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
