---
type: atom
id: api/quantexpr/neutralize
summary: 'QuantExpr.neutralize: 做中性化处理'
status: active
version: 1
tags: ["api-doc", "quantexpr", "normalization"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/zscore", "api/quantexpr/standardize", "api/quantexpr/normalization", "api/quantexpr/winsorize", "api/quantexpr/sigmoid", "api/quantexpr/demean", "api/quantexpr/demedian"]
---
# QuantExpr.neutralize

## 签名

```
QuantExpr.neutralize(by[, add_intercept])
```

## 说明

做中性化处理

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
