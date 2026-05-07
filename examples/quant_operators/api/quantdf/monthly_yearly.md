---
type: atom
id: api/quantdf/monthly_yearly
summary: 'QuantDF.monthly_yearly: 生成月度/年度收益透视表'
status: active
version: 1
tags: ["api-doc", "quantdf", "reporting"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/perf_eval_report", "api/quantdf/perf_eval_summarize", "api/quantdf/monthly_yearly_active", "api/quantdf/optimize"]
---
# QuantDF.monthly_yearly

## 签名

```
QuantDF.monthly_yearly(*[, returns, compound])
```

## 说明

生成月度/年度收益透视表

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
