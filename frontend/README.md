# CodeMemory Operator UI

The frontend is a local React/Vite adapter over the FastAPI backend. It does not define canonical memory semantics; Build, search, review actions, golden questions, validation, and reindex delegate to Core-backed REST endpoints.

## Run locally

From the repository root, start both backend and frontend:

```powershell
python bin/codememory.py dev
```

Or run the frontend separately after the backend is listening on port 8000:

```powershell
Set-Location frontend
npm install
npm run dev
```

Default URLs:

- Operator UI: `http://127.0.0.1:5300`
- Backend API: `http://127.0.0.1:8000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

Vite proxies `/api` to the local backend. Data requests carry `X-Codememory-Dataset`; the backend accepts exact aliases from contained `examples/` discovery or the optional server-owned `CODEMEMORY_INSTANCE_REGISTRY`.

## Current views

- Graph: imports DAG and canonical Build state
- List: browse and filter memory inventory
- Dashboard: stats, validate, and reindex
- Review: proposed Atoms and modification patches with explicit merge/reject
- Personal (Personal datasets only): valid Capture feed, Topic/Claim provenance, explicit timeline, and one confirmed batch review
- Memory detail: metadata, rendered Build output, backlinks, and read-only golden questions

The UI does not run an LLM evaluator, expose arbitrary filesystem roots, edit Capture, run maintenance/Git delivery, or expose semantic vectors/private-local state.

External Personal roots are registered outside the repository:

```yaml
instances:
  mymemory: D:\work\MyMemory
```

Set `CODEMEMORY_INSTANCE_REGISTRY` to that absolute YAML path before starting the backend. Dataset responses contain only safe alias metadata; registry roots are not reindexed during server startup.

## Verification

```powershell
npm run build
npm run lint
npm run test:e2e:ci
```

Playwright uses `http://127.0.0.1:5300` and starts the configured backend/frontend web servers through `playwright.config.ts`.
