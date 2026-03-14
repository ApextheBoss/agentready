"""
Generate a static HTML report of Agent Readiness scores for top websites.
Outputs to docs/ for GitHub Pages deployment.
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from scanner import scan

# Top 50 sites to scan — mix of AI companies, dev tools, major brands
SITES = [
    "https://openai.com",
    "https://anthropic.com",
    "https://google.com",
    "https://github.com",
    "https://stripe.com",
    "https://vercel.com",
    "https://netlify.com",
    "https://cloudflare.com",
    "https://aws.amazon.com",
    "https://docs.python.org",
    "https://react.dev",
    "https://nextjs.org",
    "https://fastapi.tiangolo.com",
    "https://huggingface.co",
    "https://replicate.com",
    "https://together.ai",
    "https://mistral.ai",
    "https://cohere.com",
    "https://perplexity.ai",
    "https://cursor.com",
    "https://linear.app",
    "https://notion.so",
    "https://slack.com",
    "https://discord.com",
    "https://shopify.com",
    "https://wordpress.org",
    "https://medium.com",
    "https://dev.to",
    "https://stackoverflow.com",
    "https://wikipedia.org",
    "https://nytimes.com",
    "https://bbc.com",
    "https://spotify.com",
    "https://twitch.tv",
    "https://reddit.com",
    "https://hackernews.com",
    "https://producthunt.com",
    "https://techcrunch.com",
    "https://fly.io",
    "https://render.com",
    "https://railway.app",
    "https://supabase.com",
    "https://planetscale.com",
    "https://sentry.io",
    "https://datadog.com",
    "https://grafana.com",
    "https://elastic.co",
    "https://mongodb.com",
    "https://docker.com",
    "https://kubernetes.io",
]


async def scan_all():
    results = []
    for url in SITES:
        try:
            result = await scan(url)
            results.append(result)
            print(f"✅ {url}: {result['overall_score']}/100 ({result['grade']})")
        except Exception as e:
            print(f"❌ {url}: {e}")
            results.append({"url": url, "overall_score": 0, "grade": "F", "checks": [], "error": str(e)})
    return sorted(results, key=lambda r: r["overall_score"], reverse=True)


def grade_color(grade):
    return {
        "A": "#22c55e", "B": "#84cc16", "C": "#eab308",
        "D": "#f97316", "F": "#ef4444"
    }.get(grade, "#888")


def generate_html(results):
    now = datetime.now(timezone.utc).strftime("%B %d, %Y")
    rows = ""
    for i, r in enumerate(results, 1):
        color = grade_color(r["grade"])
        domain = r["url"].replace("https://", "").replace("http://", "").rstrip("/")
        rows += f"""
        <tr>
          <td>{i}</td>
          <td><a href="{r['url']}" target="_blank">{domain}</a></td>
          <td style="color:{color};font-weight:700">{r['overall_score']}</td>
          <td style="color:{color};font-weight:700">{r['grade']}</td>
        </tr>"""

    avg = sum(r["overall_score"] for r in results) / len(results) if results else 0
    passing = sum(1 for r in results if r["overall_score"] >= 60)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Readiness Report — {now}</title>
<meta name="description" content="Weekly report scoring how well top websites serve AI agents. Built by Apex, an autonomous AI agent.">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
  h1 {{ font-size: 2rem; color: #D4621A; margin-bottom: 8px; }}
  .date {{ color: #888; margin-bottom: 32px; }}
  .stats {{ display: flex; gap: 24px; margin-bottom: 32px; flex-wrap: wrap; }}
  .stat {{ background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 20px; flex: 1; min-width: 150px; }}
  .stat-value {{ font-size: 2rem; font-weight: 700; color: #D4621A; }}
  .stat-label {{ color: #888; font-size: 0.9rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 12px; overflow: hidden; }}
  th {{ background: #222; padding: 12px 16px; text-align: left; font-weight: 600; color: #D4621A; }}
  td {{ padding: 10px 16px; border-top: 1px solid #2a2a2a; }}
  tr:hover {{ background: #222; }}
  a {{ color: #D4621A; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .footer {{ margin-top: 40px; color: #555; font-size: 0.85rem; text-align: center; }}
  .footer a {{ color: #888; }}
</style>
</head>
<body>
<div class="container">
  <h1>👑 Agent Readiness Report</h1>
  <p class="date">{now} — Scanning {len(results)} websites</p>

  <div class="stats">
    <div class="stat">
      <div class="stat-value">{avg:.0f}</div>
      <div class="stat-label">Average Score</div>
    </div>
    <div class="stat">
      <div class="stat-value">{passing}/{len(results)}</div>
      <div class="stat-label">Passing (60+)</div>
    </div>
    <div class="stat">
      <div class="stat-value">{results[0]['overall_score'] if results else 0}</div>
      <div class="stat-label">Highest Score</div>
    </div>
  </div>

  <table>
    <thead><tr><th>#</th><th>Website</th><th>Score</th><th>Grade</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>

  <div class="footer">
    <p>Built by <a href="https://x.com/ApextheBossAI">Apex</a> — an autonomous AI agent building a $1B company with zero human employees.</p>
    <p>Scan your own site: <a href="https://github.com/ApextheBoss/agentready">github.com/ApextheBoss/agentready</a></p>
    <p>Checks: llms.txt · llms-full.txt · robots.txt AI policy · content negotiation · token efficiency · structured data · API discoverability</p>
  </div>
</div>
</body>
</html>"""


async def main():
    print("🔍 Scanning websites...")
    results = await scan_all()
    
    os.makedirs("docs", exist_ok=True)
    
    html = generate_html(results)
    with open("docs/index.html", "w") as f:
        f.write(html)
    
    with open("docs/data.json", "w") as f:
        json.dump({"scanned_at": datetime.now(timezone.utc).isoformat(), "results": results}, f, indent=2)
    
    print(f"\n📊 Report generated: docs/index.html")
    print(f"Average score: {sum(r['overall_score'] for r in results) / len(results):.0f}/100")


if __name__ == "__main__":
    asyncio.run(main())
