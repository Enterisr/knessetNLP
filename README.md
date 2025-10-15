# Knesset NLP Platform

The Knesset NLP project ingests parliamentary protocols, enriches them with metadata, filters and embeds utterances, and finally exposes a semantic search API over a FAISS vector index. This repository contains the end-to-end pipeline as well as the ZeroMQ-based inference service consumed by the client application.

## Pipeline Architecture

The production pipeline is orchestrated from [`pipeline.py`](pipeline.py) and can be summarized as follows:

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
│ Quality Filtering │  trash_utterances_detector/     • Logistic regression removes procedural “noise” utterances
└────────┬──────────┘
         │
┌────────▼──────────┐
│ Embedding & FAISS │  processing/embedder.py         • SBERT (AlephBERT) embeddings + vector index build
└────────┬──────────┘
         │
┌────────▼──────────┐
│ Repo Service      │  processing/expose_repo.py      • ZeroMQ server answering semantic search queries
└───────────────────┘
```

Key characteristics:

- **Hebrew-first embedding**: We use [`imvladikon/sentence-transformers-alephbert`](https://huggingface.co/imvladikon/sentence-transformers-alephbert) for sentence embeddings, dramatically improving topical relevance over earlier multilingual models.
- **Noise reduction**: A logistic-regression classifier filters procedural utterances ("מי בעד?" etc.), achieving ~0.65 F1 with high recall so that meaningful speech is retained.
- **Sentiment analysis**: Parliamentary-tailored `classla/xlm-r-parlasent` tags utterances as positive/negative/neutral without requiring large-scale translation.
- **Scalable search**: The FAISS index contains ~1M utterances (~5 GB in float32) and powers MK-level analytics and semantic retrieval for the client app.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for `clientApp` development)
- Docker 24+ and Docker Compose (optional, for containerized deployment)
- CUDA-capable GPU recommended for faster embedding (CPU works but is significantly slower)

### Local configuration

Create the expected folders before running the pipeline:

- `utterances/part_*/*.json` – raw committee protocol dumps
- `committee_data/` – pipeline output (utterances, metadata, FAISS artifacts)
- `committie_index/` – persisted FAISS index for the repo service
- `trash_utterances_detector/` – trained classifier artifacts (`classifier.pkl`, `embeddings.npy`, …)

Optional cached artifacts (`utterance_embeddings.npy`, `utterances_data.pkl`, `filtered_utterance_embeddings.npy`, `utter_ids.npy`) can be placed in the corresponding folders to skip expensive recomputation.

## Running the Pipeline

The pipeline entry point accepts a few convenience flags:

```bash
python -m pipeline --run-pipeline [--force-refresh]
```

- `--run-pipeline` (or `--complete`): execute the full ETL flow shown above.
- `--force-refresh`: ignore cached data and rebuild everything from scratch (slow but useful after schema changes).

Running without `--run-pipeline` starts only the repository service bootstrapping (`processing.init_repo_server`) and assumes that required artifacts already exist.

Logs are written according to `utils/logger_config.py`; monitor them to track progress through each stage.

## Serving Semantic Search

You can either run the Python service directly or use Docker Compose.

### Docker Compose

```bash
docker compose up --build
```

Environment variables supported by the service:

| Variable        | Default   | Description                                                         |
| --------------- | --------- | ------------------------------------------------------------------- |
| `REPO_HOST`     | `0.0.0.0` | Interface the ZeroMQ REP socket binds to                            |
| `REPO_PORT`     | `5555`    | TCP port exposed by the service                                     |
| `FORCE_REFRESH` | `0`       | Set to `1` to rebuild embeddings & FAISS index inside the container |

Supply overrides via an `.env` file or `docker compose` command-line flags.

Once running, the service exposes `tcp://localhost:5555`. Example request:

```python
import json
import zmq

ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.connect("tcp://127.0.0.1:5555")
sock.send_string(json.dumps({"query": "חינוך חובה"}))
print(sock.recv_string())
```

### Manual Docker usage

```bash
docker build -t knesset-nlp-repo .
docker run --rm -p 5555:5555 \
  -e REPO_PORT=5555 -e REPO_HOST=0.0.0.0 -e FORCE_REFRESH=0 \
  -v ${PWD}/utterances:/app/utterances:ro \
  -v ${PWD}/committie_index:/app/committie_index \
  -v ${PWD}/logs:/app/logs \
  -v ${PWD}/trash_utterances_detector:/app/trash_utterances_detector:ro \
  knesset-nlp-repo
```

### Development tips

- **Trigger FAISS rebuild**: `python -m processing.expose_repo`
- **Open shell in container**: `docker compose exec repo-service bash`
- **Persisted volumes**: `committie_index/` and `logs/` are mounted so indexes and logs survive restarts.
- **Scaling**: Run multiple replicas behind a load balancer if needed; ensure each instance mounts the same index volume.

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

Use the Python snippet above or the client application to validate responses.
