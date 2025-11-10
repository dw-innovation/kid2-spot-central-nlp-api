<img width="1280" height="200" alt="Github-Banner_spot" src="https://github.com/user-attachments/assets/bec5a984-2f1f-44e7-b50d-cc6354d823cd" />

# 🧠 SPOT Central NLP API

This repository contains the **central orchestration layer** of the SPOT system.  
It transforms user queries from natural language into structured **SPOT YAML**, enriches them with **OSM tag bundles**, and routes requests through the appropriate AI models and APIs.

This service is the core of the SPOT pipeline, managing LLM inference, tag search, and query execution.

---

## 🚀 Quickstart

Build the docker container:

```bash
docker build -t spot_central_api:latest . 
```

Then run it:

```bash
docker run -p 80:8080 --env-file .env spot_central_api:latest
```

---

## ⚙️ Environment Variables

Below are the most relevant environment variables used in this module. For full configuration, see `.env.example`.

### 🔄 Runtime / OSM Database

| Variable | Description |
|----------|-------------|
| `DATABASE_NAME` | Name of the OSM database (used by downstream query engine). |
| `TABLE_VIEW` | Target table/view within the OSM DB. |
| `DATABASE_USER` | Username for the OSM DB. |
| `DATABASE_PASSWORD` | **Secret**: Password for OSM DB. |
| `DATABASE_HOST` | Hostname of the OSM DB server. |
| `DATABASE_PORT` | Port for the DB connection. |
| `MAX_AREA` | Max allowed search area. |
| `TIMEOUT` | Max response time for downstream query. |
| `JWT_SECRET` | **Secret**: Used for authentication. |

### 🔍 OSM Tag Search (Elasticsearch)

| Variable | Description |
|----------|-------------|
| `OSM_KG` | Path or endpoint for the OSM knowledge graph. |
| `SEARCH_ENGINE_HOST` | Host URL of the Elasticsearch instance. |
| `SEARCH_ENGINE_INDEX` | Index name used for tag bundle search. |
| `SENT_TRANSFORMER` | Sentence transformer model used for semantic search. |
| `MANUAL_MAPPING` | Path to static mapping file for OSM bundles. |
| `SEARCH_CONFIDENCE` | Threshold for semantic search match. |
| `COLOR_MAPPING` | Path to color bundle mapping definitions. |

### 🤖 LLM & Orchestration

| Variable | Description |
|----------|-------------|
| `T5_ENDPOINT` | Endpoint for T5-based parser (legacy). |
| `CHATGPT_ENDPOINT` | Endpoint for GPT model (optional fallback). |
| `HF_LLAMA_ENDPOINT_PROD` | HuggingFace endpoint for production inference. |
| `HF_LLAMA_ENDPOINT_DEV` | HuggingFace endpoint for development inference. |
| `HF_ACCESS_TOKEN` | **Secret**: Token for HuggingFace API access. |
| `PROMPT_FILE` | Path to prompt template file. |
| `PROMPT_FILE_DEV` | Development version of prompt template. |
| `SEARCH_ENDPOINT` | URL for semantic search API. |
| `COLOR_BUNDLE_SEARCH` | API endpoint for color-matching queries. |

### 🗂️ Persistence (MongoDB)

| Variable | Description |
|----------|-------------|
| `MONGO_URI` | **Secret**: MongoDB connection URI. |
| `MONGO_DB_NAME` | Name of the MongoDB database. |
| `MONGO_COLLECTION_NAME` | Name of the collection for saving sessions/results. |

> **🔒 Security Note:** Never commit real secrets. Always use `.env.example` and avoid pushing sensitive values to version control.

---

## 🔑 Features

- Converts unstructured text into structured YAML-based SPOT queries
- Orchestrates inference using a given LLM endpoint (e.g. Huggingface)
- Enriches YAML with semantic OSM tag bundles via Elasticsearch
- Stores and retrieves sessions from MongoDB
- Validates, filters, and forwards queries to downstream APIs

---

## 🧩 Part of the SPOT System

This module communicates with:
- [`osm-tag-search-api`](https://github.com/dw-innovation/kid2-spot-osm-tag-search-api) — for finding matching OSM tags
- [`osm-query-api`](https://github.com/dw-innovation/kid2-spot-osm-query-api) — to execute geospatial database queries
- [`frontend`](https://github.com/dw-innovation/kid2-spot-frontend) — the user-facing UI

---

## 🔗 Related Docs

- [Main SPOT Repo](https://github.com/dw-innovation/kid2-spot)
- [Frontend UI](https://github.com/dw-innovation/kid2-spot-frontend)
- [OSM Tag Search API](https://github.com/dw-innovation/kid2-spot-osm-tag-search-api)
- [OSM Query API](https://github.com/dw-innovation/kid2-spot-osm-query-api)

---

## 🙌 Contributing

We welcome contributions of all kinds — from developers, journalists, mappers, and more!  
See [CONTRIBUTING.md](https://github.com/dw-innovation/kid2-spot/blob/main/CONTRIBUTING.md) for how to get started.
Also see our [Code of Conduct](https://github.com/dw-innovation/kid2-spot/blob/main/CODE_OF_CONDUCT.md).

---

## 📜 License

Licensed under [AGPLv3](../LICENSE).
