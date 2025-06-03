import requests
import os
from dotenv import load_dotenv
from loguru import logger
from yaml_parser import validate_and_fix_yaml
from adopt_generation import adopt_generation

logger.add(f"{__name__}.log", rotation="500 MB")

load_dotenv()

HF_LLAMA_ENDPOINT_PROD = os.getenv("HF_LLAMA_ENDPOINT_PROD")
HF_LLAMA_ENDPOINT_DEV = os.getenv("HF_LLAMA_ENDPOINT_DEV")
HF_ACCESS_TOKEN = os.getenv("HF_ACCESS_TOKEN")
HF_MAX_NEW_TOKEN = os.getenv("HF_MAX_NEW_TOKEN", 1048)
HF_TOP_P = os.getenv("HF_TOP_P", 0.1)
HF_TEMPERATURE = os.getenv("HF_TEMPERATURE", 0.001)
PROMPT_FILE = os.getenv("PROMPT_FILE")

with open(PROMPT_FILE, 'r') as file:
    PROMPT = file.read()

headers = {
	"Accept" : "application/json",
	"Authorization": f'Bearer {HF_ACCESS_TOKEN}',
	"Content-Type": "application/json"
}
def query(payload, environment):
    
    endpoint = HF_LLAMA_ENDPOINT_DEV if environment == "development" else HF_LLAMA_ENDPOINT_PROD
    response = requests.post(endpoint, headers=headers, json=payload)
    print(response)
    # response = response.json()
    return response
    # return response[0]['generated_text']


class LlamaInference:
    def generate(self, sentence, environment):
        output = query({
            "inputs": sentence.lower(),
            "prompt": PROMPT,
            "max_new_tokens": HF_MAX_NEW_TOKEN,
            "top_p": HF_TOP_P,
            "temperature": HF_TEMPERATURE
        }, environment)
        return output

    def get_raw_output(self, response):
        sentence = response.json()[0]['generated_text']
        return sentence


    def adopt(self, raw_response):
        result = validate_and_fix_yaml(raw_response)
        result = adopt_generation(result)
        return result


if __name__ == '__main__':
    output = query({
        "inputs": "find all bars that are called \"trink\" that are close to a kiosk in bonn",
        "prompt": PROMPT,
        "max_new_tokens": HF_MAX_NEW_TOKEN,
        "top_p": HF_TOP_P,
        "temperature": HF_TEMPERATURE
    })

    print(output)