---
type: atom
id: api/quantdf/cross_sectional
summary: 'QuantDF.cross_sectional: 对每个截面应用 QuantExpr 操作——比如对每列 zscore'
status: active
version: 1
tags: ["api-doc", "quantdf", "time-ops"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/time_series", "api/quantdf/rolling", "api/quantdf/downsample", "api/quantdf/select"]
---
# QuantDF.cross_sectional

## 签名

```
QuantDF.cross_sectional([exprs])
```

## 说明

对每个截面应用 QuantExpr 操作——比如对每列 zscore

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
