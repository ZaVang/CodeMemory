---
type: atom
id: api/quantexpr/weekly_win_ratio
summary: 'QuantExpr.weekly_win_ratio: 按周聚合后计算周胜率'
status: active
version: 1
tags: ["api-doc", "quantexpr", "scheduled"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/monthly_max_drawdown", "api/quantexpr/monthly_win_ratio", "api/quantexpr/weekly_max_drawdown"]
---
# QuantExpr.weekly_win_ratio

## 签名

```
QuantExpr.weekly_win_ratio([date_col, compound])
```

## 说明

按周聚合后计算周胜率

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
