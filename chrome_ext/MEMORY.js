// MEMORY.js - Layer 2: Load and search the vector index bundle
// Performs local cosine similarity search

let V = null;      // Float32Array of all vectors
let N = 0;         // Number of vectors
let D = 768;       // Dimension (must match your embedding model)
let META = null;   // Array of metadata objects

/**
 * Parse NumPy .npy file header and return data offset
 * Format: magic (6 bytes) + version (2 bytes) + header_len (2 or 4 bytes) + header dict
 */
function parseNpyHeader(buffer) {
  const view = new DataView(buffer);
  
  // Check magic number
  const magic = String.fromCharCode(view.getUint8(0)) + 
                String.fromCharCode(view.getUint8(1)) + 
                String.fromCharCode(view.getUint8(2)) + 
                String.fromCharCode(view.getUint8(3)) + 
                String.fromCharCode(view.getUint8(4)) + 
                String.fromCharCode(view.getUint8(5));
  
  if (magic !== '\x93NUMPY') {
    throw new Error('Not a valid NumPy .npy file');
  }
  
  const major = view.getUint8(6);
  const minor = view.getUint8(7);
  
  let headerLen;
  let headerOffset;
  
  if (major === 1) {
    // Version 1.0: header length is 2 bytes (little-endian)
    headerLen = view.getUint16(8, true);
    headerOffset = 10;
  } else if (major === 2) {
    // Version 2.0: header length is 4 bytes (little-endian)
    headerLen = view.getUint32(8, true);
    headerOffset = 12;
  } else {
    throw new Error(`Unsupported NumPy version: ${major}.${minor}`);
  }
  
  // Data starts after header
  return headerOffset + headerLen;
}

/**
 * Initialize memory from bundle (loads once)
 */
async function initMemory() {
  if (V) return; // Already loaded
  
  try {
    // Load metadata
    const metaResp = await fetch(chrome.runtime.getURL('bundle/meta.json'));
    if (!metaResp.ok) {
      throw new Error(`Failed to load meta.json: ${metaResp.status} ${metaResp.statusText}`);
    }
    META = await metaResp.json();
    
    // Try to load vectors - first try .npy, then fall back to .bin
    let vecResp;
    let isNpy = false;
    
    try {
      vecResp = await fetch(chrome.runtime.getURL('bundle/vectors.npy'));
      if (vecResp.ok) {
        isNpy = true;
        console.log('Loading vectors from .npy file...');
      }
    } catch (e) {
      console.log('.npy file not found, trying .bin...');
    }
    
    if (!isNpy) {
      vecResp = await fetch(chrome.runtime.getURL('bundle/vectors.bin'));
    }
    
    if (!vecResp.ok) {
      throw new Error(`Failed to load vectors file: ${vecResp.status} ${vecResp.statusText}. Make sure either vectors.npy or vectors.bin exists in the bundle/ directory.`);
    }
    
    const buf = await vecResp.arrayBuffer();
    
    // Parse based on file type
    if (isNpy) {
      // Parse .npy header and extract data
      const dataOffset = parseNpyHeader(buf);
      V = new Float32Array(buf, dataOffset);
      console.log(`Parsed .npy file, data starts at byte ${dataOffset}`);
    } else {
      // Raw binary file
      V = new Float32Array(buf);
    }
    
    N = META.length;
    D = 768; // Set to your embedding dimension
    
    // Validate
    if (V.length !== N * D) {
      throw new Error(
        `Bundle mismatch: vectors file has ${V.length} floats, ` +
        `but meta.json has ${N} rows × ${D} dims = ${N * D} expected. ` +
        `Please regenerate the bundle using the Colab script.`
      );
    }
    
    console.log(`✓ MEMORY loaded: ${N} vectors (${D}D), ${(V.length * 4 / 1024).toFixed(1)} KB`);
  } catch (error) {
    console.error('MEMORY initialization error:', error);
    throw new Error(`Failed to initialize vector database: ${error.message}`);
  }
}

/**
 * Dot product between vector at index i and query vector qv
 */
function dot(a, offset, b) {
  let sum = 0;
  for (let i = 0; i < b.length; i++) {
    sum += a[offset + i] * b[i];
  }
  return sum;
}

/**
 * Find top-k indices by score
 */
function topK(scores, k) {
  return scores
    .map((s, i) => [s, i])
    .sort((a, b) => b[0] - a[0])
    .slice(0, k)
    .map(x => x[1]);
}

/**
 * Search for top-k most similar vectors
 * @param {Float32Array} qv - Query vector (normalized)
 * @param {number} k - Number of results
 * @returns {Array} Array of {score, meta} objects
 */
export async function search(qv, k = 24) {
  await initMemory();
  
  // Compute cosine similarity for all vectors
  const scores = new Array(N);
  for (let i = 0; i < N; i++) {
    scores[i] = dot(V, i * D, qv);
  }
  
  // Get top-k indices
  const idxs = topK(scores, k);
  
  // Return results with metadata
  return idxs.map(i => ({
    score: scores[i],
    meta: META[i]
  }));
}

console.log('✓ Supply Chain Risk Monitor - MEMORY layer loaded');

