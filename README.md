# Supply Chain Risk Monitor

**A privacy-preserving, local RAG Chrome extension for real-time supplier risk analysis**

## Overview

This Chrome extension uses a 5-layer RAG (Retrieval-Augmented Generation) architecture to surface internal supplier risk intelligence while you browse external news, vendor sites, or internal documents. All processing happens **locally in your browser** - no cloud APIs, no data exfiltration.

### Key Features

✅ **Private & Local** - All retrieval and analysis runs client-side  
✅ **Portable Index** - Single bundle (vectors.bin + meta.json) ships with extension  
✅ **5-Layer Architecture** - Clean separation: PERCEPTION → MEMORY → ACTION → DECISION → AGENT  
✅ **Real-time Analysis** - Instant risk summaries as you browse  
✅ **Customizable** - Easily update critical suppliers, risk keywords, and prioritization rules  

## Architecture

```
┌─────────────┐
│ PERCEPTION  │  Extract supplier/location/risk keywords from page
└──────┬──────┘
       │
┌──────▼──────┐
│   MEMORY    │  Load & search vector index (cosine similarity)
└──────┬──────┘
       │
┌──────▼──────┐
│   ACTION    │  Retrieve chunks, synthesize risk summary
└──────┬──────┘
       │
┌──────▼──────┐
│  DECISION   │  Prioritize based on criticality rules
└──────┬──────┘
       │
┌──────▼──────┐
│   AGENT     │  Orchestrate end-to-end flow
└─────────────┘
```

## Project Structure

```
supply-chain-risk-monitor/
│
├─ index_build/                 # Build index once (Colab or local)
│  ├─ main.py                   # Full 5-layer pipeline + index builder
│  ├─ requirements.txt
│  └─ README.md
│
├─ bundle/                      # Generated index bundle
│  ├─ vectors.bin               # Float32 embeddings (N × D)
│  └─ meta.json                 # Metadata array
│
├─ chrome_ext/                  # Chrome Extension (Manifest V3)
│  ├─ manifest.json
│  ├─ popup.html/js             # UI
│  ├─ PERCEPTION.js             # Layer 1
│  ├─ MEMORY.js                 # Layer 2
│  ├─ ACTION.js                 # Layer 3
│  ├─ DECISION.js               # Layer 4
│  ├─ AGENT.js                  # Layer 5
│  └─ bundle/                   # Copy index here
│
├─ colab_index_builder.py       # Colab-friendly builder script
└─ README.md                    # This file
```

## Quick Start

### 1. Build Index Bundle

**Option A: Local (Python)**

```bash
cd index_build
pip install -r requirements.txt
python main.py
```

This creates `bundle/vectors.bin` and `bundle/meta.json`.

**Option B: Google Colab**

1. Upload `colab_index_builder.py` to Colab
2. Install dependencies: `!pip install nomic numpy`
3. Run the script
4. Download `vectors.bin` and `meta.json`

### 2. Install Chrome Extension

```bash
# Copy index bundle to extension
cp bundle/* chrome_ext/bundle/

# Load in Chrome:
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select chrome_ext/ directory
```

### 3. Use Extension

1. Navigate to any supplier-related page
2. Click extension icon
3. Click "Analyze Current Page"
4. View risk summary with evidence

## Customization

### Add Your Data

Edit `index_build/main.py` → `demo()` function:

```python
corpus = [
    {
        "url": "https://your-source.com/article",
        "title": "Supplier XYZ audit findings",
        "supplier": "XYZ Logistics",
        "location": "Mumbai",
        "date": "2025-04-15",
        "text": "Full article text here...",
        "risk_tags": ["Temperature deviation", "Lead time"]
    },
    # ... more documents
]
```

### Update Critical Suppliers

Edit `chrome_ext/DECISION.js`:

```javascript
const CRITICAL_SUPPLIERS = new Set([
  "Your Critical Supplier 1",
  "Your Critical Supplier 2"
]);
```

