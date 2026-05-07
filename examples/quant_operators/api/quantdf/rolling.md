---
type: atom
id: api/quantdf/rolling
summary: 'QuantDF.rolling: 滚动对每个窗口应用操作'
status: active
version: 1
tags: ["api-doc", "quantdf", "time-ops"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/cross_sectional", "api/quantdf/time_series", "api/quantdf/downsample", "api/quantdf/select"]
---
# QuantDF.rolling

## 签名

```
QuantDF.rolling(exprs[, every, window])
```

## 说明

滚动对每个窗口应用操作

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
