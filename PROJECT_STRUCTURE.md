# Project Structure

Complete file layout and architecture documentation.

## Directory Tree

```
supply-chain-risk-monitor/
│
├── README.md                      # Main project documentation
├── QUICKSTART.md                  # 5-minute getting started guide
├── INSTALLATION.md                # Detailed installation instructions
├── CURSOR_AGENT_PROMPT.md         # AI assistant prompt template
├── AGENT_REVIEW.json              # Structured evaluation of agent prompt
├── PROJECT_STRUCTURE.md           # This file
├── .gitignore                     # Git ignore rules
│
├── index_build/                   # Python index builder (run once)
│   ├── main.py                    # Full 5-layer pipeline + index builder
│   ├── requirements.txt           # Python dependencies
│   └── README.md                  # Index builder docs
│
├── bundle/                        # Generated index bundle (gitignored)
│   ├── vectors.bin               # Float32 embeddings (N × D × 4 bytes)
│   └── meta.json                 # Metadata array
│
├── chrome_ext/                    # Chrome Extension (Manifest V3)
│   ├── manifest.json              # Extension configuration
│   ├── popup.html                 # Extension popup UI
│   ├── popup.js                   # Popup logic
│   ├── PERCEPTION.js              # Layer 1: Entity extraction (content script)
│   ├── MEMORY.js                  # Layer 2: Vector search
│   ├── ACTION.js                  # Layer 3: Retrieval & synthesis
│   ├── DECISION.js                # Layer 4: Prioritization
│   ├── AGENT.js                   # Layer 5: Orchestration (service worker)
│   ├── README.md                  # Extension documentation
│   └── bundle/                    # Index bundle (copy from ../bundle/)
│       ├── .gitkeep               # Keep directory in git
│       ├── vectors.bin            # (copied here)
│       └── meta.json              # (copied here)
│
└── colab_index_builder.py         # Standalone Colab script
```

## File Roles

### Root Level

| File | Purpose | When to Edit |
|------|---------|--------------|
| `README.md` | Project overview, quick start, architecture | Adding features |
| `QUICKSTART.md` | Minimal setup guide for first run | Simplifying onboarding |
| `INSTALLATION.md` | Detailed setup for all platforms | Troubleshooting, new platforms |
| `CURSOR_AGENT_PROMPT.md` | AI assistant instructions | AI development workflow |
| `AGENT_REVIEW.json` | Structured prompt evaluation | Quality assessment |
| `PROJECT_STRUCTURE.md` | This file | Project organization changes |
| `.gitignore` | Files to exclude from git | Adding build artifacts |

### index_build/

| File | Purpose | When to Edit |
|------|---------|--------------|
| `main.py` | Build index + test 5-layer pipeline | Adding data sources, changing chunking |
| `requirements.txt` | Python dependencies | Adding packages |
| `README.md` | Index builder documentation | Build process changes |

### chrome_ext/

| File | Purpose | When to Edit |
|------|---------|--------------|
| `manifest.json` | Extension config (permissions, CSP) | Permissions, version bumps |
| `popup.html` | Extension UI structure | UI layout changes |
| `popup.js` | Popup interaction logic | UI behavior, validation |
| `PERCEPTION.js` | Extract entities from page | Risk keywords, entity patterns |
| `MEMORY.js` | Load/search vector index | Embedding dimension, search logic |
| `ACTION.js` | Retrieve & synthesize | Embedder model, reranking weights |
| `DECISION.js` | Prioritization rules | Critical suppliers, risk thresholds |
| `AGENT.js` | Orchestrate pipeline | Query composition, error handling |
| `README.md` | Extension documentation | Feature additions |

### Standalone

| File | Purpose | When to Edit |
|------|---------|--------------|
| `colab_index_builder.py` | Colab-friendly builder | Colab-specific optimizations |

## Data Flow

### Build Time (Once)

```
Raw Documents (corpus)
    ↓
[index_build/main.py]
    ↓
1. Chunk text (800 chars, 120 overlap)
2. Embed with Nomic (768D)
3. L2-normalize vectors
4. Export bundle
    ↓
bundle/vectors.bin + meta.json
    ↓
(Copy to chrome_ext/bundle/)
```

### Runtime (Per Query)

