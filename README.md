# Restaurant recommendation service

AI-powered restaurant recommendations using the Hugging Face Zomato dataset and Groq.
Structured filters run first; the model only ranks a shortlist. If the model fails,
you still get catalog-backed cards (`source: fallback`).

See `DOC/Problemstatement.md`, `DOC/Architecture.md`, and `DOC/Implementation-plan.md`.

## Requirements

- Python 3.11 or newer

## Setup

From this directory (`M1-9`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

Copy environment defaults (no secrets):

```powershell
copy .env.example .env
```

Put API keys only in `.env`. That file is gitignored.

```powershell
python -c "import app"
pytest
```

## Ingest

Download the Hugging Face dataset once, normalize it, and write a local Parquet catalog.
Do **not** run ingest on every request.

```powershell
python -m app.data.ingest
```

Writes:

- `data/catalog.parquet` (override with `CATALOG_PATH`)
- `data/INGEST.md` — row count, budget tertile cutoffs, top cities / locations / cuisines

The published dataset is mostly Bangalore neighborhood listings. After ingest, use
locations and cuisines from `data/INGEST.md` or `GET /meta` (for example Banashankari
and Italian).

Reload without Hugging Face:

```powershell
python -c "from app.data.catalog import load_catalog; print(len(load_catalog()))"
```

## Configure Groq

Set a key from [console.groq.com](https://console.groq.com/) in `.env`:

```env
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
LLM_TEMPERATURE=0.3
LLM_MAX_COMPLETION_TOKENS=350
LLM_REASONING_EFFORT=low
LLM_API_KEY=gsk_...
SHORTLIST_SIZE=10
DEFAULT_TOP_K=3
CACHE_TTL_SECONDS=300
```

`GROQ_API_KEY` is accepted as an alias for `LLM_API_KEY`. Never commit `.env`.
Change `LLM_MODEL` if your Groq account lists a different chat model.
On free-tier budgets (~8K TPM / 200K TPD), keep `LLM_REASONING_EFFORT=low`,
`LLM_MAX_COMPLETION_TOKENS` small, and `SHORTLIST_SIZE` ≤ 10 so each call stays lean.
Set `CACHE_TTL_SECONDS=0` to disable the preference cache.

## Run API

Requires a local catalog (`python -m app.data.ingest` first). A Groq key is optional:
without a working model, `/recommend` still returns ranked catalog cards via fallback.

```powershell
uvicorn app.main:app --reload
```

- `GET /health` — process up and catalog loaded (503 if catalog missing)
- `GET /meta` — cities, sample locations/cuisines, budget cutoffs
- `POST /recommend` — filter shortlist, then Groq rank/explain (`source: llm`);
  empty shortlist → `no_matches`; LLM failure / bad JSON / all-invalid IDs →
  `source: fallback` (still HTTP 200)

Example:

```powershell
curl -X POST http://127.0.0.1:8000/recommend -H "Content-Type: application/json" -d "{\"location\":\"Banashankari\",\"budget\":\"medium\",\"cuisine\":\"Italian\",\"min_rating\":4.0,\"notes\":\"family-friendly\",\"top_k\":5}"
```

## Run UI

Primary UI is **PlateMatch** (light editorial design from `stitch/`), served by the API:

```powershell
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Dropdowns come from `GET /meta`;
submits call `POST /recommend`. Design tokens live in `stitch/DESIGN.md`.

For **Vercel (frontend) + Render (backend)** deploy steps, see `DOC/deployment-plan.md`.
Set `CORS_ORIGINS` on the API and `API_BASE` on Vercel (`scripts/write-api-config.js`).

Optional Streamlit UI (same recommend service):

```powershell
streamlit run app/ui/streamlit_app.py
```

## Demo script

1. Run ingest; confirm catalog path and budget cutoffs in `data/INGEST.md`.
2. `GET /health` → catalog loaded.
3. UI or API: Banashankari (or Bangalore), medium, Italian, min rating 4.0, notes
   “family-friendly”.
4. Confirm cards: name, cuisine, rating, cost, explanation; IDs exist in the catalog.
5. Tighten filters (e.g. min rating 4.9 in a sparse area) until `no_matches` and the hint appear.
6. Clear or break `LLM_API_KEY`; confirm cards still appear with `source: fallback`.
