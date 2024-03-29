import json
import os
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient

load_dotenv()

app = FastAPI()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
collection = db[os.getenv("MONGO_COLLECTION_NAME")]

MODEL_ENDPOINTS = {
    "chatgpt": os.getenv("CHATGPT_ENDPOINT"),
    "t5": os.getenv("T5_ENDPOINT")
}

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Response(BaseModel):
    imr: Dict
    inputSentence: str
    status: str
    rawOutput: object
    status: str
    modelVersion: str
    error: Optional[str]
    prompt: Optional[str]

class HTTPErrorResponse(BaseModel):
    message: str
    status: str


class RequestBody(BaseModel):
    sentence: str
    model: str


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    response_model = HTTPErrorResponse(status="error", message=str(exc.detail))
    json_compatible_item_data = jsonable_encoder(response_model)
    return JSONResponse(
        status_code=400,
        content=json_compatible_item_data,
    )


def request_model(sentence, model):
    r = requests.post(f"{MODEL_ENDPOINTS[model]}/transform-sentence-to-imr",
                      headers={'accept': 'application/json', 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                      data=json.dumps({"sentence": sentence}))
    return r


@app.post(
    "/transform-sentence-to-imr",
    response_model=Response,
    status_code=status.HTTP_200_OK,
)
def transform_sentence_to_imr(body: RequestBody):
    sentence = body.sentence
    model = body.model
    response = request_model(sentence, model)

    if response.status_code == status.HTTP_200_OK:
        model_result = response.json()
        collection.insert_one(model_result)

    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        model_result = response.json()
        collection.insert_one(model_result)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=model_result
        )

    return model_result
