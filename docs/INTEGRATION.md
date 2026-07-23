# CodeMemory Integration Guide

This guide describes the current integration surface after Personal Memory Phase 2, Importer v2, MCP/Toolkit alignment, Operator UI alignment, and the allowlisted Personal owner workspace.

CodeMemory has one semantic core and several adapters:

```text
CLI / Python / MCP / Toolkit / REST / Operator UI
                         ↓
                 shared Core handlers
                         ↓
        Markdown atoms + imports DAG + index
```

Adapters translate arguments and results. Canonical build, search, proposal, validation, and source behavior belongs to `src/codememory/`.

---

## 1. Install and run the example root

From a clean checkout:

```powershell
pip install -e .

python -m codememory.cli --root examples/investment reindex
python -m codememory.cli --root examples/investment validate
python -m codememory.cli --root examples/investment search --query "semiconductor risk"
python -m codememory.cli --root examples/investment build user/investment/context --budget 2000
```

`build` is the primary assembly verb. It follows the explicit imports DAG, applies the requested dependency depth and budget, and renders a ContextPack. The older `resolve` and `context-pack` CLI/API names remain compatibility aliases over the same pipeline; new integrations should call `build`.

Every adapter binds a memory root. For trusted local CLI use, pass it explicitly:

```powershell
python -m codememory.cli --root D:\memory\work validate
```

The CLI also accepts `CODEMEMORY_ROOT` when `--root` is omitted. MCP has a stricter contract: the environment variable is mandatory for every server process.

---

## 2. Canonical read and write paths

### Discover, then build

Search finds candidate entry atoms. Build assembles canonical context only from explicit imports:

```powershell
python -m codememory.cli --root examples/investment search `
  --query "risk preference" `
  --tags investment

python -m codememory.cli --root examples/investment build `
  user/investment/context `
  --depth recommended `
  --budget 2000 `
  --format xml-markdown
```

Supported build formats are `xml-markdown`, `markdown`, `plain-markdown`, and `json`. A semantic-type `--focus` may keep matching nodes at full text while other included nodes degrade to summaries; it does not discover or add dependencies.

### Owner CLI writes

The CLI `create` command creates a new Atom or Schema skeleton. Use `update` to fill owner-authored content and imports:

```powershell
python -m codememory.cli --root D:\memory\work create `
  --id user/project/new-decision `
  --tags project,decision `
  --propose

python -m codememory.cli --root D:\memory\work update `
  user/project/new-decision `
  --change-note "Fill reviewed decision" `
  --summary "Choose the queue-backed worker design" `
  --body "# Decision`n`nUse the queue-backed worker design." `
  --import-required user/project/context
```

Proposal rules are explicit:

- `create --propose` creates a new `status: proposed` Atom. It is excluded from default search/build until owner merge.
- `propose <existing-id>` creates a modification patch without changing target bytes.
- `proposals` lists modification patches.
- `merge <memory-id-or-proposal-id>` accepts either proposal kind.
- `reject <memory-id-or-proposal-id>` archives a proposed Atom or discards a patch record.

```powershell
python -m codememory.cli --root D:\memory\work propose user/project/context `
  --reason "Clarify the current constraint" `
  --summary "Updated reviewed summary"

python -m codememory.cli --root D:\memory\work proposals
python -m codememory.cli --root D:\memory\work merge prop_01...
```

### Validation and golden questions

```powershell
python -m codememory.cli --root D:\memory\work reindex
python -m codememory.cli --root D:\memory\work validate
python -m codememory.cli --root D:\memory\work test user/project/context --budget 2000
```

`test` exports declared golden questions plus assembled context and remains provider-free. An external runner may record results with `test report`.

The explicit eval harness runs the same scored questions against three frozen conditions:

```powershell
python -m codememory.cli --root D:\memory\work eval user/project/context `
  --llm-config D:\config\llm_gateway.yaml `
  --answer-model smart `
  --judge-model smart `
  --budget 2000 `
  --output D:\reports\context-eval.json
