"""
Supply Chain Risk Monitor — Index Builder + Local Pipeline Test
This file explicitly calls: PERCEPTION, MEMORY, ACTION, DECISION, AGENT.
Run in Colab or locally. Exports bundle/vectors.bin + bundle/meta.json.
"""

import os, json, re, math, time
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np
from tqdm import tqdm

# --- (A) CONFIG ---------------------------------------------------------------
EMBED_DIM = 768  # set to your nomic embedding dimensionality
MODEL_NAME = "nomic-embed-text-v1.5"  # example; change to a model you can run
BUNDLE_DIR = os.path.join("..", "bundle")
os.makedirs(BUNDLE_DIR, exist_ok=True)

# Optionally define critical suppliers for DECISION logic
CRITICAL_SUPPLIERS_THIS_Q = {"Acme Logistics", "ZenCold Chain", "BlueRoute Pharma 3PL"}

# --- (B) UTILITIES ------------------------------------------------------------
def l2_normalize(X: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
    return (X / norms).astype(np.float32)

def cosine_topk(X: np.ndarray, q: np.ndarray, k: int = 8):
    # X: (N, D) normalized, q: (D,) normalized
    scores = X @ q
    idx = np.argpartition(scores, -k)[-k:]
    idx = idx[np.argsort(scores[idx])[::-1]]
    return idx, scores[idx]

def chunk_text(text: str, size: int = 800, overlap: int = 120) -> List[str]:
    text = re.sub(r"\s+", " ", text.strip())
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i+size])
        i += max(1, size - overlap)
    return out

# --- (C) (Mock) PERCEPTION ----------------------------------------------------
# In the Chrome extension, PERCEPTION.js will read the page and detect supplier/location/risk terms.
# Here, we implement a Python mirror for local testing and for query construction.
RISK_KEYWORDS = [
    "temperature", "cold chain", "deviation", "non-compliance", "delay",
    "breakdown", "lead time", "stockout", "damage", "spoilage", "QA audit",
    "QA finding", "GxP", "GDP", "SLA breach", "ambient", "refrigerated"
]

def perceive_from_text(page_text: str) -> Dict[str, Any]:
    # naive detection: pull candidate supplier names (Capitalized tokens) and risk keywords
    suppliers = set(re.findall(r"\b([A-Z][A-Za-z0-9&\-]+(?:\s+[A-Z][A-Za-z0-9&\-]+){0,2})\b", page_text))
    suppliers = {s for s in suppliers if len(s.split()) <= 3 and len(s) >= 3}
    risk_hits = [kw for kw in RISK_KEYWORDS if kw.lower() in page_text.lower()]

    # location heuristic
    locations = set(re.findall(r"\b(India|Mumbai|Bangalore|Cochin|Hyderabad|Delhi|Chennai|Pune)\b", page_text, re.I))

    return {
        "supplier_candidates": list(suppliers),
        "locations": list(locations),
        "risk_keywords_found": risk_hits,
        "query_seed": " ".join(sorted(set(risk_hits + list(locations))))
    }

# --- (D) EMBEDDING (Nomic) ----------------------------------------------------
# We keep it import-guarded so this file can be read without nomic installed.
def embed_texts_nomic(texts: List[str], model_name: str = MODEL_NAME) -> np.ndarray:
    from nomic import embed
    embs = embed.text(texts, model=model_name)
    X = np.array(embs, dtype=np.float32)
    if X.shape[1] != EMBED_DIM:
        raise ValueError(f"Expected dim {EMBED_DIM}, got {X.shape[1]}")
    return l2_normalize(X)

# --- (E) MEMORY: build / load index ------------------------------------------
@dataclass
class MetaRow:
    id: int
    url: str
    supplier: str
    location: str
    date: str
    title: str
    chunk_text: str
    risk_tags: List[str]

class MemoryIndex:
    def __init__(self, vectors: np.ndarray, meta: List[MetaRow]):
        self.X = vectors  # (N, D), L2-normalized
        self.meta = meta

    @classmethod
    def from_bundle(cls, bundle_dir: str, dim: int) -> "MemoryIndex":
        vec_path = os.path.join(bundle_dir, "vectors.bin")
        meta_path = os.path.join(bundle_dir, "meta.json")
        V = np.fromfile(vec_path, dtype=np.float32)
        if V.size % dim != 0:
            raise ValueError("vectors.bin size is not divisible by dim")
        X = V.reshape(-1, dim)
        with open(meta_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        meta = [MetaRow(**r) for r in raw]
        if X.shape[0] != len(meta):
            raise ValueError("vectors count != meta rows")
        return cls(X, meta)

    def search(self, q_vec: np.ndarray, k: int = 8):
        idx, scores = cosine_topk(self.X, q_vec, k)
        rows = [(float(scores[i]), self.meta[int(idx[i])]) for i in range(len(idx))]
        return rows

# --- (F) ACTION: retrieval + risk summarization -------------------------------
def lexical_boost(query: str, text: str) -> int:
    q = set([t for t in re.split(r"\W+", query.lower()) if t])
    hits = sum(1 for t in q if t in text.lower())
    return hits

def retrieve(memory: MemoryIndex, embed_query_fn, query: str, k: int = 8):
    qv = embed_query_fn([query])[0]  # (D,)
    hits = memory.search(qv, max(k * 3, 24))
    # re-rank (semantic + light lexical)
    rescored = []
    for score, m in hits:
        lb = lexical_boost(query, m.chunk_text)
        rescored.append((score + 0.02 * lb, m))
    rescored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in rescored[:k]]

