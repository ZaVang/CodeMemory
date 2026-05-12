# Git Hooks for CodeMemory

## Install

```bash
git config core.hooksPath .githooks
```

## Uninstall

```bash
git config --unset core.hooksPath
```

## Hooks

| Hook | Description |
|------|-------------|
| `post-commit` | Runs `bin/codememory-hook` — skeletonizes changed `.md`/`.py`/`.js`/`.ts`/`.go`/`.rs`/`.java` files after each commit |
