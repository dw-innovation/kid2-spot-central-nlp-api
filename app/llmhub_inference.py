import os
from dataclasses import dataclass

from adopt_generation import adopt_generation
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import ValidationError
from yaml_parser import validate_and_fix_yaml

logger.add(f"{__name__}.log", rotation="500 MB")

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("LLMHUB_MODEL"),
    base_url=os.getenv("LLMHUB_ENDPOINT"),
    api_key=os.getenv("LLMHUB_KEY"),
    timeout=240,
    max_tokens=10000,
)

PROMPT_FILE = os.environ.get("PROMPT_FILE", "prompt.txt")

with open(PROMPT_FILE, "r") as f:
    SYSTEM_PROMPT = f.read()


@dataclass
class LLMHubResponse:
    """Minimal response wrapper returned by LLMHubInference.generate()."""

    content: object
    status_code: int = 200


async def query(sentence: str, environment: str) -> LLMHubResponse:
    """
    Invoke the structured LLM to extract an IMR from the given sentence.

    Args:
        sentence (str): The user sentence to process.
        environment (str): Execution environment indicator (e.g., "dev", "prod").

    Returns:
        LLMHubResponse: Wrapper with an IMROutput on success (200)
            or an error string on failure (400).
    """
    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"SENTENCE: {sentence}\n\nOUTPUT:"),
        ]
        response = await llm.ainvoke(messages)
        return LLMHubResponse(content=response.content, status_code=200)

    except Exception as e:
        logger.exception("LLM query failed")
        return LLMHubResponse(content=str(e), status_code=400)


class LLMHubInference:
    """
    Thin wrapper around a LLM Hub generation endpoint.

    Provides:
      - request construction and dispatch
      - extraction of the structured model output
      - adaptation into the final IMR graph shape
    """

    async def generate(self, sentence: str, environment: str) -> LLMHubResponse:
        """
        Generate a structured IMR using the LLM endpoint.

        Args:
            sentence (str): Input sentence to process.
            environment (str): Execution environment indicator (e.g., "dev", "prod").

        Returns:
            LLMHubResponse: Wrapper with IMROutput on success or error string on failure.
        """
        return await query(sentence.lower(), environment)

    def get_raw_output(self, response: LLMHubResponse) -> str:
        """
        Extract the IMROutput from the response wrapper.

        Args:
            response (LLMHubResponse): Response wrapper returned by `generate`.

        Returns:
            IMROutput: The structured output from the LLM.
        """
        return response

    def adopt(self, raw_response: object) -> dict:
        """
        Convert the structured IMROutput into the final IMR graph shape.

        Args:
            raw_response (IMROutput): Validated Pydantic model from the LLM.

        Returns:
            dict: The adopted result with 'imr' and 'display' keys.
        """
        result = validate_and_fix_yaml(raw_response.content)
        result = adopt_generation(result)
        return result


if __name__ == "__main__":
    import asyncio

    async def main():
        output = await query(
            'find all bars that are called "trink" that are close to a kiosk in bonn',
            environment="dev",
        )
        print(output)

    asyncio.run(main())