### Customize Risk Keywords

Edit `chrome_ext/PERCEPTION.js`:

```javascript
const RISK_KEYWORDS = [
  "your keyword",
  // ... more keywords
];
```

## How It Works

### Index Building (One-time)

1. **Chunk** documents into 800-char segments with 120-char overlap
2. **Embed** chunks using Nomic embeddings (768D)
3. **L2-normalize** vectors for cosine similarity
4. **Export** vectors.bin (Float32Array) + meta.json

### Extension Runtime (Per Query)

1. **PERCEPTION** extracts supplier/location/risks from current page
2. **MEMORY** loads bundle and performs cosine similarity search
3. **ACTION** retrieves top-k chunks, reranks with lexical boost
4. **ACTION** synthesizes risk summary (aggregates tags, creates evidence)
5. **DECISION** prioritizes based on rules (critical supplier, temp risk, etc.)
6. **AGENT** returns structured card to popup UI

## Development

### Test Pipeline Locally

```bash
cd index_build
python main.py
```

This runs the complete 5-layer pipeline in Python and prints a demo risk summary.

### File Roles

| File | Purpose |
|------|---------|
| `index_build/main.py` | Python mirror of 5 layers + index builder |
| `colab_index_builder.py` | Standalone Colab script |
| `chrome_ext/PERCEPTION.js` | Content script: extract page entities |
| `chrome_ext/MEMORY.js` | Load bundle, cosine search |
| `chrome_ext/ACTION.js` | Retrieve & synthesize |
| `chrome_ext/DECISION.js` | Prioritization logic |
| `chrome_ext/AGENT.js` | Background orchestrator |
| `chrome_ext/popup.*` | UI layer |

## Production Recommendations

### 🚀 Performance

- Use ONNX Runtime Web or transformers.js for real embeddings (replace mock in `ACTION.js`)
- Consider FAISS-wasm for larger indices (>10K vectors)
- Lazy-load bundle only when popup opens

### 🔒 Security

- Encrypt bundle files if sensitive
- Add authentication for centralized distribution
- Use Content Security Policy

### 📊 Quality

- Log query/result pairs for ranking improvements
- A/B test lexical boost weight
- Collect user feedback on relevance

### 🔧 Maintenance

- Build incremental index updates (append-only)
- Version bundle format for backward compat
- Monitor bundle size vs load time

## Use Cases

- **Pharma Supply Chain**: Monitor cold chain vendors for temperature deviations
- **Manufacturing**: Track raw material supplier quality issues
- **Logistics**: Alert on carrier delays, port congestion
- **Compliance**: Surface GxP/GDP findings for critical vendors
- **Procurement**: Risk-score suppliers before contract renewal

## Technical Specs

| Component | Technology |
|-----------|-----------|
| Embedding Model | Nomic embed-text-v1.5 (768D) |
| Vector Format | Float32 binary, L2-normalized |
| Search Method | Cosine similarity (dot product) |
| Chunking | 800 chars, 120 overlap |
| Reranking | Semantic + lexical (0.02 weight) |
| Browser API | Chrome Extensions Manifest V3 |

## Troubleshooting

### Bundle mismatch error
- Verify: `vectors.bin` size = N × D × 4 bytes
- Check: `meta.json` array length = N

### No results
- Ensure bundle files exist in `chrome_ext/bundle/`
- Try broader query terms
- Check console for errors

### Slow queries
- Index too large (>50K vectors)? Consider FAISS-wasm
- Check embedding model performance

## License

MIT License - feel free to adapt for your organization.

## Contributing

This is a reference implementation. Contributions welcome:
- Better embedding models
- Improved reranking
- Multi-language support
- Mobile (Firefox, Safari) support

## Cursor Agent Prompt

For AI-assisted development with Cursor, see `CURSOR_AGENT_PROMPT.md` for a structured, reasoning-aware prompt template.

---

**Built for privacy-conscious supply chain teams who need real-time risk intelligence without cloud dependencies.**

