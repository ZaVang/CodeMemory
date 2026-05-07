---
type: atom
id: api/quantdf/optimize
summary: 'QuantDF.optimize: 按日期逐期运行组合优化器——会调用 QuantExpr.optimize'
status: active
version: 1
tags: ["api-doc", "quantdf", "reporting"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/perf_eval_report", "api/quantdf/perf_eval_summarize", "api/quantdf/monthly_yearly", "api/quantdf/monthly_yearly_active"]
---
# QuantDF.optimize

## 签名

```
QuantDF.optimize(exprs)
```

## 说明

按日期逐期运行组合优化器——会调用 QuantExpr.optimize

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
