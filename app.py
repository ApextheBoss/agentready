"""
AgentReady API — FastAPI app for scanning websites.
x402 payment-gated detailed scans.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
from scanner import scan, format_report

from x402 import x402ResourceServer
from x402.http import HTTPFacilitatorClient, FacilitatorConfig
from x402.http.middleware.fastapi import payment_middleware
from x402.mechanisms.evm.exact import ExactEvmServerScheme

# x402 payment setup — Base Sepolia testnet (eip155:84532)
# Using testnet because the public x402 facilitator only supports testnets.
# Will switch to mainnet (eip155:8453) when facilitator adds mainnet support.
MY_WALLET = "0x74075f7330f4A88758AC815fC7F779b4147c64EF"
FACILITATOR_URL = "https://www.x402.org/facilitator"

facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL))
x402_server = x402ResourceServer(facilitator)
x402_server.register("eip155:84532", ExactEvmServerScheme())

# Routes that require payment
x402_routes = {
    "POST /api/scan/detailed": {
        "accepts": {
            "scheme": "exact",
            "payTo": MY_WALLET,
            "price": "$0.50",
            "network": "eip155:84532",
        }
    },
    "GET /api/scan/detailed": {
        "accepts": {
            "scheme": "exact",
            "payTo": MY_WALLET,
            "price": "$0.50",
            "network": "eip155:84532",
        }
    },
}

app = FastAPI(
    title="AgentReady",
    description="Score any website's AI agent readiness. Like PageSpeed Insights, but for AI agents.",
    version="0.1.0",
)

# Add x402 payment middleware
@app.middleware("http")
async def x402_payment_middleware(request: Request, call_next):
    mw = payment_middleware(x402_routes, x402_server)
    return await mw(request, call_next)


class ScanRequest(BaseModel):
    url: str


class ScanResponse(BaseModel):
    url: str
    overall_score: int
    grade: str
    checks: list
    scan_time_ms: int
    scanned_at: str


LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgentReady — Is Your Website Ready for AI Agents?</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; min-height: 100vh; }
  .container { max-width: 720px; margin: 0 auto; padding: 60px 20px; }
  h1 { font-size: 2.5rem; margin-bottom: 8px; color: #D4621A; }
  .subtitle { font-size: 1.1rem; color: #888; margin-bottom: 40px; }
  .scan-form { display: flex; gap: 12px; margin-bottom: 40px; }
  input[type="url"] { flex: 1; padding: 14px 18px; border: 2px solid #333; background: #1a1a1a; color: #fff; border-radius: 8px; font-size: 1rem; }
  input[type="url"]:focus { border-color: #D4621A; outline: none; }
  button { padding: 14px 28px; background: #D4621A; color: #fff; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }
  button:hover { background: #e0752e; }
  button:disabled { background: #555; cursor: wait; }
  .results { background: #1a1a1a; border-radius: 12px; padding: 32px; border: 1px solid #333; }
  .score-circle { width: 120px; height: 120px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; font-size: 2.5rem; font-weight: 700; }
  .grade-A { border: 4px solid #22c55e; color: #22c55e; }
  .grade-B { border: 4px solid #84cc16; color: #84cc16; }
  .grade-C { border: 4px solid #eab308; color: #eab308; }
  .grade-D { border: 4px solid #f97316; color: #f97316; }
  .grade-F { border: 4px solid #ef4444; color: #ef4444; }
  .check { padding: 16px 0; border-bottom: 1px solid #2a2a2a; }
  .check:last-child { border-bottom: none; }
  .check-header { display: flex; justify-content: space-between; align-items: center; }
  .check-name { font-weight: 600; font-size: 1rem; }
  .check-score { font-size: 0.9rem; color: #888; }
  .check-detail { font-size: 0.9rem; color: #aaa; margin-top: 4px; }
  .check-rec { font-size: 0.85rem; color: #D4621A; margin-top: 4px; }
  .icon { font-size: 1.2rem; margin-right: 8px; }
  .footer { text-align: center; margin-top: 60px; color: #555; font-size: 0.85rem; }
  .footer a { color: #D4621A; text-decoration: none; }
  #loading { display: none; text-align: center; padding: 40px; color: #888; }
  .hidden { display: none !important; }
</style>
</head>
<body>
<div class="container">
  <h1>👑 AgentReady</h1>
  <p class="subtitle">Is your website ready for AI agents? Get a score in seconds.</p>
  
  <form class="scan-form" id="scanForm">
    <input type="url" id="urlInput" placeholder="https://example.com" required>
    <button type="submit" id="scanBtn">Scan</button>
  </form>
  
  <div id="loading">Scanning... ⏳</div>
  <div id="results" class="hidden"></div>
  
  <div class="footer">
    Built by <a href="https://x.com/ApextheBossAI" target="_blank">Apex</a> — an AI agent building a $1B business with zero human employees.
    <br>Open source on <a href="https://github.com/ApextheBoss/agentready" target="_blank">GitHub</a>.
  </div>
</div>

<script>
document.getElementById('scanForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const url = document.getElementById('urlInput').value;
  const btn = document.getElementById('scanBtn');
  const loading = document.getElementById('loading');
  const results = document.getElementById('results');
  
  btn.disabled = true;
  loading.style.display = 'block';
  results.classList.add('hidden');
  
  try {
    const r = await fetch('/api/scan', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url})
    });
    const data = await r.json();
    
    const icons = {pass: '✅', warn: '⚠️', fail: '❌'};
    
    let html = `
      <div class="score-circle grade-${data.grade}">${data.overall_score}</div>
      <p style="text-align:center;margin-bottom:24px;color:#888;">Grade: ${data.grade} · ${data.scan_time_ms}ms</p>
    `;
    
    for (const c of data.checks) {
      html += `
        <div class="check">
          <div class="check-header">
            <span class="check-name"><span class="icon">${icons[c.status]||'?'}</span>${c.name}</span>
            <span class="check-score">${c.score}/${c.max_score}</span>
          </div>
          <div class="check-detail">${c.detail}</div>
          ${c.recommendation ? `<div class="check-rec">→ ${c.recommendation}</div>` : ''}
        </div>
      `;
    }
    
    results.innerHTML = `<div class="results">${html}</div>`;
    results.classList.remove('hidden');
  } catch (err) {
    results.innerHTML = `<div class="results"><p style="color:#ef4444;">Error: ${err.message}</p></div>`;
    results.classList.remove('hidden');
  }
  
  btn.disabled = false;
  loading.style.display = 'none';
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return LANDING_HTML


@app.post("/api/scan")
async def api_scan(req: ScanRequest):
    if not req.url:
        raise HTTPException(400, "URL is required")
    result = await scan(req.url)
    return result.to_dict()


@app.get("/api/scan")
async def api_scan_get(url: str):
    if not url:
        raise HTTPException(400, "URL parameter is required")
    result = await scan(url)
    return result.to_dict()


def _generate_detailed_report(result) -> dict:
    """Generate detailed remediation report from scan result."""
    data = result.to_dict()
    
    remediation_guides = []
    for check in data["checks"]:
        guide = {
            "name": check["name"],
            "status": check["status"],
            "score": check["score"],
            "max_score": check["max_score"],
            "detail": check["detail"],
            "recommendation": check.get("recommendation", ""),
        }
        
        # Add detailed remediation steps based on check type
        if check["status"] == "fail":
            guide["priority"] = "HIGH"
            guide["remediation_steps"] = _get_remediation_steps(check["name"])
            guide["estimated_effort"] = "1-2 hours"
        elif check["status"] == "warn":
            guide["priority"] = "MEDIUM"
            guide["remediation_steps"] = _get_remediation_steps(check["name"])
            guide["estimated_effort"] = "30 minutes"
        else:
            guide["priority"] = "LOW"
            guide["remediation_steps"] = ["No action needed — this check is passing."]
            guide["estimated_effort"] = "None"
        
        remediation_guides.append(guide)
    
    return {
        **data,
        "report_type": "detailed",
        "remediation_guides": remediation_guides,
        "compliance_notes": {
            "eu_ai_act": "AI agent accessibility may fall under EU AI Act transparency requirements.",
            "section_508": "Structured data and machine-readable content improve accessibility compliance.",
        },
        "competitive_benchmark": f"Average score across 66 scanned sites: 34/100. Your score: {data['overall_score']}/100.",
    }


def _get_remediation_steps(check_name: str) -> list[str]:
    """Return specific remediation steps for each check type."""
    steps = {
        "robots.txt": [
            "Create a robots.txt file at your domain root",
            "Add 'User-agent: *' with appropriate Allow/Disallow rules",
            "Consider adding specific rules for AI agents (GPTBot, ClaudeBot, etc.)",
            "Test with: curl https://yourdomain.com/robots.txt",
        ],
        "Structured Data": [
            "Add JSON-LD structured data to your pages (<script type='application/ld+json'>)",
            "Use Schema.org vocabulary (Organization, Product, Article, etc.)",
            "Validate with Google's Rich Results Test",
            "Add at minimum: name, description, url properties",
        ],
        "OpenAPI/API Spec": [
            "Create an openapi.json or openapi.yaml at /openapi.json",
            "Document all public API endpoints with parameters and response schemas",
            "Use Swagger UI or Redoc for interactive documentation",
            "Link it from your robots.txt or sitemap",
        ],
        "Security Headers": [
            "Add Content-Security-Policy header",
            "Add X-Content-Type-Options: nosniff",
            "Add Strict-Transport-Security header",
            "Add X-Frame-Options: DENY or SAMEORIGIN",
        ],
        "llms.txt": [
            "Create /.well-known/llms.txt or /llms.txt at your domain root",
            "Include a plain-text description of your site/product for LLMs",
            "Keep it concise — 500-2000 words covering key info",
            "Reference: llmstxt.org for the emerging standard",
        ],
    }
    # Return matching steps or generic ones
    for key, val in steps.items():
        if key.lower() in check_name.lower():
            return val
    return [
        "Review the check details above for specific issues",
        "Implement the recommendation provided",
        "Re-scan to verify the fix",
    ]


@app.post("/api/scan/detailed")
async def api_scan_detailed(req: ScanRequest):
    """Detailed scan with remediation guide. Requires x402 payment ($0.50 USDC on Base)."""
    if not req.url:
        raise HTTPException(400, "URL is required")
    result = await scan(req.url)
    return _generate_detailed_report(result)


@app.get("/api/scan/detailed")
async def api_scan_detailed_get(url: str):
    """Detailed scan with remediation guide. Requires x402 payment ($0.50 USDC on Base)."""
    if not url:
        raise HTTPException(400, "URL parameter is required")
    result = await scan(url)
    return _generate_detailed_report(result)
