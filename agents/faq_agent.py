import json
from services.faq_engine import retrieve_faq

FAQ_PATH = "data/faq_all.json"


def load_faq():
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


FAQ_DATA = load_faq()

FAQ_THRESHOLD = 0.55 


def answer_faq(query: str):
    result = retrieve_faq(query, threshold=FAQ_THRESHOLD)

    if not result:
        return None

    return result.get("answer")