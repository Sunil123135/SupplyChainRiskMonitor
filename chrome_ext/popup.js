document.getElementById('go').onclick = async () => {
  const queryInput = document.getElementById('q');
  const statusEl = document.getElementById('status');
  const resultEl = document.getElementById('result');
  const button = document.getElementById('go');
  
  const query = queryInput.value.trim();
  
  // Update UI
  button.disabled = true;
  statusEl.textContent = '🔄 Scanning page and analyzing risks...';
  resultEl.innerHTML = '';
  
  try {
    // Send message to background script (AGENT)
    const resp = await chrome.runtime.sendMessage({ 
      type: 'USER_QUERY', 
      query: query 
    });
    
    statusEl.textContent = '';
    button.disabled = false;
    
    if (resp.error) {
      resultEl.innerHTML = `<div class="card"><div style="color:#c5221f;">Error: ${resp.error}</div></div>`;
      return;
    }
    
    const R = resp.card;
    
    // Build result card
    const div = document.createElement('div');
    div.className = 'card';
    
    // Priority badge
    const priorityClass = R.priority === 'critical' ? 'critical' : 'normal';
    const priorityIcon = R.priority === 'critical' ? '⚠️' : '✅';
    
    // Top risks tags
    const tagsHtml = (R.top_risks || [])
      .map(t => `<span class="tag">${t.tag} <span class="tag-count">(${t.count})</span></span>`)
      .join('');
    
    // Evidence items
    const evidenceHtml = (R.evidence || [])
      .map(e => `
        <div class="evidence-item">
          <a href="${e.url}" target="_blank">${e.title || e.url}</a>
          <div class="snippet">${e.snippet}</div>
        </div>
      `)
      .join('');
    
    div.innerHTML = `
      <div class="priority ${priorityClass}">${priorityIcon} ${R.priority || 'normal'} priority</div>
      
      <div class="meta">
        <strong>Supplier:</strong> ${R.supplier || 'Unknown'} &nbsp;&nbsp;
        <strong>Location:</strong> ${R.location || 'Unknown'}
      </div>
      
      ${R.query_used ? `<div class="meta" style="font-size:12px;"><strong>Query:</strong> ${R.query_used}</div>` : ''}
      
      <div class="section">
        <div class="section-title">🏷️ Top Risk Factors</div>
        ${tagsHtml || '<span style="color:#5f6368;">No risks identified</span>'}
      </div>
      
      <div class="section">
        <div class="section-title">📄 Evidence</div>
        ${evidenceHtml || '<div style="color:#5f6368;">No evidence found</div>'}
      </div>
    `;
    
    resultEl.appendChild(div);
    
  } catch (error) {
    statusEl.textContent = '';
    button.disabled = false;
    
    // Enhanced error message with troubleshooting
    let helpText = 'Check the browser console (F12) for more details.';
    
    if (error.message.includes('Failed to fetch') || error.message.includes('Failed to load')) {
      helpText = 'Make sure the bundle files (vectors.npy or vectors.bin + meta.json) are in the chrome_ext/bundle/ directory. You may need to reload the extension after adding files.';
    } else if (error.message.includes('Bundle mismatch')) {
      helpText = 'The vector file and metadata don\'t match. Please regenerate the bundle using the Colab script (colab_index_builder.py).';
    }
    
    resultEl.innerHTML = `
      <div class="card">
        <div style="color:#c5221f;">
          <strong>⚠️ Error:</strong> ${error.message}
        </div>
        <div style="margin-top:8px;font-size:12px;color:#5f6368;line-height:1.4;">
          ${helpText}
        </div>
        <div style="margin-top:8px;font-size:11px;color:#888;">
          💡 Tip: Open browser DevTools (F12) → Console tab for detailed error logs
        </div>
      </div>
    `;
    console.error('Extension error:', error);
  }
};

// Allow Enter key to trigger analysis
document.getElementById('q').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    document.getElementById('go').click();
  }
});

