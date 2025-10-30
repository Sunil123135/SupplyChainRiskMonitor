# Quick Start Guide

**Get the Supply Chain Risk Monitor running in 5 minutes**

## Prerequisites

- Python 3.8+ (for index building)
- Chrome or Edge browser
- Basic command line knowledge

## Step 1: Clone/Download Project

```bash
# If you have this project, navigate to it
cd supply-chain-risk-monitor
```

## Step 2: Build Index (Choose One)

### Option A: Local Python (Recommended for First Test)

```bash
cd index_build
pip install -r requirements.txt
python main.py
```

**Output:**
```
Embedding 6 chunks...
Exported vectors to ../bundle/vectors.bin
Exported metadata to ../bundle/meta.json
...
✓ SUPPLIER RISK SUMMARY CARD
```

### Option B: Google Colab (For Custom Data)

1. Open [Google Colab](https://colab.research.google.com/)
2. Upload `colab_index_builder.py`
3. Run:
   ```python
   !pip install nomic numpy
   # Then run the script
   ```
4. Download `vectors.bin` and `meta.json`

## Step 3: Install Chrome Extension

```bash
# Copy bundle to extension
cp bundle/vectors.bin chrome_ext/bundle/
cp bundle/meta.json chrome_ext/bundle/

# Or on Windows:
# copy bundle\vectors.bin chrome_ext\bundle\
# copy bundle\meta.json chrome_ext\bundle\
```

**Load in Chrome:**

1. Open Chrome → `chrome://extensions/`
2. Toggle **"Developer mode"** (top right)
3. Click **"Load unpacked"**
4. Select the `chrome_ext/` folder
5. Pin the extension (puzzle icon → pin)

## Step 4: Test It Out

1. Navigate to a test page (or create one):
   ```html
   <!-- test.html -->
   <h1>Breaking: Acme Logistics Cold Chain Issues in Mumbai</h1>
   <p>Temperature deviations reported during shipment handling...</p>
   ```

2. Click the extension icon

3. Click **"Analyze Current Page"**

4. View the risk summary:
   - Priority level
   - Supplier & location
   - Top risk factors
   - Evidence with sources

## Troubleshooting

### "Failed to load meta.json"
✅ **Fix:** Ensure bundle files are in `chrome_ext/bundle/`
```bash
ls chrome_ext/bundle/
# Should show: vectors.bin  meta.json
```

### "Bundle mismatch" error
✅ **Fix:** Rebuild index
```bash
cd index_build
python main.py
```

### No results shown
✅ **Fix:** Try a more specific query in the search box:
```
Acme temperature Mumbai
```

### Extension won't load
✅ **Fix:** Check Manifest V3 compatibility
- Chrome 88+ or Edge 88+
- Check browser console (F12) for errors

## Next Steps

### Customize for Your Organization

1. **Add your data** → Edit `index_build/main.py`:
   ```python
   corpus = [
       {
           "url": "https://your-source.com/doc",
           "title": "Your Document",
           "supplier": "Your Supplier",
           "location": "Your Location",
           "date": "2025-04-15",
           "text": "Full text here...",
           "risk_tags": ["Your Risk Tag"]
       }
   ]
   ```

2. **Update critical suppliers** → Edit `chrome_ext/DECISION.js`:
   ```javascript
   const CRITICAL_SUPPLIERS = new Set([
       "Your Critical Supplier"
   ]);
   ```

3. **Rebuild index:**
   ```bash
   cd index_build
   python main.py
   cp ../bundle/* ../chrome_ext/bundle/
   ```

4. **Reload extension** → `chrome://extensions/` → Click reload icon

## Performance Tips

- Index size < 10K vectors: ~100ms queries
- Index size > 50K vectors: Consider FAISS optimization
- First load takes 100-500ms (bundle load)
- Subsequent queries: 50-200ms

## Support

- 📖 Full docs: `README.md`
- 🏗️ Architecture: `chrome_ext/README.md`
- 🤖 AI prompt: `CURSOR_AGENT_PROMPT.md`
- 📊 Review: `AGENT_REVIEW.json`

---

**You're now monitoring supplier risks in real-time! 🎉**

