import json
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient

from llama_inference import LlamaInference
from t5_inference import T5Inference

load_dotenv()

app = FastAPI()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
collection = db[os.getenv("MONGO_COLLECTION_NAME")]

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

MODEL_INFERENCES = {
    'llama': LlamaInference(),
    't5': T5Inference()
}


@app.post(
    "/transform-sentence-to-imr",
    response_model=Response,
    status_code=status.HTTP_200_OK,
)
def transform_sentence_to_imr(body: RequestBody):
    sentence = body.sentence.lower()
    model = body.model

    response = MODEL_INFERENCES[model].generate(sentence)


    if response.status_code == status.HTTP_200_OK:
        raw_output = MODEL_INFERENCES[model].get_raw_output(response)
        adopted_result = MODEL_INFERENCES[model].adopt(raw_output)

        print("==adopted result==")
        print(adopted_result)

        model_result = {
            'inputSentence': sentence,
            'imr': adopted_result,
            'rawOutput': raw_output,
            'modelVersion': model,
            'status': 'success'
        }

        collection.insert_one(model_result)

    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        error_response = response.json()
        error_message = error_response.get('message', '')
        
        cleaned_message = error_message.replace('\'', '\"').replace('None', 'null')
        cleaned_message = cleaned_message.replace('\\n', '\\\\n')
        
        error_details = json.loads(cleaned_message)
        collection.insert_one({
            "timestamp": error_details.get('timestamp'),
            "inputSentence": error_details.get('inputSentence'),
            "imr": error_details.get('imr'),
            "rawOutput": error_details.get('rawOutput'),
            "status": "error",
            "error": error_details.get('error'),
            "modelVersion": error_details.get('modelVersion'),
            "prompt": error_details.get('prompt'),
        })
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_response
        )
    else:
        raise HTTPException(
            status_code=response.status_code, detail="An unexpected error occurred."
        )

    return model_result
