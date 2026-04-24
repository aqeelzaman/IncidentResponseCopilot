from typing import List

# Lazy-loaded singleton — first call downloads the model (~90 MB, cached to disk)
_model = None
_MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_DIM = 384


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed(text: str) -> List[float]:
    """Embed a single string using all-MiniLM-L6-v2 (local, no API key)."""
    return _get_model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed a batch of strings."""
    return _get_model().encode(texts, normalize_embeddings=True, batch_size=32).tolist()
