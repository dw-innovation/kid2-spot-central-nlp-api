from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

model = 'llama'
# model = 't5'

test_sentences = [
        "Find all italian restaurants that are no more than 200 meters from a fountain in London.",
        "Find supermarkets whose height is larger than 10 and with a red roof",
        "find me restaurants in berlin",
        "find me wind turbine in bonn",
        "find all kiosks within a park",
        "find all bars",
        "Find all book stores of brand thalia",
        "loking for discounter in lombrady. must be 100 metres way from a medical suppy store. there shuld be also hairdresser close to the discounter and the medical supply store.",
        "find mural, 300 yards form burger king restaurant with pakring spotts in laborde, cordoba, argentina",
        "i am looking for an italian restaurant with outdoor seating, the restaurant is within 300 meters from train tracks and a railway bridge.",
        "I am looking for locations. I searching for an communications tower who is located within construction site. The aforementioned tower are locate in close distances to H&M.",
        "i look for a restaurant in makkah, saudi arabia. i would like the restaurant to be either Nusret or Kebap",
        "show me a place with three benches that are within 30 m of each other 100 m from a river in cologne",
        "Find a park next to a two lane road in berlin",
        "public bin within 50 meters from a bus  stop"
    ]

for test_sentence in test_sentences:
    response = client.post("/transform-sentence-to-imr", headers={"X-Token": "coneofsilence"},
                           json={"sentence": test_sentence,
                                 "model": model,
                                 "username": "kid-test",
                                 "environment": "production"})
    print(response)
    # response = client.post("/transform-sentence-to-imr", headers={"X-Token": "coneofsilence"},
    #                        json={"sentence": test_sentence,
    #                              "model": model,
    #                              "username": "kid-test",
    #                              "environment": "development"})
    # print(response)

    print("==sentence==")
    print(test_sentence)

    print("==response==")
    print(response.json())

    assert response.status_code==200

    # print("==sentence==")
    # print(test_sentence)
    #
    # print("==response==")
    # print(response.json())
    #
    # assert response.status_code==200
