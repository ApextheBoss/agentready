"""
AgentReady Scanner — Score any website's AI agent readiness.
Zero dependencies beyond stdlib + httpx.
"""

import httpx
import re
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urlparse, urljoin


@dataclass
class Check:
    name: str
    score: int  # 0-100
    max_score: int
    status: str  # pass, warn, fail
    detail: str
    recommendation: str = ""


@dataclass
class ScanResult:
    url: str
    overall_score: int = 0
    grade: str = "F"
    checks: list = field(default_factory=list)
    scan_time_ms: int = 0
    scanned_at: str = ""

    def to_dict(self):
        return asdict(self)


AI_CRAWLERS = [
    "GPTBot", "ChatGPT-User", "Google-Extended", "ClaudeBot",
    "Anthropic-AI", "CCBot", "PerplexityBot", "Bytespider",
    "Amazonbot", "FacebookBot", "cohere-ai",
]


async def check_llms_txt(client: httpx.AsyncClient, base_url: str) -> Check:
    """Check for /llms.txt presence and validity."""
    url = urljoin(base_url, "/llms.txt")
    try:
        r = await client.get(url, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            content = r.text.strip()
            if len(content) < 10:
                return Check("llms.txt", 5, 15, "warn", "Found but nearly empty", "Add meaningful content describing your site for LLMs")
            # Check if it's valid markdown with links
            has_links = bool(re.findall(r'\[.*?\]\(.*?\)', content))
            has_headings = bool(re.findall(r'^#+\s', content, re.MULTILINE))
            if has_links and has_headings:
                return Check("llms.txt", 15, 15, "pass", f"Valid llms.txt ({len(content)} chars, has links and structure)")
            elif has_links or has_headings:
                return Check("llms.txt", 10, 15, "warn", f"Found ({len(content)} chars) but missing {'links' if not has_links else 'headings'}", "Add markdown links to detailed docs and section headings")
            else:
                return Check("llms.txt", 7, 15, "warn", f"Found ({len(content)} chars) but no structure", "Add markdown headings and links to detailed documentation pages")
        return Check("llms.txt", 0, 15, "fail", f"Not found (HTTP {r.status_code})", "Create /llms.txt with a markdown overview of your site. See llmstxt.org")
    except Exception as e:
        return Check("llms.txt", 0, 15, "fail", f"Error: {e}", "Create /llms.txt — see llmstxt.org for the standard")


async def check_llms_full_txt(client: httpx.AsyncClient, base_url: str) -> Check:
    """Check for /llms-full.txt presence."""
    url = urljoin(base_url, "/llms-full.txt")
    try:
        r = await client.get(url, follow_redirects=True, timeout=10)
        if r.status_code == 200 and len(r.text.strip()) > 50:
            return Check("llms-full.txt", 10, 10, "pass", f"Found ({len(r.text)} chars)")
        return Check("llms-full.txt", 0, 10, "fail", "Not found", "Create /llms-full.txt with expanded content from all linked pages in llms.txt")
    except:
        return Check("llms-full.txt", 0, 10, "fail", "Not found", "Create /llms-full.txt")


async def check_robots_txt(client: httpx.AsyncClient, base_url: str) -> Check:
    """Check robots.txt for AI crawler policies."""
    url = urljoin(base_url, "/robots.txt")
    try:
        r = await client.get(url, follow_redirects=True, timeout=10)
        if r.status_code != 200:
            return Check("robots.txt AI Policy", 10, 15, "warn", "No robots.txt found", "Consider adding robots.txt with explicit AI crawler policies")

        content = r.text.lower()
        blocked = []
        allowed = []
        for crawler in AI_CRAWLERS:
            if f"user-agent: {crawler.lower()}" in content:
                # Check if disallowed
                lines = content.split('\n')
                in_block = False
                for line in lines:
                    if f"user-agent: {crawler.lower()}" in line:
                        in_block = True
                    elif line.strip().startswith("user-agent:"):
                        in_block = False
                    elif in_block and "disallow: /" in line:
                        blocked.append(crawler)
                        in_block = False
                        break
                else:
                    if in_block:
                        allowed.append(crawler)

        if blocked and not allowed:
            return Check("robots.txt AI Policy", 3, 15, "fail", f"Blocks AI crawlers: {', '.join(blocked)}", "Consider allowing AI crawlers to improve agent accessibility")
        elif blocked:
            return Check("robots.txt AI Policy", 8, 15, "warn", f"Allows: {', '.join(allowed[:3])}. Blocks: {', '.join(blocked[:3])}", "Review which AI crawlers you want to allow")
        elif allowed:
            return Check("robots.txt AI Policy", 15, 15, "pass", f"Explicitly allows: {', '.join(allowed[:5])}")
        else:
            return Check("robots.txt AI Policy", 10, 15, "warn", "No explicit AI crawler rules", "Add User-agent rules for GPTBot, ClaudeBot, etc.")

    except:
        return Check("robots.txt AI Policy", 5, 15, "warn", "Could not fetch robots.txt")


async def check_content_negotiation(client: httpx.AsyncClient, base_url: str) -> Check:
    """Check if site supports text/markdown content negotiation."""
    try:
        r = await client.get(base_url, headers={"Accept": "text/markdown"}, follow_redirects=True, timeout=10)
        content_type = r.headers.get("content-type", "")
        if "text/markdown" in content_type:
            return Check("Content Negotiation", 15, 15, "pass", "Serves markdown via Accept: text/markdown")
        # Also check .md extension
        parsed = urlparse(base_url)
        md_url = base_url.rstrip('/') + "/index.html.md"
        r2 = await client.get(md_url, follow_redirects=True, timeout=10)
        if r2.status_code == 200 and "<!DOCTYPE" not in r2.text[:100]:
            return Check("Content Negotiation", 10, 15, "warn", "Supports .md extension but not Accept header", "Add Accept: text/markdown content negotiation support")
        return Check("Content Negotiation", 0, 15, "fail", "No markdown content negotiation", "Serve markdown versions via Accept: text/markdown header or .md URL extensions")
    except:
        return Check("Content Negotiation", 0, 15, "fail", "Could not test content negotiation")


async def check_token_efficiency(client: httpx.AsyncClient, base_url: str) -> Check:
    """Estimate how token-efficient the page is for LLMs."""
    try:
        r = await client.get(base_url, follow_redirects=True, timeout=10)
        html = r.text
        html_size = len(html)

        # Strip tags to get text content
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text_size = len(text)

        if html_size == 0:
            return Check("Token Efficiency", 0, 15, "fail", "Empty page")

        ratio = text_size / html_size
        # Rough token estimate (1 token ≈ 4 chars)
        estimated_tokens = text_size // 4

        if ratio > 0.4:
            return Check("Token Efficiency", 15, 15, "pass", f"Good signal-to-noise: {ratio:.0%} text content ({estimated_tokens:,} est. tokens)")
        elif ratio > 0.2:
            return Check("Token Efficiency", 10, 15, "warn", f"Moderate: {ratio:.0%} text ({estimated_tokens:,} est. tokens)", "Reduce boilerplate HTML/JS to improve token efficiency for LLMs")
        else:
            return Check("Token Efficiency", 5, 15, "fail", f"Poor: {ratio:.0%} text ({estimated_tokens:,} est. tokens)", "Heavy page — consider serving a stripped-down version for AI agents")
    except:
        return Check("Token Efficiency", 0, 15, "fail", "Could not analyze page content")


async def check_structured_data(client: httpx.AsyncClient, base_url: str) -> Check:
    """Check for structured data (JSON-LD, schema.org)."""
    try:
        r = await client.get(base_url, follow_redirects=True, timeout=10)
        html = r.text

        has_jsonld = bool(re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>', html))
        has_schema = "schema.org" in html
        has_opengraph = bool(re.findall(r'<meta[^>]*property=["\']og:', html))

        score = 0
        found = []
        if has_jsonld:
            score += 7
            found.append("JSON-LD")
        if has_schema:
            score += 5
            found.append("Schema.org")
        if has_opengraph:
            score += 3
            found.append("OpenGraph")

        score = min(score, 15)

        if found:
            return Check("Structured Data", score, 15, "pass" if score >= 10 else "warn", f"Found: {', '.join(found)}", "" if score >= 10 else "Add JSON-LD structured data for better agent understanding")
        return Check("Structured Data", 0, 15, "fail", "No structured data found", "Add JSON-LD with schema.org types to help agents understand your content")
    except:
        return Check("Structured Data", 0, 15, "fail", "Could not check structured data")


async def check_api_docs(client: httpx.AsyncClient, base_url: str) -> Check:
    """Check for API documentation discoverability."""
    api_paths = [
        "/openapi.json", "/swagger.json", "/api-docs", "/docs",
        "/api", "/.well-known/openapi.json", "/openapi.yaml",
    ]
    found = []
    try:
        for path in api_paths:
            url = urljoin(base_url, path)
            try:
                r = await client.get(url, follow_redirects=True, timeout=5)
                if r.status_code == 200:
                    found.append(path)
            except:
                continue

        if found:
            return Check("API Discoverability", 5, 5, "pass", f"API docs at: {', '.join(found)}")
        return Check("API Discoverability", 0, 5, "warn", "No standard API documentation endpoints found", "If you have an API, publish OpenAPI/Swagger docs at /openapi.json")
    except:
        return Check("API Discoverability", 0, 5, "warn", "Could not check API documentation")


async def scan(url: str) -> ScanResult:
    """Run all checks against a URL and return scored result."""
    start = time.time()

    # Normalize URL
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    result = ScanResult(url=url)

    async with httpx.AsyncClient(
        headers={"User-Agent": "AgentReady/1.0 (https://agentready.dev)"},
        verify=False,
    ) as client:
        checks = [
            check_llms_txt(client, base_url),
            check_llms_full_txt(client, base_url),
            check_robots_txt(client, base_url),
            check_content_negotiation(client, base_url),
            check_token_efficiency(client, base_url),
            check_structured_data(client, base_url),
            check_api_docs(client, base_url),
        ]

        import asyncio
        results = await asyncio.gather(*checks, return_exceptions=True)

        for r in results:
            if isinstance(r, Check):
                result.checks.append(r)
            else:
                result.checks.append(Check("Error", 0, 10, "fail", str(r)))

    total_score = sum(c.score for c in result.checks)
    max_score = sum(c.max_score for c in result.checks)
    result.overall_score = round((total_score / max_score) * 100) if max_score > 0 else 0

    if result.overall_score >= 90:
        result.grade = "A"
    elif result.overall_score >= 75:
        result.grade = "B"
    elif result.overall_score >= 60:
        result.grade = "C"
    elif result.overall_score >= 40:
        result.grade = "D"
    else:
        result.grade = "F"

    result.scan_time_ms = int((time.time() - start) * 1000)
    result.scanned_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return result


def format_report(result: ScanResult) -> str:
    """Format scan result as a readable text report."""
    lines = [
        f"# AgentReady Score: {result.overall_score}/100 (Grade: {result.grade})",
        f"URL: {result.url}",
        f"Scanned: {result.scanned_at} ({result.scan_time_ms}ms)",
        "",
        "## Results",
        "",
    ]

    icons = {"pass": "✅", "warn": "⚠️", "fail": "❌"}

    for c in result.checks:
        lines.append(f"{icons.get(c.status, '?')} **{c.name}** — {c.score}/{c.max_score}")
        lines.append(f"   {c.detail}")
        if c.recommendation:
            lines.append(f"   → {c.recommendation}")
        lines.append("")

    recs = [c for c in result.checks if c.recommendation and c.status != "pass"]
    if recs:
        lines.append("## Top Recommendations")
        lines.append("")
        for i, c in enumerate(sorted(recs, key=lambda x: x.score), 1):
            lines.append(f"{i}. **{c.name}**: {c.recommendation}")

    return "\n".join(lines)


if __name__ == "__main__":
    import asyncio
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://anthropic.com"
    result = asyncio.run(scan(url))
    print(format_report(result))
