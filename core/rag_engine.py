"""
StudyMate RAG Engine - Advanced Retrieval-Augmented Generation
Handles document processing, embedding, and intelligent retrieval
"""

import os
import json
import numpy as np
import hashlib
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Optional imports
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

class RAGEngine:
    """Advanced RAG system with FAISS vector storage and intelligent retrieval"""
    
    def __init__(self):
        print("🔍 Initializing RAG Engine...")
        
        # Initialize embedding model
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = int(os.getenv("EMBEDDING_DIMENSION", 384))
        
        # Configuration
        self.chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 200))
        self.max_retrieve = int(os.getenv("MAX_CHUNKS_RETRIEVE", 10))
        
        # Storage setup
        self.storage_dir = Path("rag_storage")
        self.storage_dir.mkdir(exist_ok=True)
        
        # User data structures
        self.user_indices = {}      # user_id -> FAISS index
        self.user_chunks = {}       # user_id -> chunk metadata
        self.user_embeddings = {}   # user_id -> embeddings (fallback)
        self.user_documents = {}    # user_id -> document info
        
        # Capabilities
        self.faiss_available = FAISS_AVAILABLE
        
        print(f"✅ RAG Engine ready - FAISS: {self.faiss_available}, Model: {model_name}")
    
    async def add_document(
        self, 
        text_content: str, 
        filename: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Add document to user's RAG system"""
        try:
            print(f"📄 Processing document: {filename} for user: {user_id}")
            
            # Initialize user storage if needed
            if user_id not in self.user_indices:
                await self._initialize_user_storage(user_id)
            
            # Create chunks from document
            chunks = self._create_chunks(text_content, filename)
            if not chunks:
                return {"success": False, "message": "No content could be extracted"}
            
            print(f"📝 Created {len(chunks)} chunks from {filename}")
            
            # Generate embeddings with batch processing
            chunk_texts = [chunk["content"] for chunk in chunks]
            
            # Process embeddings in smaller batches to manage memory
            batch_size = 32  # Process 32 chunks at a time
            embeddings_list = []
            
            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i:i+batch_size]
                batch_embeddings = self.embedding_model.encode(batch, show_progress_bar=False)
                embeddings_list.append(batch_embeddings)
            
            # Combine batches
            embeddings = np.vstack(embeddings_list) if embeddings_list else np.array([])
            
            # Store in FAISS or fallback storage
            if self.faiss_available and self.user_indices[user_id] is not None:
                # Add to FAISS index
                if len(embeddings) > 0:
                    self.user_indices[user_id].add(embeddings.astype('float32'))
                    print(f"✅ Added {len(embeddings)} embeddings to FAISS index")
            else:
                # Fallback to simple storage
                if user_id not in self.user_embeddings:
                    self.user_embeddings[user_id] = []
                if len(embeddings) > 0:
                    self.user_embeddings[user_id].extend(embeddings.tolist())
                    print(f"✅ Added {len(embeddings)} embeddings to simple storage")
            
            # Store chunk metadata
            self.user_chunks[user_id].extend(chunks)
            
            # Clean up large arrays from memory
            del embeddings
            del embeddings_list
            del chunk_texts
            
            # Update document registry
            doc_info = {
                "filename": filename,
                "upload_date": datetime.now().isoformat(),
                "chunks_count": len(chunks),
                "text_length": len(text_content)
            }
            
            if user_id not in self.user_documents:
                self.user_documents[user_id] = []
            self.user_documents[user_id].append(doc_info)
            
            # Save to disk
            await self._save_user_data(user_id)
            
            return {
                "success": True,
                "message": f"Successfully processed {filename}",
                "chunks_created": len(chunks)
            }
            
        except Exception as e:
            print(f"❌ Error adding document: {e}")
            return {"success": False, "message": str(e)}
    
    async def retrieve_relevant_chunks(
        self, 
        query: str, 
        user_id: str, 
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for query"""
        try:
            if user_id not in self.user_chunks or not self.user_chunks[user_id]:
                return []
            
            top_k = top_k or self.max_retrieve
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            if self.faiss_available and self.user_indices.get(user_id) is not None:
                # Use FAISS for retrieval
                return await self._faiss_retrieve(query_embedding, user_id, top_k)
            else:
                # Use simple similarity search
                return await self._simple_retrieve(query_embedding, user_id, top_k)
                
        except Exception as e:
            print(f"❌ Error retrieving chunks: {e}")
            return []
    
    async def _faiss_retrieve(
        self, 
        query_embedding: np.ndarray, 
        user_id: str, 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve using FAISS index"""
        try:
            index = self.user_indices[user_id]
            chunks = self.user_chunks[user_id]
            
            # Search in FAISS
            scores, indices = index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(chunks))
            )
            
            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if 0 <= idx < len(chunks):
                    chunk = chunks[idx].copy()
                    chunk["relevance_score"] = float(score)
                    chunk["retrieval_method"] = "faiss"
                    results.append(chunk)
            
            # Sort by relevance score (higher is better for inner product)
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"❌ FAISS retrieval error: {e}")
            return []
    
    async def _simple_retrieve(
        self, 
        query_embedding: np.ndarray, 
        user_id: str, 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Simple cosine similarity retrieval"""
        try:
            if user_id not in self.user_embeddings:
                return []
            
            embeddings = np.array(self.user_embeddings[user_id])
            chunks = self.user_chunks[user_id]
            
            # Calculate cosine similarities
            query_norm = np.linalg.norm(query_embedding)
            similarities = []
            
            for i, doc_embedding in enumerate(embeddings):
                doc_norm = np.linalg.norm(doc_embedding)
                if doc_norm > 0 and query_norm > 0:
                    similarity = np.dot(query_embedding[0], doc_embedding) / (query_norm * doc_norm)
                    similarities.append((similarity, i))
            
            # Sort by similarity and get top_k
            similarities.sort(reverse=True, key=lambda x: x[0])
            top_similarities = similarities[:min(top_k, len(similarities))]
            
            # Format results
            results = []
            for similarity, idx in top_similarities:
                if 0 <= idx < len(chunks):
                    chunk = chunks[idx].copy()
                    chunk["relevance_score"] = float(similarity)
                    chunk["retrieval_method"] = "cosine"
                    results.append(chunk)
            
            return results
            
        except Exception as e:
            print(f"❌ Simple retrieval error: {e}")
            return []
    
    def _create_chunks(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """Create overlapping text chunks with metadata"""
        chunks = []
        
        # Split into sentences first for better chunk boundaries
        sentences = self._split_into_sentences(text)
        
        current_chunk_parts = []
        current_length = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            # Check if adding this sentence would exceed chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk_parts:
                # Create chunk
                current_chunk = " ".join(current_chunk_parts).strip()
                chunk_id = hashlib.md5(f"{filename}_{chunk_index}".encode()).hexdigest()
                chunks.append({
                    "id": chunk_id,
                    "content": current_chunk,
                    "source_file": filename,
                    "chunk_index": chunk_index,
                    "word_count": current_length,
                    "created_at": datetime.now().isoformat()
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk_parts = [overlap_text, sentence] if overlap_text else [sentence]
                current_length = len(" ".join(current_chunk_parts).split())
                chunk_index += 1
            else:
                # Add sentence to current chunk
                current_chunk_parts.append(sentence)
                current_length += sentence_length
        
        # Add final chunk if there's content
        if current_chunk_parts:
            current_chunk = " ".join(current_chunk_parts).strip()
            chunk_id = hashlib.md5(f"{filename}_{chunk_index}".encode()).hexdigest()
            chunks.append({
                "id": chunk_id,
                "content": current_chunk,
                "source_file": filename,
                "chunk_index": chunk_index,
                "word_count": current_length,
                "created_at": datetime.now().isoformat()
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for better chunking"""
        import re
        
        # Simple sentence splitting (can be enhanced with NLTK/spaCy)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap_text(self, text: str, overlap_words: int) -> str:
        """Get last N words for chunk overlap"""
        words = text.split()
        if len(words) <= overlap_words:
            return text
        return " ".join(words[-overlap_words:])
    
    async def _initialize_user_storage(self, user_id: str):
        """Initialize storage for new user"""
        if self.faiss_available:
            # Create FAISS index
            index_type = os.getenv("FAISS_INDEX_TYPE", "IndexFlatIP")
            if index_type == "IndexFlatIP":
                self.user_indices[user_id] = faiss.IndexFlatIP(self.embedding_dim)
            else:
                self.user_indices[user_id] = faiss.IndexFlatL2(self.embedding_dim)
        else:
            self.user_indices[user_id] = None
            self.user_embeddings[user_id] = []
        
        self.user_chunks[user_id] = []
        self.user_documents[user_id] = []
        
        # Try to load existing data
        await self._load_user_data(user_id)
    
    async def _save_user_data(self, user_id: str):
        """Save user's RAG data to disk"""
        try:
            user_dir = self.storage_dir / user_id
            user_dir.mkdir(exist_ok=True)
            
            # Save FAISS index
            if self.faiss_available and self.user_indices.get(user_id) is not None:
                index_path = user_dir / "faiss_index.bin"
                faiss.write_index(self.user_indices[user_id], str(index_path))
            
            # Save embeddings (fallback storage)
            if user_id in self.user_embeddings:
                embeddings_path = user_dir / "embeddings.json"
                with open(embeddings_path, "w") as f:
                    json.dump(self.user_embeddings[user_id], f)
            
            # Save chunks metadata
            chunks_path = user_dir / "chunks.json"
            with open(chunks_path, "w", encoding="utf-8") as f:
                json.dump(self.user_chunks[user_id], f, ensure_ascii=False, indent=2)
            
            # Save document registry
            docs_path = user_dir / "documents.json"
            with open(docs_path, "w", encoding="utf-8") as f:
                json.dump(self.user_documents[user_id], f, ensure_ascii=False, indent=2)
            
            print(f"💾 Saved RAG data for user: {user_id}")
            
        except Exception as e:
            print(f"❌ Error saving user data: {e}")
    
    async def _load_user_data(self, user_id: str):
        """Load user's existing RAG data"""
        try:
            user_dir = self.storage_dir / user_id
            if not user_dir.exists():
                return
            
            # Load FAISS index
            index_path = user_dir / "faiss_index.bin"
            if self.faiss_available and index_path.exists():
                self.user_indices[user_id] = faiss.read_index(str(index_path))
            
            # Load embeddings
            embeddings_path = user_dir / "embeddings.json"
            if embeddings_path.exists():
                with open(embeddings_path, "r") as f:
                    self.user_embeddings[user_id] = json.load(f)
            
            # Load chunks
            chunks_path = user_dir / "chunks.json"
            if chunks_path.exists():
                with open(chunks_path, "r", encoding="utf-8") as f:
                    self.user_chunks[user_id] = json.load(f)
            
            # Load documents
            docs_path = user_dir / "documents.json"
            if docs_path.exists():
                with open(docs_path, "r", encoding="utf-8") as f:
                    self.user_documents[user_id] = json.load(f)
            
            print(f"📂 Loaded RAG data for user: {user_id}")
            
        except Exception as e:
            print(f"❌ Error loading user data: {e}")
    
    async def get_user_document_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive document statistics"""
        if user_id not in self.user_chunks:
            return {
                "total_chunks": 0,
                "total_documents": 0,
                "documents": [],
                "storage_method": "none"
            }
        
        chunks = self.user_chunks[user_id]
        documents = self.user_documents.get(user_id, [])
        
        # Calculate statistics
        unique_files = set(chunk["source_file"] for chunk in chunks)
        total_words = sum(chunk.get("word_count", 0) for chunk in chunks)
        
        return {
            "total_chunks": len(chunks),
            "total_documents": len(unique_files),
            "total_words": total_words,
            "documents": documents,
            "storage_method": "faiss" if self.faiss_available else "simple",
            "last_updated": max([doc.get("upload_date", "") for doc in documents], default="")
        }
    
    async def clear_user_documents(self, user_id: str) -> bool:
        """Clear all documents for a user"""
        try:
            # Clear in-memory data
            if user_id in self.user_indices:
                del self.user_indices[user_id]
            if user_id in self.user_chunks:
                del self.user_chunks[user_id]
            if user_id in self.user_embeddings:
                del self.user_embeddings[user_id]
            if user_id in self.user_documents:
                del self.user_documents[user_id]
            
            # Clear disk storage
            user_dir = self.storage_dir / user_id
            if user_dir.exists():
                import shutil
                shutil.rmtree(user_dir)
            
            print(f"🗑️ Cleared all documents for user: {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing user documents: {e}")
            return False
    
    async def search_documents(
        self, 
        user_id: str, 
        query: str, 
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Advanced document search with filters"""
        try:
            # Get relevant chunks
            chunks = await self.retrieve_relevant_chunks(query, user_id)
            
            # Apply filters if provided
            if filters:
                if "filename" in filters:
                    chunks = [c for c in chunks if filters["filename"] in c["source_file"]]
                if "min_score" in filters:
                    chunks = [c for c in chunks if c["relevance_score"] >= filters["min_score"]]
                if "date_from" in filters:
                    chunks = [c for c in chunks if c.get("created_at", "") >= filters["date_from"]]
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error searching documents: {e}")
            return []