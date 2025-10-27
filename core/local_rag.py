"""
Local RAG System - Offline document retrieval and processing
"""

import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from pathlib import Path
import hashlib

# Optional imports
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️  FAISS not available. Install with: pip install faiss-cpu")

class LocalRAG:
    def __init__(self):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        
        # Storage paths
        self.storage_dir = Path("rag_storage")
        self.storage_dir.mkdir(exist_ok=True)
        
        # User-specific storage
        self.user_indices = {}  # user_id -> faiss index or simple storage
        self.user_chunks = {}   # user_id -> list of text chunks with metadata
        self.user_embeddings = {}  # user_id -> embeddings (if FAISS not available)
        
    async def add_document(self, text_content: str, user_id: str, file_path: str) -> bool:
        """Add document to user's RAG system"""
        try:
            print(f"🔧 Adding document to RAG for user: {user_id}")
            
            # Initialize user storage if needed
            if user_id not in self.user_indices:
                print(f"🆕 Initializing storage for new user: {user_id}")
                await self._initialize_user_storage(user_id)
            
            # Chunk the document
            chunks = self._chunk_text(text_content, file_path)
            print(f"📄 Created {len(chunks)} chunks from document")
            
            if not chunks:
                print("❌ No chunks created from document")
                return False
            
            # Generate embeddings
            texts = [chunk["content"] for chunk in chunks]
            embeddings = self.embedding_model.encode(texts)
            
            if FAISS_AVAILABLE and self.user_indices[user_id] is not None:
                # Add to FAISS index
                self.user_indices[user_id].add(embeddings.astype('float32'))
            else:
                # Store embeddings in simple list
                if user_id not in self.user_embeddings:
                    self.user_embeddings[user_id] = []
                self.user_embeddings[user_id].extend(embeddings.tolist())
            
            # Store chunks with metadata
            self.user_chunks[user_id].extend(chunks)
            
            # Save to disk
            await self._save_user_data(user_id)
            
            return True
            
        except Exception as e:
            print(f"Error adding document to RAG: {e}")
            return False
    
    async def retrieve_relevant_chunks(self, query: str, user_id: str, top_k: int = 5) -> List[Dict]:
        """Retrieve most relevant chunks for query"""
        try:
            if user_id not in self.user_chunks or len(self.user_chunks.get(user_id, [])) == 0:
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            if FAISS_AVAILABLE and self.user_indices[user_id] is not None:
                # Search in FAISS index
                scores, indices = self.user_indices[user_id].search(
                    query_embedding.astype('float32'), 
                    min(top_k, len(self.user_chunks[user_id]))
                )
                
                # Return relevant chunks with scores
                relevant_chunks = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < len(self.user_chunks[user_id]):
                        chunk = self.user_chunks[user_id][idx].copy()
                        chunk["relevance_score"] = float(score)
                        relevant_chunks.append(chunk)
                
                return relevant_chunks
            else:
                # Simple similarity search without FAISS
                return await self._simple_similarity_search(query_embedding, user_id, top_k)
            
        except Exception as e:
            print(f"Error retrieving chunks: {e}")
            return []
    
    async def _simple_similarity_search(self, query_embedding, user_id: str, top_k: int) -> List[Dict]:
        """Simple similarity search when FAISS is not available"""
        try:
            if user_id not in self.user_embeddings:
                return []
            
            import numpy as np
            
            # Calculate cosine similarity
            query_norm = np.linalg.norm(query_embedding)
            similarities = []
            
            for i, doc_embedding in enumerate(self.user_embeddings[user_id]):
                doc_embedding = np.array(doc_embedding)
                doc_norm = np.linalg.norm(doc_embedding)
                
                if doc_norm > 0 and query_norm > 0:
                    similarity = np.dot(query_embedding[0], doc_embedding) / (query_norm * doc_norm)
                    similarities.append((similarity, i))
            
            # Sort by similarity and get top_k
            similarities.sort(reverse=True, key=lambda x: x[0])
            top_similarities = similarities[:min(top_k, len(similarities))]
            
            # Return relevant chunks
            relevant_chunks = []
            for similarity, idx in top_similarities:
                if idx < len(self.user_chunks[user_id]):
                    chunk = self.user_chunks[user_id][idx].copy()
                    chunk["relevance_score"] = float(similarity)
                    relevant_chunks.append(chunk)
            
            return relevant_chunks
            
        except Exception as e:
            print(f"Error in simple similarity search: {e}")
            return []
    
    def _chunk_text(self, text: str, file_path: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """Split text into overlapping chunks"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            # Create chunk metadata
            chunk_id = hashlib.md5(f"{file_path}_{i}".encode()).hexdigest()
            
            chunks.append({
                "id": chunk_id,
                "content": chunk_text,
                "source_file": file_path,
                "chunk_index": len(chunks),
                "word_count": len(chunk_words)
            })
        
        return chunks
    
    async def _initialize_user_storage(self, user_id: str):
        """Initialize storage for new user"""
        if FAISS_AVAILABLE:
            # Create FAISS index
            self.user_indices[user_id] = faiss.IndexFlatIP(self.embedding_dim)
        else:
            # Use simple list storage as fallback
            self.user_indices[user_id] = None
            self.user_embeddings[user_id] = []
        
        self.user_chunks[user_id] = []
        
        # Try to load existing data
        await self._load_user_data(user_id)
    
    async def _save_user_data(self, user_id: str):
        """Save user's RAG data to disk"""
        try:
            user_dir = self.storage_dir / user_id
            user_dir.mkdir(exist_ok=True)
            
            # Save FAISS index if available
            if FAISS_AVAILABLE and self.user_indices[user_id] is not None:
                faiss.write_index(self.user_indices[user_id], str(user_dir / "index.faiss"))
            
            # Save embeddings if using simple storage
            if user_id in self.user_embeddings:
                with open(user_dir / "embeddings.json", "w", encoding="utf-8") as f:
                    json.dump(self.user_embeddings[user_id], f, indent=2)
            
            # Save chunks metadata
            with open(user_dir / "chunks.json", "w", encoding="utf-8") as f:
                json.dump(self.user_chunks[user_id], f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving user data: {e}")
    
    async def _load_user_data(self, user_id: str):
        """Load user's existing RAG data"""
        try:
            user_dir = self.storage_dir / user_id
            
            if not user_dir.exists():
                return
            
            # Load FAISS index if available
            index_path = user_dir / "index.faiss"
            if FAISS_AVAILABLE and index_path.exists():
                self.user_indices[user_id] = faiss.read_index(str(index_path))
            
            # Load embeddings if using simple storage
            embeddings_path = user_dir / "embeddings.json"
            if embeddings_path.exists():
                with open(embeddings_path, "r", encoding="utf-8") as f:
                    self.user_embeddings[user_id] = json.load(f)
            
            # Load chunks
            chunks_path = user_dir / "chunks.json"
            if chunks_path.exists():
                with open(chunks_path, "r", encoding="utf-8") as f:
                    self.user_chunks[user_id] = json.load(f)
                    
        except Exception as e:
            print(f"Error loading user data: {e}")
    
    async def get_user_document_stats(self, user_id: str) -> Dict:
        """Get statistics about user's uploaded documents"""
        if user_id not in self.user_chunks:
            return {"total_chunks": 0, "total_documents": 0}
        
        chunks = self.user_chunks[user_id]
        unique_files = set(chunk["source_file"] for chunk in chunks)
        
        return {
            "total_chunks": len(chunks),
            "total_documents": len(unique_files),
            "documents": list(unique_files)
        }