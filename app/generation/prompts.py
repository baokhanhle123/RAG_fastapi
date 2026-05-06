SYSTEM_PROMPT = """You are a precise assistant answering questions about a system manual.

Rules:
- Answer ONLY from the provided context. If the context does not contain the answer, say you do not know.
- Quote or paraphrase faithfully. Do not invent procedures, parameter names, or values.
- Reference sources inline using the bracketed marker [page N] for the page numbers shown in the context.
- Be concise. Prefer numbered steps for procedures.
"""


def build_user_message(question: str, context_blocks: list[str]) -> str:
    context = "\n\n".join(context_blocks)
    return f"""Context:
{context}

Question: {question}

Answer:"""


def format_context_block(idx: int, page: int, section_path: list[str], text: str) -> str:
    section = " > ".join(section_path) if section_path else "(no section)"
    return f"[{idx}] page {page} | {section}\n{text}"
