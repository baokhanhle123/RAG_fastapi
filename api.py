from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import tempfile
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ✅ UPDATED IMPORTS
from langchain_community.document_loaders import UnstructuredPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA

# Initialize FastAPI app
target_port = int(os.getenv("PORT", 8000))
app = FastAPI(title="Document QA via RAG")

# Pydantic model for responses
class QAResponse(BaseModel):
    query: str
    answer: str
    source_documents: Optional[list]

@app.post("/rag", response_model=QAResponse)
async def rag_endpoint(
    file: UploadFile = File(...),
    query: str = Form(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200)
):
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or TXT.")

    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    # Load document
    loader = UnstructuredPDFLoader(tmp_path) if suffix == '.pdf' else TextLoader(tmp_path, encoding='utf8')
    docs = loader.load()

    # Chunk text
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)

    # Vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # RAG Chain
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(),
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )

    result = qa({"query": query})
    answer = result.get("result") or result.get("answer")
    sources = [
        {
            "snippet": doc.page_content[:200].replace('\n', ' '),
            "metadata": doc.metadata
        }
        for doc in result.get("source_documents", [])
    ]

    os.remove(tmp_path)

    return JSONResponse(content={
        "query": query,
        "answer": answer,
        "source_documents": sources
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=target_port)
