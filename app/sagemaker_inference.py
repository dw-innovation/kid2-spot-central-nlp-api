import ast
import os
import boto3
from dotenv import load_dotenv
from loguru import logger
import json
from yaml_parser import validate_and_fix_yaml
from adopt_generation import adopt_generation
from fastapi.responses import JSONResponse

logger.add(f"{__name__}.log", rotation="500 MB")

load_dotenv()

class SageMakerInference:
    """
    Thin wrapper around a Hugging Face-hosted LLaMA text generation endpoint.

    Provides:
      - request construction and dispatch
      - extraction of raw generated text
      - adaptation/validation of the model output into a structured IMR
    """
    def __init__(self):
        session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
        print(os.getenv("AWS_REGION"))
        print(os.getenv("AWS_ENDPOINT_NAME"))
        print(os.getenv("AWS_PROFILE"))
        self.client = session.client(
            "sagemaker-runtime",
            region_name=os.getenv("AWS_REGION"),
        )
        self.endpoint_name = os.getenv("AWS_ENDPOINT_NAME")

    def generate(self, sentence, environment):
        """
        Generate text using the underlying LLaMA endpoint.

        Args:
            sentence (str): Input sentence to process. Will be lowercased before
                being sent.
            environment (str): Execution environment indicator (e.g., "dev", "prod").
                Passed through to maintain a consistent signature; currently unused.

        Returns:
            requests.Response: The HTTP response returned by the inference service.
        """


        content_type = 'application/json'
        payload = json.dumps({"inputs": sentence})

        _response = self.client.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType=content_type,
            Body=payload
        )

        body = json.loads(_response["Body"].read().decode())

        return JSONResponse(
            content=body,
            status_code=_response["ResponseMetadata"]["HTTPStatusCode"]
        )
        return response

    def get_raw_output(self, response):
        """
        Extract the generated text from the inference response.

        Args:
            response (requests.Response): Response object returned by `generate`
                or `query`. Expected JSON shape is a list whose first element
                contains the key 'generated_text'.

        Returns:
            str: The generated text string.

        Raises:
            KeyError/IndexError/ValueError: If the response JSON does not match
            the expected structure.
        """
        sentence = json.loads(json.loads(response.body.decode("utf-8"))[0])[0]["generated_text"]
        return sentence

    def adopt(self, raw_response):
        """
        Validate, fix, and adapt raw model output into the final IMR structure.

        Pipeline:
          1) `validate_and_fix_yaml` to ensure well-formed YAML/structure.
          2) `adopt_generation` to convert the validated data into the target IMR.

        Args:
            raw_response (str): Raw generated text to be parsed and adapted.

        Returns:
            dict: The adopted/normalized IMR object ready for persistence or return.

        Raises:
            Exception: If validation or adoption fails downstream.
        """
        result = validate_and_fix_yaml(raw_response)
        result = adopt_generation(result)
        return result

if __name__ == '__main__':
    model = SageMakerInference()
    result = model.generate('I look for restaurant in Koblenz', environment='development')
    print(result)