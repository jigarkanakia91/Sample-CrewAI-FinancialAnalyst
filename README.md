# Sample-CrewAI-FinancialAnalyst

A **multi-agent AI system** for financial news analysis and market sentiment assessment, powered by **CrewAI** and **NVIDIA NIM**.

## 🎯 Project Purpose

This project demonstrates a practical application of multi-agent AI workflows to automate financial analysis. It combines autonomous agents with human-in-the-loop validation to:

- **Scrape** the latest financial news from Yahoo Finance for any stock ticker
- **Analyze** each article for sentiment (Positive/Negative/Neutral) and market impact (1-10 rating)
- **Synthesize** individual analyses into a unified market perspective with bullish/bearish signals
- **Validate** results through human review before saving to disk

The pipeline showcases CrewAI's task orchestration, structured output validation, and human-in-the-loop approval gates—all in a single, pure Python implementation.

## 🏗️ Architecture

The system uses three autonomous agents working in sequence:

1. **News Researcher Agent** — Fetches the latest news headlines, summaries, and URLs for a given stock ticker
2. **Financial Analyst Agent** — Rates each article for sentiment and impact on the stock/market
3. **Market Strategist Agent** — Synthesizes findings into a single market outlook with confidence scores and key drivers

All agents are coordinated by CrewAI's sequential process engine and produce **validated Pydantic models** for structured, type-safe output.

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Agent Framework** | [CrewAI](https://github.com/joaomdmoura/crewai) (v0.86.0+) | Multi-agent orchestration and task management |
| **LLM Backend** | [NVIDIA NIM](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-foundation-models/containers/nim) (Llama 3.1 70B) | Language model inference via API |
| **LLM Integration** | CrewAI's native LLM class (litellm backend) | Seamless NVIDIA NIM support |
| **Web Scraping** | [Requests](https://requests.readthedocs.io/) + [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) + [LXML](https://lxml.de/) | HTML parsing & news extraction |
| **Fallback Data** | [yfinance](https://github.com/ranaroussi/yfinance) | Alternative news source if scraping fails |
| **Data Validation** | [Pydantic](https://docs.pydantic.dev/) (v2.6+) | Structured output schemas & validation |
| **Configuration** | [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |

## 📋 Requirements

```
crewai>=0.86.0
crewai-tools>=0.17.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
python-dotenv>=1.0.0
yfinance>=0.2.40
pydantic>=2.6.0
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/jigarkanakia91/Sample-CrewAI-FinancialAnalyst.git
cd Sample-CrewAI-FinancialAnalyst
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your NVIDIA NIM API key:

```
NVIDIA_NIM_API_KEY=your_api_key_here
NVIDIA_MODEL=meta/llama-3.1-70b-instruct
```

Obtain your API key from [NVIDIA NGC](https://catalog.ngc.nvidia.com/).

### 3. Run the Analysis

```bash
python app.py
```

**Example interaction:**

```
Enter stock ticker (e.g. NVDA, AAPL, TSLA): NVDA

[... CrewAI agents run sequentially ...]

============================================================
FINAL MARKET PERSPECTIVE REPORT
============================================================
{
  "ticker": "NVDA",
  "overall_sentiment": "Bullish",
  "confidence_score": 8,
  "summary": "Strong positive momentum driven by AI demand...",
  "key_drivers": ["AI chip demand", "Revenue growth", "Market expansion"]
}
============================================================

Approve and save this report to disk? (y/n): y
Saved to report_NVDA.json
```

## 📊 Output Structure

The system produces structured JSON reports with the following schema:

```json
{
  "ticker": "NVDA",
  "overall_sentiment": "Bullish|Bearish|Neutral",
  "confidence_score": 8,
  "summary": "One-paragraph market outlook",
  "key_drivers": ["Driver 1", "Driver 2", "Driver 3"]
}
```

Each rated article includes:
- **title** — Article headline
- **url** — Link to full article
- **sentiment** — Positive, Negative, or Neutral
- **rating** — Impact score (1-10)
- **rationale** — One-sentence explanation

## 🔄 Workflow Process

```
┌─────────────────────────────────────────┐
│  User inputs ticker (e.g., NVDA)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  News Researcher Agent                  │
│  → Scrapes Yahoo Finance news           │
│  → Returns list of articles             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Financial Analyst Agent                │
│  → Rates sentiment & impact             │
│  → Produces scored articles             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Market Strategist Agent                │
│  → Synthesizes perspective              │
│  → Assigns bullish/bearish outlook      │
│  → [HUMAN-IN-THE-LOOP GATE]             │
└──────────────┬──────────────────────────┘
               │
         ┌─────┴─────┐
         │           │
         ▼           ▼
      [YES]       [NO]
         │           │
         ▼           ▼
   Save Report    Discard &
    to Disk       Retry
```

## 🔐 Human-in-the-Loop Validation

The system includes **two levels of human oversight**:

1. **CrewAI Native Gate** — The `perspective_task` has `human_input=True`, prompting for approval within the agent loop
2. **Application Gate** — After all agents complete, users explicitly approve before persisting reports to disk

This ensures high-quality, reviewed output before any data is committed.

## 🛠️ Key Features

✅ **Pure Python, Single File** — No external UI frameworks; run from CLI  
✅ **Structured Validation** — Pydantic models ensure type-safe, validated output  
✅ **Graceful Fallback** — Falls back to yfinance if HTML scraping is blocked  
✅ **Sequential Agent Orchestration** — Tasks execute in logical order with context passing  
✅ **Human Review Gates** — Multiple checkpoints for manual validation  
✅ **NVIDIA NIM Integration** — Demonstrates cutting-edge AI infrastructure  

## 📝 Example Report

After running the analysis and approving, a file like `report_NVDA.json` is saved:

```json
{
  "ticker": "NVDA",
  "rated_articles": [
    {
      "title": "NVIDIA Stock Surges on AI Demand",
      "url": "https://finance.yahoo.com/...",
      "sentiment": "Positive",
      "rating": 9,
      "rationale": "Strong earnings and continued AI infrastructure growth."
    },
    {
      "title": "Chip Shortage Concerns Weigh on Sector",
      "url": "https://finance.yahoo.com/...",
      "sentiment": "Negative",
      "rating": 6,
      "rationale": "Potential supply chain disruptions may impact margins."
    }
  ],
  "overall_sentiment": "Bullish",
  "confidence_score": 8,
  "summary": "NVIDIA remains a market leader with strong fundamentals driven by AI demand...",
  "key_drivers": ["AI Growth", "Earnings Beat", "Supply Chain Stability"]
}
```

## 🤖 Agent Details

### News Researcher
- **Role:** Senior Financial News Researcher
- **Tools:** Yahoo Finance News Scraper
- **Output:** Structured list of recent articles with metadata

### Financial Analyst
- **Role:** Senior Financial Analyst
- **Goal:** Rate sentiment and market impact of each article
- **Experience:** 15+ years in equity analysis (backstory)

### Market Strategist
- **Role:** Chief Market Strategist
- **Goal:** Synthesize findings into unified market outlook
- **Audience:** Investment committees and decision-makers

## 🔧 Configuration

Edit the following in `app.py` to customize:

```python
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
llm = LLM(
    model=f"nvidia_nim/{NVIDIA_MODEL}",
    temperature=0.3,  # Lower = more deterministic
)
```

Or override via `.env`:
```
NVIDIA_MODEL=meta/llama-3.1-405b-instruct  # Use 405B model instead
```

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report issues and suggest improvements
- Submit pull requests with enhancements
- Fork and adapt for your use case

## 📚 Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [NVIDIA NIM Catalog](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-foundation-models/containers/nim)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [BeautifulSoup4 Guide](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## ⚠️ Disclaimer

This project is for educational and research purposes. It is not financial advice. Always conduct your own due diligence before making investment decisions. The AI-generated analyses are informational and should not be solely relied upon for trading or investment decisions.

---

**Built with ❤️ using CrewAI and NVIDIA NIM**
