---
type: atom
id: api/quantexpr/monthly_max_drawdown
summary: 'QuantExpr.monthly_max_drawdown: 计算月频收益序列的最大回撤'
status: active
version: 1
tags: ["api-doc", "quantexpr", "scheduled"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/monthly_win_ratio", "api/quantexpr/weekly_max_drawdown", "api/quantexpr/weekly_win_ratio"]
---
# QuantExpr.monthly_max_drawdown

## 签名

```
QuantExpr.monthly_max_drawdown([date_col, compound])
```

## 说明

计算月频收益序列的最大回撤

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
