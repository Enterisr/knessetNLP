# Knesset NLP Repository Service

This project exposes the Knesset utterance similarity search as a ZeroMQ service.  
The container builds the FAISS index (when missing) and serves search requests through `processing.expose_repo`.

## Prerequisites

- Docker 24+ and Docker Compose plugin
- Local data folders:
  - `utterances/part_*/*.json` – raw utterance exports used to rebuild embeddings
  - `committie_index/` – holds the persisted protocols (created on first run)
  - `trash_utterances_detector/` – contains the trained classifier artifacts (`classifier.pkl`, `embeddings.npy`, …)
- Optional cached artifacts (mounted if you already have them):
  - `utterance_embeddings.npy`, `utterances_data.pkl`, `filtered_utterance_embeddings.npy`, `utter_ids.npy` (a map between embedding id and pkl ids)
  - pkl is the db for now, might change to relational db later

> 💡 The first run with `FORCE_REFRESH=1` can take a long time because embeddings are recomputed. Subsequent runs reuse the cached files.
> You should proabably run it with a CUDA enabled machine

## Quick start

```powershell
# Build the image and start the service
docker compose up --build
```

The service listens on `tcp://localhost:5555`. You can connect with any ZeroMQ REQ client and send JSON payloads such as:

```json
{ "query": "חינוך חובה" }
```

## Environment variables

| Variable        | Default   | Description                                                         |
| --------------- | --------- | ------------------------------------------------------------------- |
| `REPO_HOST`     | `0.0.0.0` | Interface the ZeroMQ REP socket binds to                            |
| `REPO_PORT`     | `5555`    | TCP port exposed by the service                                     |
| `FORCE_REFRESH` | `0`       | Set to `1` to rebuild embeddings & FAISS index inside the container |

Set variables with `docker compose`:

```powershell
docker compose up --build --force-recreate ^
  --env-file .env
```

(Or edit the `docker-compose.yml` values directly.)

## Lifecycle tips

- **Persisting results**: The compose file mounts `committie_index/` and `logs/` so the FAISS index and logs survive container restarts.
- **Cold start**: Mount precomputed `utterance_embeddings.npy` and `utterances_data.pkl` if available to skip re-embedding. Otherwise expect a long initialization on first boot.
- **Scaling**: Run multiple replicas behind a load balancer by overriding the `service` name and port mapping in compose or a Kubernetes deployment.

## Manual Docker usage

```powershell
# Build
docker build -t knesset-nlp-repo .

# Run (example with explicit volumes)
docker run --rm -p 5555:5555 `
  -e REPO_PORT=5555 -e REPO_HOST=0.0.0.0 -e FORCE_REFRESH=0 `
  -v ${PWD}/utterances:/app/utterances:ro `
  -v ${PWD}/committie_index:/app/committie_index `
  -v ${PWD}/logs:/app/logs `
  -v ${PWD}/trash_utterances_detector:/app/trash_utterances_detector:ro `
  knesset-nlp-repo
```

## Development inside the container

```powershell
# Open a shell in the running container
docker compose exec repo-service bash

# Trigger a FAISS rebuild
python -m processing.expose_repo
```

Logs are written to `/app/logs` (mounted to `./logs`).

## Health check

After the container finishes booting you should see a log line similar to:

```
processing.expose_repo - INFO - Starting ZeroMQ server on tcp://0.0.0.0:5555
```

To verify the endpoint manually:

```python
import zmq, json
ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.connect("tcp://127.0.0.1:5555")
sock.send_string(json.dumps({"query": "חינוך"}))
print(sock.recv_string())
```