```

- `context_pack` uses the canonical build output.
- `full_memory` uses every assemblable Atom/Schema summary and authored body in stable ID order.
- `no_memory` sends no memory context.

Only questions with a non-empty `expect` are scored. The answer model never receives `expect`; the blind judge receives only the question, expected points, and candidate answer. Calls use structured output, temperature 0, and no tools/Web.

This is an explicit provider path: the two memory arms send memory text to the configured provider, and `full_memory` may send the entire canonical library. Review provider privacy and cost before running it. The report stores answers/verdicts and safe usage/latency/hash metadata, but not prompts, memory contexts, config paths, credentials, raw responses, or thinking. Without `--output`, JSON is printed to stdout; an existing output file is rejected unless `--overwrite` is explicit.

Eval remains a trusted owner/CI CLI/Python handler. It is intentionally absent from MCP, Toolkit, REST, and the Operator UI.

---

## 3. Source Artifacts and explicit expansion

Long source material belongs in the Source Artifact registry. Atoms reference it through `source_refs`; build renders those references but never silently inlines the source body.

```powershell
python -m codememory.cli --root D:\memory\work source add docs\design.md `
  --id src/design `
  --kind markdown `
  --summary "Design source"

python -m codememory.cli --root D:\memory\work source check src/design
python -m codememory.cli --root D:\memory\work source expand src/design --max-chars 2000

python -m codememory.cli --root D:\memory\work update user/project/context `
  --change-note "Attach reviewed source" `
  --source-ref src/design `
  --source-ref-summary "Design source"
```

Expansion supports local Markdown, text, and code artifacts. Results include artifact ID, path/URI, registry/current hashes, freshness status, selected range, truncation, content, and a bounded message. Missing, stale, and unsupported sources are structured states.

---

## 4. Markdown importer review flow

The deterministic importer is the default and has no provider dependency:

```powershell
python -m codememory.cli --root D:\memory\work compile-md D:\corpus `
  --review-id corpus-v1 `
  --tags migration

python -m codememory.cli --root D:\memory\work materialize-review corpus-v1 --accept-all
python -m codememory.cli --root D:\memory\work validate
```

It registers each document as a stable Source Artifact, emits one anchor candidate per document and one derived candidate per non-empty paragraph, and preserves exact paragraph/line provenance. Materialized files are always `status: proposed`; owner merge is still required.

The optional semantic proposer is explicit opt-in:

```powershell
pip install -e ".[llm]"

python -m codememory.cli --root D:\memory\work compile-md D:\corpus `
  --review-id corpus-semantic-v1 `
  --proposer llm `
  --llm-config D:\config\llm_gateway.yaml `
  --llm-model smart
```

Only this path loads the gateway adapter or sends source text to the configured provider. The model can propose typed semantic drafts and bounded imports, but CodeMemory owns IDs, paths, provenance validation, cycle checks, and forced-proposed materialization. Reusing the same review ID with identical source/options is idempotent; changed inputs conflict before a model call or write.

---

## 5. Python Core API

Use the Python API for trusted in-process integrations:

```python
from pathlib import Path

from codememory import (
    build_context_pack,
    render_context_pack,
    reindex,
    search,
    validate,
)

root = Path("examples/investment")
reindex(root)

results = search(root, query="risk preference")
pack = build_context_pack(
    root,
    "user/investment/context",
    depth="recommended",
    budget=2000,
)
rendered = render_context_pack(pack, output_format="xml-markdown")
errors, warnings = validate(root)
```

For adapter code, prefer the functions in `codememory.handlers`; they preserve CLI/MCP/REST result contracts. Do not reimplement imports traversal, filtering, proposal state transitions, or source freshness in an adapter.

---

## 6. Root-bound Agent Toolkit

`CodememoryToolkit` exports the same provider-neutral catalog to Sandbox, OpenAI, Anthropic, and Gemini shapes:

```python
from codememory.integrations import CodememoryToolkit

toolkit = CodememoryToolkit(root="examples/investment")

