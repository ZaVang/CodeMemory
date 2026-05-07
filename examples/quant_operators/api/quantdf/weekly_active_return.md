---
type: atom
id: api/quantdf/weekly_active_return
summary: 'QuantDF.weekly_active_return: 将日超额收益按周聚合为带标签的 dataframe'
status: active
version: 1
tags: ["api-doc", "quantdf", "return-agg"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/interval_return", "api/quantdf/monthly_return", "api/quantdf/weekly_return", "api/quantdf/monthly_active_return"]
---
# QuantDF.weekly_active_return

## 签名

```
QuantDF.weekly_active_return(*[, returns, benchmark])
```

## 说明

将日超额收益按周聚合为带标签的 dataframe

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
