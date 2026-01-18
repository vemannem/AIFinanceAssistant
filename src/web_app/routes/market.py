"""Market data endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yfinance as yf
from datetime import datetime, timedelta
from src.core.market_data import MarketDataProvider
from src.core.logger import get_logger
from src.core.config import Config

logger = get_logger(__name__, Config.LOG_LEVEL)
router = APIRouter()

# Initialize market data provider
market_provider = MarketDataProvider()


class QuoteResponse(BaseModel):
    """Quote response with market and dividend data."""
    ticker: str
    price: float
    currency: str
    change: float
    change_pct: float
    dividend_yield: float
    dividend_frequency: str
    next_dividend_date: str
    annual_dividend_per_share: float
    timestamp: str


class QuotesRequest(BaseModel):
    """Request for multiple quotes."""
    tickers: List[str]


class QuotesResponse(BaseModel):
    """Response with multiple quotes and dividends."""
    quotes: Dict[str, QuoteResponse]
    timestamp: str


# Mock dividend data fallback
MOCK_DIVIDEND_DATA = {
    "AAPL": {"yield": 0.5, "frequency": "Quarterly", "next_date": "2026-02-15", "annual_per_share": 0.94},
    "MSFT": {"yield": 0.84, "frequency": "Quarterly", "next_date": "2026-02-20", "annual_per_share": 3.17},
    "JPM": {"yield": 2.5, "frequency": "Quarterly", "next_date": "2026-01-20", "annual_per_share": 4.95},
    "JNJ": {"yield": 2.8, "frequency": "Quarterly", "next_date": "2026-03-01", "annual_per_share": 4.42},
    "BND": {"yield": 4.2, "frequency": "Monthly", "next_date": "2026-01-31", "annual_per_share": 3.36},
    "AGG": {"yield": 3.8, "frequency": "Monthly", "next_date": "2026-01-31", "annual_per_share": 3.61},
    "PYPL": {"yield": 0, "frequency": "None", "next_date": "N/A", "annual_per_share": 0},
}


def get_dividend_info(ticker: str) -> Dict[str, Any]:
    """Get dividend info for ticker with fallback to mock data."""
    try:
        ticker_upper = ticker.upper()
        ticker_obj = yf.Ticker(ticker_upper)
        info = ticker_obj.info or {}
        
        dividend_yield = (info.get('dividendYield', 0) * 100)
        annual_dividend = info.get('trailingAnnualDividendRate', 0)
        frequency = "Quarterly" if dividend_yield > 0 else "None"
        next_date = info.get('exDividendDate', "N/A")
        
        if annual_dividend > 0 or dividend_yield > 0:
            logger.info(f"✅ Real dividend data for {ticker_upper}: {dividend_yield:.2f}%")
            return {
                "yield": round(dividend_yield, 2),
                "frequency": frequency,
                "next_date": next_date,
                "annual_per_share": round(annual_dividend, 2),
            }
        elif ticker_upper in MOCK_DIVIDEND_DATA:
            mock = MOCK_DIVIDEND_DATA[ticker_upper]
            logger.info(f"⚠️  Using mock dividend data for {ticker_upper}")
            return mock
        else:
            return {"yield": 0, "frequency": "None", "next_date": "N/A", "annual_per_share": 0}
    except Exception as e:
        logger.warning(f"Failed to fetch dividend for {ticker}: {str(e)}")
        ticker_upper = ticker.upper()
        if ticker_upper in MOCK_DIVIDEND_DATA:
            return MOCK_DIVIDEND_DATA[ticker_upper]
        return {"yield": 0, "frequency": "None", "next_date": "N/A", "annual_per_share": 0}


@router.get("/market/quote/{ticker}")
async def get_quote(ticker: str) -> QuoteResponse:
    """
    Get current quote for a ticker including market and dividend data.
    
    Args:
        ticker: Stock ticker (e.g., "AAPL")
        
    Returns:
        QuoteResponse with price and dividend info
    """
    try:
        # Get market price
        quote = market_provider.get_quote(ticker.upper())
        
        # Get dividend data
        dividend = get_dividend_info(ticker.upper())
        
        logger.info(f"Quote fetched for {ticker}: ${quote['price']}")
        return QuoteResponse(
            ticker=quote['ticker'],
            price=quote['price'],
            currency=quote['currency'],
            change=quote['change'],
            change_pct=quote['change_pct'],
            dividend_yield=dividend['yield'],
            dividend_frequency=dividend['frequency'],
            next_dividend_date=dividend['next_date'],
            annual_dividend_per_share=dividend['annual_per_share'],
            timestamp=quote['timestamp']
        )
    except Exception as e:
        logger.error(f"Failed to fetch quote for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {str(e)}")


@router.post("/market/quotes")
async def get_quotes(request: QuotesRequest) -> QuotesResponse:
    """
    Get current quotes for multiple tickers with market and dividend data.
    
    Args:
        request: QuotesRequest with list of tickers
        
    Returns:
        QuotesResponse with all market and dividend data
    """
    try:
        quotes = {}
        for ticker in request.tickers:
            try:
                # Get market price
                quote = market_provider.get_quote(ticker.upper())
                
                # Get dividend data
                dividend = get_dividend_info(ticker.upper())
                
                quotes[ticker.upper()] = QuoteResponse(
                    ticker=quote['ticker'],
                    price=quote['price'],
                    currency=quote['currency'],
                    change=quote['change'],
                    change_pct=quote['change_pct'],
                    dividend_yield=dividend['yield'],
                    dividend_frequency=dividend['frequency'],
                    next_dividend_date=dividend['next_date'],
                    annual_dividend_per_share=dividend['annual_per_share'],
                    timestamp=quote['timestamp']
                )
            except Exception as e:
                logger.warning(f"Failed to fetch quote for {ticker}: {str(e)}")
                # Continue with other tickers
        
        if not quotes:
            raise HTTPException(status_code=500, detail="Failed to fetch any quotes")
        
        logger.info(f"Quotes fetched for {len(quotes)} tickers with dividend data")
        return QuotesResponse(
            quotes=quotes,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        logger.error(f"Failed to fetch quotes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quotes: {str(e)}")
