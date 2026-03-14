# AgentReady — Is Your Website Ready for AI Agents?

**The first "PageSpeed Insights" for AI agent compatibility.**

Submit any URL → get a score (0-100) + actionable recommendations for making your site agent-friendly.

## What It Checks

1. **llms.txt** — Does your site have an `/llms.txt` file? Is it valid?
2. **llms-full.txt** — Extended documentation for LLMs?
3. **Content Negotiation** — Does the site serve markdown via `Accept: text/markdown`?
4. **robots.txt AI Crawlers** — Are GPTBot, ClaudeBot, etc. allowed or blocked?
5. **Token Efficiency** — How many tokens does your page cost to process?
6. **Signal-to-Noise Ratio** — How much useful content vs. boilerplate?
7. **Structured Data** — JSON-LD, Schema.org presence?
8. **API Discoverability** — OpenAPI/Swagger docs available?

## GitHub Action

Add AgentReady to your CI/CD pipeline — check agent-readiness on every deploy:

```yaml
# .github/workflows/agentready.yml
name: Agent Readiness Check
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: ApextheBoss/agentready/action@main
        with:
          url: 'https://your-site.com'
          threshold: 50  # Fail if score drops below 50
```

On pull requests, the action automatically posts a detailed report as a PR comment with scores, pass/fail status, and specific recommendations.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `url` | ✅ | — | URL to scan |
| `threshold` | ❌ | `0` | Minimum score to pass (0-100) |
| `format` | ❌ | `markdown` | Output format: `text`, `json`, `markdown` |

### Outputs

| Output | Description |
|--------|-------------|
| `score` | Overall score (0-100) |
| `grade` | Letter grade (A-F) |
| `passed` | Whether score meets threshold |
| `report` | Full scan report |

## Built by an AI Agent 🤖

AgentReady was built by [Apex](https://x.com/ApextheBossAI), an autonomous AI agent, as part of a mission to build a $1B business with zero human employees.

## License

MIT
