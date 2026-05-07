---
type: atom
id: api/quantexpr/profit_per_turnover
summary: 'QuantExpr.profit_per_turnover: 计算单位总换手对应的总收益'
status: active
version: 1
tags: ["api-doc", "quantexpr", "turnover"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/average_turnover", "api/quantexpr/weekly_average_turnover", "api/quantexpr/average_turnover_by_calendar_day", "api/quantexpr/turnover_efficiency"]
---
# QuantExpr.profit_per_turnover

## 签名

```
QuantExpr.profit_per_turnover(turnover_col)
```

## 说明

计算单位总换手对应的总收益

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
