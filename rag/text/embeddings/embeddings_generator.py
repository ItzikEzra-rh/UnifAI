from transformers import AutoTokenizer, AutoModel
import torch
from typing import List
import numpy as np

class EmbeddingsGenerator:
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def generate_embeddings(self, text_chunks: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a list of text chunks"""
        embeddings = []
        for chunk in text_chunks:
            inputs = self.tokenizer(
                chunk,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Mean pooling to get chunk embedding
            embedding = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
            embeddings.append(embedding)
        
        return embeddings
