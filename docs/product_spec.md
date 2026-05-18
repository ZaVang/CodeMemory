# CodeMemory Product Spec

> **Historical document**  
> 这是早期 Phase 1 实现说明，保留用于追溯原型阶段决策。  
> 自 2026-05-18 起，产品定义以 `docs/prd.md` 为准，架构定义以 `docs/architecture.md` 为准。

## Goal
Implement Phase 1 of the Memory Atomization Protocol — a dependency-aware memory system for AI agents.

## Core Deliverables

### 1. Memory File Format (Layer 1)
- Markdown + YAML frontmatter files with base fields (type, id, summary, status, created, updated, version, tags, source, summary_hash)
- Four primitives: Atom, Schema, Instance, Composite
- Three-tier imports: required / recommended / related

### 2. CLI Tool (Layer 2)
Single-file Python CLI (`bin/codememory.py`) with:
- `create`: Generate template memory files + auto-update index.json
- `resolve`: Build dependency DAG → topological sort → token budget pruning → output merged context
- `reindex`: Scan all .md files, rebuild index.json
- `validate`: Cycle detection + broken link check + schema compliance

### 3. Sample Data
8 memory files covering investment decision scenario:
- 4 atoms (semiconductor-thesis, risk-tolerance, position-semiconductor, position-cash)
- 1 schema (decision)
- 1 instance (february-buy → decision schema)
- 2 composites (current-holdings, context)

## Architecture
```
codememory.py (single file, ~400 lines)
├── parse_frontmatter()     # YAML extraction + body separation
├── compute_body_hash()     # sha256(body)[:7]
├── estimate_tokens()       # len(text) as proxy
├── load_index/save_index() # .codememory/index.json CRUD
├── cmd_create()            # template generation + index update
├── cmd_reindex()           # full scan rebuild
├── cmd_resolve()           # DAG → topo sort → budget trim
│   ├── build_dag()
│   ├── detect_cycle()
│   └── topological_sort()
├── cmd_validate()          # cycle + broken links + schema
└── main()                  # argparse CLI entry
```

## Dependencies
- Python 3.13 (available)
- pyyaml 6.0.3 (available)
- No other external dependencies

## Success Criteria
1. `reindex` produces index.json with 8 entries
2. `validate` returns 0 errors on sample data
3. `resolve user/investment/context --depth required` outputs 6 memories in topological order
4. `resolve` with tight budget degrades required memories to summary-only
5. `create` generates valid template + updates index
6. Cycle detection: validate warns, resolve skips + continues
