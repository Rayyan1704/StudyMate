"""
StudyMate AI Engine - Advanced AI routing and processing
Handles smart query routing, RAG, and response generation
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import numpy as np
import json
from pathlib import Path

# Optional imports
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from .document_processor import DocumentProcessor
from .rag_engine import RAGEngine
from .notes_generator import NotesGenerator
from models.api_models import ChatResponse

class AIEngine:
    """Advanced AI Engine with smart routing and multi-modal capabilities"""
    
    def __init__(self):
        print("🧠 Initializing AI Engine...")
        
        # Initialize Gemini AI
        self.gemini_available = False
        self.gemini_model = None
        self._init_gemini()
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.rag_engine = RAGEngine()
        self.notes_generator = NotesGenerator()
        
        # Capabilities
        self.faiss_available = FAISS_AVAILABLE
        
        # User data tracking
        self.user_contexts = {}  # user_id -> context data
        
        print(f"✅ AI Engine ready - Gemini: {self.gemini_available}, FAISS: {self.faiss_available}")
    
    def _init_gemini(self):
        """Initialize Gemini AI"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and api_key != "your_gemini_api_key_here":
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.gemini_available = True
                print("✅ Gemini AI initialized")
            else:
                print("⚠️  Gemini API key not configured")
        except Exception as e:
            print(f"❌ Gemini initialization error: {e}")
    
    async def process_query(
        self, 
        query: str, 
        user_id: str, 
        session_id: str,
        mode: str = "chat",
        context: Optional[Dict] = None
    ) -> ChatResponse:
        """
        Smart query processing with mode-aware routing
        
        Modes:
        - chat: General conversation
        - tutor: Educational tutoring with examples
        - notes: Generate structured notes
        - quiz: Generate quizzes and questions
        """
        
        start_time = datetime.now()
        
        try:
            # Check if user has documents (session-specific)
            session_user_id = f"{user_id}_{session_id}"
            user_docs = await self.rag_engine.get_user_document_stats(session_user_id)
            has_documents = user_docs.get("total_chunks", 0) > 0
            
            print(f"🔍 Processing query - User: {user_id}, Mode: {mode}, Has docs: {has_documents}")
            
            # Route based on mode and available data
            if mode == "notes":
                if has_documents:
                    print("📝 Notes mode with documents - using RAG")
                    response = await self._process_with_rag(query, session_user_id, mode)
                    source = "rag_notes"
                else:
                    print("📝 Notes mode without documents - using generator")
                    response = await self._generate_notes_response(query, user_id, context)
                    source = "notes_generator"
            elif mode == "quiz":
                if has_documents:
                    print("❓ Quiz mode with documents - using RAG")
                    response = await self._process_with_rag(query, session_user_id, mode)
                    source = "rag_quiz"
                else:
                    print("❓ Quiz mode without documents - using generator")
                    response = await self._generate_quiz_response(query, user_id, context)
                    source = "quiz_generator"
            elif has_documents:
                # If user has documents, try RAG first for most queries
                if self._is_document_query(query) or len(query.split()) <= 10:
                    response = await self._process_with_rag(query, session_user_id, mode)
                    source = "rag"
                    # If RAG doesn't find relevant content, fall back to Gemini with document context
                    if "couldn't find relevant information" in response:
                        response = await self._process_with_gemini_and_docs(query, session_user_id, mode, context)
                        source = "gemini+rag"
                else:
                    response = await self._process_with_gemini(query, user_id, mode, context)
                    source = "gemini"
            else:
                response = await self._process_with_gemini(query, user_id, mode, context)
                source = "gemini"
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            return ChatResponse(
                content=response,
                source=source,
                session_id=session_id,
                user_id=user_id,
                mode=mode,
                metadata={
                    "response_time": response_time,
                    "has_documents": has_documents,
                    "document_chunks": user_docs.get("total_chunks", 0),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            print(f"❌ Query processing error: {e}")
            return ChatResponse(
                content=f"I encountered an error processing your request: {str(e)}",
                source="error",
                session_id=session_id,
                user_id=user_id,
                mode=mode,
                metadata={"error": str(e)}
            )
    
    def _is_document_query(self, query: str) -> bool:
        """Determine if query is about uploaded documents"""
        doc_keywords = [
            "document", "pdf", "file", "uploaded", "notes", "material", "content",
            "what does", "according to", "in the document", "from the file",
            "explain from", "summarize", "key points", "main topics", "topics",
            "discuss", "covered", "mentioned", "this", "these", "chapter",
            "section", "page", "lecture", "study", "course", "subject", "create",
            "generate", "make", "write", "note", "summary", "overview"
        ]
        query_lower = query.lower()
        
        # More aggressive matching for document queries
        has_doc_keywords = any(keyword in query_lower for keyword in doc_keywords)
        
        # If query is short and vague, assume it's about documents if they exist
        is_short_query = len(query.split()) <= 10
        has_question_words = any(word in query_lower for word in ["what", "how", "why", "explain", "tell", "show", "create", "generate", "make", "write"])
        
        # In notes mode, always try to use documents first
        return has_doc_keywords or (is_short_query and has_question_words)
    
    async def _process_with_rag(self, query: str, user_id: str, mode: str) -> str:
        """Process query using RAG with user documents"""
        try:
            # Retrieve relevant chunks (more for comprehensive responses)
            top_k = 10 if mode == "notes" else 5
            relevant_chunks = await self.rag_engine.retrieve_relevant_chunks(
                query=query,
                user_id=user_id,
                top_k=top_k
            )
            
            if not relevant_chunks:
                return "I couldn't find relevant information in your uploaded documents. Try rephrasing your question or check if the content exists in your files."
            
            # Create context from chunks
            context = "\n\n".join([
                f"[From {chunk['source_file']}]: {chunk['content']}"
                for chunk in relevant_chunks
            ])
            
            # Generate response with Gemini if available
            if self.gemini_available:
                prompt = self._create_rag_prompt(query, context, mode)
                response = self.gemini_model.generate_content(prompt)
                
                # Post-process response to improve structure
                if mode == "notes":
                    return self._format_notes_response(response.text)
                else:
                    return response.text
            else:
                # Fallback: structured response without AI
                return self._format_rag_fallback(query, relevant_chunks)
                
        except Exception as e:
            return f"Error processing with documents: {str(e)}"
    
    def _format_notes_response(self, response: str) -> str:
        """Format RAG response for better structure in notes mode"""
        try:
            # Remove excessive asterisks and improve structure
            formatted = response
            
            # Replace markdown with HTML for better rendering
            formatted = formatted.replace('**', '')
            formatted = formatted.replace('*', '')
            
            # Add proper structure if not present
            if not any(heading in formatted.lower() for heading in ['definition', 'examples', 'applications']):
                # Try to add structure based on content
                lines = formatted.split('\n')
                structured_content = []
                
                current_section = ""
                for line in lines:
                    line = line.strip()
                    if line:
                        if len(line) < 100 and ':' not in line and not line.startswith('-'):
                            # Likely a heading
                            structured_content.append(f"\n<h3>{line}</h3>\n")
                        else:
                            structured_content.append(line)
                
                formatted = '\n'.join(structured_content)
            
            return formatted
            
        except Exception as e:
            print(f"Error formatting notes response: {e}")
            return response
    
    async def _process_with_gemini(
        self, 
        query: str, 
        user_id: str, 
        mode: str,
        context: Optional[Dict] = None
    ) -> str:
        """Process query using Gemini AI with enhanced context"""
        
        if not self.gemini_available:
            return """I'm running in limited mode without full AI capabilities.

To unlock complete StudyMate features:
1. Configure your Gemini API key in the .env file
2. Restart the application
3. Enjoy AI-powered tutoring, explanations, and note generation!

For now, you can still upload documents and I'll help you search through them."""

        try:
            prompt = self._create_enhanced_gemini_prompt(query, mode, context, user_id)
            response = self.gemini_model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"AI processing error: {str(e)}"
    
    def _create_rag_prompt(self, query: str, context: str, mode: str) -> str:
        """Create optimized prompt for RAG responses"""
        
        mode_instructions = {
            "chat": "Provide a conversational, helpful response",
            "tutor": "Act as an educational tutor. Explain concepts clearly with examples, break down complex topics, and encourage learning",
            "notes": "Create structured, well-organized notes with headings and bullet points",
            "quiz": "Generate relevant questions and explanations based on the content"
        }
        
        instruction = mode_instructions.get(mode, mode_instructions["chat"])
        
        return f"""You are StudyMate AI, a personalized learning companion. {instruction}.

Based on the following content from the user's study materials, answer their question:

CONTEXT FROM DOCUMENTS:
{context}

STUDENT'S QUESTION: {query}

Please provide a comprehensive, educational response that:
1. Directly answers the question using the provided context
2. Explains concepts in simple, clear terms
3. Uses examples when helpful
4. Connects ideas to broader learning objectives
5. Encourages further exploration of the topic

If the context doesn't fully answer the question, mention what additional information would be helpful."""
    
    def _create_enhanced_gemini_prompt(
        self, 
        query: str, 
        mode: str, 
        context: Optional[Dict],
        user_id: str
    ) -> str:
        """Create enhanced prompt with conversation context"""
        
        base_prompt = "You are StudyMate AI, a personalized learning companion for students worldwide."
        
        mode_prompts = {
            "chat": f"{base_prompt} Engage in helpful, educational conversation. Provide well-structured responses with clear explanations.",
            "tutor": f"{base_prompt} Act as an expert tutor. Explain concepts step-by-step with examples, analogies, and encourage learning through detailed breakdowns.",
            "notes": f"{base_prompt} Generate comprehensive, well-structured study notes with clear headings, bullet points, numbered lists, and examples.",
            "quiz": f"{base_prompt} Create educational quizzes, practice questions, and learning assessments based on the conversation context."
        }
        
        prompt = mode_prompts.get(mode, mode_prompts["chat"])
        
        # Add conversation history for context
        if context and context.get('chat_history'):
            chat_history = context['chat_history']
            if chat_history:
                prompt += "\n\n**CONVERSATION HISTORY:**\n"
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    role = "Student" if msg['role'] == 'user' else "StudyMate"
                    prompt += f"{role}: {msg['content']}\n"
                prompt += "\n"
        
        # Add conversation context
        if context and context.get('conversation_context'):
            conv_context = context['conversation_context']
            if conv_context.get('keywords'):
                prompt += f"**TOPICS DISCUSSED:** {', '.join(conv_context['keywords'][:10])}\n"
        
        prompt += f"\n**CURRENT QUESTION:** {query}\n"
        
        # Add formatting instructions
        prompt += "\n**RESPONSE FORMATTING REQUIREMENTS:**\n"
        prompt += "- Use clear headings (## for main topics, ### for subtopics)\n"
        prompt += "- Use bullet points (-) for lists\n"
        prompt += "- Use numbered lists (1.) for steps or sequences\n"
        prompt += "- Use **bold** for important terms\n"
        prompt += "- Use *italics* for emphasis\n"
        prompt += "- Include examples and analogies when helpful\n"
        prompt += "- Structure your response logically with clear sections\n"
        
        # Add mode-specific instructions
        if mode == "tutor":
            prompt += "\n**TUTORING APPROACH:**\n"
            prompt += "- Break down complex concepts into simple steps\n"
            prompt += "- Use analogies and real-world examples\n"
            prompt += "- Include visual descriptions and diagrams when helpful\n"
            prompt += "- Suggest relevant images, charts, or diagrams that would aid understanding\n"
            prompt += "- When explaining scientific concepts, mathematical formulas, or processes, describe visual representations\n"
            prompt += "- For complex topics, suggest creating mind maps, flowcharts, or concept diagrams\n"
            prompt += "- Include ASCII art or simple text diagrams when appropriate\n"
            prompt += "- Break down complex concepts into simple steps\n"
            prompt += "- Provide real-world examples and analogies\n"
            prompt += "- Ask rhetorical questions to engage thinking\n"
            prompt += "- Build on previous conversation context\n"
            prompt += "- Encourage further questions and exploration\n"
            
            # Special handling for study plan queries
            if "study plan" in query.lower() or "schedule" in query.lower() or "timetable" in query.lower():
                prompt += "\n**STUDY PLAN REQUIREMENTS:**\n"
                prompt += "- Provide a comprehensive study plan with clear objectives\n"
                prompt += "- Include a detailed weekly/daily timetable in HTML table format\n"
                prompt += "- Specify time slots, subjects, and activities\n"
                prompt += "- Add break times and review sessions\n"
                prompt += "- Make the timetable realistic and achievable\n"
                prompt += "- Use proper HTML table structure with headers and styling\n"
        elif mode == "notes":
            prompt += "\n**NOTES FORMAT:**\n"
            prompt += "- Create comprehensive study notes from our conversation\n"
            prompt += "- Include all key concepts discussed\n"
            prompt += "- Use clear hierarchical structure with HTML headings\n"
            prompt += "- Add summary and key takeaways\n"
            prompt += "- Make it suitable for review and study\n"
            prompt += "- For large documents (80+ pages), provide 5-6 page comprehensive summaries\n"
            prompt += "- Include ALL important concepts in simplified manner\n"
            prompt += "- Structure: Heading → Definition → Examples → Applications → Technologies → Use Cases\n"
            prompt += "- Use HTML formatting instead of markdown asterisks\n"
            prompt += "- Avoid excessive use of asterisks (*) in formatting\n"
        elif mode == "quiz":
            prompt += "\n**QUIZ CREATION:**\n"
            prompt += "- Generate questions based on our conversation topics\n"
            prompt += "- Include multiple choice, short answer, and essay questions\n"
            prompt += "- Provide detailed explanations for answers\n"
            prompt += "- Vary difficulty levels from basic to advanced\n"
        
        return prompt
    
    def _create_gemini_prompt(
        self, 
        query: str, 
        mode: str, 
        context: Optional[Dict],
        user_id: str
    ) -> str:
        """Create optimized prompt for general Gemini responses (legacy)"""
        return self._create_enhanced_gemini_prompt(query, mode, context, user_id)
    
    def _format_rag_fallback(self, query: str, chunks: List[Dict]) -> str:
        """Format RAG response when Gemini is not available"""
        
        response = f"**Based on your uploaded documents:**\n\n"
        response += f"**Question:** {query}\n\n"
        response += "**Relevant Information Found:**\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            source = Path(chunk['source_file']).name
            content = chunk['content'][:500] + "..." if len(chunk['content']) > 500 else chunk['content']
            response += f"**{i}. From {source}:**\n{content}\n\n"
        
        response += "---\n*For AI-powered analysis and explanations, please configure your Gemini API key.*"
        
        return response
    
    async def _generate_notes_response(
        self, 
        query: str, 
        user_id: str, 
        context: Optional[Dict]
    ) -> str:
        """Generate structured notes"""
        return await self.notes_generator.generate_notes(
            topic=query,
            user_id=user_id,
            context=context,
            gemini_model=self.gemini_model if self.gemini_available else None
        )
    
    async def _generate_quiz_response(
        self, 
        query: str, 
        user_id: str, 
        context: Optional[Dict]
    ) -> str:
        """Generate quiz questions"""
        if not self.gemini_available:
            return "Quiz generation requires AI capabilities. Please configure your Gemini API key."
        
        prompt = f"""Generate a comprehensive quiz based on: {query}

Create 5-10 questions with:
1. Multiple choice questions with 4 options each
2. Clear explanations for correct answers
3. Difficulty levels (easy, medium, hard)
4. Learning objectives for each question

Format as an interactive quiz that helps students learn."""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Quiz generation error: {str(e)}"
    
    # Document management methods
    async def process_document(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Process uploaded document"""
        try:
            # Extract text
            text_content = await self.document_processor.extract_text_from_bytes(
                file_content, filename
            )
            
            if not text_content:
                return {
                    "success": False,
                    "message": "Could not extract text from file",
                    "file_info": {"filename": filename, "size": len(file_content)}
                }
            
            # Process with RAG (session-specific)
            session_user_id = f"{user_id}_{session_id}"
            result = await self.rag_engine.add_document(
                text_content=text_content,
                filename=filename,
                user_id=session_user_id
            )
            
            return {
                "success": result["success"],
                "message": f"Successfully processed {filename}",
                "file_info": {
                    "filename": filename,
                    "size": len(file_content),
                    "text_length": len(text_content)
                },
                "chunks_created": result.get("chunks_created", 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing {filename}: {str(e)}",
                "file_info": {"filename": filename, "size": len(file_content)}
            }
    
    async def get_user_documents(self, user_id: str) -> Dict[str, Any]:
        """Get user's document statistics"""
        return await self.rag_engine.get_user_document_stats(user_id)
    
    async def _process_with_gemini_and_docs(self, query: str, user_id: str, mode: str, context: Optional[Dict] = None) -> str:
        """Process query with Gemini AI using document context"""
        try:
            # Get some document chunks for context
            doc_chunks = await self.rag_engine.retrieve_relevant_chunks(
                query=query,
                user_id=user_id,
                top_k=3
            )
            
            # Build enhanced prompt with document context
            doc_context = ""
            if doc_chunks:
                doc_context = "\n\n**DOCUMENT CONTEXT:**\n"
                for chunk in doc_chunks:
                    source_file = Path(chunk['source_file']).name
                    content = chunk['content'][:800] + "..." if len(chunk['content']) > 800 else chunk['content']
                    doc_context += f"**From {source_file}:**\n{content}\n\n"
            
            # Create enhanced prompt
            base_prompt = self._create_enhanced_gemini_prompt(query, mode, context, user_id)
            enhanced_query = f"""{base_prompt}

{doc_context}

**INSTRUCTIONS:**
- Use the document context above to provide accurate, specific answers
- Reference the documents when relevant
- If the documents don't contain the answer, clearly state that
- Provide comprehensive explanations based on the available information"""

            if not self.gemini_available:
                return "I apologize, but the AI service is currently unavailable. Please try again later."
            
            response = self.gemini_model.generate_content(enhanced_query)
            return response.text if response and response.text else "I couldn't generate a response. Please try rephrasing your question."
            
        except Exception as e:
            print(f"❌ Error processing with Gemini+Docs: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    async def clear_user_documents(self, user_id: str) -> bool:
        """Clear all user documents"""
        return await self.rag_engine.clear_user_documents(user_id)
    
    # Notes and export methods
    async def generate_notes(
        self,
        topic: str,
        user_id: str,
        format_type: str = "markdown",
        detail_level: str = "medium",
        include_examples: bool = True
    ) -> str:
        """Generate comprehensive study notes"""
        return await self.notes_generator.generate_comprehensive_notes(
            topic=topic,
            user_id=user_id,
            format_type=format_type,
            detail_level=detail_level,
            include_examples=include_examples,
            gemini_model=self.gemini_model if self.gemini_available else None
        )
    
    async def export_notes(
        self,
        content: str,
        format_type: str,
        filename: str
    ) -> str:
        """Export notes to file"""
        return await self.notes_generator.export_notes(
            content=content,
            format_type=format_type,
            filename=filename
        )