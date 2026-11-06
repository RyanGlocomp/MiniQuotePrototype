# Mini Quote Builder

Learning build of the Option A Quotation & Pricing Builder: upload → extract → review →
approve → client-formatted Excel. Same shape as the full system, smaller scope.
The design doc (system design, data flow, use cases, milestones) is the source of truth.

## Rules that never bend
- Only stage c (structuring) calls a model. Pricing, Excel and the totals check are plain Python.
- Unknown values stay `null`, never 0. Pricing refuses to run while any are missing.
- No file is generated without an approval tied to the current `pricing_hash`.
- After LibreOffice recalc, the file's totals must equal the approved preview, to the sen.

## Layout
```
api/app/pricing.py    d  Decimal pricing, RM0.10 round-up, tax half-up, pricing_hash
api/app/populate.py   e  writes only mapped cells into the client template
api/app/recalc.py     f  soffice headless recalc + read-back check
api/app/registry.py      Client x Brand -> template + mapping
api/app/main.py          FastAPI: /health, /templates (job routes in M4)
templates/               registry.yaml, demo_client/{quote_template.xlsx, mapping.yaml}
samples/                 reviewed_demo.json with hand-checked expected totals
```

## Run the tests (CPU only; no Docker, GPU or Ollama needed)
```bash
cd api && uv sync && uv run pytest -q
```
Rebuild the demo template: `uv run --project api python templates/demo_client/make_template.py`

## Milestones
| # | Status | What |
|---|---|---|
| M0 | done, api running on 127.0.0.1:8107 | Compose skeleton, `/health`, Dockerfile |
| M1 | done, 18 tests passing | pricing → Excel → LibreOffice recalc → read-back |
| M2 | next | parsers: PDF, PNG, .xlsx |
| M3 | | LLM structuring: qwen3-vl:8b (OCR), qwen3.8:27b (text), already on the Spark |
| M4 | | job API, states, approval gate, SQLite audit |
| M5 | | Next.js page (Node 22 via nvm in ~) |
| M6 | | swap Ollama for vLLM via `.env` |

## Shared DGX Spark etiquette
Compose project `mqb-ryan`, host ports bound to 127.0.0.1 (8107 API, 3107 web), the
existing host Ollama is reused rather than started again, `mem_limit` on containers.
Starting containers, pulling models or running vLLM is done only after checking with
the other Spark users.
