---
type: atom
id: api/quantdf/interval_return
summary: 'QuantDF.interval_return: 计算区间收益表'
status: active
version: 1
tags: ["api-doc", "quantdf", "return-agg"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/monthly_return", "api/quantdf/weekly_return", "api/quantdf/monthly_active_return", "api/quantdf/weekly_active_return"]
---
# QuantDF.interval_return

## 签名

```
QuantDF.interval_return(*[, returns, compound])
```

## 说明

计算区间收益表

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
