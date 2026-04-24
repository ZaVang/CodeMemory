---
type: schema
id: schemas/decision
summary: "决策类记忆的结构模板，包含 what/why/when/confidence/outcome"
status: active
created: 2026-04-24
updated: 2026-04-24
version: 1
tags: [meta, template]
fields:
  - name: what
    type: string
    required: true
  - name: why
    type: string
    required: true
  - name: when
    type: date
    required: true
  - name: confidence
    type: float
    required: true
  - name: outcome
    type: string
    required: false
---

# Decision Schema

所有"决策类"记忆应遵循此结构。适用于投资决策、项目决策、技术选型等场景。

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| what | string | ✅ | 做了什么决定 |
| why | string | ✅ | 决策理由 |
| when | date | ✅ | 决策时间 |
| confidence | float | ✅ | 决策时的确信度 (0-1) |
| outcome | string | ❌ | 后续结果（可后补） |
