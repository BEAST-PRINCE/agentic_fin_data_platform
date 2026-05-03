import abc
import sys
from typing import List

class BaseEmbedder(abc.ABC):
    @abc.abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
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

class FastEmbedEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = 'BAAI/bge-small-en-v1.5'):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name)
        
    def embed(self, texts: List[str]) -> List[List[float]]:
        # fastembed returns an iterator of numpy arrays
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

class EmbedderFactory:
    @staticmethod
    def get_embedder(engine: str = 'sentence-transformers', **kwargs) -> BaseEmbedder:
        if engine == 'sentence-transformers':
            return SentenceTransformerEmbedder(**kwargs)
        elif engine == 'fastembed':
            return FastEmbedEmbedder(**kwargs)
        else:
            raise ValueError(f"Unknown embedding engine: {engine}")
