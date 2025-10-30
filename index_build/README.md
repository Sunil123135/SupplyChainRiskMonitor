# Index Builder

This directory contains the Python code to build the vector index bundle for the Supply Chain Risk Monitor extension.

## Overview

The `main.py` script implements the complete 5-layer RAG pipeline:
- **PERCEPTION**: Extract supplier/location/risk keywords from text
- **MEMORY**: Build and load vector index with cosine similarity search
- **ACTION**: Retrieve relevant chunks and synthesize risk summaries
- **DECISION**: Prioritize risks based on criticality
- **AGENT**: Orchestrate the entire flow end-to-end

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Local Build
```bash
python main.py
```

This will:
1. Create sample supplier documents
2. Chunk and embed them using Nomic embeddings
3. Export `../bundle/vectors.bin` and `../bundle/meta.json`
4. Run a demo query showing the complete pipeline

### Output
- `../bundle/vectors.bin`: Float32 array of L2-normalized embeddings (N × D)
- `../bundle/meta.json`: Array of metadata objects with supplier, location, risk tags, etc.

## Customization

Edit `main.py` to:
- Add your own corpus in the `demo()` function
- Change `EMBED_DIM` if using a different embedding model
- Update `CRITICAL_SUPPLIERS_THIS_Q` for your organization
- Modify risk keywords in `RISK_KEYWORDS`

## Next Steps

After building the index:
1. Copy `bundle/vectors.bin` and `bundle/meta.json` to `chrome_ext/bundle/`
2. Install the Chrome extension
3. Test on real supplier pages

