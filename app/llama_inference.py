import requests
import os
from dotenv import load_dotenv
from loguru import logger
from yaml_parser import validate_and_fix_yaml
from adopt_generation import adopt_generation

logger.add(f"{__name__}.log", rotation="500 MB")

load_dotenv()

HF_LLAMA_ENDPOINT = os.getenv("HF_LLAMA_ENDPOINT")

HF_ACCESS_TOKEN = os.getenv("HF_ACCESS_TOKEN")
HF_MAX_NEW_TOKEN = os.getenv("HF_MAX_NEW_TOKEN", 1048)
HF_TOP_P = os.getenv("HF_TOP_P", 0.1)
HF_TEMPERATURE = os.getenv("HF_TEMPERATURE", 0.001)

PROMPT_FILE = os.getenv("PROMPT_FILE")

with open(PROMPT_FILE, 'r') as file:
    PROMPT = file.read()

headers = {
    "Accept": "application/json",
    "Authorization": f'Bearer {HF_ACCESS_TOKEN}',
    "Content-Type": "application/json"
}


def query(payload, environment):
    """
    Send a POST request to the configured Hugging Face LLaMA inference endpoint.

    Args:
        payload (dict): JSON-serializable body for the inference request. Expected
            keys include:
              - "inputs" (str): The input text.
              - "prompt" (str): The system or few-shot prompt to prepend.
              - "max_new_tokens" (int/str): Max tokens to generate.
              - "top_p" (float/str): Nucleus sampling parameter.
              - "temperature" (float/str): Sampling temperature.
        environment (str): Execution environment indicator (e.g., "dev", "prod").
            Currently not used in this function, but accepted for interface parity
            and potential routing/telemetry.

    Returns:
        requests.Response: The raw HTTP response from the inference endpoint.
    """
    endpoint = HF_LLAMA_ENDPOINT
    response = requests.post(endpoint, headers=headers, json=payload)
    return response

class LlamaInference:
    """
    Thin wrapper around a Hugging Face-hosted LLaMA text generation endpoint.

    Provides:
      - request construction and dispatch
      - extraction of raw generated text
      - adaptation/validation of the model output into a structured IMR
    """
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
        output = query({
            "inputs": sentence.lower(),
            "prompt": PROMPT,
            "max_new_tokens": HF_MAX_NEW_TOKEN,
            "top_p": HF_TOP_P,
            "temperature": HF_TEMPERATURE
        }, environment)
        return output

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
        sentence = response.json()[0]['generated_text']
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
    """
    Manual test harness: performs a single query against the LLaMA endpoint
    and prints the raw `requests.Response`. Useful for connectivity checks.

    Notes:
        - Uses the globally loaded PROMPT and sampling parameters.
        - Assumes HF_* environment variables are correctly set.
    """
    output = query({
        "inputs": "find all bars that are called \"trink\" that are close to a kiosk in bonn",
        "prompt": PROMPT,
        "max_new_tokens": HF_MAX_NEW_TOKEN,
        "top_p": HF_TOP_P,
        "temperature": HF_TEMPERATURE
    })

    print(output)
