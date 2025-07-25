import requests

files = {'file': open('test_PCCC_table.pdf', 'rb')}
data = {'query': 'Tóm tắt', 'chunk_size': 1000, 'chunk_overlap': 200}
response = requests.post("http://127.0.0.1:8000/rag", files=files, data=data)
print(response.json())
