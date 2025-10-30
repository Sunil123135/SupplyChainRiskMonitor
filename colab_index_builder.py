"""
Supply Chain Risk Monitor — Colab-Friendly Index Builder
Copy this entire file to Google Colab and run it to generate the index bundle.
Downloads vectors.bin + meta.json at the end.

SETUP IN GOOGLE COLAB:
1. Install dependencies: !pip install -q nomic numpy
2. Authenticate with Nomic: !nomic login
   (Or get API key from https://atlas.nomic.ai/cli-login)
3. Run the main() function
"""

import os, json, re
from typing import List, Dict, Any

# These imports are for Google Colab environment - may not be available locally
import numpy as np  # type: ignore
from nomic import embed  # type: ignore

# --- CONFIG -------------------------------------------------------------------
EMBED_DIM = 768  # Nomic embedding dimension
MODEL_NAME = "nomic-embed-text-v1.5"
BUNDLE_DIR = "/content/bundle"  # Colab path
os.makedirs(BUNDLE_DIR, exist_ok=True)

# --- UTILITIES ----------------------------------------------------------------
def l2_normalize(X: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
    return (X / norms).astype(np.float32)

def chunk_text(text: str, size: int = 800, overlap: int = 120) -> List[str]:
    text = re.sub(r"\s+", " ", text.strip())
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i+size])
        i += max(1, size - overlap)
    return out

# --- EMBEDDING ----------------------------------------------------------------
def embed_texts_nomic(texts: List[str]) -> np.ndarray:
    """Use Nomic to embed texts. Install: !pip install nomic"""
    print(f"Embedding {len(texts)} chunks with {MODEL_NAME}...")
    
    try:
        embs = embed.text(texts, model=MODEL_NAME, task_type="search_document")
        X = np.array(embs['embeddings'] if isinstance(embs, dict) else embs, dtype=np.float32)
        if X.shape[1] != EMBED_DIM:
            raise ValueError(f"Expected dim {EMBED_DIM}, got {X.shape[1]}")
        return l2_normalize(X)
    except Exception as e:
        error_msg = str(e)
        if "Failed to fetch" in error_msg or "401" in error_msg or "authentication" in error_msg.lower():
            print("\n" + "="*70)
            print("ERROR: Nomic API Authentication Failed")
            print("="*70)
            print("\nTo fix this, run the following command in a Colab cell:")
            print("\n  !nomic login\n")
            print("Or set your API key:")
            print("\n  import os")
            print('  os.environ["NOMIC_API_KEY"] = "your-api-key-here"\n')
            print("Get your API key from: https://atlas.nomic.ai/cli-login")
            print("="*70 + "\n")
        raise RuntimeError(f"Embedding failed: {error_msg}")

# --- BUILD INDEX --------------------------------------------------------------
def build_index(raw_docs: List[Dict[str, Any]]):
    """
    raw_docs: list of dicts with:
      - url: str
      - title: str
      - supplier: str
      - location: str
      - date: str
      - text: str
      - risk_tags: List[str] (optional)
    """
    # 1) Chunk
    rows = []
    for d in raw_docs:
        chunks = chunk_text(d["text"])
        for ch in chunks:
            rows.append({
                "url": d["url"],
                "title": d["title"],
                "supplier": d.get("supplier", ""),
                "location": d.get("location", ""),
                "date": d.get("date", ""),
                "chunk_text": ch,
                "risk_tags": d.get("risk_tags", [])
            })
    
    # 2) Embed
    texts = [r["chunk_text"] for r in rows]
    X = embed_texts_nomic(texts)
    
    # 3) Export bundle
    vec_path = os.path.join(BUNDLE_DIR, "vectors.bin")
    X.tofile(vec_path)
    print(f"✓ Exported {X.shape[0]} vectors ({X.nbytes / 1024:.1f} KB) to {vec_path}")
    
    meta = []
    for i, r in enumerate(rows):
        meta.append({
            "id": i,
            "url": r["url"],
            "supplier": r["supplier"],
            "location": r["location"],
            "date": r["date"],
            "title": r["title"],
            "chunk_text": r["chunk_text"],
            "risk_tags": r["risk_tags"]
        })
    
    meta_path = os.path.join(BUNDLE_DIR, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"✓ Exported {len(meta)} metadata rows to {meta_path}")
    
    return vec_path, meta_path