```
User browses page
    ↓
[PERCEPTION.js] Extract supplier/location/risks
    ↓
[AGENT.js] Compose query
    ↓
[ACTION.js] Embed query (mock or real)
    ↓
[MEMORY.js] Cosine similarity search
    ↓
[ACTION.js] Rerank with lexical boost
    ↓
[ACTION.js] Synthesize risk summary
    ↓
[DECISION.js] Prioritize (critical/normal)
    ↓
[popup.js] Display card
```

## Architecture Layers

### Layer 1: PERCEPTION
- **File**: `PERCEPTION.js`
- **Type**: Content script (runs on every page)
- **Input**: DOM content, page text
- **Output**: Entities (suppliers, locations, risk keywords)
- **Key Functions**:
  - `perceive()`: Extract structured context from page
  - `getSelectionOrText()`: Get relevant text

### Layer 2: MEMORY
- **File**: `MEMORY.js`
- **Type**: ES6 module (loaded by ACTION)
- **Input**: Query vector (Float32Array, 768D)
- **Output**: Top-k results with scores
- **Key Functions**:
  - `initMemory()`: Load bundle (once)
  - `search(qv, k)`: Cosine similarity search
  - `dot()`: Vector dot product
  - `topK()`: Find top-k indices

### Layer 3: ACTION
- **File**: `ACTION.js`
- **Type**: ES6 module (loaded by AGENT)
- **Input**: Query string, top-k param
- **Output**: Risk summary object
- **Key Functions**:
  - `retrieve(query, k)`: Fetch & rerank chunks
  - `synthesizeRiskSummary()`: Aggregate tags & evidence
  - `embedQuery()`: Query → vector (TODO: replace mock)
  - `lexicalBoost()`: Compute term overlap

### Layer 4: DECISION
- **File**: `DECISION.js`
- **Type**: ES6 module (loaded by AGENT)
- **Input**: Supplier name, risk summary
- **Output**: Priority level (critical/high/normal)
- **Key Functions**:
  - `decide()`: Apply prioritization rules
- **Rules**:
  1. Critical supplier → critical
  2. Temperature risk → critical
  3. Compliance risk → critical
  4. Many risks → high

### Layer 5: AGENT
- **File**: `AGENT.js`
- **Type**: Service worker (background)
- **Input**: User query, page context
- **Output**: Final risk card
- **Key Functions**:
  - Message handler: Orchestrate pipeline
  - Error handling & fallbacks

### UI Layer
- **Files**: `popup.html`, `popup.js`
- **Type**: Extension popup
- **Input**: User clicks, query input
- **Output**: Visual risk card
- **Features**:
  - Query input field
  - Analyze button
  - Status messages
  - Styled risk card

## Module Dependencies

```
popup.js
    ↓ (chrome.runtime.sendMessage)
AGENT.js
    ↓ (import)
    ├── ACTION.js
    │       ↓ (import)
    │   MEMORY.js
    │
    └── DECISION.js

PERCEPTION.js (standalone content script)
```

## Build Artifacts

### bundle/vectors.bin
- **Format**: Raw Float32Array binary
- **Size**: N × D × 4 bytes (e.g., 1000 chunks × 768 dims × 4 = 3.1 MB)
- **Encoding**: Little-endian float32
- **Layout**: Row-major (chunk0_dim0, chunk0_dim1, ..., chunk1_dim0, ...)

### bundle/meta.json
- **Format**: JSON array
- **Size**: Depends on text length (typically 100-500 KB)
- **Schema**:
  ```json
  [
    {
      "id": 0,
      "url": "https://...",
      "title": "...",
      "supplier": "...",
      "location": "...",
      "date": "YYYY-MM-DD",
      "chunk_text": "...",
      "risk_tags": ["...", "..."]
    }
  ]
  ```

## Configuration Points

### Embedding Dimension
- **Python**: `index_build/main.py` → `EMBED_DIM = 768`
- **JavaScript**: `chrome_ext/MEMORY.js` → `let D = 768;`
- **Must match** or bundle will fail validation

### Critical Suppliers
- **Python**: `index_build/main.py` → `CRITICAL_SUPPLIERS_THIS_Q`
- **JavaScript**: `chrome_ext/DECISION.js` → `CRITICAL_SUPPLIERS`
- **Keep in sync** for consistent priority logic

