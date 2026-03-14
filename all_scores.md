# AgentReady: The State of AI Agent Readiness (March 2026)

**66 tech websites scanned. Average score: 36/100. The web is not ready for AI agents.**

## The Data

### AI Companies (The Irony)
| Site | Score | Grade |
|------|-------|-------|
| openai.com | 17 | F |
| perplexity.ai | 17 | F |
| crewai.com | 20 | F |
| platform.openai.com | 22 | F |
| groq.com | 26 | F |
| anthropic.com | 26 | F |
| huggingface.co | 26 | F |
| langchain.com | 26 | F |
| stability.ai | 33 | F |
| mistral.ai | 37 | F |
| autogen.microsoft.com | 41 | D |
| docs.anthropic.com | 42 | D |
| cursor.com | 50 | D |
| cohere.com | 50 | D |
| docs.langchain.com | 70 | C |

### Dev Tools & Platforms
| Site | Score | Grade |
|------|-------|-------|
| midjourney.com | 17 | F |
| fly.io | 22 | F |
| notion.so | 34 | F |
| figma.com | 31 | F |
| github.com | 42 | D |
| cloudflare.com | 42 | D |
| supabase.com | 42 | D |
| posthog.com | 42 | D |
| replit.com | 48 | D |
| shopify.com | 50 | D |
| eleven-labs.com | 50 | D |
| vercel.com | 53 | D |
| cal.com | 53 | D |
| railway.app | 56 | D |
| stripe.com | 56 | D |
| resend.com | 56 | D |
| dub.co | 58 | D |
| linear.app | 64 | C |

### Big Tech & Infrastructure
| Site | Score | Grade |
|------|-------|-------|
| hashicorp.com | 17 | F |
| aws.amazon.com | 20 | F |
| databricks.com | 20 | F |
| snowflake.com | 20 | F |
| google.com | 28 | F |
| learn.microsoft.com | 31 | F |
| grafana.com | 31 | F |
| microsoft.com | 33 | F |
| elastic.co | 39 | F |
| confluent.io | 39 | F |
| datadog.com | 42 | D |
| docs.aws.amazon.com | 44 | D |
| docs.github.com | 53 | D |
| twilio.com | 56 | D |
| modal.com | 59 | D |
| sentry.io | 74 | C |

## Key Findings
- **0 out of 66 sites scored an A or B**
- **Only 4 sites scored above D** (sentry.io, docs.langchain.com, linear.app, and one more)
- **Average score: ~36/100**
- **AI companies average: 33/100** — worse than the overall average
- The companies building AI agents can't even serve AI agents

## What We Check
1. `/llms.txt` — structured content description for LLMs
2. `/llms-full.txt` — expanded version
3. `robots.txt` — AI crawler permissions
4. Structured data (JSON-LD, OpenGraph)
5. Semantic HTML structure
6. API discoverability
7. Content accessibility (clean text extraction)

## Try It
- **CLI:** `pip install agentready` (coming soon)
- **GitHub Action:** `uses: ApextheBoss/agentready/action@main`
- **GitHub:** github.com/ApextheBoss/agentready
