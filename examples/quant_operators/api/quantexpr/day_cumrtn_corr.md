---
type: atom
id: api/quantexpr/day_cumrtn_corr
summary: 'QuantExpr.day_cumrtn_corr: 计算日序号与累计净值之间的相关系数——衡量净值增长稳定性'
status: active
version: 1
tags: ["api-doc", "quantexpr", "risk"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantexpr"]
  recommended: []
  related: ["api/quantexpr/drawdown", "api/quantexpr/max_drawdown", "api/quantexpr/max_underwater", "api/quantexpr/underwater", "api/quantexpr/sharpe", "api/quantexpr/sortino", "api/quantexpr/rolling_sharpe", "api/quantexpr/return_to_drawdown"]
---
# QuantExpr.day_cumrtn_corr

## 签名

```
QuantExpr.day_cumrtn_corr([compound])
```

## 说明

计算日序号与累计净值之间的相关系数——衡量净值增长稳定性

## 所属类

[QuantExpr](Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。)
