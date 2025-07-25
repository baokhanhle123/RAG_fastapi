# 🔍 OpenAI RAG Agent for PCCC Document Querying

This project is a **FastAPI-based Retrieval-Augmented Generation (RAG)** system that allows users to upload PCCC documents (in PDF or TXT format) and ask natural language questions. It uses **LangChain**, **FAISS**, and **OpenAI's GPT** to search and answer questions based on document content.

---

## 📂 Project Structure

| File/Folder                  | Description                                              |
|------------------------------|---------------------------------------------------------|
| `OpenAI_PCCC_Agent.ipynb`    | Original Jupyter Notebook prototype                     |
| `api.py`                     | FastAPI server to handle document upload and RAG query  |
| `request.py`                 | Example client script using `requests`                  |
| `requirements.txt`           | All Python dependencies                                 |
| `*.pdf`                      | Example PCCC documents for testing                      |
| `.env`                       | Environment file to store `OPENAI_API_KEY`              |

---

## ⚙️ 1. Install Requirements

1. **Create and activate your virtual environment** (optional but recommended).

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your OpenAI API key:**
   - Add this to your `.env` file:
     ```bash
     OPENAI_API_KEY=sk-xxxxxx...
     ```
   - *Or* set it manually in your terminal before running:
     ```bash
     export OPENAI_API_KEY=sk-xxxxxx...
     ```

---

## 🚀 2. Run FastAPI Server

Run the FastAPI app using:
```bash
uvicorn api:app --reload
```

You should see the server running at:

📍 http://127.0.0.1:8000

---

## 🧪 3. Try the API via Swagger UI

Visit:  
http://127.0.0.1:8000/docs

There, you can test the `/rag` endpoint by:
- Uploading a PDF or TXT file.
- Typing a question like: `"What are the fire escape requirements?"`
- Optionally tuning:
  - `chunk_size` (default: 1000)
  - `chunk_overlap` (default: 200)

---

## ✅ 4. Query via `curl` or Python

### 🔁 Using curl:

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/rag' \
  -F 'file=@PCCC.pdf' \
  -F 'query=What is the main content of this document?' \
  -F 'chunk_size=1000' \
  -F 'chunk_overlap=200'
```

### 🐍 Using Python:

```python
import requests

files = {'file': open('PCCC.pdf', 'rb')}
data = {
    'query': 'What is the main point?',
    'chunk_size': 1000,
    'chunk_overlap': 200
}
response = requests.post("http://127.0.0.1:8000/rag", files=files, data=data)
print(response.json())
```

---