# --- DEMO DATA ----------------------------------------------------------------
def get_demo_corpus() -> List[Dict[str, Any]]:
    
    return [

    {
        "url": "https://www.dhl.com/global-en/delivered/global-trade/five-factors-affecting-supply-chain-management.html",
        "title": "Five Factors Affecting Global Supply Chain Management",
        "supplier": "DHL Supply Chain",
        "location": "Global",
        "date": "2025-04-10",
        "text": "DHL identifies five key disruption factors — geopolitical tensions, raw material shortages, labor constraints, inflation, and energy instability — impacting supply continuity.",
        "risk_tags": ["Geopolitical risk", "Energy crisis", "Labor shortage", "Inflation", "Material shortage"]
    },
    {
        "url": "https://www.dhl.com/in-en/home/supply-chain/insights-and-trends.html",
        "title": "India Logistics Insights 2025",
        "supplier": "DHL Supply Chain India",
        "location": "India",
        "date": "2025-03-28",
        "text": "Analysis highlights rising logistics costs in India due to freight bottlenecks and port congestion. Emphasizes digital visibility as the first step to risk resilience.",
        "risk_tags": ["Freight bottleneck", "Port congestion", "Digital visibility", "Cost escalation"]
    },
    {
        "url": "https://www.maersk.com/insights/resilience/2024/08/22/logistics-strategies-and-disruptions",
        "title": "Logistics Strategies for Managing Disruptions",
        "supplier": "Maersk Logistics",
        "location": "Global",
        "date": "2025-02-22",
        "text": "Maersk outlines integrated ocean-to-land strategies to absorb supply chain shocks. Advocates multimodal flexibility and nearshoring to manage unpredictability.",
        "risk_tags": ["Multimodal logistics", "Nearshoring", "Resilience", "Disruption strategy"]
    },
    {
        "url": "https://newsroom.kuehne-nagel.com/kuehnenagels-seanews-helps-to-navigate-supply-chain-disruptions-and-trends/",
        "title": "SeaNews: Navigating Supply Chain Disruptions",
        "supplier": "Kuehne + Nagel",
        "location": "Europe/Asia",
        "date": "2025-03-15",
        "text": "Reports rising ocean freight disruptions due to port labor strikes and container imbalances. Emphasizes predictive analytics to mitigate customer delays.",
        "risk_tags": ["Port strikes", "Container imbalance", "Predictive analytics", "Customer delay"]
    },
    {
        "url": "https://www.gxo.com/news/automation-resilience-2025",
        "title": "Warehouse Automation Boosts Resilience",
        "supplier": "GXO Logistics",
        "location": "Global",
        "date": "2025-02-10",
        "text": "GXO demonstrates how robotics and AI-driven workflows minimize disruption risk caused by labor volatility and seasonal demand surges.",
        "risk_tags": ["Labor volatility", "Automation", "AI", "Seasonal demand"]
    },
    {
        "url": "https://europe.xpo.com/en/resource-center/5-supply-chain-challenges-and-how-to-overcome-them/",
        "title": "Top 5 Supply Chain Challenges 2025",
        "supplier": "XPO Logistics",
        "location": "Europe",
        "date": "2025-01-15",
        "text": "Discusses disruptions from cross-border customs delays, data silos, and fuel price volatility. Recommends centralized visibility platforms for mitigation.",
        "risk_tags": ["Customs delays", "Fuel volatility", "Data silos", "Visibility"]
    },
    {
        "url": "https://www.allcargologistics.com/newsroom/supply-chain-resilience-2025",
        "title": "Indian Supply Chain Resilience Outlook",
        "supplier": "Allcargo Logistics",
        "location": "India",
        "date": "2025-04-03",
        "text": "Allcargo highlights multimodal infrastructure expansion in India as a buffer against monsoon and highway disruptions. Encourages container digitalization.",
        "risk_tags": ["Monsoon disruption", "Infrastructure", "Digitalization", "Multimodal transport"]
    },
    {
        "url": "https://www.delhivery.com/insights/network-optimization-2025",
        "title": "Network Optimization to Counter Disruptions",
        "supplier": "Delhivery",
        "location": "India",
        "date": "2025-02-20",
        "text": "Delhivery shares insights on predictive rerouting algorithms to handle last-mile disruptions during adverse weather and festival surges.",
        "risk_tags": ["Last-mile", "Weather", "Festival surge", "Predictive routing"]
    },
    {
        "url": "https://www.gati.com/news/supply-chain-performance-resilience-2025",
        "title": "Supply Chain Resilience in Surface Transport",
        "supplier": "Gati Ltd",
        "location": "India",
        "date": "2025-03-12",
        "text": "Reports seasonal truck shortages and route bottlenecks across Northern India. Focuses on AI-assisted route planning to reduce dwell time.",
        "risk_tags": ["Truck shortage", "Route bottleneck", "AI routing", "Dwell time"]
    },
    {
        "url": "https://www.safexpress.com/newsroom/logistics-resilience-2025",
        "title": "Safexpress Focuses on Delivery Predictability",
        "supplier": "Safexpress",
        "location": "India",
        "date": "2025-02-05",
        "text": "Safexpress introduces IoT-enabled tracking for long-haul shipments to prevent pilferage and enhance ETA accuracy across India’s fragmented road network.",
        "risk_tags": ["IoT tracking", "Pilferage", "ETA accuracy", "Road fragmentation"]
    },
    {
        "url": "https://www.tcil.com/insights/transportation-disruption-report-2025",
        "title": "Transportation Disruption Report 2025",
        "supplier": "Transport Corporation of India (TCI)",
        "location": "India",
        "date": "2025-04-02",
        "text": "Highlights fuel cost fluctuations and driver unavailability as top two causes for service delays. Suggests dynamic pricing for sustainability.",
        "risk_tags": ["Fuel cost", "Driver shortage", "Dynamic pricing", "Sustainability"]
    },
    {
        "url": "https://www.fedex.com/en-us/shipping/insights/supply-chain-resilience.html",
        "title": "Building Supply Chain Resilience Through Predictive Analytics",
        "supplier": "FedEx",
        "location": "Global",
        "date": "2025-03-22",
        "text": "FedEx emphasizes proactive disruption detection via data fusion from weather, customs, and traffic signals for resilient operations.",
        "risk_tags": ["Predictive analytics", "Weather risk", "Traffic data", "Customs alerts"]
    },
    {
        "url": "https://www.ups.com/us/en/supplychain/insights/disruption-resilience.page",
        "title": "Resilient Supply Chains Amid Global Volatility",
        "supplier": "UPS Supply Chain Solutions",
        "location": "Global",
        "date": "2025-02-18",
        "text": "UPS shares strategies for dealing with geopolitical uncertainty and cyber disruptions in logistics networks. Recommends multi-tier risk mapping.",
        "risk_tags": ["Cyber risk", "Geopolitical", "Multi-tier mapping"]
    },
    {
        "url": "https://www.dsv.com/en/insights/2025-disruption-index",
        "title": "2025 Global Supply Chain Disruption Index",
        "supplier": "DSV Logistics",
        "location": "Global",
        "date": "2025-04-11",
        "text": "DSV publishes its first disruption index tracking lead time variance and mode shifts across major trade corridors.",
        "risk_tags": ["Lead time variance", "Mode shift", "Trade corridor"]
    },
    {
        "url": "https://www.dbschenker.com/global/about/insights/resilience-and-sustainability",
        "title": "Resilience and Sustainability in Supply Chains",
        "supplier": "DB Schenker",
        "location": "Global",
        "date": "2025-03-05",
        "text": "DB Schenker focuses on dual sourcing and energy-efficient transport to mitigate environmental and supply disruptions.",
        "risk_tags": ["Dual sourcing", "Energy efficiency", "Environmental risk"]
    },
    {
        "url": "https://www.cevalogistics.com/en/insights/supply-chain-trends-2025",
        "title": "Supply Chain Trends and Challenges",
        "supplier": "CEVA Logistics",
        "location": "Asia Pacific",
        "date": "2025-02-24",
        "text": "CEVA identifies nearshoring and trade wars as primary drivers of logistics volatility in Asia Pacific.",
        "risk_tags": ["Trade war", "Nearshoring", "Volatility"]
    },
    {
        "url": "https://www.agility.com/insights/global-disruption-tracker",
        "title": "Agility Global Disruption Tracker",
        "supplier": "Agility Logistics",
        "location": "Global",
        "date": "2025-03-01",
        "text": "Provides real-time dashboard on transport congestion and inventory pile-ups due to Red Sea route disruptions.",
        "risk_tags": ["Route disruption", "Inventory pile-up", "Red Sea"]
    },
    {
        "url": "https://www.bluedart.com/insights/aviation-logistics-2025",
        "title": "Aviation Logistics Resilience 2025",
        "supplier": "Blue Dart Express",
        "location": "India",
        "date": "2025-04-06",
        "text": "Blue Dart expands its air network to minimize disruption during highway closures and natural disasters. Focus on express pharma cold chain.",
        "risk_tags": ["Air logistics", "Cold chain", "Natural disaster"]
    },
    {
        "url": "https://www.cma-cgm.com/news/2025-supply-chain-risk-insights",
        "title": "CMA CGM Risk and Resilience Insights",
        "supplier": "CMA CGM",
        "location": "Global",
        "date": "2025-02-16",
        "text": "CMA CGM reports vessel rerouting due to geopolitical conflicts impacting container turnaround in the Suez corridor.",
        "risk_tags": ["Vessel rerouting", "Geopolitical", "Suez corridor"]
    },
    {
        "url": "https://www.kerrylogistics.com/en/insights/supply-chain-risk-2025",
        "title": "Managing Asia-Pacific Supply Chain Risks",
        "supplier": "Kerry Logistics",
        "location": "APAC",
        "date": "2025-03-19",
        "text": "Focus on digital freight visibility and warehouse diversification to mitigate lockdown-related disruptions in Asia.",
        "risk_tags": ["Digital visibility", "Warehouse diversification", "Lockdown"]
    },
    {
        "url": "https://www.rhenus.group/en/insights/supply-chain-challenges-2025",
        "title": "Rhenus Group Supply Chain Challenges 2025",
        "supplier": "Rhenus Logistics",
        "location": "Europe/India",
        "date": "2025-02-28",
        "text": "Rhenus explores integrated customs brokerage and smart container tracking to reduce administrative delays.",
        "risk_tags": ["Customs", "Smart tracking", "Administrative delay"]
    },
    {
        "url": "https://www.bollore-logistics.com/en/news/supply-chain-insights-2025",
        "title": "Resilient Logistics in Francophone Africa",
        "supplier": "Bolloré Logistics",
        "location": "Africa",
        "date": "2025-03-08",
        "text": "Highlights security and infrastructure challenges in West African corridors; recommends satellite tracking for convoys.",
        "risk_tags": ["Security", "Infrastructure", "Satellite tracking"]
    },
    {
        "url": "https://www.jbstransport.com/insights/logistics-2025",
        "title": "Indian 3PL Outlook and Risk Management",
        "supplier": "JBS Transport India",
        "location": "India",
        "date": "2025-02-10",
        "text": "Highlights driver attrition and fuel inflation pressures impacting mid-size 3PL service reliability.",
        "risk_tags": ["Driver attrition", "Fuel inflation", "Service reliability"]
    },
    {
        "url": "https://www.geodis.com/news/supply-chain-disruption-2025",
        "title": "Building Resilience through Data Integration",
        "supplier": "GEODIS",
        "location": "Europe",
        "date": "2025-04-09",
        "text": "GEODIS uses AI for real-time supply chain mapping to preempt disruption in key pharma lanes.",
        "risk_tags": ["AI mapping", "Pharma", "Real-time data"]
    },
    {
        "url": "https://www.nipponexpress.com/news/global-resilience-2025",
        "title": "Nippon Express Global Resilience Plan",
        "supplier": "Nippon Express",
        "location": "Japan/Global",
        "date": "2025-01-25",
        "text": "Outlines disaster-preparedness protocols across Japanese ports to handle seismic or tsunami disruptions.",
        "risk_tags": ["Disaster", "Seismic risk", "Preparedness"]
    },
    {
        "url": "https://www.sinotrans.com/en/news/supply-chain-risk-asia-2025",
        "title": "Asia-Pacific Supply Chain Volatility Report",
        "supplier": "Sinotrans",
        "location": "China/SEA",
        "date": "2025-03-27",
        "text": "Reports container shortages and trucking bans impacting export flow to ASEAN. Highlights digital customs integration.",
        "risk_tags": ["Container shortage", "Trucking ban", "Customs integration"]
    },
    {
        "url": "https://www.aramex.com/news/global-supply-chain-updates-2025",
        "title": "Aramex Global Supply Chain Updates",
        "supplier": "Aramex",
        "location": "Middle East/India",
        "date": "2025-02-13",
        "text": "Aramex shares regional disruption reports due to Red Sea rerouting and last-mile e-commerce spikes.",
        "risk_tags": ["Red Sea", "Last-mile", "E-commerce surge"]
    },
    {
        "url": "https://www.damco.com/insights/logistics-risk-2025",
        "title": "Logistics Risk and Opportunity in Emerging Markets",
        "supplier": "Damco",
        "location": "Emerging Markets",
        "date": "2025-04-12",
        "text": "Damco discusses infrastructure volatility and regulatory uncertainty in Africa and South Asia.",
        "risk_tags": ["Infrastructure", "Regulatory risk", "Emerging markets"]
    },
    {
        "url": "https://www.mitsubishilogistics.co.jp/en/news/2025-supply-chain-report",
        "title": "Japan Supply Chain Report 2025",
        "supplier": "Mitsubishi Logistics",
        "location": "Japan",
        "date": "2025-03-16",
        "text": "Highlights semiconductor logistics disruptions due to export restrictions and supplier concentration.",
        "risk_tags": ["Semiconductor", "Export restriction", "Supplier concentration"]
    },
    {
        "url": "https://www.yusen-logistics.com/news/supply-chain-insights-2025",
        "title": "Yusen Logistics Risk Insights 2025",
        "supplier": "Yusen Logistics",
        "location": "APAC",
        "date": "2025-04-04",
        "text": "Yusen reports pandemic-related aftershocks in freight reliability. Introduces real-time ETA predictive dashboards.",
        "risk_tags": ["Pandemic aftershock", "ETA dashboard", "Freight reliability"]
    },
    {
        "url": "https://www.supplychaindigital.com/supply-chain-risk-management/maersk-76-european-shippers-face-costly-disruptions",
        "title": "European Shippers Face Costly Disruptions",
        "supplier": "Maersk Europe",
        "location": "Europe",
        "date": "2025-03-09",
        "text": "Survey finds 76% of European shippers experienced cost escalation due to transport delays, strikes, and supplier insolvency.",
        "risk_tags": ["Transport delay", "Strikes", "Supplier insolvency", "Cost escalation"]
    },
    {
        "url": "https://www.capgemini.com/insights/expert-perspectives/capgemini-and-kuehne-nagel-revolutionizing-end-to-end-supply-chain-orchestration/",
        "title": "Digital Orchestration of Global Supply Chains",
        "supplier": "Capgemini & Kuehne + Nagel",
        "location": "Global",
        "date": "2025-02-12",
        "text": "Joint initiative leverages data orchestration to predict disruptions before they cascade across multi-tier networks.",
        "risk_tags": ["Data orchestration", "Prediction", "Multi-tier network"]
    }
]


