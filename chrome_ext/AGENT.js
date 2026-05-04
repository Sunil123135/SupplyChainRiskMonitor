// AGENT.js - Layer 5: Orchestrate the complete RAG pipeline
// Background service worker that coordinates all layers

import { retrieve, synthesizeRiskSummary } from './ACTION.js';
import { decide } from './DECISION.js';
import { generateReplenishmentReport, buildForecastCard } from './DEMAND_FORECAST.js';

/**
 * Main agent orchestration: PERCEPTION → MEMORY → ACTION → DECISION
 */
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'USER_QUERY') {
    // Handle async processing
    (async () => {
      try {
        // Step 1: Get context from current page (PERCEPTION)
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        let context = null;
        try {
          context = await chrome.tabs.sendMessage(tab.id, { type: 'GET_CONTEXT' });
        } catch (error) {
          console.warn('Could not get page context:', error);
          // Fallback to empty context
          context = {
            url: tab.url || '',
            title: tab.title || '',
            supplier_candidates: [],
            locations: [],
            risk_keywords_found: [],
            context_preview: ''
          };
        }
        
        // Step 2: Extract entities
        const supplier = (context?.supplier_candidates?.[0]) || "";
        const location = (context?.locations?.[0]) || "";
        const riskSeed = (context?.risk_keywords_found || []).join(' ');
        
        // Step 3: Build query (combine user input + page context)
        const userQuery = (msg.query || '').trim();
        const queryParts = [userQuery, supplier, location, riskSeed].filter(Boolean);
        const query = queryParts.join(' ').trim() || 'cold chain deviation India';
        
        console.log('🔍 Agent query:', query);
        
        // Step 4: ACTION - Retrieve relevant chunks (uses MEMORY internally)
        const hits = await retrieve(query, 8);
        console.log(`📚 Retrieved ${hits.length} chunks`);
        
        // Step 5: ACTION - Synthesize risk summary
        const summary = synthesizeRiskSummary(
          supplier || "Unknown Supplier",
          location || "Unknown",
          hits
        );
        
        // Step 6: DECISION - Prioritize
        const { priority } = decide({ supplier, summary });

        // Step 7: DEMAND_FORECAST - Replenishment recommendations (if data provided)
        let forecastCard = {};
        if (msg.inventory && msg.salesHistory) {
          const recs = generateReplenishmentReport(
            msg.inventory,
            msg.salesHistory,
            { referenceDate: msg.referenceDate }
          );
          forecastCard = buildForecastCard(recs);
          console.log(`📦 Demand forecast: ${recs.length} SKUs need attention`);
        }

        // Step 8: Assemble final card
        const card = {
          title: "Supplier risk summary",
          query_used: query,
          priority: priority,
          ...summary,
          ...forecastCard,
        };
        
        console.log('✅ Agent analysis complete:', card);
        
        sendResponse({ card });
      } catch (error) {
        console.error('❌ Agent error:', error);
        sendResponse({ 
          error: error.message,
          card: {
            title: "Error",
            supplier: "Unknown",
            location: "Unknown",
            priority: "normal",
            top_risks: [],
            evidence: []
          }
        });
      }
    })();
    
    // Return true to indicate async response
    return true;
  }
});

// Service worker lifecycle logging
self.addEventListener('install', (event) => {
  console.log('✓ Supply Chain Risk Monitor - Service Worker installed');
});

self.addEventListener('activate', (event) => {
  console.log('✓ Supply Chain Risk Monitor - Service Worker activated');
});

console.log('✓ Supply Chain Risk Monitor - AGENT layer loaded');

