# SPOT Central NLP API
This API can request multiple machine learning models for transforming sentences into imr format.


You need to set the following parameters in `.env`:

```text
T5_ENDPOINT=...
CHATGPT_ENDPOINT=...
MONGO_URI=...
MONGO_DB_NAME=...
MONGO_COLLECTION_NAME=...
```

You can refer to the following repositories for setting up model endpoints:
- [ChatGPT](https://github.com/dw-innovation/kid2-spot-chatgpt-api) 
- [T5 Models](https://github.com/dw-innovation/kid2-spot-nlp-api) 


## Installation
docker build -t spot_central_api:latest .
docker run -p 80:8080 --env-file .env spot_central_api:latest