# --- MAIN ---------------------------------------------------------------------
def main():
    print("=" * 70)
    print("Supply Chain Risk Monitor - Index Builder (Colab)")
    print("=" * 70)
    
    # Check if running in Colab and provide setup instructions
    try:
        import google.colab  # type: ignore
        print("\n⚠️  FIRST TIME SETUP:")
        print("   If you get 'Failed to fetch' error, authenticate with Nomic:")
        print("   Run: !nomic login")
        print("   Or visit: https://atlas.nomic.ai/cli-login")
        print()
    except ImportError:
        pass
    
    # Get corpus (replace with your data source)
    corpus = get_demo_corpus()
    print(f"\nProcessing {len(corpus)} documents...")
    
    # Build index
    vec_path, meta_path = build_index(corpus)
    
    print("\n" + "=" * 70)
    print("✓ Index build complete!")
    print("=" * 70)
    print(f"\nFiles created:")
    print(f"  - {vec_path}")
    print(f"  - {meta_path}")
    
    # Download in Colab
    print("\n📦 Downloading files...")
    try:
        from google.colab import files  # type: ignore
        files.download(vec_path)
        files.download(meta_path)
        print("✓ Download started - check your browser's download folder")
    except ImportError:
        print("Not running in Colab - files saved to:", BUNDLE_DIR)
    
    print("\n🚀 Next steps:")
    print("  1. Copy vectors.bin and meta.json to chrome_ext/bundle/")
    print("  2. Load chrome_ext/ as unpacked extension in Chrome")
    print("  3. Navigate to a supplier page and click the extension icon")

if __name__ == "__main__":
    # FIRST RUN IN COLAB? Uncomment these lines:
    # !pip install -q nomic numpy
    # !nomic login
    
    main()

