---
type: atom
id: api/quantexpr
summary: 'QuantExpr: Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。
  (40 个方法)'
status: active
version: 1
tags: ["api-doc", "quantexpr", "class-overview"]
intensity: 7
maturity: draft
imports:
  required: []
  recommended: []
  related: []
---
    # QuantExpr

    ## 概述

    Quant Expression — 对单个收益率序列或 alpha 预测值进行量化操作。所有方法作用于一个 expression 对象。

    ## 方法列表

    - [nav](api/quantexpr/nav) — 从收益率序列计算累计净值序列
- [total_return](api/quantexpr/total_return) — 从收益率序列计算区间总收益率
- [annualized_return](api/quantexpr/annualized_return) — 从收益率序列计算年化收益率
- [annualized_volatility](api/quantexpr/annualized_volatility) — 从收益率序列计算年化波动率
- [daily_win_ratio](api/quantexpr/daily_win_ratio) — 计算日频胜率
- [active_return](api/quantexpr/active_return) — 给定收益率相对于基准收益率的超额收益率
- [annualized_active_return](api/quantexpr/annualized_active_return) — 计算相对基准的年化超额收益率
- [total_active_return](api/quantexpr/total_active_return) — 计算相对基准的区间总超额收益率
- [drawdown](api/quantexpr/drawdown) — 从收益率序列计算回撤序列
- [max_drawdown](api/quantexpr/max_drawdown) — 计算最大回撤
- [max_underwater](api/quantexpr/max_underwater) — 计算最长连续水下期数
- [underwater](api/quantexpr/underwater) — 从收益率序列计算连续水下天数序列
- [sharpe](api/quantexpr/sharpe) — 从收益率序列计算年化 Sharpe 比率
- [sortino](api/quantexpr/sortino) — 从收益率序列计算年化 Sortino 比率
- [rolling_sharpe](api/quantexpr/rolling_sharpe) — 计算固定窗口滚动 Sharpe 比率
- [return_to_drawdown](api/quantexpr/return_to_drawdown) — 计算年化收益与绝对最大回撤之比
- [day_cumrtn_corr](api/quantexpr/day_cumrtn_corr) — 计算日序号与累计净值之间的相关系数——衡量净值增长稳定性
- [ols](api/quantexpr/ols) — 做 OLS 回归
- [ols_residuals](api/quantexpr/ols_residuals) — 做 OLS 回归取残差
- [ridge](api/quantexpr/ridge) — 做 ridge 回归
- [lasso](api/quantexpr/lasso) — 做 lasso 回归
- [zscore](api/quantexpr/zscore) — 求 z-score 标准化
- [standardize](api/quantexpr/standardize) — 标准化
- [normalization](api/quantexpr/normalization) — 做归一化
- [winsorize](api/quantexpr/winsorize) — 做 winsorization 缩尾处理
- [sigmoid](api/quantexpr/sigmoid) — 求 sigmoid 变换
- [demean](api/quantexpr/demean) — 求去均值
- [demedian](api/quantexpr/demedian) — 求去中位数
- [neutralize](api/quantexpr/neutralize) — 做中性化处理
- [optimize](api/quantexpr/optimize) — 通过优化器将 alpha 预测值变换为仓位权重
- [clean](api/quantexpr/clean) — 清洗脏数据（去除 NaN/Inf 等）
- [average_turnover](api/quantexpr/average_turnover) — 计算平均日换手
- [weekly_average_turnover](api/quantexpr/weekly_average_turnover) — 计算每周汇总换手后的平均值
- [average_turnover_by_calendar_day](api/quantexpr/average_turnover_by_calendar_day) — 计算按自然日摊薄后的平均换手
- [turnover_efficiency](api/quantexpr/turnover_efficiency) — 计算换手效率指标
- [profit_per_turnover](api/quantexpr/profit_per_turnover) — 计算单位总换手对应的总收益
- [monthly_max_drawdown](api/quantexpr/monthly_max_drawdown) — 计算月频收益序列的最大回撤
- [monthly_win_ratio](api/quantexpr/monthly_win_ratio) — 按月聚合后计算月胜率
- [weekly_max_drawdown](api/quantexpr/weekly_max_drawdown) — 计算周频收益序列的最大回撤
- [weekly_win_ratio](api/quantexpr/weekly_win_ratio) — 按周聚合后计算周胜率
