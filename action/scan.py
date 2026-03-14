#!/usr/bin/env python3
"""AgentReady GitHub Action scanner — standalone, no external deps beyond httpx."""

import asyncio
import json
import os
import sys
import re
import time
from urllib.parse import urlparse, urljoin

import httpx

AI_CRAWLERS = [
    "GPTBot", "ChatGPT-User", "Google-Extended", "ClaudeBot",
    "Anthropic-AI", "CCBot", "PerplexityBot", "Bytespider",
    "Amazonbot", "FacebookBot", "cohere-ai",
]


async def check_llms_txt(client, base_url):
    url = urljoin(base_url, "/llms.txt")
    try:
        r = await client.get(url, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            text = r.text
            has_links = bool(re.findall(r'\[.*?\]\(.*?\)', text))
            has_sections = text.count('#') >= 2
            quality = 100 if (has_links and has_sections) else 70 if has_links else 50
            return {"name": "llms.txt", "score": quality, "max": 100, "status": "pass",
                    "detail": f"Found /llms.txt ({len(text)} chars)", "rec": ""}
        return {"name": "llms.txt", "score": 0, "max": 100, "status": "fail",
                "detail": f"No /llms.txt (HTTP {r.status_code})",
                "rec": "Add /llms.txt — see https://llmstxt.org"}
    except Exception as e:
        return {"name": "llms.txt", "score": 0, "max": 100, "status": "fail",
                "detail": str(e), "rec": "Add /llms.txt"}


async def check_llms_full_txt(client, base_url):
    url = urljoin(base_url, "/llms-full.txt")
    try:
        r = await client.get(url, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            return {"name": "llms-full.txt", "score": 100, "max": 100, "status": "pass",
                    "detail": f"Found ({len(r.text)} chars)", "rec": ""}
        return {"name": "llms-full.txt", "score": 0, "max": 100, "status": "warn",
                "detail": "Not found", "rec": "Add /llms-full.txt for comprehensive content"}
    except Exception:
        return {"name": "llms-full.txt", "score": 0, "max": 100, "status": "warn",
                "detail": "Not found", "rec": "Add /llms-full.txt"}


async def check_robots_txt(client, base_url):
    url = urljoin(base_url, "/robots.txt")
    try:
        r = await client.get(url, follow_redirects=True, timeout=10)
        if r.status_code != 200:
            return {"name": "robots.txt AI crawlers", "score": 50, "max": 100, "status": "warn",
                    "detail": "No robots.txt", "rec": "Add robots.txt with AI crawler rules"}
        text = r.text.lower()
        blocked = [c for c in AI_CRAWLERS if c.lower() in text and "disallow" in text]
        allowed = [c for c in AI_CRAWLERS if c.lower() not in text or "allow" in text]
        if len(blocked) == 0:
            return {"name": "robots.txt AI crawlers", "score": 100, "max": 100, "status": "pass",
                    "detail": "No AI crawlers blocked", "rec": ""}
        ratio = len(blocked) / len(AI_CRAWLERS)
        score = int(100 * (1 - ratio))
        return {"name": "robots.txt AI crawlers", "score": score, "max": 100, "status": "warn",
                "detail": f"Blocked: {', '.join(blocked)}", "rec": "Consider allowing AI crawlers"}
    except Exception:
        return {"name": "robots.txt AI crawlers", "score": 50, "max": 100, "status": "warn",
                "detail": "Could not fetch", "rec": ""}


async def check_content_negotiation(client, base_url):
    try:
        r = await client.get(base_url, headers={"Accept": "text/markdown"}, follow_redirects=True, timeout=10)
        ct = r.headers.get("content-type", "")
        if "markdown" in ct:
            return {"name": "Content negotiation", "score": 100, "max": 100, "status": "pass",
                    "detail": "Supports text/markdown", "rec": ""}
        return {"name": "Content negotiation", "score": 0, "max": 100, "status": "fail",
                "detail": f"Returns {ct}", "rec": "Support Accept: text/markdown for AI-friendly content"}
    except Exception:
        return {"name": "Content negotiation", "score": 0, "max": 100, "status": "fail",
                "detail": "Error", "rec": "Support Accept: text/markdown"}


async def check_structured_data(client, base_url):
    try:
        r = await client.get(base_url, follow_redirects=True, timeout=10)
        html = r.text
        has_jsonld = "application/ld+json" in html
        has_schema = "schema.org" in html
        has_og = 'property="og:' in html or "property='og:" in html
        score = 0
        if has_jsonld: score += 40
        if has_schema: score += 30
        if has_og: score += 30
        status = "pass" if score >= 70 else "warn" if score > 0 else "fail"
        return {"name": "Structured data", "score": score, "max": 100, "status": status,
                "detail": f"JSON-LD: {'✓' if has_jsonld else '✗'}, Schema.org: {'✓' if has_schema else '✗'}, OpenGraph: {'✓' if has_og else '✗'}",
                "rec": "" if score >= 70 else "Add JSON-LD structured data and OpenGraph tags"}
    except Exception:
        return {"name": "Structured data", "score": 0, "max": 100, "status": "fail",
                "detail": "Error", "rec": "Add structured data"}


async def scan(url):
    start = time.time()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    async with httpx.AsyncClient(headers={"User-Agent": "AgentReady/1.0"}) as client:
        checks = await asyncio.gather(
            check_llms_txt(client, base),
            check_llms_full_txt(client, base),
            check_robots_txt(client, base),
            check_content_negotiation(client, base),
            check_structured_data(client, base),
        )

    weights = {"llms.txt": 30, "llms-full.txt": 15, "robots.txt AI crawlers": 20,
               "Content negotiation": 20, "Structured data": 15}
    total = 0
    for c in checks:
        w = weights.get(c["name"], 15)
        total += (c["score"] / c["max"]) * w

    score = int(total)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    elapsed = int((time.time() - start) * 1000)

    return {"url": url, "score": score, "grade": grade, "checks": checks, "time_ms": elapsed}


def format_markdown(result):
    lines = [
        f"# 🤖 AgentReady Score: {result['score']}/100 ({result['grade']})",
        f"**URL:** {result['url']}",
        "",
        "| Check | Score | Status | Detail |",
        "|-------|-------|--------|--------|",
    ]
    for c in result["checks"]:
        icon = "✅" if c["status"] == "pass" else "⚠️" if c["status"] == "warn" else "❌"
        lines.append(f"| {c['name']} | {c['score']}/{c['max']} | {icon} | {c['detail']} |")

    recs = [c for c in result["checks"] if c.get("rec")]
    if recs:
        lines.extend(["", "### Recommendations"])
        for c in recs:
            lines.append(f"- **{c['name']}:** {c['rec']}")

    lines.append(f"\n*Scanned in {result['time_ms']}ms by [AgentReady](https://github.com/ApextheBoss/agentready)*")
    return "\n".join(lines)


async def main():
    url = os.environ.get("SCAN_URL", "")
    threshold = int(os.environ.get("THRESHOLD", "0"))
    fmt = os.environ.get("FORMAT", "markdown")

    if not url:
        print("Error: SCAN_URL not set")
        sys.exit(1)

    result = await scan(url)
    passed = result["score"] >= threshold

    # GitHub Actions outputs
    gh_output = os.environ.get("GITHUB_OUTPUT", "")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"score={result['score']}\n")
            f.write(f"grade={result['grade']}\n")
            f.write(f"passed={str(passed).lower()}\n")

    # Generate report
    if fmt == "json":
        report = json.dumps(result, indent=2)
    elif fmt == "markdown":
        report = format_markdown(result)
    else:
        report = f"AgentReady Score: {result['score']}/100 ({result['grade']})"
        for c in result["checks"]:
            report += f"\n  {c['name']}: {c['score']}/{c['max']} ({c['status']})"

    print(report)

    # Save for PR comment
    with open("/tmp/agentready-report.md", "w") as f:
        f.write(format_markdown(result))

    # GitHub Actions step summary
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(format_markdown(result))

    if not passed:
        print(f"\n❌ Score {result['score']} is below threshold {threshold}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
