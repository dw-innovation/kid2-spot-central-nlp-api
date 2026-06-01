import os
from dataclasses import dataclass

import requests
from adopt_generation import adopt_generation
from dotenv import load_dotenv
from imr_schema import IMROutput
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from yaml_parser import validate_and_fix_yaml

logger.add(f"{__name__}.log", rotation="500 MB")

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("LLMHUB_MODEL"),
    base_url=os.getenv("LLMHUB_ENDPOINT"),
    api_key=os.getenv("LLMHUB_KEY"),
)

structured_llm = llm.with_structured_output(IMROutput)

PROMPT_FILE = os.environ.get("PROMPT_FILE", "prompt.txt")

with open(PROMPT_FILE, "r") as f:
    SYSTEM_PROMPT = f.read()


@dataclass
class LLMHubResponse:
    """Minimal response wrapper returned by LLMHubInference.generate()."""

    content: object
    status_code: int = 200


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
        LLMHubResponse: Wrapper with generated content and HTTP status code.
    """
    try:
        sentence = payload["inputs"]
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"SENTENCE: {sentence}"),
        ]
        response = structured_llm.invoke(messages)
        return LLMHubResponse(content=response, status_code=200)
    except Exception as e:
        return LLMHubResponse(content=str(e), status_code=400)


class LLMHubInference:
    """
    Thin wrapper around a LLM Hub generation endpoint.

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
        sentence = sentence.lower()
        prompt = SYSTEM_PROMPT.replace("<INPUT_SENTENCE>", sentence)
        output = query(
            {
                "inputs": prompt,
                # "prompt": PROMPT,
                # "max_new_tokens": HF_MAX_NEW_TOKEN,
                # "top_p": HF_TOP_P,
                # "temperature": HF_TEMPERATURE,
            },
            environment,
        )
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
        return response.content

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
        parsed_dict = raw_response.model_dump(exclude_none=True)
        result = adopt_generation(parsed_dict)
        return result


if __name__ == "__main__":
    """
    Manual test harness: performs a single query against the LLaMA endpoint
    and prints the raw `requests.Response`. Useful for connectivity checks.

    Notes:
        - Uses the globally loaded PROMPT and sampling parameters.
        - Assumes HF_* environment variables are correctly set.
    """
    output = query(
        {
            "inputs": 'find all bars that are called "trink" that are close to a kiosk in bonn',
            # # "prompt": PROMPT,
            # "max_new_tokens": HF_MAX_NEW_TOKEN,
            # "top_p": HF_TOP_P,
            # "temperature": HF_TEMPERATURE,
        }
    )

    print(output)
