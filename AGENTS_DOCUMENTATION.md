# AI Finance Assistant - Agents Documentation

**Status:** Phase 2A Complete  
**Last Updated:** January 14, 2026  
**Total Agents:** 3 Built + 3 Planned

---

## Table of Contents

1. [Finance Q&A Agent](#finance-qa-agent-phase-1) (Phase 1)
2. [Portfolio Analysis Agent](#portfolio-analysis-agent-phase-2a) (Phase 2A)
3. [Market Analysis Agent](#market-analysis-agent-phase-2a) (Phase 2A)
4. [Planned Agents](#planned-agents) (Phase 2B)

---

## Finance Q&A Agent (Phase 1)

### Purpose
Answers financial education questions using RAG (Retrieval-Augmented Generation) to provide accurate, cited information from the knowledge base.

### Use Cases
- "What is an ETF?"
- "How do I calculate portfolio allocation?"
- "What are capital gains taxes?"
- "What's the difference between mutual funds and ETFs?"
- "How should I rebalance my portfolio?"

### System Prompt
```
You are a financial education assistant with access to a knowledge base of finance articles.

Your role is to:
1. Answer financial questions accurately and clearly
2. Use retrieved articles to support your answers
3. Explain concepts in simple, beginner-friendly terms
4. Provide citations for all information you use
5. Disclaim that this is educational, not financial advice

Guidelines:
- Always cite sources when you use information from articles
- Break down complex concepts into understandable parts
- Provide practical examples when helpful
- Be honest about limitations of your knowledge
- Suggest consulting a financial advisor for personal advice
```

### Input Format
```python
{
    "message": str,                          # User's question (required)
    "session_id": str,                       # Optional UUID for conversation
    "category_filter": str,                  # Optional (etfs, portfolio, tax, etc.)
    "conversation_history": List[ChatMessage]  # Optional previous messages
}
```

### Output Format
```python
AgentOutput(
    answer_text: str,        # Detailed answer with explanation
    citations: List[Dict],   # Sources used
                            # [{"title": "...", "source_url": "...", "category": "..."}]
    tool_calls_made: List[str],  # ["pinecone_retrieval", "openai_chat"]
    structured_data: Dict    # {"chunks_retrieved": int}
)
```

### Example Interaction

**User Query:**
```
What is an ETF and how does it differ from a mutual fund?
```

**Agent Processing:**
1. **Retrieve:** Query Pinecone for ETF-related articles
2. **Search:** Find top-5 matching chunks from knowledge base
3. **Filter:** Keep matches above 0.50 relevance threshold
4. **Generate:** Pass context + question to GPT-4o-mini
5. **Extract:** Pull citations from retrieved chunks
6. **Return:** Structured response with answer + sources

**Response:**
```json
{
  "session_id": "uuid-123",
  "message": "An ETF (Exchange-Traded Fund) is a type of investment fund...",
  "citations": [
    {
      "title": "Exchange-Traded Fund (ETF): What It Is and How to Invest",
      "source_url": "https://investopedia.com/terms/e/etf.asp",
      "category": "etfs"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "tools_used": ["pinecone_retrieval", "openai_chat"],
    "chunks_retrieved": 1
  }
}
```

### Dependencies
- **RAG Retriever:** Pinecone semantic search
- **LLM Provider:** OpenAI gpt-4o-mini
- **Knowledge Base:** 34 chunks from 25 financial articles

### Code Location
- File: `src/agents/finance_qa.py`
- Entry Point: `get_finance_qa_agent()`

### Key Capabilities
✅ Semantic search across knowledge base  
✅ Multi-turn conversation support  
✅ Source attribution  
✅ Graceful fallback (RAG failure → LLM-only answer)  
✅ Category filtering for focused results  
✅ Session tracking for conversation context

---

## Portfolio Analysis Agent (Phase 2A)

### Purpose
Analyzes investment portfolios to provide comprehensive metrics, diversification scoring, risk assessment, and rebalancing recommendations.

### Use Cases
- "Analyze my portfolio: 100 shares AAPL, 50 GOOGL, 200 BND"
- "What's my diversification score?"
- "Should I rebalance my portfolio?"
- "How concentrated is my portfolio in technology?"
- "What's my risk level based on my holdings?"

### System Prompt
```
You are a portfolio analysis assistant specializing in investment metrics.

Your role is to:
1. Analyze provided holdings for allocation and risk
2. Calculate diversification metrics using industry standards
3. Identify concentration risks
4. Provide rebalancing suggestions
5. Explain findings in clear, actionable terms

Key metrics you calculate:
- Asset allocation (percentage per holding)
- Diversification score (0-100, Herfindahl index)
- Risk level (low/moderate/high)
- Asset class distribution
- Concentration risk analysis
- Rebalancing recommendations

Guidelines:
- Use data-driven analysis
- Provide clear visual breakdowns (percentages)
- Flag concentration risks (>50% in single position)
- Suggest diversification if score <50
- Mention this is educational, not personal financial advice
```

### Input Format
```python
holdings_data = {
    "holdings": [
        {
            "ticker": str,              # Stock symbol (e.g., "AAPL")
            "quantity": float,          # Number of shares
            "current_price": float,     # Current market price
            "cost_basis": float         # Original purchase price (optional)
        },
        # ... more holdings
    ],
    "analysis_type": str  # "allocation"|"diversification"|"rebalance"|"full"
}
```

### Output Format
```python
AgentOutput(
    answer_text: str,  # Detailed narrative analysis
    structured_data: {
        "total_portfolio_value": float,
        "holdings_count": int,
        "allocation": [
            {
                "ticker": str,
                "quantity": float,
                "current_price": float,
                "position_value": float,
                "allocation_pct": float,
                "gain_loss": float
            }
        ],
        "diversification_score": float,      # 0-100
        "risk_level": str,                   # "low"|"moderate"|"high"
        "asset_class_distribution": {
            "large_cap": float,
            "small_cap": float,
            "bonds": float,
            "international": float,
            "commodities": float,
            "other": float
        },
        "total_return": float,
        "largest_position": {
            "ticker": str,
            "allocation_pct": float
        },
        "rebalancing": {  # Only if requested
            "required_trades": [...],
            "rebalance_urgency": "low|medium|high"
        }
    },
    tool_calls_made: ["market_data_retrieval", "portfolio_calculation"],
    citations: []  # No citations for calculated metrics
)
```

### Example Interaction

**User Query:**
```
Portfolio:
- 100 AAPL @ $189.95
- 50 GOOGL @ $141.20
- 200 BND @ $82.30
Analyze it.
```

**Agent Processing:**
1. **Parse Holdings:** Extract ticker, quantity, price
2. **Calculate Metrics:** 
   - Total value = (100 × 189.95) + (50 × 141.20) + (200 × 82.30) = $42,515
   - Allocation = [44.7% AAPL, 16.6% GOOGL, 38.7% BND]
   - Diversification = 93.4/100 (excellent)
   - Risk = Moderate (61.3% stocks, 38.7% bonds)
3. **Assess Concentration:** Largest position 44.7% (acceptable)
4. **Generate Recommendations:** Suggestion to maintain current allocation
5. **Return:** Full analysis narrative + metrics

**Response:**
```json
{
  "message": "## Portfolio Analysis Report\n\n### Overview\n- Total Value: $42,515.00\n- Holdings: 3\n- Total Return: +11.88%\n- Risk Level: MODERATE\n\n### Allocation\n- AAPL: 44.7% ($18,995.00)\n- BND: 38.7% ($16,460.00)\n- GOOGL: 16.6% ($7,060.00)\n\n### Diversification\n- Score: 93.4/100\n- Status: Excellent - Well diversified\n\n### Recommendations\nYour portfolio is well-balanced...",
  "structured_data": {
    "total_portfolio_value": 42515.00,
    "diversification_score": 93.4,
    "risk_level": "moderate",
    "allocation": [...],
    "asset_distribution": {
      "large_cap": 61.3,
      "bonds": 38.7
    }
  }
}
```

### Dependencies
- **Market Data Provider:** Current prices (via yFinance)
- **Portfolio Calculator:** Metrics computation
- **No LLM Required:** Pure calculation + narrative formatting

### Code Location
- File: `src/agents/portfolio_analysis.py`
- Entry Point: `get_portfolio_analysis_agent()`
- Calculator: `src/core/portfolio_calc.py`

### Key Capabilities
✅ Real-time price data (from yFinance)  
✅ Herfindahl diversification index  
✅ Asset class classification  
✅ Concentration risk warnings  
✅ Rebalancing suggestions  
✅ Gain/loss calculations  
✅ Risk level assessment  

### Metrics Explained

**Diversification Score (0-100):**
- 0-30: Concentrated (risky)
- 30-70: Adequate diversification
- 70-100: Excellent diversification
- Uses Herfindahl index: higher = more concentrated

**Risk Level:**
- LOW: <30% equities, high bond allocation
- MODERATE: 30-80% equities, balanced allocation
- HIGH: >80% equities or <30 diversification score

**Asset Classes:**
- Large cap: AAPL, MSFT, GOOGL, etc.
- Small cap: Smaller market cap stocks
- Bonds: BND, AGG, TLT, etc.
- International: Foreign stocks/funds
- Commodities: Gold, oil, etc.

---

## Market Analysis Agent (Phase 2A)

### Purpose
Provides real-time market data including stock quotes, historical trends, fundamental metrics, and multi-ticker comparisons.

### Use Cases
- "What's the price of Apple stock?"
- "Show me the 1-year trend for AAPL"
- "Compare AAPL, GOOGL, and MSFT"
- "What are the fundamentals for Tesla?"
- "Give me historical data for SPY"

### System Prompt
```
You are a market data and analysis assistant.

Your role is to:
1. Provide real-time stock quotes and prices
2. Retrieve historical price data
3. Display fundamental metrics
4. Compare multiple stocks
5. Format data in clear, readable format

Data types you provide:
- Current price with daily change
- Historical trends (direction, range, volatility)
- Fundamentals (P/E, EPS, market cap, dividend, etc.)
- Technical data (volume, 52-week high/low)
- Multi-ticker comparisons

Guidelines:
- Format prices with $ symbol
- Show percentage changes with direction (📈📉)
- Provide date ranges for historical data
- Include currency information
- Always note data recency
- Flag missing or delayed data
```

### Input Format
```python
query_data = {
    "tickers": List[str],              # ["AAPL", "GOOGL"]
    "analysis_type": str,              # "quote"|"historical"|"fundamentals"|"comparison"
    # Additional optional parameters
    "period": str,                     # "1d"|"1mo"|"3mo"|"1y"|"5y" (default: "1y")
    "interval": str                    # "1d"|"1wk"|"1mo" (default: "1d")
}
```

### Output Format
```python
AgentOutput(
    answer_text: str,  # Formatted market data narrative
    structured_data: {
        # For single quote:
        "ticker": str,
        "price": float,
        "currency": str,
        "change": float,
        "change_pct": float,
        "timestamp": str,
        
        # For historical:
        "period": str,
        "data": [
            {
                "date": str,
                "close": float,
                "high": float,
                "low": float,
                "volume": int
            }
        ],
        "min_price": float,
        "max_price": float,
        "trend": str,  # "upward"|"downward"
        
        # For fundamentals:
        "company_name": str,
        "pe_ratio": float,
        "eps": float,
        "market_cap": int,
        "dividend_yield": float,
        "52_week_high": float,
        "52_week_low": float,
        "sector": str,
        "industry": str,
        
        # For multiple quotes:
        "quotes": List[Dict],
        "total_count": int,
        "successful_count": int,
        "failed": List[Dict]
    },
    tool_calls_made: ["market_data_retrieval"],
    citations: []  # Market data is not cited
)
```

### Example Interactions

#### Example 1: Single Quote
**User Query:**
```
What's the current price of Apple?
```

**Response:**
```json
{
  "message": "## Market Quote - AAPL\n\n**Current Price:** $189.95\n**Change:** 📈 +2.45 (+1.31%)\n**Currency:** USD\n**Updated:** 2024-01-15T15:30:00Z",
  "structured_data": {
    "ticker": "AAPL",
    "price": 189.95,
    "currency": "USD",
    "change": 2.45,
    "change_pct": 1.31,
    "timestamp": "2024-01-15T15:30:00Z"
  }
}
```

#### Example 2: Historical Data
**User Query:**
```
Show me Apple's price history for the past year
```

**Response:**
```json
{
  "message": "## Historical Data - AAPL (1y)\n\n### Trend: UPWARD\n### Range: $124.17 - $199.62\n### Recent Close: $189.95\n\nThe stock has been upward over the past 1y. Price ranged from $124.17 to $199.62.",
  "structured_data": {
    "ticker": "AAPL",
    "period": "1y",
    "trend": "upward",
    "min_price": 124.17,
    "max_price": 199.62,
    "data": [
      {"date": "2023-01-15", "close": 150.0, "high": 152.0, "low": 148.0, "volume": 1000000},
      ...
      {"date": "2024-01-15", "close": 189.95, "high": 191.5, "low": 188.2, "volume": 1500000}
    ]
  }
}
```

#### Example 3: Multi-Ticker Comparison
**User Query:**
```
Compare AAPL, GOOGL, and MSFT
```

**Response:**
```json
{
  "message": "## Market Comparison\n\nQuotes Retrieved: 3/3\n\n- **AAPL**: $189.95 📈 +1.31%\n- **GOOGL**: $141.20 📉 -0.45%\n- **MSFT**: $378.50 📈 +2.10%",
  "structured_data": {
    "quotes": [
      {"ticker": "AAPL", "price": 189.95, "change": 2.45, "change_pct": 1.31},
      {"ticker": "GOOGL", "price": 141.20, "change": -0.65, "change_pct": -0.45},
      {"ticker": "MSFT", "price": 378.50, "change": 7.75, "change_pct": 2.10}
    ],
    "total_count": 3,
    "successful_count": 3,
    "failed": []
  }
}
```

#### Example 4: Fundamentals
**User Query:**
```
What are Apple's fundamentals?
```

**Response:**
```json
{
  "message": "## Fundamentals - Apple Inc. (AAPL)\n\n### Key Metrics\n- **P/E Ratio:** 28.5\n- **EPS:** $6.65\n- **Market Cap:** $2,800,000,000,000\n- **Dividend Yield:** 0.48%\n\n### 52-Week Range\n- **High:** $199.62\n- **Low:** $124.17\n- **Avg Volume:** 50,000,000\n\n### Classification\n- **Sector:** Technology\n- **Industry:** Consumer Electronics",
  "structured_data": {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "pe_ratio": 28.5,
    "eps": 6.65,
    "market_cap": 2800000000000,
    "dividend_yield": 0.48,
    "52_week_high": 199.62,
    "52_week_low": 124.17,
    "avg_volume": 50000000,
    "sector": "Technology",
    "industry": "Consumer Electronics"
  }
}
```

### Dependencies
- **Market Data Provider:** yFinance for real-time/historical data
- **No LLM Required:** Pure data retrieval + formatting
- **Natural Language Processing:** Regex-based ticker extraction from user message

### Code Location
- File: `src/agents/market_analysis.py`
- Entry Point: `get_market_analysis_agent()`
- Data Provider: `src/core/market_data.py`

### Key Capabilities
✅ Real-time quotes (via yFinance)  
✅ Historical data (1d to 5y periods)  
✅ Fundamental metrics  
✅ Ticker extraction from natural language  
✅ Multi-ticker batch processing  
✅ Error handling for invalid tickers  
✅ Change indicators (📈📉)  
✅ Volume and price range data  

### Analysis Types

| Type | Input | Output | Use Case |
|------|-------|--------|----------|
| `quote` | ticker | Current price + daily change | "What's AAPL trading at?" |
| `historical` | ticker + period | Price history + trend | "1-year trend for SPY?" |
| `fundamentals` | ticker | P/E, EPS, market cap, sector | "Apple's fundamentals?" |
| `comparison` | list of tickers | Side-by-side comparison | "Compare AAPL vs GOOGL" |

---

## Planned Agents

### Goal Planning Agent (Phase 2B)

**Purpose:** Projects financial goals and calculates required monthly savings

**Will Use:**
- Market Data Provider (for growth projections)
- Portfolio Calculator (for current position analysis)

**System Prompt:**
```
You are a financial goal planning assistant.

Your role is to:
1. Analyze current financial situation
2. Define and evaluate financial goals
3. Calculate required savings/returns
4. Project timelines
5. Suggest allocation strategies
6. Show risk vs reward tradeoffs

Key calculations:
- Time-based projections (years to goal)
- Monthly contribution calculations
- Growth rate assumptions
- Risk-adjusted returns
- Milestone tracking

Guidelines:
- Use realistic return assumptions (7% stocks, 3% bonds)
- Show sensitivity analysis (best/worst case)
- Adjust for inflation
- Flag unrealistic goals
- Suggest diverse approaches
```

### Tax Education Agent (Phase 2B)

**Purpose:** Answers tax-related financial questions using RAG

**Will Use:**
- RAG Retriever (tax-specific article filtering)
- LLM Provider (gpt-4o-mini)

**System Prompt:**
```
You are a tax education specialist.

Your role is to:
1. Explain tax concepts clearly
2. Discuss capital gains, losses, and reporting
3. Explain retirement accounts (401k, IRA, Roth)
4. Discuss tax-advantaged strategies
5. Provide tax timeline information

Important disclaimers:
- This is educational only, not tax advice
- Recommend consulting a CPA/tax professional
- Tax laws vary by location
- Tax situations are complex and individual

Key topics:
- Capital gains (short-term vs long-term)
- Tax-loss harvesting
- 401k and IRA contributions
- Roth conversions
- Quarterly estimated taxes
- Tax deductions for investors
```

### News Synthesizer Agent (Phase 2B)

**Purpose:** Aggregates market news and sentiment analysis

**Will Use:**
- Market Data Provider (for context)
- News API (future integration)

**System Prompt:**
```
You are a financial news synthesis assistant.

Your role is to:
1. Aggregate relevant market news
2. Assess sentiment (bullish/bearish/neutral)
3. Highlight impactful events
4. Connect news to market movements
5. Provide context and analysis

Data you synthesize:
- Breaking news and announcements
- Earnings surprises
- Economic data releases
- Market sentiment indicators
- Insider trading activity
- Analyst ratings changes

Guidelines:
- Separate fact from speculation
- Note confidence levels
- Provide balanced perspective
- Flag potential impacts
- Cite news sources
- Timestamp all updates
```

---

## Agent Integration Architecture

```
User Request
    ↓
[Intent Detection] (Future: LangGraph)
    ↓
    ├─→ Finance Q&A Agent
    │   ├─ RAGRetriever (Pinecone)
    │   └─ LLM (OpenAI)
    │
    ├─→ Market Analysis Agent
    │   └─ Market Data Provider (yFinance)
    │
    ├─→ Portfolio Analysis Agent
    │   ├─ Market Data Provider (yFinance)
    │   └─ Portfolio Calculator
    │
    ├─→ Goal Planning Agent (Phase 2B)
    │   ├─ Market Data Provider
    │   └─ Portfolio Calculator
    │
    ├─→ Tax Education Agent (Phase 2B)
    │   ├─ RAGRetriever (Pinecone)
    │   └─ LLM (OpenAI)
    │
    └─→ News Synthesizer Agent (Phase 2B)
        ├─ Market Data Provider
        └─ News API (Future)
    ↓
[Response Synthesizer] (Future: LangGraph)
    ↓
HTTP Response (FastAPI)
    ↓
Frontend Display
```

---

## Agent Output Format (Unified)

All agents return `AgentOutput`:

```python
@dataclass
class AgentOutput:
    answer_text: str                    # Human-readable narrative
    structured_data: Optional[Dict]     # Machine-readable metrics/data
    citations: List[Dict[str, str]]     # [{"title": "...", "source_url": "...", "category": "..."}]
    tool_calls_made: List[str]          # ["pinecone_retrieval", "openai_chat", ...]
```

**answer_text:** Formatted narrative for display
- Markdown formatting
- Clear sections with headers
- Examples and explanations
- Disclaimers where applicable

**structured_data:** JSON-serializable data for frontend
- Charts/visualizations
- Tables
- Metrics
- Programmatic access

**citations:** Source attribution
- Only for RAG-based agents
- Includes title, URL, category
- Used for transparency

**tool_calls_made:** Execution tracking
- Which modules were invoked
- For logging and monitoring
- Helps debug issues

---

## Example: Multi-Agent Conversation Flow (Future)

```
User: "I have $50k in AAPL and $30k in BND. How's my diversification and what 
should I do to reach a $100k retirement goal in 5 years?"

1. Intent Detection:
   - Intents: [portfolio_analysis, goal_planning]
   - Agents to invoke: [PortfolioAgent, GoalPlanningAgent]

2. Portfolio Analysis Agent:
   Input: holdings_data
   Output: {
     "allocation": [62.5% AAPL, 37.5% BND],
     "diversification_score": 65.0,
     "risk_level": "moderate"
   }

3. Goal Planning Agent:
   Input: current_value=$80k, goal=$100k, horizon=5 years, risk=moderate
   Output: {
     "monthly_contribution": 287.50,
     "projected_timeline": "4.8 years",
     "required_return": "5.2% annual"
   }

4. Response Synthesizer:
   Merge outputs → "Your portfolio is 65% diversified. To reach $100k 
   in 5 years, you need to contribute $287.50/month..."

5. Return to User:
   - Full analysis from Portfolio agent
   - Goal projection from Goal Planning agent
   - Integrated recommendation
```

---

## Testing Agents

### Run All Tests
```bash
# Phase 1 tests
/usr/bin/python3 test_backend.py

# Phase 2A tests
/usr/bin/python3 test_phase2a.py
```

### Test Individual Agents

```python
# Finance Q&A Agent
from src.agents.finance_qa import get_finance_qa_agent
agent = get_finance_qa_agent()
output = await agent.execute("What is an ETF?")

# Portfolio Analysis Agent
from src.agents.portfolio_analysis import get_portfolio_analysis_agent
agent = get_portfolio_analysis_agent()
output = await agent.execute(
    "Analyze portfolio",
    holdings_data={"holdings": [...]}
)

# Market Analysis Agent
from src.agents.market_analysis import get_market_analysis_agent
agent = get_market_analysis_agent()
output = await agent.execute(
    "What's Apple's price?",
    query_data={"tickers": ["AAPL"]}
)
```

---

## Summary Table

| Agent | Phase | Purpose | Primary Tool | Requires LLM | Citations |
|-------|-------|---------|--------------|-------------|-----------|
| Finance Q&A | 1 | Education Q&A | Pinecone RAG | Yes | Yes |
| Portfolio Analysis | 2A | Portfolio Metrics | Portfolio Calc | No | No |
| Market Analysis | 2A | Stock Data | yFinance | No | No |
| Goal Planning | 2B | Savings Projections | Market Data + Calc | Yes | No |
| Tax Education | 2B | Tax Q&A | Pinecone RAG | Yes | Yes |
| News Synthesizer | 2B | News Aggregation | News API | Yes | Yes |

---

**Status:** 3 Agents Built ✅ | 3 Agents Designed 📋 | Ready for Phase 2B 🚀
