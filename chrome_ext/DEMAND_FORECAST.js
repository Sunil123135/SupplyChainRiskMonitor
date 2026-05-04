// DEMAND_FORECAST.js - Demand forecasting + reorder point calculations
// Computes replenishment recommendations from in-memory sales and inventory data.
// All processing is local — no external API calls.

/**
 * Filter out cancelled / refunded sales records.
 * @param {Object[]} records
 * @returns {Object[]}
 */
function filterCompletedSales(records) {
  return records.filter(r => r.status !== 'cancelled' && r.status !== 'refunded');
}

/**
 * Compute average and max daily demand for a product over a lookback window.
 *
 * @param {string} productId
 * @param {Object[]} salesHistory  - [{ productId, sku, date (ISO), unitsSold, status }]
 * @param {Object}  [opts]
 * @param {number}  [opts.lookbackDays=30]
 * @param {number}  [opts.peakWindowDays=7]
 * @param {string}  [opts.referenceDate]  - ISO date string; defaults to today
 * @returns {{ avgDailyDemand: number, maxDailyDemand: number }}
 */
export function computeDemandStats(productId, salesHistory, opts = {}) {
  const { lookbackDays = 30, peakWindowDays = 7, referenceDate } = opts;

  const ref = referenceDate ? new Date(referenceDate) : new Date();
  ref.setHours(0, 0, 0, 0);

  const completed = filterCompletedSales(salesHistory).filter(r => r.productId === productId);

  const msPerDay = 86_400_000;

  // Average over full lookback window
  const lookbackCutoff = new Date(ref - lookbackDays * msPerDay);
  const totalUnits = completed
    .filter(r => new Date(r.date) >= lookbackCutoff)
    .reduce((sum, r) => sum + r.unitsSold, 0);
  const avgDailyDemand = totalUnits / lookbackDays;

  // Max single-day demand within the peak window
  const peakCutoff = new Date(ref - peakWindowDays * msPerDay);
  const dailyTotals = {};
  completed
    .filter(r => new Date(r.date) >= peakCutoff)
    .forEach(r => {
      dailyTotals[r.date] = (dailyTotals[r.date] || 0) + r.unitsSold;
    });
  const maxDailyDemand = Object.keys(dailyTotals).length
    ? Math.max(...Object.values(dailyTotals))
    : avgDailyDemand;

  return { avgDailyDemand, maxDailyDemand };
}

/**
 * Calculate reorder point and safety stock.
 *
 * reorderPoint = (avgDailyDemand × leadTimeDays) + safetyStock
 * safetyStock  = (maxDailyDemand − avgDailyDemand) × leadTimeDays
 *
 * @param {number} avgDailyDemand
 * @param {number} maxDailyDemand
 * @param {number} leadTimeDays
 * @returns {{ reorderPoint: number, safetyStock: number }}
 */
export function calculateReorderPoint(avgDailyDemand, maxDailyDemand, leadTimeDays) {
  const safetyStock = Math.ceil((maxDailyDemand - avgDailyDemand) * leadTimeDays);
  const reorderPoint = Math.ceil(avgDailyDemand * leadTimeDays + safetyStock);
  return { reorderPoint, safetyStock };
}

/**
 * Generate replenishment recommendations for a list of inventory records.
 * Only returns SKUs with urgency "critical" or "warning", sorted by days of supply ascending.
 *
 * @param {Object[]} inventory  - [{ productId, sku, quantityOnHand, quantityOnOrder, supplierLeadTimeDays }]
 * @param {Object[]} salesHistory
 * @param {Object}  [opts]
 * @param {string}  [opts.referenceDate]
 * @returns {Object[]}  replenishment recommendations
 */
export function generateReplenishmentReport(inventory, salesHistory, opts = {}) {
  const recommendations = [];

  for (const inv of inventory) {
    const { avgDailyDemand, maxDailyDemand } = computeDemandStats(
      inv.productId, salesHistory, opts
    );
    const lead = inv.supplierLeadTimeDays ?? 14;
    const { reorderPoint, safetyStock } = calculateReorderPoint(
      avgDailyDemand, maxDailyDemand, lead
    );

    const daysOfSupply = avgDailyDemand > 0
      ? inv.quantityOnHand / avgDailyDemand
      : Infinity;

    const urgency = daysOfSupply < lead
      ? 'critical'
      : daysOfSupply < lead * 2
        ? 'warning'
        : 'ok';

    if (urgency === 'ok') continue;

    // Target qty covers 2× lead time plus safety stock, net of what's already on order
    const targetQty = Math.ceil(avgDailyDemand * lead * 2 + safetyStock);
    const recommendedOrderQty = Math.max(
      0,
      targetQty - inv.quantityOnHand - (inv.quantityOnOrder ?? 0)
    );

    recommendations.push({
      productId: inv.productId,
      sku: inv.sku,
      currentStock: inv.quantityOnHand,
      quantityOnOrder: inv.quantityOnOrder ?? 0,
      avgDailyDemand: Math.round(avgDailyDemand * 100) / 100,
      maxDailyDemand: Math.round(maxDailyDemand * 100) / 100,
      reorderPoint,
      safetyStock,
      daysOfSupply: Math.round(daysOfSupply * 10) / 10,
      urgency,
      recommendedOrderQty,
    });
  }

  recommendations.sort((a, b) => a.daysOfSupply - b.daysOfSupply);
  return recommendations;
}

/**
 * Convert replenishment recommendations into the card fragment used by AGENT.js.
 *
 * @param {Object[]} recommendations  - output of generateReplenishmentReport
 * @returns {Object}
 */
export function buildForecastCard(recommendations) {
  return {
    demandForecast: {
      criticalSkus: recommendations.filter(r => r.urgency === 'critical').map(r => r.sku),
      warningSkus:  recommendations.filter(r => r.urgency === 'warning').map(r => r.sku),
      recommendations: recommendations.map(r => ({
        sku:                 r.sku,
        urgency:             r.urgency,
        currentStock:        r.currentStock,
        daysOfSupply:        r.daysOfSupply,
        reorderPoint:        r.reorderPoint,
        recommendedOrderQty: r.recommendedOrderQty,
        avgDailyDemand:      r.avgDailyDemand,
      })),
    },
  };
}

console.log('✓ Supply Chain Risk Monitor - DEMAND_FORECAST layer loaded');
