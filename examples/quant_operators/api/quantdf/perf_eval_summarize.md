---
type: atom
id: api/quantdf/perf_eval_summarize
summary: 'QuantDF.perf_eval_summarize: 汇总一个或多个组合收益序列的绩效指标'
status: active
version: 1
tags: ["api-doc", "quantdf", "reporting"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/perf_eval_report", "api/quantdf/monthly_yearly", "api/quantdf/monthly_yearly_active", "api/quantdf/optimize"]
---
# QuantDF.perf_eval_summarize

## 签名

```
QuantDF.perf_eval_summarize(*[, returns, compound])
```

## 说明

汇总一个或多个组合收益序列的绩效指标

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
