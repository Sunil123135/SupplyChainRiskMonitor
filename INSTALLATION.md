# Installation Guide

Complete installation instructions for all platforms.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Setup](#python-setup)
3. [Building the Index](#building-the-index)
4. [Chrome Extension Setup](#chrome-extension-setup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### For Index Building

- **Python**: 3.8 or higher
- **RAM**: 4 GB minimum (8 GB recommended for large corpora)
- **Disk Space**: 500 MB for dependencies + corpus size
- **Internet**: Required for initial package downloads

### For Chrome Extension

- **Browser**: Chrome 88+ or Edge 88+ (Manifest V3 support)
- **Disk Space**: ~5-20 MB (depends on index size)
- **Internet**: Not required for extension operation (local only)

---

## Python Setup

### 1. Check Python Version

```bash
python --version
# or
python3 --version
```

Should show: `Python 3.8.x` or higher

### 2. Create Virtual Environment (Recommended)

**Linux/macOS:**
```bash
cd supply-chain-risk-monitor/index_build
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
cd supply-chain-risk-monitor\index_build
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected packages:**
- `faiss-cpu`: Vector similarity search
- `nomic`: Embedding model
- `numpy`: Numerical operations
- `tqdm`: Progress bars
- `beautifulsoup4`: HTML parsing (optional)
- `requests`: HTTP requests (optional)

---

## Building the Index

### Option 1: Local Build (Demo Data)

```bash
cd supply-chain-risk-monitor/index_build
python main.py
```

**Expected Output:**
```
Embedding 6 chunks...
✓ Exported vectors to ../bundle/vectors.bin
✓ Exported metadata to ../bundle/meta.json
Loaded 6 vectors

=== Running AGENT Pipeline ===
...
✓ SUPPLIER RISK SUMMARY CARD
{
  "title": "Supplier risk summary",
  "query_used": "Acme Logistics Mumbai cold chain deviation temperature",
  "supplier": "Acme Logistics",
  "location": "Mumbai",
  "priority": "critical",
  ...
}
```

### Option 2: Google Colab (Custom Data)

1. **Upload Script**
   - Go to [colab.research.google.com](https://colab.research.google.com/)
   - Upload `colab_index_builder.py`

2. **Install Dependencies**
   ```python
   !pip install nomic numpy
   ```

3. **Customize Data**
   - Edit the `get_demo_corpus()` function
   - Add your organization's supplier documents

4. **Run Script**
   ```python
   main()
   ```

5. **Download Bundle**
   - Files will auto-download in Colab
   - Save `vectors.bin` and `meta.json`

### Option 3: Production Build (Your Data)

1. **Prepare Data Source**
   - CSV, JSON, database, API, etc.
   - Required fields: url, title, supplier, location, date, text, risk_tags

2. **Edit main.py**
   ```python
   def load_your_data():
       # Your data loading logic
       return [
           {
               "url": "...",
               "title": "...",
               "supplier": "...",
               "location": "...",
               "date": "YYYY-MM-DD",
               "text": "...",
               "risk_tags": [...]
           }
       ]
   
   # Replace demo() corpus with:
   corpus = load_your_data()
   ```

3. **Build**
   ```bash
   python main.py
   ```

---

## Chrome Extension Setup

### 1. Copy Bundle Files

**Linux/macOS:**
```bash
cd supply-chain-risk-monitor
cp bundle/vectors.bin chrome_ext/bundle/
cp bundle/meta.json chrome_ext/bundle/
```

**Windows:**
```cmd
cd supply-chain-risk-monitor
copy bundle\vectors.bin chrome_ext\bundle\
copy bundle\meta.json chrome_ext\bundle\
```

**Verify:**
```bash
ls chrome_ext/bundle/
# Should show: .gitkeep  meta.json  vectors.bin
```

### 2. Load Extension in Chrome

1. **Open Extensions Page**
   - Navigate to `chrome://extensions/`
   - Or: Menu → Extensions → Manage Extensions

2. **Enable Developer Mode**
   - Toggle switch in top-right corner

3. **Load Unpacked Extension**
   - Click "Load unpacked" button
   - Navigate to `supply-chain-risk-monitor/chrome_ext/`
   - Click "Select Folder"

4. **Verify Installation**
   - Extension should appear in the list
   - Status: "Enabled"
   - No errors shown

5. **Pin Extension (Optional)**
   - Click puzzle icon (Extensions) in toolbar
   - Click pin icon next to "Supply Chain Risk Monitor"

---

## Verification

### Test Extension

1. **Create Test Page**
   ```html
   <!DOCTYPE html>
   <html>
   <head><title>Test Page</title></head>
   <body>
     <h1>Acme Logistics Cold Chain Issues in Mumbai</h1>
     <p>Temperature deviations reported during shipment handling.
        The cold chain was compromised during airport transfer...</p>
   </body>
   </html>
   ```

2. **Open Test Page**
   - Save as `test.html`
   - Open in Chrome: `File → Open File...`

3. **Run Analysis**
   - Click extension icon
   - Click "Analyze Current Page"
   - Should show risk summary with:
     - Priority: Critical
     - Supplier: Acme Logistics
     - Location: Mumbai
     - Risks: Temperature non-compliance, etc.

### Check Console (Optional)

1. Press `F12` to open DevTools
2. Click "Console" tab
3. Look for:
   ```
   ✓ Supply Chain Risk Monitor - PERCEPTION layer loaded
   ✓ Supply Chain Risk Monitor - MEMORY layer loaded
   ✓ Supply Chain Risk Monitor - ACTION layer loaded
   ✓ Supply Chain Risk Monitor - DECISION layer loaded
   ✓ Supply Chain Risk Monitor - AGENT layer loaded
   ✓ MEMORY loaded: 6 vectors (768D), 18.4 KB
   ```

---

## Troubleshooting

### Python Issues

#### ImportError: No module named 'nomic'
```bash
pip install nomic
# or
pip install -r requirements.txt
```

#### FAISS installation fails
```bash
# Try CPU-only version
pip install faiss-cpu --no-cache-dir

# On Apple Silicon:
conda install -c conda-forge faiss-cpu
```

#### numpy version conflicts
```bash
pip install --upgrade numpy
```

### Extension Issues

#### "Failed to load extension"
- **Check manifest.json syntax** (use JSON validator)
- **Verify all files exist** in chrome_ext/
- **Check Chrome version** (need 88+)

#### "Failed to load meta.json"
- **Ensure bundle files copied** to chrome_ext/bundle/
- **Check file permissions** (readable)
- **Verify file sizes** (not zero bytes)

#### "Bundle mismatch" error
- **Rebuild index**: `cd index_build && python main.py`
- **Re-copy files** to chrome_ext/bundle/
- **Check vectors.bin size**: Should be N × 768 × 4 bytes

#### Extension icon doesn't appear
- **Refresh extension**: chrome://extensions/ → Reload icon
- **Check errors tab** in chrome://extensions/
- **Verify manifest.json** has "action" field

### Performance Issues

#### Slow queries (>1 second)
- **Check index size**: Large vectors.bin (>50 MB)?
- **Consider FAISS optimization** for >10K vectors
- **Verify bundle not re-loading**: Check console for repeated "MEMORY loaded" messages

#### High memory usage
- **Check for memory leaks**: Chrome Task Manager → Shift+Esc
- **Reduce index size**: Fewer chunks or lower dimension
- **Close unused tabs**

### Data Issues

#### No results returned
- **Check query**: Try broader terms
- **Verify bundle loaded**: Check console
- **Inspect meta.json**: Ensure non-empty chunks

#### Wrong results
- **Review embedding quality**: Test with Python harness
- **Adjust lexical boost**: Edit ACTION.js (0.02 weight)
- **Check risk_tags**: Verify in meta.json

---

## Platform-Specific Notes

### Windows

- Use backslashes in paths: `chrome_ext\bundle\`
- Activate venv: `venv\Scripts\activate`
- Use `python` instead of `python3`

### macOS

- May need to install Xcode Command Line Tools:
  ```bash
  xcode-select --install
  ```
- Use `python3` explicitly

### Linux

- Install Python dev headers if needed:
  ```bash
  # Debian/Ubuntu
  sudo apt install python3-dev
  
  # Fedora/RHEL
  sudo dnf install python3-devel
  ```

---

## Next Steps

- ✅ Installation complete → See [QUICKSTART.md](QUICKSTART.md)
- 🔧 Customize data → See [README.md](README.md)
- 🤖 AI development → See [CURSOR_AGENT_PROMPT.md](CURSOR_AGENT_PROMPT.md)

---

**Need help?** Check the main README.md or open an issue.

