from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FAQ_JSON = BASE_DIR / "data" / "faq_all.json"
FAQ_EMBEDDINGS = BASE_DIR / "data" / "faq_embeddings.npy"
FAQ_META = BASE_DIR / "data" / "faq_index_meta.json"
FAQ_VECTORIZER = BASE_DIR / "data" / "faq_vectorizer.pkl"

import json
import os
import pickle

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

from build_faq_kb import main as build_faq_kb

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

_model = None
_embeddings = None
_faq_data = None
_faq_init_error = None
_backend = None
_vectorizer = None


def _ensure_faq_resources():
    global _model, _embeddings, _faq_data, _faq_init_error, _backend, _vectorizer

    if _model is not None and _embeddings is not None and _faq_data is not None:
        return True

    try:
        # Ensure files exist
        if not FAQ_JSON.exists() or not FAQ_EMBEDDINGS.exists():
            build_faq_kb()

        # Load backend metadata
        if FAQ_META.exists():
            meta = json.loads(FAQ_META.read_text(encoding="utf-8"))
            _backend = meta.get("backend", "sentence_transformers")
        else:
            _backend = "sentence_transformers"

        # Load embeddings + data
        _embeddings = np.load(FAQ_EMBEDDINGS)

        with open(FAQ_JSON, "r", encoding="utf-8") as f:
            _faq_data = json.load(f)

        # Load model
        if _backend == "sentence_transformers":
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")

        elif _backend == "tfidf":
            with open(FAQ_VECTORIZER, "rb") as fp:
                _vectorizer = pickle.load(fp)
            _model = "tfidf"

        else:
            raise RuntimeError(f"Unsupported FAQ backend: {_backend}")

        return True

    except Exception as exc:
        _faq_init_error = str(exc)
        return False


def retrieve_faq(query: str, threshold: float = 0.5) -> dict | None:
    if not _ensure_faq_resources():
        return None

    # 1. Exact string match first (case-insensitive)
    query_lower = query.strip().lower()
    for item in _faq_data:
        q = item.get("question", "").strip().lower()
        if q == query_lower:
            return {"answer": item.get("answer", ""), "score": 1.0}

    # 2. Vector search fallback
    if _backend == "sentence_transformers":
        query_embedding = _model.encode([query])
    else:
        query_embedding = _vectorizer.transform([query]).toarray()

    similarities = cosine_similarity(query_embedding, _embeddings)[0]
    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])
    if best_score < threshold:
        return None
    result = _faq_data[best_idx]
    return {"answer": result.get("answer", ""), "score": best_score}
    