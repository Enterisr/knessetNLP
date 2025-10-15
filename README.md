# Knesset NLP Platform

The Knesset NLP project ingests parliamentary protocols, enriches them with metadata, filters and embeds utterances, and finally exposes a semantic search API backed by a FAISS vector index. This repository contains the full ETL pipeline, a lightweight production runner for serving the vector database, and the client-facing FastAPI + React application.

## Pipeline Architecture

The orchestration entry point is [`pipeline.py`](pipeline.py). Running it with `--run-pipeline` executes the complete workflow:

```
┌───────────────────┐
│ Data Fetching     │  DataFetching/        • Downloads protocols & MK metadata from Knesset APIs
└────────┬──────────┘
         │
┌────────▼──────────┐
│ Photo Enrichment  │  DataFetching/photo_enricher.py • Adds portrait URLs and caches assets
└────────┬──────────┘
         │
┌────────▼──────────┐
│ Protocol Parsing  │  UtterancesExtraction/          • Transforms raw protocols into structured utterances
└────────┬──────────┘
         │
┌────────▼──────────┐
│ Sentiment Scoring │  sentiment/                     • Uses classla/xlm-r-parlasent over translated text when needed
└────────┬──────────┘
         │
┌────────▼──────────┐
│ Quality Filtering │  trash_utterances_detector/     • Logistic regression removes procedural "noise" utterances
└────────┬──────────┘
         │
┌────────▼──────────┐
│ Embedding & FAISS │  processing/embedder.py         • AlephBERT sentence embeddings + vector index build
└────────┬──────────┘
         │
┌────────▼──────────┐
│ Repo Bootstrap    │  processing/expose_repo.py      • Prepares ZeroMQ search server assets
└───────────────────┘
```

Key characteristics:

- **Hebrew-first embedding**: [`imvladikon/sentence-transformers-alephbert`](https://huggingface.co/imvladikon/sentence-transformers-alephbert) drives semantic similarity and dramatically improves topical relevance over multilingual baselines.
- **Noise reduction**: A logistic-regression classifier filters procedural utterances ("מי בעד?" etc.), achieving ~0.65 F1 with high recall so that meaningful speech is retained.
- **Sentiment analysis**: Parliamentary-tailored `classla/xlm-r-parlasent` tags utterances as positive/negative/neutral without requiring large-scale translation.
- **Scalable search**: The FAISS index contains ~1M utterances (~5 GB in float32) and powers MK-level analytics and semantic retrieval for the client app.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for `clientApp` development)
- `faiss-cpu` Python package (installed via `requirements.txt`)
- CUDA-capable GPU recommended for faster embedding (CPU works but is significantly slower)

Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install client dependencies if you plan to work on the React app:

```bash
cd clientApp/reactApp
npm install
```

### Expected directories & artifacts

Running `python -m pipeline --run-pipeline` will populate the repository with all derived artifacts. After the first successful
execution you should see the following outputs on disk (paths relative to the repo root):

- `committee_data/` – main pipeline output (utterances, metadata, FAISS build artifacts)
- `committie_index/` – persisted FAISS index (`*.faiss`) consumed by the search service
- `trash_utterances_detector/` – trained classifier artifacts (`classifier.pkl`, `embeddings.npy`, …)
- `filtered_utterances_data.pkl` – cached pandas DataFrame used by `prod_runner.py`

The pipeline also mirrors the raw Knesset protocol JSONs under `utterances/part_*/*.json`; if you already have historical dumps
they can be pre-seeded here to avoid downloading again. Optional caches (`utterance_embeddings.npy`, `utterances_data.pkl`,
`filtered_utterance_embeddings.npy`, `utter_ids.npy`) are respected when present and allow expensive recomputation steps to be
skipped on subsequent runs.

## Running the Data Pipeline

Execute the full ETL pipeline and bootstrap assets in one go:

```bash
python -m pipeline --run-pipeline
```

Useful flags:

- `--force-refresh` – ignore cached data and rebuild everything from scratch (slow but useful after schema changes)
- `--save-txt` – persist intermediate text files during processing

Running `python -m pipeline` without `--run-pipeline` only calls `processing.init_repo_server` and expects the embeddings/index artifacts to already exist.

Logs are written according to `utils/logger_config.py`; monitor them to track progress through each stage.

## Serving the FAISS Index in Production

[`prod_runner.py`](prod_runner.py) is the supported way to host the semantic search service. It loads the cached DataFrame and FAISS index from disk and exposes the ZeroMQ API used by the client application.

```bash
python -m prod_runner \
  --df-path path/to/filtered_utterances_data.pkl \
  --committee-index-path path/to/committie_index
```

The runner validates that both the `.pkl` DataFrame and FAISS index file exist before starting. The ZeroMQ server binds to `REPO_HOST`/`REPO_PORT` environment variables (default `0.0.0.0:5555`).

## Running the Client Application

The web client lives under [`clientApp/`](clientApp/) and consists of a FastAPI backend (`server.py`) and a React frontend (`reactApp/`).

1. Start the ZeroMQ search service (either via `prod_runner.py` or `python -m pipeline` once artifacts exist).
2. Launch the API server:
   ```bash
   cd clientApp
   python server.py
   ```
   Environment variables:
   - `ZMQ_SERVER` – address of the ZeroMQ service (defaults to `tcp://127.0.0.1:5555`)
   - `ZMQ_TIMEOUT` – request timeout in milliseconds (default `500000`)
   - `DEVELOPMENT` – set to `true` to serve React from the Vite dev server instead of static assets.
3. In a separate terminal (development mode only), run the React dev server:
   ```bash
   cd clientApp/reactApp
   npm run dev
   ```
   Build for production with `npm run build`; the FastAPI server automatically serves `reactApp/dist` when `DEVELOPMENT` is not `true`.

## Key Insights from `DEV_NOTES.md`

The development log captures the rationale behind many architectural decisions:

- **Translation choices**: Early experiments with `googletrans` were abandoned in favor of a self-hosted LibreTranslate instance to batch-translate efficiently when English resources are required. Ultimately, Hebrew-native models drastically reduced translation needs.
- **Embedding evolution**: Transitioned from generic multilingual SBERT models to the Hebrew-focused AlephBERT variant, which delivered markedly better semantic relevance and less "trash" retrieval.
- **Sentiment strategy**: Leveraged `classla/xlm-r-parlasent`, trained on parliamentary corpora, to obtain reliable sentiment labels without massive manual annotation.
- **Noise filtering**: Built a logistic-regression classifier (with rapidfuzz-assisted name normalization) to filter procedural utterances, calibrated for high recall (~0.94) so that critical statements are retained.
- **Scalability considerations**: Full corpus contains ~1 M utterances (~5 GB of embeddings); supports GPU acceleration (Colab/remote machines) and includes partitioned processing plus a `force_refresh` flag to control recomputation.
- **Clustering & analytics**: HDBSCAN/DBSCAN clustering is explored for MK subject profiling; results inform future visualization and scoring features.

Refer to [`DEV_NOTES.md`](DEV_NOTES.md) for the full chronological context and experimental details.

## Health Check

After boot, expect to see a log line similar to:

```
processing.expose_repo - INFO - Starting ZeroMQ server on tcp://0.0.0.0:5555
```

Use the FastAPI endpoint (`GET /api/query`) or the React UI to validate responses.
