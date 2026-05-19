# Frontend Audit Report — 2026-05-18

## Scope

Reviewed the React/Vite frontend after the Markdown Memory Compiler core/CLI work. The audit focused on whether the frontend blocks the current release, whether there is dead code that should be removed, and which follow-up refactors would make the UI architecture clearer.

## What was fixed in this pass

- Removed unused frontend imports and local variables that blocked TypeScript compilation.
- Fixed `UserSettings.theme` typing in the dark-mode keyboard shortcut so persisted settings keep the exact `light | dark | system` type.
- Added `access_count` to the search result API type because `SearchBar` already renders freshness metadata from that field.
- Tightened Cytoscape style callback typings and removed unsupported/unused graph style properties so the production build succeeds.

## Current verification status

| Check | Status | Notes |
|---|---|---|
| `npm run build` | Pass | TypeScript + Vite production build now completes. Vite still warns that the main chunk is larger than 500 kB. |
| `npm run lint` | Needs follow-up | The remaining failures are React Hooks / React Refresh architecture rules rather than TypeScript blockers. |

## Remaining frontend follow-up work

### 1. Split large stateful components

`App.tsx` and `GraphCanvas.tsx` are doing too much. This causes many hook dependency warnings and makes memoization fragile.

Recommended split:

- `App.tsx`: routing/view orchestration only.
- `useOperationErrors()`: toast queue + auto-dismiss timers.
- `useThemeSettings()`: theme persistence, system theme listener, keyboard toggle.
- `useDatasets()`: dataset loading/switching/reindex lifecycle.
- `GraphCanvas` sub-hooks: graph fetch, cytoscape setup, layout, interaction handlers, resolve highlighting.

### 2. Fix React Hooks lint debt

`npm run lint` still reports these categories:

- `react-hooks/set-state-in-effect`: state derivation inside effects should be moved into initial state, event handlers, or reducers where possible.
- `react-hooks/exhaustive-deps`: callbacks passed from parents should be stable, or effects should include dependencies and avoid stale closures.
- `react-hooks/preserve-manual-memoization`: some memoized callbacks depend on values that change too broadly.
- `react-refresh/only-export-components`: shared constants/functions should move out of component files.

### 3. Code-split the frontend bundle

The production build succeeds, but Vite reports the main JS chunk is above 500 kB. The likely split points are:

- Cytoscape graph view (`GraphCanvas`).
- Markdown rendering/detail panel (`MemoryDetail`).
- Settings/onboarding surfaces.

### 4. Consider a Web review surface later

The current Memory Compiler is intentionally Core/CLI-only. If the product needs a frontend review workflow later, add it as a separate feature over the review JSON contract instead of coupling it directly into the compiler package.

## Recommendation

No frontend change is required for the Core/CLI Markdown Compiler MVP beyond the TypeScript build fixes already made here. The next frontend sprint should focus on splitting `App.tsx` / `GraphCanvas.tsx` and retiring the React Hooks lint debt before adding a Memory Compiler review UI.