openai_tools = toolkit.get_tools_for_openai()
anthropic_tools = toolkit.get_tools_for_anthropic()
gemini_tools = toolkit.get_tools_for_gemini()
```

A standard root exposes exactly five tools:

| Tool | Purpose | Read-only |
|---|---|---:|
| `build_memory` | Assemble canonical context through imports | yes |
| `search_memories` | Discover candidate Atoms lexically | yes |
| `expand_source` | Explicitly read a registered source | yes |
| `create_memory` | Create a complete new Atom in one Core write | no |
| `propose_memory` | Queue a modification patch against an existing Atom | no |

The toolkit binds one resolved root at construction. Exported schemas do not include `root`, and caller payloads cannot redirect reads or writes. `create_memory` requires complete `id`, `summary`, and `body` fields; it can include tags/import lists and `propose`. `propose_memory` never changes target bytes before owner merge.

Register the same surface with `harnesslib`:

```python
import asyncio

from codememory.integrations import CodememoryToolkit
from harnesslib.sandbox import Sandbox


async def main() -> None:
    sandbox = Sandbox()
    toolkit = CodememoryToolkit(root="examples/investment")
    await toolkit.register_to_sandbox(sandbox)
    print([tool.name for tool in sandbox.list_tools()])


asyncio.run(main())
```

`examples/example_agent.py` is a runnable no-provider demonstration. It copies the investment root to a temporary directory before invoking write tools, so the checked-in example remains unchanged.

---

## 7. MCP server

Each MCP process must bind one explicit instance:

```powershell
$env:CODEMEMORY_ROOT = "D:\memory\work"
codememory-mcp
```

Startup fails if `CODEMEMORY_ROOT` is missing, absent, or not a directory. `tools/list` selects the same profile-specific catalog as Toolkit, and `tools/call` uses the same dispatcher. Standard tool schemas never expose a root argument.

A valid JSON-RPC call uses only tool inputs:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "build_memory",
    "arguments": {
      "id": "user/investment/context",
      "budget": 2000,
      "format": "json"
    }
  }
}
```

---

## 8. Personal Profile extension

Initialize Personal Profile roots explicitly. This does not run `git init` or create a remote:

```powershell
python -m codememory.cli init D:\memory\MyMemory --profile personal
python -m codememory.cli --root D:\memory\MyMemory capture "Remember this decision"
python -m codememory.cli --root D:\memory\MyMemory reindex
python -m codememory.cli --root D:\memory\MyMemory search --kind capture incubator_topic atom --query decision
python -m codememory.cli --root D:\memory\MyMemory read cap_01...
```

Personal roots expose the standard five Agent tools plus six extensions:

- `capture_memory`
- `read_memory`
- `maintenance_status`
- `maintain_memory`
- `resume_memory_maintenance`
- `review_personal_memory`

Agent-created canonical Atoms in Personal Profiles are always proposed. Capture and Incubator objects participate in typed discovery/read, but canonical build accepts only Atom entrypoints.

Daily maintenance is driven by the repository Personal Memory Skill:

```powershell
python -m codememory.cli --root D:\memory\MyMemory maintenance status
python -m codememory.cli --root D:\memory\MyMemory maintenance run --changeset changeset.json
python -m codememory.cli --root D:\memory\MyMemory maintenance resume
python -m codememory.cli --root D:\memory\MyMemory review-batch --file decisions.json
```

Maintenance consumes every valid unconsumed Capture exactly once, catches up missed runs, and resumes the same pending run after interruption. Git commit/push is disabled by default and enabled only in the Profile. A sensitive-scan block still allows Capture append but blocks new maintenance and delivery until the owner repairs and resumes the same run.

Optional local semantic discovery is a separate, derived read path. Install its optional dependency, configure an existing model directory under the Profile's ignored `private_local`, then build explicitly:

```powershell
pip install -e ".[semantic]"
python -m codememory.cli --root D:\memory\MyMemory semantic status
python -m codememory.cli --root D:\memory\MyMemory semantic index
python -m codememory.cli --root D:\memory\MyMemory search `
  --query "career direction" `
  --semantic `
  --kind capture incubator_topic incubator_claim atom
