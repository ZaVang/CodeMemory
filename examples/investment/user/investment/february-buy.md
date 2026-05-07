---
type: atom
schema: schemas/decision
id: user/investment/february-buy
summary: 2月重仓半导体ETF，基于AI存储爆发+国产替代判断，置信度0.8
status: active
created: 2026-02-15
updated: 2026-04-24
version: 2
tags:
- investment
- decision
source:
  platform: antigravity
  created_by: user
summary_hash: a22ae67
what: 重仓半导体ETF（512480），仓位从10%加到40%
why: AI存储爆发 + 国产替代加速，双核心驱动确定性高
when: 2026-02-15
confidence: 0.8
outcome: 截至4月涨15%，判断暂时正确
imports:
  required:
  - id: user/investment/semiconductor-thesis
  - id: user/investment/risk-tolerance
    pin: v1
    reason: 决策基于当时的激进风险偏好（v1），不是后来调整后的中高偏好
stability: 155.0
stability_source: manual
---




# 2月重仓半导体决策

基于半导体主线判断，结合当时的风险偏好，决定将仓位从 10% 大幅加到 40%。

## 决策过程

1. 春节期间复盘了整个 AI 产业链，确认存储和制造是最确定的两条线
2. 评估自身风险偏好（当时是激进型），认为 40% 仓位在可承受范围内
3. 选择 ETF 而非个股，降低个股风险

## 后续追踪

- 2026-03-01: 涨了 5%，信心增强
- 2026-03-15: 遇到回调 -8%，有些焦虑但没有减仓
- 2026-04-15: 涨了 15%，开始考虑是否止盈
- 2026-04-20: 维持持仓，主线逻辑未变