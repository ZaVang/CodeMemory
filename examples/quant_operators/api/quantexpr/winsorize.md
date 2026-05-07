---
type: atom
id: api/quantexpr/winsorize
summary: 'QuantExpr.winsorize: 做 winsorization 缩尾处理'
status: active
version: 1
tags: ["api-doc", "quantexpr", "normalization"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/zscore", "api/quantexpr/standardize", "api/quantexpr/normalization", "api/quantexpr/sigmoid", "api/quantexpr/demean", "api/quantexpr/demedian", "api/quantexpr/neutralize"]
---
# QuantExpr.winsorize

## 签名

```
QuantExpr.winsorize([quantile, sigma])
```

## 说明

做 winsorization 缩尾处理

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
