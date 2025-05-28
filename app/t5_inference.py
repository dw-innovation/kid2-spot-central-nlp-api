from dotenv import load_dotenv
from yaml_parser import validate_and_fix_yaml
from adopt_generation import adopt_generation
import requests
import json
import os

load_dotenv()

T5_ENDPOINT = os.getenv("T5_ENDPOINT")

class T5Inference:

    def generate(self, sentence, environment):
        response = requests.post(f"{T5_ENDPOINT}/transform-sentence-to-imr",
                          headers={'accept': 'application/json', 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                          data=json.dumps({"sentence": sentence}))
        return response


    def get_raw_output(self, response):
        sentence = response.json()
        return sentence['rawOutput']


    def adopt(self, raw_response):
        result = validate_and_fix_yaml(raw_response)
        result = adopt_generation(result)
        return result

