import requests
import json

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

def upload_document(file_path, chunk_size=1000, chunk_overlap=200):
    """
    Upload a document and get document_id for future queries.
    """
    print(f"📤 Uploading document: {file_path}")
    
    files = {'file': open(file_path, 'rb')}
    data = {
        'chunk_size': chunk_size, 
        'chunk_overlap': chunk_overlap
    }
    
    response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Filename: {result['filename']}")
        print(f"   Chunks: {result['chunks_count']}")
        print(f"   Status: {result['status']}")
        return result['document_id']
    else:
        print(f"❌ Upload failed: {response.text}")
        return None

def query_document(document_id, query):
    """
    Query a previously uploaded document using its ID.
    """
    print(f"\n❓ Querying document: {query}")
    
    data = {
        "document_id": document_id,
        "query": query
    }
    
    response = requests.post(f"{BASE_URL}/query", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Query successful!")
        print(f"   Answer: {result['answer']}")
        print(f"   Sources: {len(result['source_documents'])} chunks found")
        return result
    else:
        print(f"❌ Query failed: {response.text}")
        return None

def list_documents():
    """
    List all uploaded documents.
    """
    response = requests.get(f"{BASE_URL}/documents")
    if response.status_code == 200:
        result = response.json()
        print(f"📋 Available documents: {len(result['documents'])}")
        for doc in result['documents']:
            print(f"   - {doc['document_id'][:8]}... | {doc['filename']} | {doc['chunks_count']} chunks")
        return result
    else:
        print(f"❌ Failed to list documents: {response.text}")
        return None

# Example usage
if __name__ == "__main__":
    print("🚀 Testing RAG API with separate upload/query endpoints\n")
    
    # Step 1: Upload document
    document_id = upload_document('document/test_PCCC_table.pdf')
    
    if document_id:
        # Step 2: Ask multiple questions without re-uploading
        queries = [
            "Tóm tắt nội dung chính",
            "What are the key requirements?", 
            "Các quy định về an toàn là gì?"
        ]
        
        for query in queries:
            query_document(document_id, query)
            print("-" * 50)
        
        # Step 3: List all documents
        print("\n📋 Listing all documents:")
        list_documents()
