---
type: atom
id: api/quantdf
summary: 'QuantDF: Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。 (19 个方法)'
status: active
version: 1
tags: ["api-doc", "quantdf", "class-overview"]
intensity: 7
maturity: draft
imports:
  required: []
  recommended: []
  related: []
---
    # QuantDF

    ## 概述

    Quant DataFrame — 在 DataFrame 级别进行截面/时序/滚动操作。底层计算委托给 QuantExpr。

    ## 方法列表

    - [cross_sectional](api/quantdf/cross_sectional) — 对每个截面应用 QuantExpr 操作——比如对每列 zscore
- [time_series](api/quantdf/time_series) — 对每个时间序列应用 QuantExpr 操作——比如对每行做 sharpe
- [rolling](api/quantdf/rolling) — 滚动对每个窗口应用操作
- [downsample](api/quantdf/downsample) — 将数据降频到指定频率
- [select](api/quantdf/select) — 选取标准 index 列和指定表达式
- [interval_return](api/quantdf/interval_return) — 计算区间收益表
- [monthly_return](api/quantdf/monthly_return) — 将日收益率按月聚合为带标签的 dataframe
- [weekly_return](api/quantdf/weekly_return) — 将日收益率按周聚合为带标签的 dataframe
- [monthly_active_return](api/quantdf/monthly_active_return) — 将日超额收益按月聚合为带标签的 dataframe
- [weekly_active_return](api/quantdf/weekly_active_return) — 将日超额收益按周聚合为带标签的 dataframe
- [monthly_drawdown](api/quantdf/monthly_drawdown) — 计算月频收益序列对应的回撤表
- [weekly_drawdown](api/quantdf/weekly_drawdown) — 计算周频收益序列对应的回撤表
- [perf_eval_report](api/quantdf/perf_eval_report) — 生成绩效评估 HTML 报告——综合调用多种 QuantExpr 指标
- [perf_eval_summarize](api/quantdf/perf_eval_summarize) — 汇总一个或多个组合收益序列的绩效指标
- [monthly_yearly](api/quantdf/monthly_yearly) — 生成月度/年度收益透视表
- [monthly_yearly_active](api/quantdf/monthly_yearly_active) — 生成月度/年度超额收益透视表
- [optimize](api/quantdf/optimize) — 按日期逐期运行组合优化器——会调用 QuantExpr.optimize
- [to_layout](api/quantdf/to_layout) — 将结果 dataframe 转换为指定布局格式
- [to_terminal](api/quantdf/to_terminal) — 将结果 dataframe 渲染为适合终端阅读的字符串
