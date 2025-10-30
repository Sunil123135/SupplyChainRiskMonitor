// PERCEPTION.js - Layer 1: Extract supplier/location/risk keywords from page
// Runs as content script on every page

const RISK_KEYWORDS = [
  "temperature", "cold chain", "deviation", "non-compliance", "delay",
  "breakdown", "lead time", "stockout", "damage", "spoilage", "QA audit",
  "QA finding", "GxP", "GDP", "SLA breach", "ambient", "refrigerated",
  "scrap", "complaints", "deviations", "warning", "recall", "quality issue",
  "contamination", "expiry", "expired", "shipment delay", "customs delay"
];

/**
 * Get text from selection or page content
 */
function getSelectionOrText() {
  // First try to get selected text
  const sel = window.getSelection ? String(window.getSelection()).trim() : '';
  if (sel && sel.length > 20) {
    return sel;
  }
  
  // Fall back to page content
  const metaDesc = document.querySelector('meta[name=description]')?.content || '';
  const bodyText = document.body?.innerText || '';
  
  // Combine and limit to 6000 chars for performance
  return (metaDesc + ' ' + bodyText).slice(0, 6000);
}

/**
 * PERCEPTION: Extract entities and context from page
 */
function perceive() {
  const text = getSelectionOrText();
  
  // Extract potential supplier names (capitalized sequences)
  const supplierMatches = Array.from(
    text.matchAll(/\b([A-Z][A-Za-z0-9&\-]+(?:\s+[A-Z][A-Za-z0-9&\-]+){0,2})\b/g)
  );
  const supplierSet = new Set(
    supplierMatches
      .map(m => m[1])
      .filter(s => s.length >= 3 && s.split(' ').length <= 3)
  );
  
  // Extract locations
  const locationMatches = Array.from(
    text.matchAll(/\b(India|Mumbai|Bangalore|Cochin|Hyderabad|Delhi|Chennai|Pune|US|USA|Europe|Canada|China|Asia|Singapore|Thailand|Vietnam)\b/gi)
  );
  const locations = Array.from(new Set(locationMatches.map(m => m[1])));
  
  // Find risk keywords present in text
  const risksFound = RISK_KEYWORDS.filter(keyword => 
    text.toLowerCase().includes(keyword.toLowerCase())
  );
  
  return {
    url: location.href,
    title: document.title,
    supplier_candidates: Array.from(supplierSet).slice(0, 5),
    locations: locations.slice(0, 5),
    risk_keywords_found: risksFound,
    context_preview: text.slice(0, 1000)
  };
}

// Listen for context requests from popup/background
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'GET_CONTEXT') {
    try {
      const context = perceive();
      sendResponse(context);
    } catch (error) {
      console.error('PERCEPTION error:', error);
      sendResponse({ 
        error: error.message,
        url: location.href,
        title: document.title,
        supplier_candidates: [],
        locations: [],
        risk_keywords_found: [],
        context_preview: ''
      });
    }
  }
});

console.log('✓ Supply Chain Risk Monitor - PERCEPTION layer loaded');

