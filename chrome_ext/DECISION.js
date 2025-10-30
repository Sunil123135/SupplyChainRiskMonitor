// DECISION.js - Layer 4: Prioritize risks based on criticality
// Determines priority level for supplier risks

// Define critical suppliers (update with your organization's critical vendors)
const CRITICAL_SUPPLIERS = new Set([
  "Acme Logistics",
  "ZenCold Chain",
  "BlueRoute Pharma 3PL"
]);

/**
 * Decide priority level for a risk summary
 * @param {Object} params
 * @param {string} params.supplier - Supplier name
 * @param {Object} params.summary - Risk summary from ACTION layer
 * @returns {Object} Decision with priority level
 */
export function decide({ supplier, summary }) {
  let priority = "normal";
  
  // Rule 1: Critical if supplier is in critical list
  if (supplier && CRITICAL_SUPPLIERS.has(supplier)) {
    priority = "critical";
  }
  
  // Rule 2: Critical if temperature-related risks found
  const hasTemperatureRisk = (summary.top_risks || []).some(risk => 
    risk.tag.toLowerCase().includes('temperature') ||
    risk.tag.toLowerCase().includes('cold chain') ||
    risk.tag.toLowerCase().includes('ambient')
  );
  
  if (hasTemperatureRisk) {
    priority = "critical";
  }
  
  // Rule 3: Critical if compliance-related risks found
  const hasComplianceRisk = (summary.top_risks || []).some(risk => 
    risk.tag.toLowerCase().includes('non-compliance') ||
    risk.tag.toLowerCase().includes('gdp') ||
    risk.tag.toLowerCase().includes('gxp') ||
    risk.tag.toLowerCase().includes('audit')
  );
  
  if (hasComplianceRisk) {
    priority = "critical";
  }
  
  // Rule 4: High priority for multiple risk factors
  const riskCount = (summary.top_risks || []).reduce((sum, r) => sum + r.count, 0);
  if (riskCount >= 5 && priority === "normal") {
    priority = "high";
  }
  
  return { priority };
}

console.log('✓ Supply Chain Risk Monitor - DECISION layer loaded');

