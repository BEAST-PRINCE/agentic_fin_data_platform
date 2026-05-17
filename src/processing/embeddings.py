import abc
import sys
from typing import List

class BaseEmbedder(abc.ABC):
    @abc.abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        pass

    @property
    @abc.abstractmethod
    def device(self) -> str:
        pass

class SentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', device: str = 'cuda'):
        from sentence_transformers import SentenceTransformer
        import torch
        
        # Fallback to CPU if CUDA is not actually available
        # IMPORTANT: Must use stderr — stdout is the MCP JSONRPC transport
        if device == 'cuda' and not torch.cuda.is_available():
            print("WARNING: CUDA requested but not available. Falling back to CPU.", file=sys.stderr)
            device = 'cpu'
            
        self.model = SentenceTransformer(model_name, device=device)
        
    def embed(self, texts: List[str]) -> List[List[float]]:
        # Returns numpy array, convert to nested list of floats
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    @property
    def device(self) -> str:
        return str(self.model.device)

class FastEmbedEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = 'BAAI/bge-small-en-v1.5', **kwargs):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name)
        
    def embed(self, texts: List[str]) -> List[List[float]]:
        # fastembed returns an iterator of numpy arrays
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

    @property
    def device(self) -> str:
        try:
            return ", ".join(self.model.model.active_providers)
        except Exception:
            return "CPU (ONNX)"

class EmbedderFactory:
    @staticmethod
    def get_embedder(engine: str = 'sentence-transformers', **kwargs) -> BaseEmbedder:
        from src.common import config
        
        # Get model_name from kwargs, falling back to .env configuration
        model_name = kwargs.pop('model_name', None) or config.VECTOR_EMBEDDING_MODEL
        
        if engine == 'sentence-transformers':
            return SentenceTransformerEmbedder(model_name=model_name, **kwargs)
        elif engine == 'fastembed':
            # FastEmbed models sometimes need matching the format expected by the fastembed library
            return FastEmbedEmbedder(model_name=model_name, **kwargs)
        else:
            raise ValueError(f"Unknown embedding engine: {engine}")
