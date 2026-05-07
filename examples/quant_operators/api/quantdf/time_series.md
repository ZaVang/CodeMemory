---
type: atom
id: api/quantdf/time_series
summary: 'QuantDF.time_series: 对每个时间序列应用 QuantExpr 操作——比如对每行做 sharpe'
status: active
version: 1
tags: ["api-doc", "quantdf", "time-ops"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/cross_sectional", "api/quantdf/rolling", "api/quantdf/downsample", "api/quantdf/select"]
---
# QuantDF.time_series

## 签名

```
QuantDF.time_series(exprs)
```

## 说明

对每个时间序列应用 QuantExpr 操作——比如对每行做 sharpe

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
