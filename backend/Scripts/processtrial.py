from typing import List, Optional
import hashlib
import pickle
import os
from pathlib import Path
from langchain_google_vertexai import VertexAIEmbeddings

class CachedVertexEmbeddings(VertexAIEmbeddings):
    def __init__(self, cache_dir: str = ".embedding_cache", batch_size: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.batch_size = batch_size

    def _get_cache_path(self, text: str) -> Path:
        # Create a unique filename based on text content
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.pkl"

    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        cache_path = self._get_cache_path(text)
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        return None

    def _cache_embedding(self, text: str, embedding: List[float]):
        cache_path = self._get_cache_path(text)
        with open(cache_path, 'wb') as f:
            pickle.dump(embedding, f)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        all_embeddings = []
        texts_to_embed = []
        cached_indices = []

        # Check cache first
        for i, text in enumerate(texts):
            cached_embedding = self._get_cached_embedding(text)
            if cached_embedding is not None:
                all_embeddings.append(cached_embedding)
                cached_indices.append(i)
            else:
                texts_to_embed.append(text)

        # Process uncached texts in batches
        if texts_to_embed:
            for i in range(0, len(texts_to_embed), self.batch_size):
                batch = texts_to_embed[i:i + self.batch_size]
                batch_embeddings = super().embed_documents(batch)
                
                # Cache the new embeddings
                for text, embedding in zip(batch, batch_embeddings):
                    self._cache_embedding(text, embedding)
                
                all_embeddings.extend(batch_embeddings)

        # Reconstruct the original order
        final_embeddings = [None] * len(texts)
        embed_idx = 0
        for i in range(len(texts)):
            if i in cached_indices:
                final_embeddings[i] = all_embeddings[cached_indices.index(i)]
            else:
                final_embeddings[i] = all_embeddings[embed_idx]
                embed_idx += 1

        return final_embeddings

# Modified EmbeddingModel class
class EmbeddingModel:
    @staticmethod
    def get_embedding_model():
        embeddings = CachedVertexEmbeddings(
            model_name="text-embedding-005",
            batch_size=5,
            cache_dir=".embedding_cache"
        )
        return embeddings