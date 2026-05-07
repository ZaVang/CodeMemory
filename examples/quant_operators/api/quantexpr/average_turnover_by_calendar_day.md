---
type: atom
id: api/quantexpr/average_turnover_by_calendar_day
summary: 'QuantExpr.average_turnover_by_calendar_day: 计算按自然日摊薄后的平均换手'
status: active
version: 1
tags: ["api-doc", "quantexpr", "turnover"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/average_turnover", "api/quantexpr/weekly_average_turnover", "api/quantexpr/turnover_efficiency", "api/quantexpr/profit_per_turnover"]
---
# QuantExpr.average_turnover_by_calendar_day

## 签名

```
QuantExpr.average_turnover_by_calendar_day([date_col])
```

## 说明

计算按自然日摊薄后的平均换手

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
