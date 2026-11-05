"""
Simple Vector Store - Lightweight alternative to ChromaDB
Uses numpy for vector operations and pickle for persistence
"""
import os
import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple


class SimpleVectorStore:
    """
    Lightweight vector database using numpy
    
    Stores:
        - embeddings: numpy array of vectors
        - ids: list of document IDs
        - metadatas: list of metadata dicts
        - documents: list of text documents
    """
    
    def __init__(self, name: str, persist_directory: str = "./vector_db"):
        self.name = name
        self.persist_directory = persist_directory
        self.persist_file = os.path.join(persist_directory, f"{name}.pkl")
        
        # Create directory if not exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize storage
        self.embeddings = None  # numpy array of shape (n_docs, embedding_dim)
        self.ids = []
        self.metadatas = []
        self.documents = []
        
        # Load existing data if available
        self._load()
    
    def _load(self):
        """Load persisted data"""
        if os.path.exists(self.persist_file):
            try:
                with open(self.persist_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data.get('embeddings')
                    self.ids = data.get('ids', [])
                    self.metadatas = data.get('metadatas', [])
                    self.documents = data.get('documents', [])
            except Exception as e:
                print(f"Warning: Could not load vector store: {e}")
    
    def _save(self):
        """Persist data to disk"""
        try:
            with open(self.persist_file, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embeddings,
                    'ids': self.ids,
                    'metadatas': self.metadatas,
                    'documents': self.documents
                }, f)
        except Exception as e:
            print(f"Warning: Could not save vector store: {e}")
    
    def upsert(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        documents: List[str]
    ):
        """
        Add or update documents
        
        Args:
            ids: List of document IDs
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts
            documents: List of text documents
        """
        embeddings_array = np.array(embeddings)
        
        for i, doc_id in enumerate(ids):
            # Check if ID exists
            if doc_id in self.ids:
                # Update existing
                idx = self.ids.index(doc_id)
                self.embeddings[idx] = embeddings_array[i]
                self.metadatas[idx] = metadatas[i]
                self.documents[idx] = documents[i]
            else:
                # Add new
                if self.embeddings is None:
                    self.embeddings = embeddings_array[i:i+1]
                else:
                    self.embeddings = np.vstack([self.embeddings, embeddings_array[i:i+1]])
                
                self.ids.append(doc_id)
                self.metadatas.append(metadatas[i])
                self.documents.append(documents[i])
        
        # Persist
        self._save()
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query for similar documents
        
        Args:
            query_embeddings: List of query vectors
            n_results: Number of results to return
            where: Filter conditions (optional)
        
        Returns:
            Dict with ids, distances, metadatas
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return {'ids': [[]], 'distances': [[]], 'metadatas': [[]]}
        
        query_array = np.array(query_embeddings)
        
        # Calculate cosine distances for all queries
        all_ids = []
        all_distances = []
        all_metadatas = []
        
        for query_vector in query_array:
            # Calculate cosine similarity
            # cosine_similarity = dot(A, B) / (norm(A) * norm(B))
            similarities = np.dot(self.embeddings, query_vector) / (
                np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vector)
            )
            
            # Convert similarity to distance (1 - similarity)
            distances = 1 - similarities
            
            # Apply filters if provided
            valid_indices = list(range(len(self.ids)))
            if where:
                valid_indices = []
                for idx, metadata in enumerate(self.metadatas):
                    match = True
                    for key, condition in where.items():
                        if isinstance(condition, dict) and '$contains' in condition:
                            # Check if metadata[key] contains the value
                            if key not in metadata or condition['$contains'] not in metadata[key]:
                                match = False
                                break
                        else:
                            # Exact match
                            if key not in metadata or metadata[key] != condition:
                                match = False
                                break
                    if match:
                        valid_indices.append(idx)
            
            # Get top N results from valid indices
            if valid_indices:
                valid_distances = distances[valid_indices]
                valid_ids = [self.ids[i] for i in valid_indices]
                valid_metadatas = [self.metadatas[i] for i in valid_indices]
                
                # Sort by distance (ascending)
                sorted_indices = np.argsort(valid_distances)[:n_results]
                
                result_ids = [valid_ids[i] for i in sorted_indices]
                result_distances = [float(valid_distances[i]) for i in sorted_indices]
                result_metadatas = [valid_metadatas[i] for i in sorted_indices]
            else:
                result_ids = []
                result_distances = []
                result_metadatas = []
            
            all_ids.append(result_ids)
            all_distances.append(result_distances)
            all_metadatas.append(result_metadatas)
        
        return {
            'ids': all_ids,
            'distances': all_distances,
            'metadatas': all_metadatas
        }
    
    def count(self) -> int:
        """Return number of documents"""
        return len(self.ids)
    
    def delete(self, ids: List[str]):
        """Delete documents by ID"""
        indices_to_keep = [i for i, doc_id in enumerate(self.ids) if doc_id not in ids]
        
        if self.embeddings is not None:
            self.embeddings = self.embeddings[indices_to_keep]
        self.ids = [self.ids[i] for i in indices_to_keep]
        self.metadatas = [self.metadatas[i] for i in indices_to_keep]
        self.documents = [self.documents[i] for i in indices_to_keep]
        
        self._save()


class SimpleVectorDB:
    """
    Simple vector database manager
    Mimics ChromaDB API
    """
    
    def __init__(self, path: str = "./vector_db"):
        self.path = path
        self.collections = {}
    
    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None):
        """Get or create a collection"""
        if name not in self.collections:
            self.collections[name] = SimpleVectorStore(name, self.path)
        return self.collections[name]
