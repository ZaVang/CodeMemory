---
type: atom
id: api/quantdf/downsample
summary: 'QuantDF.downsample: 将数据降频到指定频率'
status: active
version: 1
tags: ["api-doc", "quantdf", "time-ops"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/cross_sectional", "api/quantdf/time_series", "api/quantdf/rolling", "api/quantdf/select"]
---
# QuantDF.downsample

## 签名

```
QuantDF.downsample(exprs, freq)
```

## 说明

将数据降频到指定频率

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
