---
type: atom
id: api/quantdf/weekly_drawdown
summary: 'QuantDF.weekly_drawdown: 计算周频收益序列对应的回撤表'
status: active
version: 1
tags: ["api-doc", "quantdf", "drawdown"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/monthly_drawdown"]
---
# QuantDF.weekly_drawdown

## 签名

```
QuantDF.weekly_drawdown(*[, returns, compound])
```

## 说明

计算周频收益序列对应的回撤表

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