def synthesize_risk_summary(supplier: str, location: str, top_hits: List[MetaRow]) -> Dict[str, Any]:
    tags = []
    evidence = []
    for h in top_hits:
        tags.extend(h.risk_tags or [])
        snippet = h.chunk_text.strip()[:240] + ("…" if len(h.chunk_text) > 240 else "")
        evidence.append({"url": h.url, "title": h.title, "snippet": snippet})
    # de-duplicate & count
    tag_counts = {}
    for t in tags:
        tag_counts[t] = tag_counts.get(t, 0) + 1
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "supplier": supplier,
        "location": location,
        "top_risks": [{"tag": t, "count": c} for t, c in sorted_tags[:6]],
        "evidence": evidence[:6]
    }

# --- (G) DECISION -------------------------------------------------------------
def prioritize(summary: Dict[str, Any]) -> Dict[str, Any]:
    supplier = summary["supplier"]
    priority = "normal"
    if supplier in CRITICAL_SUPPLIERS_THIS_Q:
        priority = "critical"
    if any(t["tag"].lower().startswith("temperature") for t in summary["top_risks"]):
        priority = "critical"
    summary["priority"] = priority
    return summary

# --- (H) AGENT (Python harness) ----------------------------------------------
def agent_run(page_text: str, memory: MemoryIndex, embed_query_fn):
    # PERCEPTION
    perceived = perceive_from_text(page_text)
    # Build a query blending seeds + top supplier candidate if any
    supplier = (perceived["supplier_candidates"][:1] or [""])[0]
    location = (perceived["locations"][:1] or [""])[0]
    query = " ".join(filter(None, [supplier, location, perceived["query_seed"]])).strip() or "cold chain deviation India"
    # ACTION (retrieve)
    hits = retrieve(memory, embed_query_fn, query, k=8)
    # ACTION (synthesize)
    summary = synthesize_risk_summary(supplier or "Unknown Supplier", location or "Unknown", hits)
    # DECISION
    summary = prioritize(summary)
    # AGENT output
    card = {
        "title": "Supplier risk summary",
        "query_used": query,
        **summary
    }
    return card

# --- (I) BUILD + TEST ---------------------------------------------------------
def build_and_export_index(raw_docs: List[Dict[str, str]]):
    """
    raw_docs: list of dicts with fields:
      url, title, supplier, location, date, text, (optional) risk_tags
    """
    # 1) chunk
    rows = []
    for d in raw_docs:
        chunks = chunk_text(d["text"])
        for ch in chunks:
            rows.append({
                "url": d["url"],
                "title": d["title"],
                "supplier": d.get("supplier", ""),
                "location": d.get("location", ""),
                "date": d.get("date", ""),
                "chunk_text": ch,
                "risk_tags": d.get("risk_tags", [])
            })
    # 2) embed
    texts = [r["chunk_text"] for r in rows]
    print(f"Embedding {len(texts)} chunks...")
    X = embed_texts_nomic(texts, MODEL_NAME)  # (N, D) normalized
    # 3) export bundle
    vec_path = os.path.join(BUNDLE_DIR, "vectors.bin")
    X.tofile(vec_path)
    print(f"Exported vectors to {vec_path}")
    meta = []
    for i, r in enumerate(rows):
        meta.append({
            "id": i, "url": r["url"], "supplier": r["supplier"], "location": r["location"],
            "date": r["date"], "title": r["title"], "chunk_text": r["chunk_text"],
            "risk_tags": r["risk_tags"]
        })
    meta_path = os.path.join(BUNDLE_DIR, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    print(f"Exported metadata to {meta_path}")

def demo():
    # --- sample small corpus for demonstration ---
    corpus = [
        {
            "url": "https://news.vendor.example/acme-cold-chain-report",
            "title": "ACME route audit",
            "supplier": "Acme Logistics",
            "location": "Mumbai",
            "date": "2025-04-15",
            "text": "April audit observed temperature deviation during airport handover; corrective action pending. Lead time +18h.",
            "risk_tags": ["Temperature non-compliance", "Lead time deviation"]
        },
        {
            "url": "https://internal.example/supplier-zen-cold",
            "title": "ZenCold monthly performance",
            "supplier": "ZenCold Chain",
            "location": "Hyderabad",
            "date": "2025-03-28",
            "text": "No SLA breach; however, refrigerated lane saw ambient exposure event for 25 minutes in transit from Hyderabad.",
            "risk_tags": ["Ambient exposure", "SLA risk"]
        },
        {
            "url": "https://supply-chain-news.example/india-logistics-challenges",
            "title": "India cold chain infrastructure report",
            "supplier": "Various",
            "location": "India",
            "date": "2025-03-15",
            "text": "Cold chain infrastructure in India faces challenges with temperature monitoring, especially in tier-2 cities. Recent incidents in Pune and Chennai highlight gaps in GDP compliance.",
            "risk_tags": ["Temperature monitoring", "GDP compliance", "Infrastructure"]
        }
    ]
    build_and_export_index(corpus)

    # Load bundle as MEMORY
    print("\n=== Loading Index from Bundle ===")
    memory = MemoryIndex.from_bundle(BUNDLE_DIR, EMBED_DIM)
    print(f"Loaded {len(memory.meta)} vectors")

    # Simulate a page the user is reading
    page_text = """
      Breaking: ACME Logistics faces investigation after reports of cold chain deviation in Mumbai hub.
      Temperature data suggests potential non-compliance during apron transfer.
    """

    # Run the AGENT pipeline (calls all layers)
    print("\n=== Running AGENT Pipeline ===")
    print("Page text:", page_text.strip())
    card = agent_run(page_text, memory, embed_texts_nomic)

    print("\n=== SUPPLIER RISK SUMMARY CARD ===")
    print(json.dumps(card, indent=2))

if __name__ == "__main__":
    demo()

