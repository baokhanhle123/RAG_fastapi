"""Smoke-test client for the /ask SSE endpoint.

Run the server first:
    python -m scripts.ingest document/user_manual.pdf
    uvicorn app.main:app --reload

Then:
    python request.py
"""
import json
import sys

import httpx

BASE_URL = "http://127.0.0.1:8000"


def ask(question: str) -> None:
    print(f"\n>>> {question}")
    with httpx.stream(
        "POST",
        f"{BASE_URL}/ask",
        json={"question": question},
        timeout=httpx.Timeout(60.0, read=None),
    ) as response:
        response.raise_for_status()
        event_name = "message"
        for line in response.iter_lines():
            if not line:
                continue
            if line.startswith("event:"):
                event_name = line[6:].strip()
            elif line.startswith("data:"):
                payload = json.loads(line[5:].strip())
                _render(event_name, payload)
    print()


def _render(event: str, payload: dict) -> None:
    if event == "citation":
        print("Sources:")
        for c in payload["citations"]:
            section = " > ".join(c["section_path"]) or "(no section)"
            print(f"  - page {c['page']:>3} | {section}")
        print("\nAnswer:")
    elif event == "token":
        sys.stdout.write(payload["text"])
        sys.stdout.flush()
    elif event == "done":
        return
    elif event == "error":
        print(f"\n[error] {payload['message']}")


if __name__ == "__main__":
    questions = [
        "What is the role of the Collect Agent?",
        "How does the system handle hot-reloading of plugins?",
        "What are the non-functional requirements for server-side data efficiency?",
    ]
    for q in questions:
        ask(q)
