from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv
import shutil
from typing import List, Optional
import uuid
from datetime import datetime
import json
import logging

from services.document_processor import DocumentProcessor
from services.embedding_service import EmbeddingService
from services.groq_service import GroqService
from utils.file_writer import FileWriter
from models.schemas import QueryRequest, QueryResponse, DocumentInfo, UploadResponse
from database.chroma_client import ChromaClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG FastAPI + React Starter",
    description="A complete RAG application with document processing and AI querying",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
chroma_client = ChromaClient()
document_processor = DocumentProcessor()
embedding_service = EmbeddingService()
groq_service = GroqService()
file_writer = FileWriter()

# Create upload directory if it doesn't exist
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting RAG FastAPI application...")
    await chroma_client.initialize()
    logger.info("Application started successfully!")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "RAG FastAPI + React Starter is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    try:
        # Validate file type
        allowed_extensions = {".pdf", ".txt", ".docx", ".md"}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        document_id = str(uuid.uuid4())
        filename = f"{document_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        chunks = await document_processor.process_document(file_path, file.filename)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Failed to process document")
        
        # Generate embeddings and store in Chroma
        embeddings = await embedding_service.generate_embeddings([chunk["text"] for chunk in chunks])
        
        # Store in vector database
        await chroma_client.add_documents(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            metadata={
                "filename": file.filename,
                "file_path": file_path,
                "upload_date": datetime.now().isoformat(),
                "file_size": file.size,
                "file_type": file_extension
            }
        )
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            chunks_processed=len(chunks),
            message="Document uploaded and processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents using RAG."""
    try:
        # Generate query embedding
        query_embedding = await embedding_service.generate_embeddings([request.query])
        
        # Search similar documents
        search_results = await chroma_client.query(
            query_embedding=query_embedding[0],
            n_results=request.max_results or 5
        )
        
        if not search_results or not search_results.get("documents"):
            return QueryResponse(
                query=request.query,
                answer="I couldn't find any relevant information in the uploaded documents.",
                sources=[],
                context_chunks=[]
            )
        
        # Prepare context for LLM
        context_chunks = []
        for i, doc in enumerate(search_results["documents"][0]):
            metadata = search_results.get("metadatas", [[{}]])[0][i] if search_results.get("metadatas") else {}
            context_chunks.append({
                "text": doc,
                "metadata": metadata,
                "score": search_results.get("distances", [[1.0]])[0][i] if search_results.get("distances") else 1.0
            })
        
        # Generate answer using Groq
        context_text = "\n\n".join([chunk["text"] for chunk in context_chunks])
        answer = await groq_service.generate_answer(request.query, context_text)
        
        # Extract unique sources
        sources = list(set([
            chunk["metadata"].get("filename", "Unknown")
            for chunk in context_chunks
            if chunk["metadata"].get("filename")
        ]))
        
        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            context_chunks=context_chunks[:3]  # Return top 3 chunks
        )
        
    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying documents: {str(e)}")

@app.get("/api/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents."""
    try:
        documents = await chroma_client.get_all_documents()
        return [
            DocumentInfo(
                document_id=doc["id"],
                filename=doc["metadata"].get("filename", "Unknown"),
                upload_date=doc["metadata"].get("upload_date", ""),
                file_size=doc["metadata"].get("file_size", 0),
                file_type=doc["metadata"].get("file_type", ""),
                chunks_count=doc.get("chunks_count", 0)
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving documents")

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings."""
    try:
        # Delete from vector database
        await chroma_client.delete_document(document_id)
        
        # Delete physical file
        # Note: In production, you might want to keep files or implement soft delete
        documents = await chroma_client.get_all_documents()
        for doc in documents:
            if doc["id"] == document_id:
                file_path = doc["metadata"].get("file_path")
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                break
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting document")

@app.post("/api/generate-website")
async def generate_website(request: dict):
    """Generate a complete website based on user prompt."""
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Generate website using Groq
        website_data = await groq_service.generate_website(prompt)
        
        if not website_data or "files" not in website_data:
            raise HTTPException(status_code=500, detail="Failed to generate website")
        
        files_data = website_data["files"]
        
        # Validate file paths
        validation_errors = file_writer.validate_file_paths(files_data)
        if validation_errors:
            raise HTTPException(status_code=400, detail=f"Invalid file paths: {', '.join(validation_errors)}")
        
        # Create backup of existing files
        file_writer.backup_existing_files(files_data)
        
        # Write files to filesystem
        write_results = file_writer.write_files(files_data)
        
        return {
            "message": "Website generated successfully",
            "files_written": write_results["files_written"],
            "total_files": write_results["total_files"],
            "errors": write_results["errors"],
            "success": write_results["success"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating website: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating website: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)