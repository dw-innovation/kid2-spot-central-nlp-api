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
from datetime import datetime
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
    """
    Response model returned by the `/transform-sentence-to-imr` endpoint.

    Attributes:
        timestamp (str): Time when the inference was made.
        imr (Dict): The final IMR (intermediate representation) result.
        inputSentence (str): The input sentence, lowercased.
        status (str): Status of the request (e.g., 'success', 'error').
        rawOutput (object): Raw model output before adaptation.
        modelVersion (str): Identifier for which model was used.
        error (Optional[str]): Optional error message (only present on error).
        prompt (Optional[str]): Optional prompt sent to the model.
    """
    timestamp: str
    imr: Dict
    inputSentence: str
    status: str
    rawOutput: object
    status: str
    modelVersion: str
    error: Optional[str] = None
    prompt: Optional[str] = None


class HTTPErrorResponse(BaseModel):
    """
    Response model returned in case of an HTTP error.

    Attributes:
        message (str): Description of the error.
        status (str): Error status indicator (e.g., 'error').
    """
    message: str
    status: str


class RequestBody(BaseModel):
    """
    Expected request body for the `/transform-sentence-to-imr` endpoint.

    Attributes:
        sentence (str): Sentence to be processed by the model.
        model (str): Model key to use (e.g., 'llama', 't5').
        username (str): Username of the requester.
        environment (str): Execution environment (e.g., dev, prod).
    """
    sentence: str
    model: str
    username: str
    environment: str


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom handler for HTTP exceptions.

    Args:
        request (Request): Incoming HTTP request (not used directly).
        exc (HTTPException): The raised HTTP exception.

    Returns:
        JSONResponse: A structured JSON error response with status 400.
    """
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
    """
    Transforms an input sentence into an intermediate representation (IMR)
    using the specified model ('llama' or 't5').

    Stores results or errors in the database for traceability.

    Args:
        body (RequestBody): Request payload containing input sentence,
            model name, username, and environment.

    Returns:
        dict: A dictionary with the inference result and metadata.

    Raises:
        HTTPException: If the model returns an error or an unknown status.
    """
    sentence = body.sentence.lower()
    environment = body.environment
    model = body.model
    username = body.username

    response = MODEL_INFERENCES[model].generate(sentence, environment)
    if response.status_code == status.HTTP_200_OK:
        raw_output = MODEL_INFERENCES[model].get_raw_output(response)
        adopted_result = MODEL_INFERENCES[model].adopt(raw_output)

        model_result = {
        'timestamp': f'{datetime.now():%Y-%m-%d %H:%M:%S%z}',
        'inputSentence': sentence,
        'imr': adopted_result,
        'rawOutput': raw_output,
        'modelVersion': model,
        'status': 'success',
        'username': username
        }

        collection.insert_one(model_result)

    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        error_response = response.json()
        error_message = error_response.get('message', '')

        cleaned_message = error_message.replace('\'', '\"').replace('None', 'null')
        cleaned_message = cleaned_message.replace('\\n', '\\\\n')

        error_details = json.loads(cleaned_message)
        collection.insert_one({
            'timestamp': error_details.get('timestamp'),
            'inputSentence': error_details.get('inputSentence'),
            'imr': error_details.get('imr'),
            'rawOutput': error_details.get('rawOutput'),
            'status': "error",
            'error': error_details.get('error'),
            'modelVersion': error_details.get('modelVersion'),
            'prompt': error_details.get('prompt'),
            'username': username
        })

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_response
        )
    else:
        raise HTTPException(
            status_code=response.status_code, detail="An unexpected error occurred."
        )

    return model_result
