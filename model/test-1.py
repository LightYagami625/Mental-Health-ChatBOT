# rag_gemini.py
import os
import json
import math
from typing import List, Dict, Tuple
import numpy as np
import faiss
from google import genai   # google-genai SDK
from dotenv import load_dotenv

# load .env if present
load_dotenv()

# === CONFIG ===
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY environment variable (get key from Google AI Studio).")
# initialize client (client reads GEMINI_API_KEY automatically by default)
client = genai.Client()

EMBED_MODEL = "gemini-embedding-001"   # embeddings model
GEN_MODEL = "gemini-2.5-flash"         # text generation model (example)
TOP_K = 4
INDEX_D = 1536   # choose based on chosen embedding dimensionality (gemini supports flexible dims)

# === Very small crisis detector (conservative) ===
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die", "hurt myself",
    "hang myself", "take my life", "i can't go on", "i'm going to kill myself"
]
def crisis_detector(text: str) -> bool:
    t = text.lower()
    for kw in CRISIS_KEYWORDS:
        if kw in t:
            return True
    return False

# === Helper: simple chunker ===
def chunk_text(text: str, max_chars=1200, overlap=200) -> List[str]:
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(L, start + max_chars)
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0
        if start >= L:
            break
    return chunks

# === Embedding creation (batch) ===
def embed_texts(texts: List[str], batch_size=16) -> List[List[float]]:
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        # call Gemini embed_content per docs
        res = client.models.embed_content(model=EMBED_MODEL, contents=batch)
        # res.embeddings is a list of embedding objects (per docs)
        for emb_obj in res.embeddings:
            embeddings.append(np.array(emb_obj).astype("float32"))
    return embeddings

# === Build FAISS index from documents ===
def build_index(docs: List[Dict]) -> Tuple[faiss.IndexFlatIP, Dict[int, Dict]]:
    # docs: list of {"id":..., "text":..., "meta": {...}}
    texts = [d["text"] for d in docs]
    embs = embed_texts(texts)   # list of np arrays
    # determine dimensionality from first embedding
    dim = embs[0].shape[0]
    index = faiss.IndexFlatIP(dim)   # cosine via inner product requires normalized vectors
    vectors = np.vstack(embs)
    # normalize to unit vectors for cosine similarity
    faiss.normalize_L2(vectors)
    index.add(vectors)
    # map FAISS idx -> doc metadata
    id_map = {i: docs[i] for i in range(len(docs))}
    return index, id_map

# === Retrieve top-k chunks for a query ===
def retrieve(query: str, index: faiss.IndexFlatIP, id_map: Dict[int, Dict], k=TOP_K) -> List[Dict]:
    q_emb = embed_texts([query])[0].astype("float32")
    faiss.normalize_L2(q_emb.reshape(1, -1))
    D, I = index.search(q_emb.reshape(1, -1), k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx == -1:
            continue
        r = id_map[int(idx)].copy()
        r["score"] = float(score)
        results.append(r)
    return results

# === Build prompt using retrieved context ===
def build_prompt(retrieved: List[Dict], user_input: str) -> str:
    ctx_parts = []
    for i, r in enumerate(retrieved, start=1):
        src = r.get("meta", {}).get("source", f"doc#{i}")
        ctx_parts.append(f"[{i}] source: {src}\n{r['text']}\n")
    context_text = "\n---\n".join(ctx_parts)
    system_msg = (
        "You are a supportive assistant. Use ONLY the provided CONTEXT to answer. "
        "If the user expresses immediate self-harm, do NOT provide instructions — escalate."
    )
    prompt = f"{system_msg}\n\nCONTEXT:\n{context_text}\n\nUSER: {user_input}\n\nANSWER (concise, supportive):"
    return prompt

# === Generate with Gemini ===
def generate_from_gemini(prompt: str, max_output_tokens=256) -> str:
    response = client.models.generate_content(
        model=GEN_MODEL,
        contents=prompt,
        max_output_tokens=max_output_tokens
    )
    # per quickstart, response.text returns generated text
    return response.text

# === Example usage (one-time index build) ===
def index_documents_from_files(file_paths: List[str]) -> Tuple[faiss.IndexFlatIP, Dict[int, Dict]]:
    docs = []
    for fid, path in enumerate(file_paths):
        txt = open(path, "r", encoding="utf-8").read()
        chunks = chunk_text(txt)
        for ci, c in enumerate(chunks):
            docs.append({"id": f"{fid}-{ci}", "text": c, "meta": {"source": os.path.basename(path)}})
    index, id_map = build_index(docs)
    return index, id_map

# === Put it together: query handler ===
def handle_user_message(user_msg: str, index, id_map):
    if crisis_detector(user_msg):
        # immediate local escalation
        return ("DETECTED_CRISIS",
                "I detect language that suggests you may be in immediate danger. "
                "Please contact local emergency services, a crisis line, or a trusted person. "
                "Would you like me to provide local hotline numbers or connect you to a human operator?")
    retrieved = retrieve(user_msg, index, id_map, k=TOP_K)
    prompt = build_prompt(retrieved, user_msg)
    gen = generate_from_gemini(prompt)
    # Optionally: run post-check on gen for crisis language / hallucination filters
    return ("OK", gen)

# === Running example (replace with your file paths) ===
if __name__ == "__main__":
    # Example: index two local text files
    file_list = ["dataset/doc1.txt", "dataset/doc2.txt"]  # create or replace
    index, id_map = index_documents_from_files(file_list)
    user = input("You: ")
    status, out = handle_user_message(user, index, id_map)
    if status == "DETECTED_CRISIS":
        print("SYSTEM:", out)
    else:
        print("Assistant:", out)
