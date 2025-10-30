// ACTION.js - Layer 3: Retrieve and synthesize risk information
// Uses MEMORY for retrieval and adds lexical boosting

import { search } from './MEMORY.js';

/**
 * Mock embedding function (replace with real embedder like transformers.js)
 * For production, use ONNX Runtime Web or transformers.js with a real model
 */
function l2norm(x) {
  let sum = 0;
  for (const v of x) sum += v * v;
  return Math.sqrt(sum) + 1e-12;
}

function normalize(x) {
  const n = l2norm(x);
  return Float32Array.from(x, v => v / n);
}

async function embedQuery(text) {
  // TODO: Replace with actual embedding model (transformers.js, ONNX Runtime Web)
  // This is a simple character-based hash for demo purposes only
  const D = 768;
  const v = new Float32Array(D);
  
  // Simple bag-of-chars encoding (NOT production quality!)
  for (let i = 0; i < text.length; i++) {
    const idx = text.charCodeAt(i) % D;
    v[idx] += 1;
  }
  
  return normalize(v);
}

/**
 * Compute lexical overlap score
 */
function lexicalBoost(query, text) {
  const queryTokens = new Set(
    query.toLowerCase().split(/\W+/).filter(Boolean)
  );
  
  let hits = 0;
  const lowerText = text.toLowerCase();
  
  queryTokens.forEach(token => {
    if (lowerText.includes(token)) {
      hits++;
    }
  });
  
  return hits;
}

/**
 * Retrieve top-k relevant chunks for query
 * @param {string} query - Search query
 * @param {number} k - Number of results to return
 * @returns {Array} Array of metadata objects
 */
export async function retrieve(query, k = 8) {
  // Embed query
  const qv = await embedQuery(query);
  
  // Get initial candidates (over-fetch for reranking)
  const initialK = Math.max(k * 3, 24);
  const initial = await search(qv, initialK);
  
  // Rerank with lexical boost
  const rescored = initial.map(result => ({
    ...result,
    blend: result.score + 0.02 * lexicalBoost(query, result.meta.chunk_text || '')
  }));
  
  // Sort by blended score and take top-k
  rescored.sort((a, b) => b.blend - a.blend);
  
  return rescored.slice(0, k).map(x => x.meta);
}

/**
 * Synthesize risk summary from retrieved chunks
 * @param {string} supplier - Supplier name
 * @param {string} location - Location
 * @param {Array} hits - Retrieved metadata objects
 * @returns {Object} Risk summary
 */
export function synthesizeRiskSummary(supplier, location, hits) {
  const tags = [];
  const evidence = [];
  
  // Collect all risk tags and evidence
  hits.forEach(hit => {
    // Add risk tags
    if (hit.risk_tags && Array.isArray(hit.risk_tags)) {
      tags.push(...hit.risk_tags);
    }
    
    // Create evidence snippet
    const chunkText = hit.chunk_text || '';
    const snippet = chunkText.slice(0, 240) + (chunkText.length > 240 ? '…' : '');
    
    evidence.push({
      url: hit.url,
      title: hit.title,
      snippet: snippet
    });
  });
  
  // Count tag frequencies
  const tagCounts = {};
  tags.forEach(tag => {
    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
  });
  
  // Sort by frequency and take top 6
  const topRisks = Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([tag, count]) => ({ tag, count }));
  
  return {
    supplier: supplier || 'Unknown Supplier',
    location: location || 'Unknown',
    top_risks: topRisks,
    evidence: evidence.slice(0, 6)
  };
}

console.log('✓ Supply Chain Risk Monitor - ACTION layer loaded');