### Risk Keywords
- **Python**: `index_build/main.py` → `RISK_KEYWORDS`
- **JavaScript**: `chrome_ext/PERCEPTION.js` → `RISK_KEYWORDS`
- **Customizable** per organization

### Chunk Size
- **Python**: `index_build/main.py` → `chunk_text(size=800, overlap=120)`
- **Trade-off**: Larger = more context, fewer chunks; Smaller = more granular, more chunks

### Retrieval Parameters
- **Top-k**: `ACTION.js` → `retrieve(query, k=8)`
- **Over-fetch**: `ACTION.js` → `Math.max(k*3, 24)`
- **Lexical weight**: `ACTION.js` → `0.02 * lexicalBoost(...)`

## Extension Permissions

From `manifest.json`:

```json
{
  "permissions": ["activeTab", "scripting", "storage"],
  "host_permissions": ["<all_urls>"]
}
```

- `activeTab`: Read current tab URL/title
- `scripting`: Inject content scripts
- `storage`: (Future) Cache settings
- `<all_urls>`: Run on any page

## Security Considerations

### Threat Model

✅ **Protected Against:**
- Data exfiltration (no network calls)
- XSS in bundle (only JSON/binary, no code)
- MITM on retrieval (local only)

⚠️ **Not Protected Against:**
- Malicious bundle files (validate source)
- Physical access to bundle (unencrypted)
- Browser extension compromise (standard Chrome security)

### Best Practices

1. **Validate bundle source**: Only load trusted vectors.bin/meta.json
2. **Content Security Policy**: Strict CSP in manifest.json
3. **Least privilege**: Minimal permissions
4. **Input sanitization**: Escape user queries
5. **Regular updates**: Keep dependencies patched

## Performance Profile

### Initialization (First Use)
- Load meta.json: ~20-50ms (network)
- Load vectors.bin: ~50-200ms (network)
- Parse JSON: ~10-30ms (CPU)
- **Total**: ~100-500ms

### Query (Typical)
- Embed query: ~5-20ms (mock) or ~50-200ms (real model)
- Cosine search: ~10-50ms (CPU, depends on N)
- Rerank: ~5-10ms
- Synthesize: ~5-10ms
- **Total**: ~50-200ms (mock) or ~100-400ms (real)

### Memory Usage
- vectors.bin loaded: ~3-20 MB (typical)
- meta.json loaded: ~0.5-5 MB (typical)
- V8 overhead: ~2-5 MB
- **Total**: ~5-30 MB

## Testing Strategy

### Unit Tests (Future)
- `MEMORY.js`: Test cosine search correctness
- `ACTION.js`: Test lexical boost, synthesis
- `DECISION.js`: Test prioritization rules

### Integration Tests
- End-to-end pipeline: `index_build/main.py` demo()
- Extension flow: Manual testing with test pages

### Performance Tests
- Query latency: Measure with large indices
- Memory leaks: Chrome Task Manager
- Bundle load time: Network throttling

## Extension Lifecycle

1. **Install**: User loads unpacked extension
2. **Service Worker Activation**: AGENT.js starts
3. **Page Load**: PERCEPTION.js injected as content script
4. **User Click**: Popup opens, loads popup.html/js
5. **Analyze**: popup.js → AGENT.js → pipeline → result
6. **Display**: popup.js renders card
7. **Close**: Popup dismissed, service worker may idle
8. **Repeat**: Steps 4-7 on next use

## Versioning

- **manifest.json**: `"version": "1.0.0"`
- **Semantic versioning**: MAJOR.MINOR.PATCH
  - MAJOR: Breaking changes (bundle format, API)
  - MINOR: New features (backward compatible)
  - PATCH: Bug fixes

## Future Enhancements

### Planned
- [ ] Replace mock embedder with transformers.js
- [ ] Add date range filtering
- [ ] Incremental index updates
- [ ] User feedback mechanism

### Potential
- [ ] Multi-language support
- [ ] FAISS-wasm for large indices
- [ ] Collaborative filtering
- [ ] Export reports (PDF, CSV)

---

**This structure supports:**
- ✅ Clean separation of concerns
- ✅ Easy customization
- ✅ Testability
- ✅ Performance optimization
- ✅ Security best practices