```

The adapter loads the model local-only and never downloads it. Identical builds are reused; content/model changes make the index stale until explicit rebuild. The index remains under ignored private-local state, and results are candidate IDs only: callers still use `read_memory` for Capture/Topic/Claim and `build_memory` for canonical Atoms. No REST endpoint exposes this operation, and semantic neighbors never alter imports or ContextPack assembly.

See `docs/personal-memory-profile.md` for the complete file, provenance, Claim, maintenance, and Git safety contracts.

---

## 9. REST and Operator UI

Run the local application:

```powershell
python bin/codememory.py dev
```

The REST adapter scopes data requests with `X-Codememory-Dataset`. The value must exactly match a dataset alias returned by `GET /api/datasets`; absolute paths, traversal syntax, separators, surrounding whitespace, and unknown aliases are rejected.

External Personal instances are configured by the server operator, never by a request:

```yaml
# D:\config\codememory-instances.yaml
instances:
  mymemory: D:\work\MyMemory
```

```powershell
$env:CODEMEMORY_INSTANCE_REGISTRY = "D:\config\codememory-instances.yaml"
python bin/codememory.py dev
```

The registry path must be absolute. Every root must exist and pass Personal Profile validation; aliases must be safe exact identifiers and cannot collide with demo aliases. `GET /api/datasets` returns only `name`, `memory_count`, `profile`, and `source`. Server startup reindexes contained demo datasets only, never registry instances.

Primary endpoints:

| Endpoint | Contract |
|---|---|
| `POST /api/build` | Structured ContextPack plus rendered output from one Core build |
| `POST /api/search` | Core lexical discovery with REST field mapping |
| `GET /api/reviews` | Separate proposed-Atom and modification-patch queues |
| `POST /api/reviews/atoms/merge` | Activate a proposed Atom |
| `POST /api/reviews/atoms/reject` | Archive a proposed Atom |
| `POST /api/reviews/patches/merge` | Apply a patch through canonical update/version/log semantics |
| `POST /api/reviews/patches/reject` | Remove only the patch record |
| `GET /api/tests/{memory_id}` | Read-only golden-question TestBundle |
| `GET /api/sources/expand` | Explicit source expansion through Core |
| `POST /api/validate` | Core validation diagnostics |
| `POST /api/reindex` | Rebuild the selected dataset index |
| `GET /api/personal/overview` | Valid Personal object counts and bounded diagnostic count |
| `GET /api/personal/captures` | Paginated complete/hash-valid Capture records |
| `GET /api/personal/topics` | Topic revisions with inline Claims and explicit provenance |
| `GET /api/personal/timeline` | Authored events and explicit provenance/relations only |
| `POST /api/personal/review-batch` | One owner-confirmed promote/merge/delete batch through the shared handler |

The Operator UI consumes these endpoints for Graph, List, Dashboard, Review, Build, golden-question, and Personal views. Personal navigation appears only when the selected dataset metadata says `profile: personal`. It does not define canonical memory semantics, execute an LLM evaluator, edit Capture, run maintenance/Git delivery, or expose semantic vectors/private-local state.

---

## 10. Security and boundary checklist

- Bind every Toolkit/MCP/REST request to a known root or dataset alias.
- Never put a filesystem root in an Agent tool payload.
- Treat caller-controlled memory IDs as IDs, not paths; Core rejects absolute paths, drive prefixes, backslashes, dot segments, and empty segments, then verifies resolved containment.
- Keep source expansion explicit; build carries references rather than silently inlining source bodies.
- Keep semantic importer mode opt-in and review-gated.
- Do not treat a private Git remote as encrypted storage. Content committed once may remain in Git history after working-tree deletion.
- Keep `private-local/` or the configured Personal private path ignored and untracked.

---

## 11. Related documents

- [Product definition](prd.md)
- [Architecture contract](architecture.md)
- [User guide](USER_GUIDE.md)
- [Personal Profile contract](personal-memory-profile.md)
- [Agent contribution guide](agent-memory-guide.md)
- [Repository structure](project_structure.md)
