# def request_model(sentence, model):
#     r = requests.post(f"{MODEL_ENDPOINTS[model]}/transform-sentence-to-imr",
#                       headers={'accept': 'application/json', 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
#                       data=json.dumps({"sentence": sentence}))
#     return r

class T5Inference:
    def generate(self, sentence):
        pass