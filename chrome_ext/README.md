# Supply Chain Risk Monitor - Chrome Extension

A local, privacy-preserving RAG extension that surfaces internal supplier risk data while browsing external news.

## Architecture: 5-Layer RAG System

1. **PERCEPTION.js** - Extracts supplier names, locations, and risk keywords from the current page
2. **MEMORY.js** - Loads and searches the local vector index bundle (vectors.bin + meta.json)
3. **ACTION.js** - Retrieves relevant chunks and synthesizes risk summaries
4. **DECISION.js** - Prioritizes risks based on criticality rules
5. **AGENT.js** - Orchestrates the complete pipeline (background service worker)

## Setup

### Prerequisites
- Google Chrome browser (Manifest V3 support required)
- Index bundle files (vectors.bin + meta.json)

### Generate Index Bundle

**Option 1: Local**
```bash
cd ../index_build
pip install -r requirements.txt
python main.py
```

**Option 2: Google Colab**
1. Upload `colab_index_builder.py` to Colab
2. Run the notebook
3. Download `vectors.bin` and `meta.json`

### Install Extension

1. Copy index files:
   ```bash
   cp ../bundle/vectors.bin ./bundle/
   cp ../bundle/meta.json ./bundle/
   ```

2. Load in Chrome:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `chrome_ext/` directory

3. Pin the extension to your toolbar

## Usage

1. Navigate to any supplier-related page (news article, internal doc, etc.)
2. Click the extension icon
3. (Optional) Enter a custom query to refine search
4. Click "Analyze Current Page"
5. View risk summary with priority, top risks, and evidence

## Customization

### Update Critical Suppliers
Edit `DECISION.js`:
```javascript
const CRITICAL_SUPPLIERS = new Set([
  "Your Supplier Name",
  "Another Critical Vendor"
]);
```

### Change Embedding Dimension
If using a different embedding model, update `D` in `MEMORY.js`:
```javascript
let D = 768;  // Change to your model's dimension
```

### Add Risk Keywords
Edit `PERCEPTION.js`:
```javascript
const RISK_KEYWORDS = [
  "your custom keyword",
  // ... more keywords
];
```

## Troubleshooting

### "Bundle mismatch" error
- Ensure `vectors.bin` size = (number of chunks) × (dimension) × 4 bytes
- Verify `meta.json` has same number of entries as chunks
- Rebuild index with correct dimension

### No results returned
- Check if bundle files exist in `chrome_ext/bundle/`
- Verify files are not corrupted (check file sizes)
- Try a more specific query

### Extension not loading
- Verify Manifest V3 compatibility
- Check browser console for errors (F12)
- Ensure all `.js` files are present

## Development

### Testing Locally
Use the Python test harness:
```bash
cd ../index_build
python main.py
```

This runs the same 5-layer pipeline in Python to verify logic.

### File Structure
```
chrome_ext/
├── manifest.json          # Chrome extension config
├── popup.html/js          # UI
├── PERCEPTION.js          # Layer 1: Entity extraction
├── MEMORY.js              # Layer 2: Vector search
├── ACTION.js              # Layer 3: Retrieval & synthesis
├── DECISION.js            # Layer 4: Prioritization
├── AGENT.js               # Layer 5: Orchestration
└── bundle/
    ├── vectors.bin        # Embedding vectors
    └── meta.json          # Metadata
```

## Privacy & Security

✅ **All processing happens locally** - no data leaves your browser
✅ **No external API calls** for retrieval
✅ **Index bundle is private** - contains only your organization's data
⚠️ **Bundle is unencrypted** - ensure appropriate file permissions

## Performance

- Index load time: ~100-500ms (one-time on first use)
- Query time: ~50-200ms (depends on index size)
- Memory usage: ~5-20 MB (depends on corpus size)

## Production Recommendations

1. **Replace mock embedder**: Use transformers.js or ONNX Runtime Web in `ACTION.js`
2. **Add authentication**: Protect bundle access if deploying centrally
3. **Incremental updates**: Build pipeline to update bundle without full rebuild
4. **A/B testing**: Log query/result pairs for ranking improvements
5. **Monitoring**: Add telemetry for performance and quality metrics

