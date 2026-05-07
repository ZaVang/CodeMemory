---
type: atom
id: api/quantdf/select
summary: 'QuantDF.select: 选取标准 index 列和指定表达式'
status: active
version: 1
tags: ["api-doc", "quantdf", "time-ops"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/cross_sectional", "api/quantdf/time_series", "api/quantdf/rolling", "api/quantdf/downsample"]
---
# QuantDF.select

## 签名

```
QuantDF.select(exprs)
```

## 说明

选取标准 index 列和指定表达式

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
