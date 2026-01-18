"""Dividend data endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yfinance as yf
from datetime import datetime, timedelta
from src.core.logger import get_logger
from src.core.config import Config

logger = get_logger(__name__, Config.LOG_LEVEL)
router = APIRouter()


class DividendInfo(BaseModel):
    """Dividend information for a single holding."""
    ticker: str
    yield_pct: float
    frequency: str
    next_pay_date: str
    annual_dividend_per_share: float


class DividendRequest(BaseModel):
    """Request for dividend data."""
    tickers: List[str]


class DividendResponse(BaseModel):
    """Response with dividend data."""
    dividends: Dict[str, DividendInfo]
    timestamp: str


# Mock fallback dividend data when yfinance doesn't have real data
MOCK_DIVIDEND_DATA = {
    "AAPL": {
        "yield": 0.5,
        "frequency": "Quarterly",
        "next_pay_date": "2026-02-15",
        "annual_dividend_per_share": 0.94,
    },
    "MSFT": {
        "yield": 0.84,
        "frequency": "Quarterly",
        "next_pay_date": "2026-02-20",
        "annual_dividend_per_share": 3.17,
    },
    "JPM": {
        "yield": 2.5,
        "frequency": "Quarterly",
        "next_pay_date": "2026-01-20",
        "annual_dividend_per_share": 4.95,
    },
    "JNJ": {
        "yield": 2.8,
        "frequency": "Quarterly",
        "next_pay_date": "2026-03-01",
        "annual_dividend_per_share": 4.42,
    },
    "BND": {
        "yield": 4.2,
        "frequency": "Monthly",
        "next_pay_date": "2026-01-31",
        "annual_dividend_per_share": 3.36,
    },
    "AGG": {
        "yield": 3.8,
        "frequency": "Monthly",
        "next_pay_date": "2026-01-31",
        "annual_dividend_per_share": 3.61,
    },
    "PYPL": {
        "yield": 0,
        "frequency": "None",
        "next_pay_date": "N/A",
        "annual_dividend_per_share": 0,
    },
}


def get_dividend_info(ticker: str) -> Dict[str, Any]:
    """
    Fetch real dividend information for a ticker.
    Falls back to mock data if yfinance fails.
    """
    try:
        ticker_upper = ticker.upper()
        ticker_obj = yf.Ticker(ticker_upper)
        
        # Get dividend info from yfinance
        info = ticker_obj.info or {}
        
        # Extract dividend data
        dividend_yield = info.get('dividendYield', 0) * 100  # Convert to percentage
        annual_dividend = info.get('trailingAnnualDividendRate', 0)
        
        # Determine frequency (default quarterly if not available)
        frequency = "Quarterly"
        if dividend_yield == 0:
            frequency = "None"
        
        # Get next dividend date (use estimate if not available)
        next_pay_date = info.get('exDividendDate', datetime.now() + timedelta(days=90)).isoformat()
        
        if annual_dividend > 0 or dividend_yield > 0:
            logger.info(f"✅ Real dividend data for {ticker_upper}: {dividend_yield:.2f}% yield")
            return {
                "yield": round(dividend_yield, 2),
                "frequency": frequency,
                "next_pay_date": next_pay_date,
                "annual_dividend_per_share": round(annual_dividend, 2),
            }
        else:
            # Use mock fallback if no real data
            if ticker_upper in MOCK_DIVIDEND_DATA:
                mock = MOCK_DIVIDEND_DATA[ticker_upper]
                logger.info(f"⚠️  Using mock dividend data for {ticker_upper}: {mock['yield']}% yield")
                return mock
            else:
                logger.warning(f"No dividend data found for {ticker_upper}")
                return {
                    "yield": 0,
                    "frequency": "None",
                    "next_pay_date": "N/A",
                    "annual_dividend_per_share": 0,
                }
    except Exception as e:
        logger.warning(f"Failed to fetch dividend data for {ticker}: {str(e)}")
        # Use mock fallback
        ticker_upper = ticker.upper()
        if ticker_upper in MOCK_DIVIDEND_DATA:
            mock = MOCK_DIVIDEND_DATA[ticker_upper]
            logger.info(f"⚠️  Using mock dividend data for {ticker_upper} (yfinance failed)")
            return mock
        return {
            "yield": 0,
            "frequency": "None",
            "next_pay_date": "N/A",
            "annual_dividend_per_share": 0,
        }


@router.post("/dividends/info")
async def get_dividends(request: DividendRequest) -> DividendResponse:
    """
    Get real-time dividend information for multiple tickers.
    Uses yFinance with mock fallback for testing.
    
    Args:
        request: DividendRequest with list of tickers
        
    Returns:
        DividendResponse with dividend info for all tickers
    """
    try:
        dividends = {}
        
        for ticker in request.tickers:
            try:
                div_info = get_dividend_info(ticker)
                dividends[ticker.upper()] = DividendInfo(
                    ticker=ticker.upper(),
                    yield_pct=div_info["yield"],
                    frequency=div_info["frequency"],
                    next_pay_date=div_info["next_pay_date"],
                    annual_dividend_per_share=div_info["annual_dividend_per_share"],
                )
            except Exception as e:
                logger.warning(f"Failed to fetch dividend for {ticker}: {str(e)}")
                # Add empty entry for this ticker
                dividends[ticker.upper()] = DividendInfo(
                    ticker=ticker.upper(),
                    yield_pct=0,
                    frequency="None",
                    next_pay_date="N/A",
                    annual_dividend_per_share=0,
                )
        
        if not dividends:
            raise HTTPException(status_code=500, detail="Failed to fetch dividend data")
        
        logger.info(f"Dividend data fetched for {len(dividends)} tickers")
        return DividendResponse(
            dividends=dividends,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch dividends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dividends: {str(e)}")
