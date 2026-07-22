
"""
Financial News Analysis & Rating App
-------------------------------------
CrewAI + NVIDIA NIM (pure Python, single file, no fancy UI).

Pipeline:
1. News Researcher agent scrapes Yahoo Finance news for a ticker.
2. Financial Analyst agent rates each article (sentiment + impact score).
3. Market Strategist agent gives a general market perspective.
4. Human-in-the-loop review before the report is saved.
"""

import os
import json
from typing import List

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()

# ---------------------------------------------------------------------------
# 1. LLM CONFIG — NVIDIA NIM via CrewAI's native LLM class (litellm backend)
# ---------------------------------------------------------------------------
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")

llm = LLM(
    model=f"nvidia_nim/{NVIDIA_MODEL}",   # litellm provider prefix
    api_key=os.getenv("NVIDIA_NIM_API_KEY"),
    temperature=0.3,
)

# ---------------------------------------------------------------------------
# 2. STRUCTURED OUTPUT SCHEMAS (Pydantic) — this IS the "structured JSON"
# ---------------------------------------------------------------------------
class NewsItem(BaseModel):
    title: str
    url: str
    summary: str = ""
    published: str = ""

class ScrapedNews(BaseModel):
    ticker: str
    articles: List[NewsItem]

class RatedNewsItem(BaseModel):
    title: str
    url: str
    sentiment: str = Field(description="Positive, Negative, or Neutral")
    rating: int = Field(description="Impact/importance score from 1 to 10")
    rationale: str

class AnalyzedNews(BaseModel):
    ticker: str
    rated_articles: List[RatedNewsItem]

class MarketPerspective(BaseModel):
    ticker: str
    overall_sentiment: str = Field(description="Bullish, Bearish, or Neutral")
    confidence_score: int = Field(description="1 to 10")
    summary: str
    key_drivers: List[str]

# ---------------------------------------------------------------------------
# 3. TOOL — Yahoo Finance scraper (with yfinance as safety-net fallback)
# ---------------------------------------------------------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

def _scrape_yahoo_html(ticker: str) -> list:
    url = f"https://finance.yahoo.com/quote/{ticker}/news/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    candidates = (
        soup.select('div[data-testid="storyitem"]')
        or soup.select("li.js-stream-content")
        or soup.find_all("h3")
    )

    results = []
    for c in candidates[:10]:
        link_tag = c.find("a", href=True)
        title_tag = c.find("h3") or c
        title = title_tag.get_text(strip=True) if title_tag else None
        href = link_tag["href"] if link_tag else None
        if href and href.startswith("/"):
            href = "https://finance.yahoo.com" + href
        summary_tag = c.find("p")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        if title and href:
            results.append({"title": title, "url": href, "summary": summary, "published": ""})
    return results

def _scrape_yahoo_fallback(ticker: str) -> list:
    """Fallback using yfinance if HTML scraping is blocked/DOM changed."""
    import yfinance as yf
    t = yf.Ticker(ticker)
    news = t.news or []
    return [
        {
            "title": n.get("title", ""),
            "url": n.get("link", ""),
            "summary": n.get("publisher", ""),
            "published": str(n.get("providerPublishTime", "")),
        }
        for n in news[:10]
    ]

@tool("Yahoo Finance News Scraper")
def scrape_yahoo_finance_news(ticker: str) -> str:
    """Scrapes the latest news headlines, links and summaries for a given
    stock ticker (e.g. NVDA, AAPL, TSLA) from Yahoo Finance. Returns a JSON
    string list of articles."""
    try:
        articles = _scrape_yahoo_html(ticker)
        if not articles:
            raise ValueError("No articles found via HTML scraping.")
    except Exception:
        articles = _scrape_yahoo_fallback(ticker)

    return json.dumps({"ticker": ticker, "articles": articles})

# ---------------------------------------------------------------------------
# 4. AGENTS
# ---------------------------------------------------------------------------
news_researcher = Agent(
    role="Senior Financial News Researcher",
    goal="Find the latest, most relevant news for stock ticker {ticker}",
    backstory="You are meticulous about sourcing real, current financial news "
              "and always return clean structured data, never fabricated news.",
    tools=[scrape_yahoo_finance_news],
    llm=llm,
    verbose=True,
)

financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Rate each news article's sentiment and market impact for {ticker}",
    backstory="A 15-year equity analyst who rates news 1 (irrelevant) to "
              "10 (major market mover) with clear, concise justification.",
    llm=llm,
    verbose=True,
)

market_strategist = Agent(
    role="Chief Market Strategist",
    goal="Summarize a general market perspective for {ticker} based on rated news",
    backstory="You advise investment committees. You synthesize noisy news "
              "into one clear bullish/bearish/neutral call with key drivers.",
    llm=llm,
    verbose=True,
)

# ---------------------------------------------------------------------------
# 5. TASKS
# ---------------------------------------------------------------------------
research_task = Task(
    description=(
        "Use the Yahoo Finance News Scraper tool to fetch the latest news "
        "for ticker '{ticker}'. Return the raw list of articles."
    ),
    expected_output="A JSON object with ticker and a list of articles "
                    "(title, url, summary, published).",
    agent=news_researcher,
    output_pydantic=ScrapedNews,
)

analysis_task = Task(
    description=(
        "Review each article gathered for '{ticker}'. For every article, "
        "assign: sentiment (Positive/Negative/Neutral), rating (1-10 impact "
        "on the stock/market), and a one-sentence rationale."
    ),
    expected_output="A JSON object with ticker and rated_articles list "
                    "(title, url, sentiment, rating, rationale).",
    agent=financial_analyst,
    context=[research_task],
    output_pydantic=AnalyzedNews,
)

perspective_task = Task(
    description=(
        "Based on the rated articles for '{ticker}', produce one overall "
        "general market perspective: overall_sentiment (Bullish/Bearish/"
        "Neutral), confidence_score (1-10), a short summary paragraph, and "
        "a list of the top 3 key drivers."
    ),
    expected_output="A JSON object matching the MarketPerspective schema.",
    agent=market_strategist,
    context=[analysis_task],
    output_pydantic=MarketPerspective,
    human_input=True,  # <-- native CrewAI human-in-the-loop checkpoint
)

# ---------------------------------------------------------------------------
# 6. CREW
# ---------------------------------------------------------------------------
crew = Crew(
    agents=[news_researcher, financial_analyst, market_strategist],
    tasks=[research_task, analysis_task, perspective_task],
    process=Process.sequential,
    verbose=True,
)

# ---------------------------------------------------------------------------
# 7. MAIN — run + manual human approval gate before saving
# ---------------------------------------------------------------------------
def main():
    ticker = input("Enter stock ticker (e.g. NVDA, AAPL, TSLA): ").strip().upper() or "NVDA"

    result = crew.kickoff(inputs={"ticker": ticker})

    # Try to get validated Pydantic object; fallback to raw text
    try:
        final_obj = result.pydantic.model_dump()
    except Exception:
        final_obj = {"raw_output": result.raw}

    print("\n" + "=" * 60)
    print("FINAL MARKET PERSPECTIVE REPORT")
    print("=" * 60)
    print(json.dumps(final_obj, indent=2))
    print("=" * 60)

    # Second, explicit human-in-the-loop gate before persisting anything
    approve = input("\nApprove and save this report to disk? (y/n): ").strip().lower()
    if approve == "y":
        filename = f"report_{ticker}.json"
        with open(filename, "w") as f:
            json.dump(final_obj, f, indent=2)
        print(f"Saved to {filename}")
    else:
        print("Discarded. Re-run the app to try again.")


if __name__ == "__main__":
    main()
