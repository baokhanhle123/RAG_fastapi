import os
import uuid
import tempfile
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

# ✅ UPDATED IMPORTS - Using PyPDF2 instead of Unstructured
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

# Initialize FastAPI app
app = FastAPI(title="Document QA via RAG - Enhanced", version="1.0.0")

# Global storage for vector databases and document metadata
vector_stores: Dict[str, FAISS] = {}
document_metadata: Dict[str, dict] = {}

# Pydantic models
class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_count: int
    upload_time: str

class QueryRequest(BaseModel):
    document_id: str
    query: str

class QAResponse(BaseModel):
    document_id: str
    query: str
    answer: str
    source_documents: List[dict]

@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200)
):
    """
    Upload and process a document to create vector embeddings.
    Returns a unique document_id for future queries.
    """
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or TXT.")

    # Generate unique document ID
    document_id = str(uuid.uuid4())
    
    # Save file temporarily
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # Load document using PyPDF2 (more reliable)
        if suffix == '.pdf':
            loader = PyPDFLoader(tmp_path)
        else:
            loader = TextLoader(tmp_path, encoding='utf-8')
        
        docs = loader.load()

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(docs)

        # Create embeddings and vector store
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(chunks, embeddings)

        # Store in global storage
        vector_stores[document_id] = vectorstore
        document_metadata[document_id] = {
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "chunks_count": len(chunks),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        }

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="processed",
            chunks_count=len(chunks),
            upload_time=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/query", response_model=QAResponse)
async def query_document(request: QueryRequest):
    """
    Query a previously uploaded document using its document_id.
    """
    # Check if document exists
    if request.document_id not in vector_stores:
        raise HTTPException(
            status_code=404, 
            detail=f"Document with ID {request.document_id} not found. Please upload the document first."
        )

    try:
        # Get the vector store for this document
        vectorstore = vector_stores[request.document_id]
        
        # Create RAG chain
        llm = ChatOpenAI(temperature=0)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
        
        # Execute query
        result = qa_chain.invoke({"query": request.query})
        
        # Format source documents
        source_docs = []
        for doc in result.get("source_documents", []):
            source_docs.append({
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            })
        
        return QAResponse(
            document_id=request.document_id,
            query=request.query,
            answer=result["result"],
            source_documents=source_docs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/documents")
async def list_documents():
    """
    List all uploaded documents with their metadata.
    """
    return {
        "documents": [
            {
                "document_id": doc_id,
                **metadata
            }
            for doc_id, metadata in document_metadata.items()
        ]
    }

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its associated vector store.
    """
    if document_id not in vector_stores:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
    
    # Remove from storage
    del vector_stores[document_id]
    del document_metadata[document_id]
    
    return {"message": f"Document {document_id} deleted successfully."}

@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {
        "message": "Document QA API is running!",
        "endpoints": {
            "upload": "POST /upload - Upload and process documents",
            "query": "POST /query - Query processed documents", 
            "list": "GET /documents - List all documents",
            "delete": "DELETE /documents/{id} - Delete a document"
        }
    }

if __name__ == "__main__":
    target_port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=target_port)