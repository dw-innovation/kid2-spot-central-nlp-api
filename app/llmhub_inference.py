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

MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "5"))


@dataclass
class LLMHubResponse:
    """Minimal response wrapper returned by LLMHubInference.generate()."""

    content: object
    status_code: int = 200


async def query(sentence: str, environment: str) -> LLMHubResponse:
    """
    Invoke the LLM up to MAX_RETRIES times.

    Retries when the response is None, missing .content, or content is empty.
    Uses exponential backoff (1s, 2s, 4s, ...) between attempts.
    Returns a 400 LLMHubResponse only after all retries are exhausted.

    Args:
        sentence (str): The user sentence to process.
        environment (str): Execution environment indicator (e.g., "dev", "prod").

    Returns:
        LLMHubResponse: Wrapper with model text on success (200)
            or an error string on failure (400).
    """
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"SENTENCE: {sentence}\n\nOUTPUT:"),
    ]

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await llm.ainvoke(messages)

            if (
                response is None
                or not hasattr(response, "content")
                or not response.content
            ):
                raise ValueError(
                    f"LLM returned a None or empty response (attempt {attempt})."
                )

            logger.info(f"LLM query succeeded on attempt {attempt}.")
            return LLMHubResponse(content=response.content, status_code=200)

        except Exception as e:
            last_error = e
            wait = 2 ** (attempt - 1)  # 1s, 2s, 4s, 8s, 16s
            logger.warning(
                f"LLM query failed on attempt {attempt}/{MAX_RETRIES}: {e}. Retrying in {wait}s..."
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(wait)

    logger.error(
        f"LLM query failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    )
    return LLMHubResponse(content=str(last_error), status_code=400)


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

    async def adopt(self, raw_response: object) -> dict:
        result = validate_and_fix_yaml(raw_response.content)
        result = await adopt_generation(result)
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
