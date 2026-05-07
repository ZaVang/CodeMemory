---
type: atom
id: api/quantdf/perf_eval_report
summary: 'QuantDF.perf_eval_report: 生成绩效评估 HTML 报告——综合调用多种 QuantExpr 指标'
status: active
version: 1
tags: ["api-doc", "quantdf", "reporting"]
intensity: 5
maturity: draft
imports:
  required: ["api/quantdf"]
  recommended: ["api/quantexpr"]
  related: ["api/quantdf/perf_eval_summarize", "api/quantdf/monthly_yearly", "api/quantdf/monthly_yearly_active", "api/quantdf/optimize"]
---
# QuantDF.perf_eval_report

## 签名

```
QuantDF.perf_eval_report(path, *[, returns, layout])
```

## 说明

生成绩效评估 HTML 报告——综合调用多种 QuantExpr 指标

## 所属类

[QuantDF](Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。)
